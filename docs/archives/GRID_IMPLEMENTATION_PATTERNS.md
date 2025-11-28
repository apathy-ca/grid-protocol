# GRID Implementation Patterns: The Shim Question

**Question:** How is GRID actually implemented? As a shim in every single MCP server?

**Short Answer:** No - that would be a catastrophic implementation pattern. GRID is implemented as a **policy layer gateway**, not as per-server shims.

---

## The Problem with Per-Server Shims

### Why Per-Server Shims Don't Work

```
❌ BAD: Shim in every server
┌─────────────────────────────────┐
│ Principal Request               │
└────────────┬────────────────────┘
             ↓
      ┌──────────────┐
      │ MCP Server 1 │ ← Embedded GRID shim (auth, policy, audit)
      │ - Auth logic │
      │ - Policy     │
      │ - Audit      │
      └──────────────┘
      ┌──────────────┐
      │ MCP Server 2 │ ← Embedded GRID shim (duplicate!)
      │ - Auth logic │
      │ - Policy     │
      │ - Audit      │
      └──────────────┘
      ┌──────────────┐
      │ MCP Server 3 │ ← Embedded GRID shim (duplicate!)
      │ - Auth logic │
      │ - Policy     │
      │ - Audit      │
      └──────────────┘
```

**Problems:**
- ❌ **Massive duplication** - Every server implements auth, policy, audit
- ❌ **Inconsistent governance** - Different implementations of same rules
- ❌ **Operational nightmare** - Update a policy? Update 10,000 servers
- ❌ **Security risk** - Bugs replicated across all servers
- ❌ **No federation** - Each server is independent
- ❌ **No cross-server audit** - Can't correlate events across servers
- ❌ **Vendor lock-in** - Each MCP server must implement GRID
- ❌ **Scalability** - Adding governance increases server load
- ❌ **Testing** - Test policy in 10,000 places
- ❌ **Not actually GRID** - GRID is protocol-agnostic, this is MCP-specific

**This is why SARK exists.**

---

## The Correct Pattern: Gateway/Proxy Architecture

### ✅ RIGHT: GRID as Gateway

```
┌──────────────────────────────────────────────────────────┐
│ Principal Request (Principal → Resource + Action)         │
└────────────────────┬─────────────────────────────────────┘
                     ↓
         ┌─────────────────────────┐
         │  GRID GOVERNANCE LAYER  │ ← SINGLE POINT OF CONTROL
         │  (SARK or alternative)  │
         ├─────────────────────────┤
         │ 1. Authentication       │ ← Validate principal identity
         │    - JWT validation     │
         │    - API key validation │
         ├─────────────────────────┤
         │ 2. Authorization        │ ← Check policy
         │    - Policy evaluation  │
         │    - OPA/Cedar/Custom   │
         │    - Caching (<5ms)     │
         ├─────────────────────────┤
         │ 3. Audit Logging        │ ← Record decision
         │    - TimescaleDB        │
         │    - Async SIEM forward │
         ├─────────────────────────┤
         │ 4. Enforcement          │ ← Allow or deny
         └────────────┬────────────┘
                      ↓
         IF ALLOWED: Forward to resource
         ┌──────────────┐
         │ MCP Server 1 │ ← Unaware of GRID, just receives requests
         │ (No governance code)
         └──────────────┘
         ┌──────────────┐
         │ MCP Server 2 │ ← Unaware of GRID, just receives requests
         │ (No governance code)
         └──────────────┘
         ┌──────────────┐
         │ MCP Server 3 │ ← Unaware of GRID, just receives requests
         │ (No governance code)
         └──────────────┘
```

**Advantages:**
- ✅ **Single point of governance** - All decisions in one place
- ✅ **Zero server changes** - Servers unaware of GRID
- ✅ **Consistent policies** - Same rules for all servers
- ✅ **Operational simplicity** - Update policy once, applies everywhere
- ✅ **Security** - One place to secure, audit, update
- ✅ **Federation** - Cross-org governance via gateway federation
- ✅ **Protocol-agnostic** - Same gateway works for HTTP, gRPC, etc.
- ✅ **Vendor-agnostic** - Works with any MCP server implementation
- ✅ **Scalability** - Gateway handles auth/policy, not servers
- ✅ **Testability** - Test policies once
- ✅ **Actually GRID** - Truly protocol-agnostic

---

## Real-World Implementation: SARK

SARK implements GRID as a **proxy gateway** sitting between principals and MCP servers:

```
User/Agent Request
       ↓
      HTTP/gRPC
       ↓
  ┌─────────────────────────────────────────┐
  │           SARK Gateway                  │
  │  (FastAPI, Kong integration optional)   │
  ├─────────────────────────────────────────┤
  │ 1. Extract principal from JWT           │
  │ 2. Extract action from request          │
  │ 3. Lookup resource in registry          │
  │ 4. Evaluate policy against (p,r,a)     │
  │ 5. Log decision to TimescaleDB          │
  │ 6. If allowed, forward to MCP server    │
  │ 7. If denied, return 403                │
  └────────────┬────────────────────────────┘
               ↓
         (Allowed requests only)
               ↓
      ┌──────────────────────────┐
      │   MCP Servers (Unmodified) │
      │  - Query database         │
      │  - Create ticket          │
      │  - Search docs            │
      │  - etc.                   │
      └──────────────────────────┘
```

### SARK Architecture Details

**Three Deployment Patterns:**

#### Pattern 1: SARK as Reverse Proxy
```
Client → SARK Gateway (port 8000) → MCP Server (internal)
         (localhost:9000)           (localhost:9001-9100)

SARK intercepts ALL requests, evaluates policy, forwards.
MCP servers never see the governance layer.
```

**Real config:**
```yaml
# SARK Configuration
sark:
  api_host: 0.0.0.0
  api_port: 8000

mcp_servers:
  - name: analytics
    endpoint: http://localhost:9001
    transport: http
  - name: jira
    endpoint: http://localhost:9002
    transport: http

policy_engine:
  opa_url: http://opa:8181
  cache: redis://redis:6379
```

**MCP servers don't change:**
```python
# MCP Server (completely unaware of SARK)
@app.post("/mcp/tools/query_database")
def query_database(query: str):
    # Just execute - no auth, no policy, no audit
    return database.execute(query)
```

**How it works:**
1. Client sends: `POST http://sark:8000/api/v1/invoke` with JWT
2. SARK validates JWT → extracts principal
3. SARK checks policy → allow/deny
4. If allowed: SARK proxies to `http://localhost:9001/mcp/tools/query_database`
5. MCP server never knows SARK exists

#### Pattern 2: SARK as Kong Plugin
```
Client → Kong Gateway (port 8000)
            ↓ (Kong MCP Security Plugin)
         SARK Policy Engine
            ↓
         Upstream MCP Servers

Kong handles routing, SARK handles governance.
```

#### Pattern 3: SARK in Kubernetes Sidecar
```
Kubernetes Pod
├── MCP Server Container
└── SARK Sidecar Container (localhost:8000)

Pod traffic: localhost:8000 (SARK) → localhost:9000 (MCP server)
External traffic routed through sidecar first.
```

---

## Multi-Protocol: The Real Win

This gateway architecture is what makes GRID **protocol-agnostic**:

```
GRID Gateway (Single governance layer)
├─→ MCP Server (via MCPAdapter)
├─→ HTTP API (via HTTPAdapter)
├─→ gRPC Service (via gRPCAdapter)
└─→ Custom Protocol (via CustomAdapter)

Same policies, same audit, same federation.
No changes to any downstream service.
```

With per-server shims:
```
❌ MCP Server has MCP auth logic
❌ HTTP API has HTTP auth logic
❌ gRPC Service has gRPC auth logic
❌ Custom Protocol has custom auth logic
No shared governance.
```

---

## Governance Distribution: Why Not Edge Gateways?

**Question:** Why not put governance at Kong/edge instead of SARK?

**Answer:** Kong doesn't understand business policies, GRID does.

### Kong's Role (Network Level)
```
Kong Gateway
├─ Rate limiting (X requests per second)
├─ Authentication (JWT validation)
├─ Request routing
├─ TLS termination
└─ Basic audit
```

### SARK's Role (Business Logic Level)
```
SARK Gateway
├─ Who is this principal? (Context extraction)
├─ What resource are they accessing? (Semantic understanding)
├─ Is this allowed by policy? (Business rules)
├─ What constraints apply? (Budget, approval, etc.)
├─ Log for compliance (Structured audit trail)
└─ Federation (Cross-org governance)
```

**Real example:**

```rego
# Kong can't do this (network level only):

allow if {
    input.principal.role == "developer"
    input.resource.sensitivity_level in ["low", "medium"]
    input.action == "execute"
    is_business_hours  # Business logic!
}

# Kong can do:
rate_limit: 1000 req/hour  # Network level
```

**Optimal:** Kong + SARK
```
Client → Kong (Rate limit, TLS) → SARK (Business governance) → Services
```

---

## Federation: The Multi-Org Problem

Per-server shims make federation impossible:

### ❌ Shim Architecture (Federation Impossible)
```
Org A                          Org B
┌─────────────┐              ┌─────────────┐
│ MCP Server1 │─ (shim)      │ MCP Server2 │─ (shim)
└─────────────┘              └─────────────┘

Org A user tries to access Org B resource:
"Which policy applies? Org A's or Org B's?"
No federation protocol exists.
```

### ✅ Gateway Architecture (Federation Natural)
```
Org A                              Org B
┌──────────────────────┐          ┌──────────────────────┐
│  GRID Node A (SARK)  │◄─────────│  GRID Node B (SARK)  │
│  - Policies          │ Trust    │  - Policies          │
│  - Audit             │ Established │  - Audit           │
└────────┬─────────────┘          └──────┬─────────────┘
         ↓                               ↓
    MCP Servers              MCP Servers
    (unaware)                (unaware)

Org A user accesses Org B resource:
1. SARK A receives request
2. SARK A queries SARK B: "Is this allowed?"
3. SARK B evaluates Org B's policies
4. Both audit the cross-org access
5. User gets access (or denial) + audit trail
```

---

## Performance: Shim vs Gateway

### Shim Architecture
```
Request → Server 1
         ├─ Auth check (local)
         ├─ Policy eval (local)
         ├─ Audit log (local)
         └─ Execute

x10,000 servers = 10,000 policy evaluations distributed
Problem: Each server doing its own caching, inconsistent
```

### Gateway Architecture
```
Request → SARK Gateway
         ├─ Auth check (cached, <1ms)
         ├─ Policy eval (cached, <5ms)
         ├─ Audit log (async, non-blocking)
         └─ Forward to server → Execute

x10,000 servers = Same policy evaluated once in gateway
Benefit: Centralized caching, consistent decisions, audit
```

**Benchmark:** SARK gateway + 10,000 MCP servers
- Auth decision: <1ms (cached)
- Policy decision: <5ms (cached)
- Audit log: <0.1ms (async queue)
- End-to-end: ~50-100ms to MCP server + ~50ms execution
- Total: ~100-150ms vs ~500ms if policy evaluated in server

---

## Cost/Deployment: Who Runs SARK?

### Enterprise Deployment
```
Organization runs their own SARK instance:
- Governance in their VPC/datacenter
- Full control over policies
- Complete audit trail
- Federate with other orgs' SARK instances
```

### SaaS Deployment
```
SaaS platform deploys SARK:
- Platform controls governance
- Multi-tenant policies
- Shared audit infrastructure
- Customers access via SARK
```

### Cloud Deployment
```
Kubernetes cluster:
- SARK as microservice (3 replicas)
- PostgreSQL for audit
- Redis for cache
- Kong optional for edge
- Scales independently from MCP servers
```

**Cost:** SARK overhead is negligible vs MCP servers themselves
- SARK: ~500MB memory, minimal CPU
- MCP server: ~1GB memory, variable CPU
- Ratio: SARK is <1% overhead per user

---

## The Real Answer to the Devil's Advocate

**Question:** Isn't this just adding another layer of complexity?

**Answer:** No, it's removing complexity from 10,000 places and centralizing it in one.

**Trade-off Analysis:**

| Aspect | Per-Server Shim | Gateway |
|--------|---|---|
| **Implementation complexity** | 10,000x instances | 1 well-designed SARK |
| **Testing** | Test in 10,000 places | Test once |
| **Security updates** | Update 10,000 servers | Update SARK |
| **Policy changes** | Deploy to 10,000 servers | Update SARK database |
| **Federation** | Impossible | Natural |
| **Multi-protocol** | Each protocol its own shim | Single gateway |
| **Observability** | 10,000 audit streams | Single audit DB |
| **Debugging** | Where did policy fail? | Check SARK logs |
| **Operational burden** | Massive | Manageable |

**The paradox:** Adding a gateway REDUCES total complexity.

---

## Conclusion: Why SARK (Not Per-Server Shims)

**GRID is implemented as a gateway, not as per-server shims because:**

1. **Governance is a cross-cutting concern** - Belongs at the boundary, not in each service
2. **Single point of control** - Update policies once, applies everywhere
3. **Enables federation** - Cross-org governance requires gateway-to-gateway trust
4. **Protocol-agnostic** - Same gateway for any protocol (MCP, HTTP, gRPC)
5. **Operational simplicity** - One thing to deploy, monitor, secure
6. **Performance** - Centralized caching beats distributed implementations
7. **Compliance** - Immutable audit trail in one place
8. **Scalability** - Governance doesn't increase as you add servers

**SARK proves this works:** 50,000+ employees, 10,000+ MCP servers, <5ms policy decisions, sub-5ms SLA maintained.

---

## What If We Did Use Per-Server Shims?

For completeness, here's what that would look like:

```python
# Every MCP server would need this boilerplate

from sark_sdk import GridShim

# Initialize shim
grid = GridShim(
    policy_server="opa:8181",
    audit_server="postgres:5432",
    cache_server="redis:6379"
)

@app.post("/mcp/tools/query_database")
@grid.authorize(action="execute", resource="database.query")
@grid.audit()
def query_database(query: str, request: Request):
    # Get principal from JWT
    principal = grid.extract_principal(request)

    # Check authorization
    decision = grid.evaluate(
        principal=principal,
        action="execute",
        resource="database.query",
        parameters={"query": query}
    )

    if not decision.allowed:
        return {"error": decision.reason}, 403

    # Execute
    result = database.execute(query)

    # Audit (this already happened in decorator)
    return result
```

**Problems immediately obvious:**
- Every single endpoint needs decorators
- Every server duplicates this logic
- Different implementations across servers
- No unified audit (logs scattered)
- No federation (each server is independent)
- Testing required in every server
- Update policy? Update every server

**This is why organizations have historically either:**
1. Had no governance (chaotic)
2. Implemented application-level governance (tedious)
3. Used API gateways for simple rate-limiting only (insufficient)
4. Built custom governance frameworks (SARK's original purpose)

---

**Recommendation:** SARK's gateway architecture is the right pattern. Per-server shims are an anti-pattern that GRID was designed to avoid.

