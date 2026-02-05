# SARK Implementation Plan: Closing GRID v0.1 Compliance Gaps

**Date:** February 5, 2026
**Baseline:** SARK v1.6.0, grid-core (current main)
**Target:** Full GRID v0.1 structural compliance
**Companion Document:** `docs/SARK_COMPLIANCE_REVIEW.md`

This plan is ordered by dependency: later phases depend on earlier ones. Within
each phase, work items are independent and can be parallelized.

---

## Phase 1: Core Abstractions

Everything else builds on these. The spec defines five first-class objects.
SARK currently has three (User, MCPServer, AuditEvent) and stores the other
two as untyped strings (Action) or opaque blobs (Policy rules). This phase
adds the missing structure.

### 1.1 Principal Model

**Problem:** SARK's `User` model has no `type` field. Non-human principals
(AI agents, services, devices) are stored as User rows with no way to
distinguish them. The spec requires `type`, `identity_token`, and
`revoked_at`.

**Changes:**

Add a `PrincipalType` enum to `src/sark/models/user.py`:

```python
class PrincipalType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    DEVICE = "device"
```

Add columns to the `User` model (or rename to `Principal`):

| Column | Type | Default | Notes |
|--------|------|---------|-------|
| `principal_type` | `Enum(PrincipalType)` | `HUMAN` | Indexed. Default preserves backward compat for existing rows. |
| `identity_token_type` | `String` | `null` | `"jwt"`, `"api_key"`, `"certificate"`, `"oidc"`. Tracks how this principal authenticates. |
| `revoked_at` | `DateTime(timezone=True)` | `null` | Null means active. Set on revocation. |

Alembic migration `008_add_principal_fields.py`:
- `ALTER TABLE users ADD COLUMN principal_type ...`
- `ALTER TABLE users ADD COLUMN identity_token_type ...`
- `ALTER TABLE users ADD COLUMN revoked_at ...`
- `UPDATE users SET principal_type = 'human' WHERE principal_type IS NULL`
- Add index on `principal_type`.

Update `extra_metadata` convention: document that `department`,
`clearance_level`, `region`, and other ABAC attributes go in
`extra_metadata`. The spec's `attributes` object maps to this field. No
schema change needed, but add a Pydantic validator or helper that reads
these fields out for policy evaluation input.

Update the OPA input builder (in `opa_client.py` or wherever the
`AuthorizationInput` dict is constructed) to include:

```python
"principal": {
    "id": user.id,
    "type": user.principal_type.value,
    "attributes": {
        "role": user.role,
        "teams": [t.name for t in user.teams],
        **user.extra_metadata,
    }
}
```

**Not changing:** The table stays named `users`. A full rename to
`principals` is cosmetic and would break every foreign key and query. The
column additions achieve spec compliance without that churn.

### 1.2 Action Model

**Problem:** No Action abstraction exists. Action is a freeform string like
`"tool:invoke"` passed to OPA. The spec requires a structured object with
`resource_id`, `operation` (enum), `parameters`, and `context`.

**Changes:**

Create a Pydantic model (not a database table — actions are transient
request objects, not persisted entities):

```python
# src/sark/models/action.py

class OperationType(str, enum.Enum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    CONTROL = "control"
    MANAGE = "manage"
    AUDIT = "audit"

class ActionContext(BaseModel):
    timestamp: datetime
    ip_address: str | None = None
    user_agent: str | None = None
    request_id: str | None = None
    environment: str | None = None  # dev, staging, prod

class Action(BaseModel):
    resource_id: str
    operation: OperationType
    parameters: dict | None = None
    context: ActionContext
```

Update every call site that currently passes `action` as a string. The main
entry points are:

1. **`api/routers/policy.py`** — `PolicyEvaluationRequest` schema. Change
   `action: str` to `action: Action`. This is a breaking API change; version
   it behind `/api/v2/policy/evaluate` and keep the v1 endpoint accepting
   strings with a deprecation warning.

2. **`api/routers/gateway.py`** — Gateway authorization requests. Same
   treatment: accept structured Action, fall back to string parsing.

3. **`services/policy/opa_client.py`** — The `AuthorizationInput` dict
   builder. Currently constructs `{"action": "tool:invoke"}`. Change to:

   ```python
   "action": {
       "resource_id": action.resource_id,
       "operation": action.operation.value,
       "parameters": action.parameters,
   }
   ```

4. **OPA policies** — Existing Rego policies that match on
   `input.action == "tool:invoke"` must be updated to match on
   `input.action.operation == "execute"`. Ship updated example policies.

**Migration path:** The v1 API can parse legacy string actions into the new
model. `"tool:invoke"` maps to `OperationType.EXECUTE`, `"server:register"`
maps to `OperationType.MANAGE`, etc. Build a `parse_legacy_action()` helper
for backward compatibility.

### 1.3 Resource Model

**Problem:** v1.x only has `MCPServer`. The spec requires a generic Resource
with `type` (tool | data | service | device), `classification`, `provider_id`,
`parameters_schema`, and `owner`/`managers` as full objects.

**Changes:**

The v2 `Resource` model in `models/base.py` already exists but is missing
fields. Add:

| Column | Type | Notes |
|--------|------|-------|
| `resource_type` | `Enum(ResourceType)` | `tool`, `data`, `service`, `device`, `infrastructure` |
| `provider_id` | `String` | Who provides this resource. |
| `classification` | `String` | `Public`, `Internal`, `Confidential`, `Secret`. |
| `parameters_schema` | `JSON` | JSON Schema for input validation. |
| `owner_id` | `UUID FK → users` | Owner principal. |

Add a `resource_managers` association table for the many-to-many
owner/manager relationship:

```python
resource_managers = Table(
    "resource_managers",
    Base.metadata,
    Column("resource_id", String, ForeignKey("resources.id", ondelete="CASCADE")),
    Column("user_id", UUID, ForeignKey("users.id", ondelete="CASCADE")),
)
```

Write an Alembic migration that:
- Adds the new columns to `resources`.
- Creates the `resource_managers` table.
- Adds a data migration that copies existing `MCPServer` rows into
  `resources` with `resource_type = 'tool'`, `classification = 'Internal'`,
  and `provider_id` set from the server name.

**MCPServer coexistence:** Keep `MCPServer` for MCP-specific fields
(transport, command, mcp_version, health_endpoint). Add a nullable
`resource_id` FK to `MCPServer` that links it to the generic `Resource`
row. New code paths use `Resource`; legacy code paths continue to work.

### 1.4 Policy Metadata Layer

**Problem:** Policies are stored as raw Rego text. The spec defines
structured Rule objects with PrincipalMatcher, ResourceMatcher,
ActionMatcher, Condition, and Constraint.

**Approach:** Do not replace Rego — it works and OPA needs it. Add a
metadata layer alongside the Rego that describes the policy's structure in
machine-readable form. This enables introspection, composition, and UI
tooling without changing the evaluation engine.

**Changes:**

Add a `PolicyRule` model:

```python
# src/sark/models/policy.py

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID, primary_key=True, default=uuid4)
    policy_version_id = Column(UUID, ForeignKey("policy_versions.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    effect = Column(String, nullable=False)  # "allow", "deny", "constrain"

    # Matchers stored as JSON arrays of {type, value} objects
    principal_matchers = Column(JSON, default=list)
    resource_matchers = Column(JSON, default=list)
    action_matchers = Column(JSON, default=list)

    # Conditions and constraints as JSON arrays
    conditions = Column(JSON, default=list)
    constraints = Column(JSON, default=list)

    metadata_ = Column("metadata", JSON, default=dict)
```

Add relationship to `PolicyVersion`:

```python
class PolicyVersion:
    ...
    rules = relationship("PolicyRule", cascade="all, delete-orphan")
```

Add `last_updated` to `Policy`:

```python
class Policy:
    ...
    # updated_at already exists, serves as last_updated
```

**Workflow:** When a policy is created or updated, the API accepts either:
- Raw Rego (existing behavior), or
- A structured rule definition that is both stored as `PolicyRule` rows and
  compiled to Rego for OPA evaluation.

For existing policies, add a `parse_rego_metadata()` utility that does
best-effort extraction of matchers from common Rego patterns. This won't
cover every case but handles the standard RBAC/ABAC patterns from the
example policies.

### 1.5 Audit Event Fields

**Problem:** `AuditEvent` is missing 11 fields the spec requires.

**Changes:**

Add columns to `AuditEvent`:

| Column | Type | Notes |
|--------|------|-------|
| `principal_type` | `String` | `human`, `agent`, `service`, `device` |
| `principal_attributes` | `JSON` | Role, teams, department at time of event |
| `resource_type` | `String` | `tool`, `data`, `service`, `device` |
| `action_operation` | `String` | `read`, `write`, `execute`, etc. |
| `action_parameters` | `JSON` | Sanitized copy of request parameters |
| `policy_version` | `Integer` | Version of the policy that made the decision |
| `environment` | `String` | `development`, `staging`, `production` |
| `success` | `Boolean` | Whether the action completed |
| `error_message` | `Text` | Error details if failed |
| `latency_ms` | `Float` | Response time |
| `cost` | `Numeric(10,6)` | Cost attributed to this action |
| `retention_until` | `DateTime` | When this event can be deleted |

Alembic migration: `ADD COLUMN` for each. All nullable to avoid breaking
existing rows. Backfill `principal_type = 'human'` and
`environment = 'production'` for existing data.

Update `AuditService.log_event()` to accept and populate these fields.
Update `log_authorization_decision()` to pass the structured Action and
Principal objects through to the event.

---

## Phase 2: Authentication Gaps

These are independent of each other and can be worked in parallel.

### 2.1 Wire MFA into Auth Flow

**Problem:** TOTP, SMS, Push, and Email MFA implementations exist but are
not called from any login endpoint.

**Changes:**

Add MFA challenge/response endpoints:

```
POST /api/auth/mfa/challenge  — Initiates MFA (returns method + session token)
POST /api/auth/mfa/verify     — Verifies MFA code, completes login
```

Modify the login flow in `api/routers/auth.py`:

1. After successful password/OIDC/LDAP authentication, check if the user
   has MFA enabled (add `mfa_enabled: bool` and `mfa_method: str` columns
   to `User`, or store in `extra_metadata`).
2. If MFA required, return a partial session token (not a full JWT) with
   `{"status": "mfa_required", "mfa_session": "...", "methods": ["totp"]}`.
3. Client calls `/api/auth/mfa/verify` with the code.
4. On success, issue the full JWT/session.

Add MFA enforcement logic based on the spec's requirements:
- All human principals with MFA enabled.
- Critical resource access (check sensitivity_level in the policy
  evaluation response).
- Configurable via `MFA_REQUIRED_FOR_SENSITIVITY` setting.

### 2.2 SAML Signature Verification

**Problem:** SAML ACS endpoint parses XML but does not verify signatures,
conditions, audience, or issuer.

**Changes in `services/auth/providers/saml.py`:**

1. After base64-decoding the SAMLResponse, verify the XML signature using
   the IdP's X.509 certificate (already available in settings as
   `saml_idp_x509_cert`). Use `signxml` or `xmlsec1` library.

2. Check assertion conditions:
   - `NotBefore <= now <= NotOnOrAfter`
   - `AudienceRestriction` contains our SP entity ID.

3. Validate `Issuer` matches `saml_idp_entity_id`.

4. Wire the `saml_want_assertions_signed` and `saml_want_messages_signed`
   settings (currently dead config) to actually enforce verification.

5. Complete the ACS endpoint TODO: create a session and set the cookie
   after successful verification, then redirect to `RelayState`.

### 2.3 OIDC PKCE

**Problem:** PKCE parameters are accepted but never generated or sent.

**Changes in `services/auth/providers/oidc.py`:**

1. During `get_authorization_url()`, generate a `code_verifier`
   (cryptographic random, 43-128 characters) and derive `code_challenge`
   (S256 hash).

2. Include `code_challenge` and `code_challenge_method=S256` in the
   authorization URL query parameters.

3. Store `code_verifier` in Redis alongside the OIDC state.

4. During token exchange in the callback, include `code_verifier` in the
   token request body.

### 2.4 LDAP Connection Pooling

**Problem:** Each LDAP operation creates a new connection.

**Changes in `services/auth/providers/ldap.py`:**

Replace per-operation `Connection()` calls with an `ldap3.ServerPool` +
`ldap3.Connection` pool. Use `ldap3`'s built-in connection strategy
`REUSABLE` which maintains a pool of connections:

```python
from ldap3 import Server, Connection, ServerPool, REUSABLE

server = Server(self.server_url, use_ssl=self.use_ssl)
self._pool = Connection(
    server,
    user=self.bind_dn,
    password=self.bind_password,
    client_strategy=REUSABLE,
    pool_size=10,
    pool_lifetime=300,
)
```

This replaces `asyncio.to_thread(Connection(...))` per request with a
shared pool.

---

## Phase 3: SIEM and Audit Pipeline

### 3.1 Wire SIEM Forwarding

**Problem:** `_forward_to_siem()` in `audit_service.py` is a TODO that sets
a timestamp and returns without calling any provider.

**Changes:**

The SIEM provider implementations already exist under
`services/audit/siem/`. The fix is to instantiate the correct provider at
service init and call it:

```python
# In AuditService.__init__()
if settings.siem_enabled:
    if settings.siem_provider == "splunk":
        from sark.services.audit.siem.splunk import SplunkForwarder
        self._siem = SplunkForwarder(settings)
    elif settings.siem_provider == "datadog":
        from sark.services.audit.siem.datadog import DatadogForwarder
        self._siem = DatadogForwarder(settings)
    else:
        self._siem = None

# In _forward_to_siem()
async def _forward_to_siem(self, event: AuditEvent) -> None:
    if self._siem is None:
        return
    try:
        await self._siem.send(event)
        event.siem_forwarded = datetime.now(UTC)
        await self.db.commit()
    except Exception as e:
        logger.error("SIEM forwarding failed", error=str(e), event_id=str(event.id))
```

Remove the Kafka reference from documentation until an implementation
exists, or implement a Kafka forwarder using `aiokafka`.

### 3.2 Audit Retention Enforcement

**Problem:** The TimescaleDB retention policy is commented out in migration
004. The spec requires configurable retention with a `retention_until`
field.

**Changes:**

1. Uncomment the retention policy in migration 004 or add a new migration
   that enables it:
   ```sql
   SELECT add_retention_policy('audit_events', INTERVAL '365 days');
   ```

2. When creating audit events, set `retention_until` based on configuration:
   ```python
   event.retention_until = datetime.now(UTC) + timedelta(
       days=settings.audit_retention_days  # default 365
   )
   ```

3. Add a setting `AUDIT_RETENTION_DAYS` (default: 365 for enterprise, 90
   for home).

---

## Phase 4: Protocol Adapters

### 4.1 MCP Tool Invocation

**Problem:** `MCPAdapter.invoke()` returns `{"stubbed": True}`.

**Changes:**

The adapter needs to actually call the MCP server. The implementation
differs by transport:

**HTTP transport:**
```python
async def _invoke_http(self, resource, capability, request):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{resource.endpoint}/tools/call",
            json={
                "jsonrpc": "2.0",
                "method": "tools/call",
                "params": {
                    "name": capability.name,
                    "arguments": request.arguments,
                },
                "id": request.context.get("request_id", str(uuid4())),
            },
            timeout=30.0,
        )
        result = response.json()
        return InvocationResult(
            success="error" not in result,
            result=result.get("result"),
            error=result.get("error", {}).get("message"),
            metadata={"adapter": "mcp", "transport": "http"},
        )
```

**SSE transport:** Similar to HTTP but using an SSE client to send the
request and read the streamed response.

**stdio transport:** Requires process lifecycle management. Launch the MCP
server process (using `command` from MCPServer), communicate via
stdin/stdout JSON-RPC. This is the most complex transport; consider using
the `mcp` Python SDK's `StdioServerParameters` if available, or implement a
process pool.

### 4.2 MCP stdio Capability Discovery

**Problem:** `_get_capabilities_stdio()` returns an empty list.

**Changes:**

Implement process management for stdio MCP servers:

```python
async def _get_capabilities_stdio(self, resource):
    process = await asyncio.create_subprocess_exec(
        *shlex.split(resource.endpoint),  # command stored in endpoint
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Send initialize + tools/list via JSON-RPC over stdin
    request = json.dumps({
        "jsonrpc": "2.0",
        "method": "tools/list",
        "params": {},
        "id": 1,
    }) + "\n"
    stdout, _ = await asyncio.wait_for(
        process.communicate(request.encode()),
        timeout=10.0,
    )
    tools = json.loads(stdout)
    return self._parse_mcp_tools(resource, tools.get("result", {}).get("tools", []))
```

Add process pooling for long-lived stdio servers (optional optimization).

### 4.3 MCP Streaming

**Problem:** `invoke_streaming()` yields placeholder events.

**Changes:**

Implement SSE-based streaming for HTTP/SSE transports. For stdio, stream
by reading stdout line-by-line. The existing stub already has the right
event structure (`start`, `data`, `end`); replace the static yields with
actual reads from the transport.

---

## Phase 5: Rust Integration (grid-core)

### 5.1 Wire grid-core into SARK

**Problem:** `factory.py` has `RustOPAClient` and `RustPolicyCache` stubs
that raise `NotImplementedError`. The real code is in the `grid-core` repo.

**Changes:**

1. Add `grid-core` as a dependency. In `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   rust = ["grid-core"]
   ```

2. Update `factory.py` to import from `grid_core`:
   ```python
   try:
       from grid_core import RustOPAEngine, RustCache
       RUST_AVAILABLE = True
   except ImportError:
       RUST_AVAILABLE = False
   ```

3. Replace the `RustOPAClient` stub with the existing
   `rust_opa_client.py` implementation (457 lines, already written for
   this purpose). Update its import from `sark.sark_opa` to `grid_core`.

4. Replace the `RustPolicyCache` stub with the existing `rust_cache.py`
   implementation (509 lines). Update its import similarly.

5. Remove the `NotImplementedError` stubs entirely.

6. Verify the feature flag routing still works: `RUST_ENABLED=true` env
   var enables Rust, with fallback to Python on error.

### 5.2 Port Benchmarks to grid-core

**Problem:** grid-core has benchmark infrastructure (Criterion in
Cargo.toml) but the actual benchmark files from SARK were not ported.

**Changes:**

Copy `sark/rust/sark-opa/benches/opa_benchmarks.rs` (308 lines) to
`grid-core/crates/grid-opa/benches/` with namespace updates.

Copy `sark/rust/sark-cache/benches/cache_benchmarks.rs` (261 lines) to
`grid-core/crates/grid-cache/benches/` with namespace updates.

Uncomment the `[[bench]]` sections in both `Cargo.toml` files.

---

## Phase 6: Specification Alignment Fixes

These are smaller items that round out compliance.

### 6.1 Secret Scanner Pattern Count

**Problem:** Claims 25+ patterns, actual is 22.

**Changes:** Add patterns for:
- Azure Storage Account Keys
- Heroku API Key
- Mailgun API Key

This brings the count to 25.

### 6.2 Remove Duplicate API Key Module

**Problem:** `api_key.py` (in-memory stub) and `api_keys.py` (real
DB-backed implementation) both exist.

**Changes:** Delete `api_key.py`. Verify no imports reference it. If any
do, point them at `api_keys.py`.

### 6.3 Resolve Auth Router TODOs

**Problem:** `get_settings()` and `get_session_service()` have TODO comments
about getting values from app state instead of constructing them inline.

**Changes:** Use FastAPI's dependency injection properly. Store service
instances in `app.state` during lifespan startup (this is likely already
done for other services) and read them via `request.app.state`.

### 6.4 Update Gap Analysis Document

**Problem:** `GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md` claims 95%+
compliance. This should reflect reality.

**Changes:** After completing all phases above, update the gap analysis
with accurate compliance percentages based on the methodology in
`SARK_COMPLIANCE_REVIEW.md`. Until all phases are complete, the document
should acknowledge the gaps identified in this plan.

---

## Phase Summary

| Phase | Focus | Items | Dependencies |
|-------|-------|-------|-------------|
| 1 | Core abstractions | 5 | None (do first) |
| 2 | Authentication | 4 | Phase 1.1 (MFA needs principal_type) |
| 3 | SIEM / audit pipeline | 2 | Phase 1.5 (needs new audit fields) |
| 4 | Protocol adapters | 3 | Phase 1.2, 1.3 (needs Action + Resource) |
| 5 | Rust integration | 2 | None (independent) |
| 6 | Cleanup / alignment | 4 | Phases 1-5 |

Phases 1 and 5 have no dependencies and should start first. Phase 5 is
small and self-contained. Phase 1 is the critical path — phases 2, 3, and
4 all depend on the new models it introduces.

```
Phase 1 ─────────────────────────────────►
Phase 5 ───────►
              Phase 2 ──────────────────►
                   Phase 3 ────────────►
                        Phase 4 ───────►
                                  Phase 6 ──►
```

---

## Migration Risk Notes

**Database migrations (Phases 1, 3):** All new columns are nullable with
defaults. No existing data is destroyed. Migrations can be applied to a
running system with zero downtime (ALTER TABLE ADD COLUMN is non-blocking
in PostgreSQL).

**API breaking changes (Phase 1.2):** The Action model changes the policy
evaluation API. Version this as v2 and keep v1 with a deprecation path.

**OPA policy updates (Phase 1.2):** Changing the Action from a string to a
structured object changes the OPA input schema. All deployed Rego policies
that match on `input.action` as a string must be updated. Ship a migration
guide and updated example policies.

**Rust dependency (Phase 5):** If grid-core is not published to PyPI, SARK
will need to reference it as a git dependency or build it locally. Document
the build process (`maturin develop --release`).
