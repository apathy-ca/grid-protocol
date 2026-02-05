# SARK Compliance Review: GRID Protocol v0.1

**Review Date:** February 5, 2026
**Repositories Audited:**
- [grid-protocol](https://github.com/apathy-ca/grid-protocol) (specification)
- [sark](https://github.com/apathy-ca/sark) (reference implementation)
- [grid-core](https://github.com/apathy-ca/grid-core) (Rust performance libraries)

**Claimed Compliance:** 95%+ (per `GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md`)
**Assessed Compliance:** ~63-68%

---

## Methodology

This review compares the GRID Protocol Specification v0.1 against the actual
SARK source code on a field-by-field, feature-by-feature basis. Claims from the
gap analysis document were verified by reading the implementation, not just the
interface or documentation. Code that exists but is not wired into the running
application is noted as such.

---

## 1. Core Abstraction Alignment

The GRID spec defines five first-class abstractions. SARK's implementation of
each was compared at the data model and API level.

### 1.1 Principal (~35% aligned)

**Spec requires:** id, type (human | agent | service | device), identity_token,
attributes (role, teams, custom ABAC attributes), created_at, revoked_at.

**SARK implements:** A `User` model with id (UUID), email, full_name,
hashed_password, is_active, is_admin, role (string), extra_metadata (JSON),
created_at, updated_at.

**Gaps:**
- No `principal_type` field. Human, agent, service, and device principals
  cannot be distinguished. Non-human principals are stored as User rows.
- No `identity_token` field (spec requires this; SARK uses hashed_password).
- No `revoked_at` field.
- `role` is a freeform string, not an enum matching the spec's defined values.
- No first-class support for agent or service principals.

**Impact:** SARK cannot model the spec's multi-principal scenarios. An AI agent
delegating to another agent, or a device requesting access, has no typed
representation.

### 1.2 Resource (~45% aligned)

**Spec requires:** id, name, type (tool | data | service | device), provider_id,
sensitivity_level, classification (Public | Internal | Confidential | Secret),
capabilities array, parameters_schema (JSON Schema), owner (Principal object),
managers (Principal array), metadata with tags.

**SARK implements (v1.x):** An `MCPServer` model with id, name, transport,
endpoint, sensitivity_level, capabilities (JSON), owner_id (UUID foreign key),
team_id (UUID foreign key), tags, extra_metadata.

**SARK implements (v2.0):** A generic `Resource` model with id, name, protocol,
endpoint, sensitivity_level, metadata (JSONB).

**Gaps:**
- v1.x is MCP-server-specific, not a generic Resource.
- v2.0 is more generic but still missing: `type` (tool vs data vs service vs
  device), `provider_id`, `classification`, `parameters_schema`.
- `owner` and `managers` are ID references, not Principal objects.
- No support for multiple managers.
- `protocol` (how you connect) is not the same as `type` (what the resource is).

### 1.3 Action (~5% aligned)

**Spec requires:** A structured Action object with resource_id, operation
(read | write | execute | control | manage | audit), parameters (object),
and context (timestamp, ip_address, user_agent, request_id, environment).

**SARK implements:** Action is an unstructured string (e.g., `"tool:invoke"`,
`"server:register"`) passed as a field in the policy evaluation request. There
is no Action model, class, or schema anywhere in the codebase.

**Impact:** This is the largest single gap. The spec's Action abstraction enables
structured policy matching (e.g., "deny all write operations on critical
resources"). SARK's string-based approach makes this kind of structured reasoning
impossible at the framework level — it falls entirely to individual Rego policies
to parse action strings.

### 1.4 Policy (~20% aligned)

**Spec requires:** Structured Policy objects containing Rule arrays, where each
Rule has PrincipalMatcher, ResourceMatcher, ActionMatcher, Condition (time,
location, context, custom), Constraint (rate_limit, quota, cost, approval),
effect (allow | deny), and priority.

**SARK implements:** A `Policy` model with id, name, policy_type (enum), status
(enum), and a related `PolicyVersion` model that stores policy content as a raw
Rego text blob.

**Gaps:**
- No Rule, PrincipalMatcher, ResourceMatcher, or ActionMatcher objects.
- No Condition or Constraint objects.
- No priority field for rule evaluation order.
- Policies are opaque Rego strings. The system cannot introspect policy
  structure, enumerate which principals a policy affects, or programmatically
  compose rules.

**Note:** OPA/Rego evaluation itself works well. The gap is in the structural
metadata layer, not the evaluation engine.

### 1.5 Audit (~60% aligned)

**Spec requires:** timestamp, request_id, duration, principal_id,
principal_type, principal_attributes, resource_id, resource_type,
action_operation, action_parameters, decision, decision_reason, policy_id,
policy_version, ip_address, user_agent, environment, success, error, latency_ms,
cost, sensitivity_level, forwarded_to_siem, retention_until.

**SARK implements:** AuditEvent with id, timestamp, request_id, event_type,
severity, user_id, user_email, server_id, tool_name, decision, policy_id,
ip_address, user_agent, details (JSON), siem_forwarded.

**Gaps:**
- No `principal_type` (human/agent/service/device).
- No `principal_attributes` (role, teams).
- No `resource_type`.
- No `action_operation` or `action_parameters`.
- No `policy_version` (only policy_id).
- No `environment` (dev/staging/prod).
- No `latency_ms`, `cost`, `duration`.
- No `retention_until`.
- `siem_forwarded` timestamp is set but forwarding is not wired up (see Section 4).

### Summary Table

| Abstraction | Alignment | Severity |
|-------------|-----------|----------|
| Principal   | ~35%      | High     |
| Resource    | ~45%      | High     |
| Action      | ~5%       | Critical |
| Policy      | ~20%      | Critical |
| Audit       | ~60%      | Medium   |

---

## 2. Authentication

### 2.1 JWT — Complete

JWT authentication is production-ready. Supports HS256 and RS256, token
refresh with rotation, proper expiration handling, and audience/issuer
validation.

### 2.2 API Keys — Complete

The database-backed implementation (`api_keys.py`) is solid: scoped keys,
rate limiting, usage tracking, revocation, prefix-based lookup with hashed
storage. Note: a separate in-memory stub (`api_key.py`) also exists and
should be removed to avoid confusion.

### 2.3 OIDC — Mostly Complete, PKCE Missing

OIDC discovery, authorization flow, and token exchange work. However:
- PKCE (Proof Key for Code Exchange) parameters are accepted in kwargs but
  never used in the authorization URL or token exchange.
- ID token signature validation contains mock/placeholder logic.

### 2.4 LDAP — Functional, No Connection Pooling

LDAP bind, search, and group resolution work. However:
- Each operation creates a new LDAP connection. No connection pooling despite
  the gap analysis claiming pooling exists.
- Uses `asyncio.to_thread` with synchronous ldap3 — functional but not
  optimal for high-concurrency scenarios.

### 2.5 SAML — Incomplete (~40%)

SAML SSO login flow performs basic XML parsing of assertions. However:
- No XML signature verification.
- No assertion condition validation (NotBefore, NotOnOrAfter).
- No audience restriction check.
- No issuer validation.
- Config flags for `verify_responses` exist but are not connected to any
  verification logic.

This is a security concern if deployed in production with SAML enabled.

### 2.6 MFA — Implemented but Not Integrated

All four MFA methods (TOTP, SMS, Push, Email) have real implementations with
proper cryptographic handling. However:
- Zero MFA checks exist in the authentication router.
- No login flow calls MFA verification.
- The MFA module is entirely orphaned from the running application.

### Summary Table

| Provider | Claimed | Actual |
|----------|---------|--------|
| JWT      | Complete | Complete |
| API Keys | Complete | Complete |
| OIDC     | Complete with PKCE | PKCE not implemented; ID token validation mocked |
| LDAP     | Complete with pooling | No connection pooling |
| SAML     | Complete | ~40% — no signature verification or condition checks |
| MFA      | 4 methods | Code exists but not integrated into auth flow |

---

## 3. Protocol Adapters

### 3.1 HTTP/REST — Production-Ready

OpenAPI discovery, 5 authentication strategies, circuit breaker with
configurable thresholds, retry with exponential backoff, SSE streaming
support, proper error mapping. This is SARK's strongest adapter.

### 3.2 gRPC — Production-Ready

Server reflection for discovery, mTLS support, all 4 streaming types
(unary, server, client, bidirectional), auth interceptors, health checks.
Well-implemented.

### 3.3 MCP — Partially Stubbed

Given that SARK is specifically an MCP governance platform, this adapter
warrants scrutiny:

| Capability | Status |
|------------|--------|
| Server discovery (HTTP, SSE, stdio) | Works |
| Capability queries (HTTP, SSE) | Works |
| Capability queries (stdio) | **Stubbed** — returns `"stdio_capability_discovery_stubbed"` |
| Tool invocation | **Stubbed** — returns `{"stubbed": True}` |
| Streaming | **Stubbed** — returns `"Streaming stubbed - implementation in progress"` |

The MCP adapter can discover and catalog servers but cannot actually invoke
tools or stream results through the governance layer.

---

## 4. Audit & SIEM Integration

### 4.1 Audit Logging — Functional

AuditEvent creation, TimescaleDB hypertable storage, and query/export
endpoints all work. The immutability guarantee relies on the database model
having no UPDATE endpoints (append-only).

### 4.2 SIEM Forwarding — Not Wired Up

SIEM provider implementations exist and are real code:
- **Splunk HEC**: 344 lines, batch sending, gzip compression, retry logic.
- **Datadog Logs**: 377 lines, similar quality.
- **Generic HTTP**: Works.
- **Kafka**: Claimed in docs but no implementation exists.

However, the audit service's `_forward_to_siem()` method at
`src/sark/services/audit/audit_service.py:246` contains a TODO comment and
does not call any SIEM provider. It sets the `siem_forwarded` timestamp and
returns. The entire SIEM infrastructure is disconnected from the audit
pipeline.

---

## 5. AI-Specific Security

This is SARK's strongest area. Claims largely hold up.

### 5.1 Prompt Injection Detection — Verified

24 compiled regex patterns across 3 severity levels (high, medium, low).
Includes entropy analysis for obfuscated payloads and Unicode normalization.
262-line test suite. The claimed "20+ patterns" is accurate (24 found).

### 5.2 Secret Scanning — Verified (Slightly Overstated)

22 patterns found vs. claimed "25+". Includes OpenAI, GitHub, AWS, Stripe,
Anthropic API keys, private keys, database connection strings, JWT tokens,
and generic patterns. Auto-redaction works. Chunked processing prevents
regex catastrophic backtracking.

### 5.3 Behavioral Anomaly Detection — Verified

All 7 claimed anomaly categories are implemented as an enum:
`UNUSUAL_TOOL`, `UNUSUAL_TIME`, `UNUSUAL_DAY`, `EXCESSIVE_DATA`,
`SENSITIVITY_ESCALATION`, `RAPID_REQUESTS`, `GEOGRAPHIC_ANOMALY`.
30-day configurable baseline window. Confidence scoring and severity levels.

---

## 6. Rust Performance Layer (grid-core)

### 6.1 Current State

The Rust OPA engine and cache have been extracted from SARK into the
standalone `grid-core` repository:

| Crate | LOC | Tests | Status |
|-------|-----|-------|--------|
| grid-opa | 421 | 10 passing | Complete, no stubs |
| grid-cache | 323 | 7 passing | Complete, no stubs |

PyO3 bindings are complete and functional. The `grid_core` Python module
exports `RustOPAEngine` and `RustCache` directly.

### 6.2 Integration Gap

SARK's `factory.py` still contains stubs that raise `NotImplementedError`
with the message "waiting for opa-engine worker implementation." A separate
`rust_opa_client.py` (457 lines) exists that would work with the compiled
Rust extension, but the factory routing blocks it.

This is a wiring problem, not a missing-code problem. SARK needs to update
its dependency from the internal `sark-opa`/`sark-cache` to `grid-core` and
remove the stubs from `factory.py`.

### 6.3 Benchmarks

The SARK repo has comprehensive Criterion benchmarks (569 lines across both
crates). The grid-core repo has benchmark infrastructure configured but
benchmark files are not yet ported. Performance claims (4-10x OPA speedup,
<0.5ms cache p95) are plausible from the code structure but unverified
without running the benchmarks.

---

## 7. Gap Analysis Document Accuracy

The `GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md` in the grid-protocol
repo claims 95%+ compliance. This review finds the document systematically
overstates compliance in several ways:

### 7.1 Counting Unwired Code as Complete

| Feature | Gap Analysis Says | Code Review Finds |
|---------|-------------------|-------------------|
| MFA | "4 methods" | Code exists, not called from auth flow |
| SIEM | "Multi-SIEM (Splunk, Datadog, Kafka)" | Splunk/Datadog code exists but `_forward_to_siem()` is a TODO. Kafka has no implementation. |
| Rust OPA | "4-10x faster evaluation" | Rust code is real but SARK's factory raises NotImplementedError |

### 7.2 Claiming Full Compliance on Structurally Different Abstractions

The gap analysis marks Principal, Policy, and Audit as "Fully compliant."
Field-by-field comparison shows:

- **Principal**: Missing type enum, identity_token, revoked_at. Cannot
  represent non-human principals.
- **Policy**: Stored as raw Rego text. None of the spec's structured Rule,
  Matcher, Condition, or Constraint objects exist.
- **Audit**: Missing 11 of the spec's required fields.

### 7.3 Overstated Pattern Counts

- Secret scanning: Claims "25+ patterns," actual count is 22.

### 7.4 Omitted Stub Status

- MCP tool invocation: Not mentioned as stubbed.
- MCP streaming: Not mentioned as stubbed.
- SAML signature verification: Not mentioned as missing.
- OIDC PKCE: Not mentioned as unimplemented.

---

## 8. Revised Compliance Estimate

| Category | Weight | Actual Compliance | Weighted |
|----------|--------|-------------------|----------|
| Core abstractions (5) | 30% | ~33% | 10.0% |
| Authentication (6 providers) | 15% | ~60% | 9.0% |
| Authorization & policy eval | 15% | ~75% | 11.3% |
| Audit trail & SIEM | 10% | ~50% | 5.0% |
| Protocol adapters | 10% | ~65% | 6.5% |
| AI-specific security | 10% | ~90% | 9.0% |
| Performance (Rust layer) | 5% | ~80% | 4.0% |
| Configuration & operations | 5% | ~85% | 4.3% |
| **Total** | **100%** | | **~59%** |

Accounting for grid-core resolving the Rust integration (once wired): **~63-68%**.

---

## 9. Recommendations

### High Priority (Structural)

1. **Implement an Action model.** This is the spec's most fundamental gap.
   Define a structured Action class with operation, resource_id, parameters,
   and context. Route it through policy evaluation.

2. **Add principal_type to User (or create a Principal abstraction).** Support
   human, agent, service, and device types. This is required for the spec's
   delegation and multi-principal scenarios.

3. **Wire MFA into the auth flow.** The code is written and tested in
   isolation. It needs integration points in the login and token refresh
   endpoints.

4. **Connect SIEM forwarding.** Replace the TODO in `_forward_to_siem()` with
   actual calls to the existing Splunk/Datadog providers.

5. **Wire grid-core into SARK.** Update `factory.py` to import from
   `grid_core` instead of raising `NotImplementedError`. Remove stubs.

### Medium Priority (Completeness)

6. **Add SAML signature verification.** The current implementation is
   insecure for production use. At minimum, verify XML signatures and check
   assertion conditions.

7. **Implement OIDC PKCE.** Required for public clients per current best
   practices.

8. **Implement MCP tool invocation.** The governance platform should be able
   to invoke the tools it governs.

9. **Extend AuditEvent** with the spec's missing fields: principal_type,
   action_operation, environment, latency_ms, policy_version, retention_until.

### Lower Priority (Spec Alignment)

10. **Add structured policy metadata.** Even if policies remain as Rego text
    for evaluation, add a metadata layer with matchers, conditions, and
    constraints for introspection and composition.

11. **Extend Resource model** with type, classification, provider_id, and
    parameters_schema.

12. **Port benchmarks to grid-core** from SARK's bench files.

13. **Remove the duplicate API key stub** (`api_key.py` vs `api_keys.py`).

---

## 10. Conclusion

SARK is a substantial, well-engineered codebase with genuine production
quality in several areas: HTTP and gRPC adapters, AI security features,
OPA integration, JWT authentication, and the Rust performance libraries in
grid-core. It is not vaporware.

However, the 95% compliance claim does not withstand code-level scrutiny.
The core abstraction layer — the heart of what makes GRID a protocol rather
than just an MCP proxy — has significant structural gaps. Action and Policy
have no typed representation, Principal cannot model non-human entities, and
several features (MFA, SIEM forwarding, Rust OPA integration) exist as code
but are not connected to the running application.

The spec appears to have been written to describe what SARK aspires to be.
The gap analysis then grades SARK against that aspirational spec generously.
A more accurate framing would be: SARK implements the operational aspects of
GRID well (authn, authz decisions, audit logging, security controls) but has
not yet implemented the protocol's structural abstractions (typed principals,
resources, actions, and policies).
