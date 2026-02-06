# SARK Implementation Plan: Closing GRID v0.1 Compliance Gaps

**Date:** February 5, 2026
**Baseline:** SARK v1.6.0, grid-core (current main)
**Target:** Full GRID v0.1 structural compliance
**Companion Document:** `docs/SARK_COMPLIANCE_REVIEW.md`

There are no extant SARK installations. All changes are greenfield — no
migrations, no deprecation paths, no backward compatibility concerns.

This plan is ordered by dependency: later phases depend on earlier ones.
Within each phase, work items are independent and can be parallelized.

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

Rename the table from `users` to `principals` and the model from `User` to
`Principal`. Update all foreign keys, queries, and imports across the
codebase.

Add a `PrincipalType` enum:

```python
class PrincipalType(str, enum.Enum):
    HUMAN = "human"
    AGENT = "agent"
    SERVICE = "service"
    DEVICE = "device"
```

Add columns:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `principal_type` | `Enum(PrincipalType)` | No | Indexed. |
| `identity_token_type` | `String` | No | `"jwt"`, `"api_key"`, `"certificate"`, `"oidc"` |
| `revoked_at` | `DateTime(timezone=True)` | Yes | Null means active. |

Document that `department`, `clearance_level`, `region`, and other ABAC
attributes go in the existing `extra_metadata` JSON column. The spec's
`attributes` object maps to this field. Add a Pydantic helper that reads
these out for policy evaluation:

```python
def to_policy_input(self) -> dict:
    return {
        "id": str(self.id),
        "type": self.principal_type.value,
        "attributes": {
            "role": self.role,
            "teams": [t.name for t in self.teams],
            **(self.extra_metadata or {}),
        },
    }
```

Update the OPA input builder in `opa_client.py` to use this method instead
of manually constructing the principal dict.

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

Update every call site that currently passes `action` as a string:

1. **`api/routers/policy.py`** — Change `PolicyEvaluationRequest.action`
   from `str` to `Action`.

2. **`api/routers/gateway.py`** — Gateway authorization requests. Accept
   structured `Action`.

3. **`services/policy/opa_client.py`** — The `AuthorizationInput` dict
   builder. Currently constructs `{"action": "tool:invoke"}`. Change to:

   ```python
   "action": {
       "resource_id": action.resource_id,
       "operation": action.operation.value,
       "parameters": action.parameters,
   }
   ```

4. **OPA policies** — Update all Rego policies that match on
   `input.action == "tool:invoke"` to instead match on
   `input.action.operation == "execute"`. Update all example policies in
   both the SARK and grid-protocol repos.

### 1.3 Resource Model

**Problem:** v1.x only has `MCPServer`. The spec requires a generic
Resource with `type` (tool | data | service | device), `classification`,
`provider_id`, `parameters_schema`, and `owner`/`managers` as full objects.

**Changes:**

Replace `MCPServer` with a unified `Resource` model. MCP-specific fields
become part of the resource's metadata or a related `MCPConfig` model.

```python
class ResourceType(str, enum.Enum):
    TOOL = "tool"
    DATA = "data"
    SERVICE = "service"
    DEVICE = "device"
    INFRASTRUCTURE = "infrastructure"

class Classification(str, enum.Enum):
    PUBLIC = "Public"
    INTERNAL = "Internal"
    CONFIDENTIAL = "Confidential"
    SECRET = "Secret"

class Resource(Base):
    __tablename__ = "resources"

    id = Column(UUID, primary_key=True, default=uuid4)
    name = Column(String, nullable=False, index=True)
    resource_type = Column(Enum(ResourceType), nullable=False)
    provider_id = Column(String, nullable=False)
    sensitivity_level = Column(Enum(SensitivityLevel), nullable=False)
    classification = Column(Enum(Classification), nullable=False, default=Classification.INTERNAL)
    capabilities = Column(JSON, default=list)
    parameters_schema = Column(JSON, nullable=True)
    owner_id = Column(UUID, ForeignKey("principals.id"), nullable=False)
    metadata_ = Column("metadata", JSON, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("Principal")
    managers = relationship("Principal", secondary="resource_managers")
```

Association table:

```python
resource_managers = Table(
    "resource_managers",
    Base.metadata,
    Column("resource_id", UUID, ForeignKey("resources.id", ondelete="CASCADE")),
    Column("principal_id", UUID, ForeignKey("principals.id", ondelete="CASCADE")),
)
```

For MCP-specific fields (transport, command, mcp_version, health_endpoint),
add an `MCPConfig` model or store them in the resource's `metadata` JSON:

```python
# Option A: metadata convention
resource.metadata_ = {
    "transport": "http",
    "mcp_version": "1.0",
    "health_endpoint": "/health",
}

# Option B: dedicated table (if MCP fields grow)
class MCPConfig(Base):
    __tablename__ = "mcp_configs"
    resource_id = Column(UUID, ForeignKey("resources.id"), primary_key=True)
    transport = Column(Enum(TransportType), nullable=False)
    command = Column(String, nullable=True)
    mcp_version = Column(String, nullable=True)
    health_endpoint = Column(String, nullable=True)
```

Update all routers, services, and queries that reference `MCPServer` to use
`Resource` instead. The discovery service, tool registry, and gateway all
need updates.

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
class Effect(str, enum.Enum):
    ALLOW = "allow"
    DENY = "deny"
    CONSTRAIN = "constrain"

class PolicyRule(Base):
    __tablename__ = "policy_rules"

    id = Column(UUID, primary_key=True, default=uuid4)
    policy_version_id = Column(UUID, ForeignKey("policy_versions.id", ondelete="CASCADE"))
    name = Column(String, nullable=False)
    priority = Column(Integer, nullable=False, default=0)
    effect = Column(Enum(Effect), nullable=False)

    # Matchers as JSON arrays of {type, value} objects
    principal_matchers = Column(JSON, default=list)   # [{type: "role", value: "admin"}]
    resource_matchers = Column(JSON, default=list)    # [{type: "sensitivity", value: ["low","medium"]}]
    action_matchers = Column(JSON, default=list)      # [{type: "operation", value: "execute"}]

    # Conditions and constraints as JSON arrays
    conditions = Column(JSON, default=list)   # [{type: "time", operator: "between", value: {...}}]
    constraints = Column(JSON, default=list)  # [{type: "rate_limit", value: {requests_per_hour: 100}}]

    metadata_ = Column("metadata", JSON, default=dict)
```

Add relationship to `PolicyVersion`:

```python
class PolicyVersion:
    ...
    rules = relationship("PolicyRule", cascade="all, delete-orphan", order_by="PolicyRule.priority.desc()")
```

**Workflow:** When a policy is created or updated, the API accepts either:
- Raw Rego plus structured rule metadata, or
- A structured rule definition that is stored as `PolicyRule` rows and also
  compiled to Rego for OPA evaluation.

The policy creation endpoint should require rule metadata for new policies.
Add a `compile_rules_to_rego()` utility that generates Rego from structured
rules for the common patterns (RBAC role matching, ABAC attribute checks,
time conditions, sensitivity level gating).

### 1.5 Audit Event Fields

**Problem:** `AuditEvent` is missing 11 fields the spec requires.

**Changes:**

Add columns to `AuditEvent`:

| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `principal_type` | `String` | No | `human`, `agent`, `service`, `device` |
| `principal_attributes` | `JSON` | No | Role, teams, department at time of event |
| `resource_type` | `String` | Yes | `tool`, `data`, `service`, `device` |
| `action_operation` | `String` | No | `read`, `write`, `execute`, etc. |
| `action_parameters` | `JSON` | Yes | Sanitized copy of request parameters |
| `policy_version` | `Integer` | Yes | Version of the policy that made the decision |
| `environment` | `String` | No | From settings: `development`, `staging`, `production` |
| `success` | `Boolean` | No | Whether the action completed |
| `error_message` | `Text` | Yes | Error details if failed |
| `latency_ms` | `Float` | Yes | Response time |
| `cost` | `Numeric(10,6)` | Yes | Cost attributed to this action |
| `retention_until` | `DateTime` | No | Computed from settings at event creation |

Update `AuditService.log_event()` to accept and populate these fields from
the structured Principal and Action objects introduced in 1.1 and 1.2.

Update `log_authorization_decision()` to:
1. Accept `Principal` and `Action` as parameters.
2. Call `principal.to_policy_input()` for attributes.
3. Record `action.operation` and sanitized `action.parameters`.
4. Compute `retention_until` from `settings.audit_retention_days`.

---

## Phase 2: Authentication Gaps

These are independent of each other and can be worked in parallel.

### 2.1 Wire MFA into Auth Flow

**Problem:** TOTP, SMS, Push, and Email MFA implementations exist but are
not called from any login endpoint.

**Changes:**

Add `mfa_enabled` (bool) and `mfa_method` (string) columns to `Principal`.

Add MFA challenge/response endpoints:

```
POST /api/auth/mfa/challenge  — Initiates MFA (returns method + session token)
POST /api/auth/mfa/verify     — Verifies MFA code, completes login
```

Modify the login flow in `api/routers/auth.py`:

1. After successful password/OIDC/LDAP/SAML authentication, check
   `principal.mfa_enabled`.
2. If MFA required, return a partial session token (not a full JWT) with
   `{"status": "mfa_required", "mfa_session": "...", "methods": ["totp"]}`.
3. Client calls `/api/auth/mfa/verify` with the session token and code.
4. On success, issue the full JWT.

Add MFA enforcement rules:
- Required for all human principals with `mfa_enabled = true`.
- Required for access to critical-sensitivity resources (configurable via
  `MFA_REQUIRED_FOR_SENSITIVITY` setting).

### 2.2 SAML Signature Verification

**Problem:** SAML ACS endpoint parses XML but does not verify signatures,
conditions, audience, or issuer.

**Changes in `services/auth/providers/saml.py`:**

1. After base64-decoding the SAMLResponse, verify the XML signature using
   the IdP's X.509 certificate (available in settings as
   `saml_idp_x509_cert`). Use `signxml` or `xmlsec1`.

2. Check assertion conditions:
   - `NotBefore <= now <= NotOnOrAfter`
   - `AudienceRestriction` contains the SP entity ID.

3. Validate `Issuer` matches `saml_idp_entity_id`.

4. Wire the `saml_want_assertions_signed` and `saml_want_messages_signed`
   settings to enforce verification. These settings currently exist but are
   dead code.

5. After verification, create a session and redirect to `RelayState`.

### 2.3 OIDC PKCE

**Problem:** PKCE parameters are accepted in kwargs but never generated or
sent.

**Changes in `services/auth/providers/oidc.py`:**

1. In `get_authorization_url()`, generate a `code_verifier` (43-128
   cryptographic random characters) and derive `code_challenge` via S256.

2. Include `code_challenge` and `code_challenge_method=S256` in the
   authorization URL query parameters.

3. Store `code_verifier` in Redis keyed to the OIDC state parameter.

4. In the callback token exchange, include `code_verifier` in the token
   request body.

### 2.4 LDAP Connection Pooling

**Problem:** Each LDAP operation creates a new connection via
`asyncio.to_thread(Connection(...))`.

**Changes in `services/auth/providers/ldap.py`:**

Use `ldap3`'s built-in `REUSABLE` connection strategy:

```python
from ldap3 import Server, Connection, REUSABLE

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

Replace per-request `Connection()` calls with `self._pool` usage.

---

## Phase 3: SIEM and Audit Pipeline

### 3.1 Wire SIEM Forwarding

**Problem:** `_forward_to_siem()` in `audit_service.py` is a TODO that sets
a timestamp and returns without calling any provider.

**Changes:**

The SIEM provider implementations already exist under
`services/audit/siem/`. Instantiate the correct provider at service init
and call it:

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

**Problem:** The TimescaleDB retention policy is commented out. The spec
requires configurable retention with a `retention_until` field.

**Changes:**

1. Enable the TimescaleDB retention policy:
   ```sql
   SELECT add_retention_policy('audit_events', INTERVAL '365 days');
   ```

2. Populate `retention_until` at event creation time:
   ```python
   event.retention_until = datetime.now(UTC) + timedelta(
       days=settings.audit_retention_days  # default 365
   )
   ```

3. Add an `AUDIT_RETENTION_DAYS` setting (default: 365 for enterprise, 90
   for home).

---

## Phase 4: Protocol Adapters

### 4.1 MCP Tool Invocation

**Problem:** `MCPAdapter.invoke()` returns `{"stubbed": True}`.

**Changes:**

Implement actual MCP server calls per transport:

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

**SSE transport:** Send the request over HTTP, read the response as an SSE
event stream.

**stdio transport:** Launch the MCP server process via
`asyncio.create_subprocess_exec`, communicate over stdin/stdout JSON-RPC.
Consider using the `mcp` Python SDK's `StdioServerParameters` if available,
or implement a process pool for long-lived servers.

### 4.2 MCP stdio Capability Discovery

**Problem:** `_get_capabilities_stdio()` returns an empty list.

**Changes:**

Implement process management for stdio MCP servers:

```python
async def _get_capabilities_stdio(self, resource):
    process = await asyncio.create_subprocess_exec(
        *shlex.split(resource.endpoint),
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
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

### 4.3 MCP Streaming

**Problem:** `invoke_streaming()` yields placeholder events.

**Changes:**

Implement SSE-based streaming for HTTP/SSE transports. For stdio, stream
by reading stdout line-by-line. The existing stub has the right event
structure (`start`, `data`, `end`); replace the static yields with actual
transport reads.

---

## Phase 5: Rust Integration (grid-core)

### 5.1 Wire grid-core into SARK

**Problem:** `factory.py` has `RustOPAClient` and `RustPolicyCache` stubs
that raise `NotImplementedError`. The real code is in the `grid-core` repo.

**Changes:**

1. Add `grid-core` as a dependency in `pyproject.toml`:
   ```toml
   dependencies = [
       "grid-core",
       ...
   ]
   ```

2. Update `factory.py`:
   ```python
   from grid_core import RustOPAEngine, RustCache
   ```

3. Replace the `RustOPAClient` stub with the existing
   `rust_opa_client.py` implementation (457 lines). Update its import from
   `sark.sark_opa` to `grid_core`.

4. Replace the `RustPolicyCache` stub with the existing `rust_cache.py`
   implementation (509 lines). Update its import similarly.

5. Delete the `NotImplementedError` stubs.

### 5.2 Port Benchmarks to grid-core

**Problem:** grid-core has benchmark infrastructure (Criterion in
Cargo.toml) but the actual benchmark files from SARK were not ported.

**Changes:**

Copy and rename:
- `sark/rust/sark-opa/benches/opa_benchmarks.rs` → `grid-core/crates/grid-opa/benches/`
- `sark/rust/sark-cache/benches/cache_benchmarks.rs` → `grid-core/crates/grid-cache/benches/`

Update namespace references from `sark_opa`/`sark_cache` to
`grid_opa`/`grid_cache`. Uncomment the `[[bench]]` sections in both
`Cargo.toml` files.

---

## Phase 6: Specification Alignment Fixes

Smaller items that round out compliance.

### 6.1 Secret Scanner Pattern Count

**Problem:** Claims 25+ patterns, actual is 22.

**Changes:** Add patterns for:
- Azure Storage Account Keys
- Heroku API Key
- Mailgun API Key

### 6.2 Remove Duplicate API Key Module

**Problem:** `api_key.py` (in-memory stub) and `api_keys.py` (real
DB-backed implementation) both exist.

**Changes:** Delete `api_key.py`. Point any remaining imports at
`api_keys.py`.

### 6.3 Resolve Auth Router TODOs

**Problem:** `get_settings()` and `get_session_service()` have TODO
comments about getting values from app state.

**Changes:** Store service instances in `app.state` during lifespan
startup. Read them via FastAPI dependency injection using
`request.app.state`.

### 6.4 Update Gap Analysis Document

**Problem:** `GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md` claims 95%+
compliance.

**Changes:** After completing all phases, update the gap analysis with
accurate compliance percentages. Reference the methodology from
`SARK_COMPLIANCE_REVIEW.md`.

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
