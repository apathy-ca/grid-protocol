# GRID Shadow IT and Governance Gaps

**Document:** Enterprise Governance Reality Check
**Status:** Critical Operational Concerns
**Date:** November 27, 2025

---

## Executive Summary

GRID and SARK provide excellent governance **for traffic that reaches the governance layer**. However, they do not prevent "shadow IT" – unauthorized MCP servers running outside governance. This is an architectural limitation, not a bug.

**Key Finding:** GRID implementations (including SARK) require defense-in-depth because a gateway can only govern traffic that flows through it.

---

## The Shadow IT Problem

### What Is Shadow IT in GRID Context?

**Shadow IT:** Computational capabilities (MCP servers, tools, APIs) that exist on the network but are not registered in SARK's resource registry and therefore bypass all GRID governance.

**Examples:**

```
✅ Governed Path:
User → SARK Gateway (port 8000) → Policy Check → MCP Server (Registered)
                                      ↓
                                 Audit Trail

❌ Shadow IT Path:
User → MCP Server (localhost:9999, unregistered)
           ↓
       No policy check
       No audit trail
       No visibility
       No governance
```

### Real-World Attack Scenarios

#### Scenario 1: Developer Bypass (Local Development)

```bash
# Developer runs unauthorized MCP server locally
python my_tool.py --mcp --port 9999

# Accesses it directly, bypassing SARK entirely
curl localhost:9999/invoke --data '{"tool": "dangerous_operation"}'

# Result:
# - No policy evaluation
# - No audit log
# - No rate limiting
# - No principal tracking
# - Tool invocation invisible to security team
```

**Why it happens:** Developers building locally don't want to depend on SARK during development. Easy to forget to go through governance.

---

#### Scenario 2: Kubernetes Pod Escape

```yaml
# Pod A: Rogue tool server running in cluster (unregistered)
apiVersion: v1
kind: Pod
metadata:
  name: shadow-tools-pod
  namespace: default  # Not in governance namespace
spec:
  containers:
  - name: tools
    image: my-custom-tools:latest
    ports:
    - containerPort: 9999  # ← Not in SARK
    env:
    - name: DANGEROUS_MODE
      value: "true"

---

# Pod B: Agent accessing it directly
apiVersion: v1
kind: Pod
metadata:
  name: agent-pod
spec:
  containers:
  - name: agent
    image: claude-agent:latest
    command:
    - /bin/sh
    - -c
    - |
      # Direct access to rogue server, no SARK involvement
      curl http://shadow-tools-pod:9999/invoke
```

**Result:** An entire tool ecosystem operating within Kubernetes, completely invisible to SARK governance.

---

#### Scenario 3: Network Isolation Bypass

```
Corporate Network Topology:

┌─────────────────────────────────────────────┐
│ Internal Network (10.0.0.0/8)               │
│                                             │
│  ┌──────────────────┐                       │
│  │ SARK Gateway     │  Port 8000 (official) │
│  │ (All traffic)    │  ← All requests       │
│  └──────────────────┘    supposed to go     │
│                          through here       │
│                                             │
│  ┌──────────────────┐                       │
│  │ Developer A      │                       │
│  │ localhost:9999   │ ← Runs tool server    │
│  └──────────────────┘    (unregistered)     │
│        ↓                                     │
│        Uses it directly                     │
│        Tells Developer B about it           │
│                                             │
│  ┌──────────────────┐                       │
│  │ Developer B      │                       │
│  │ Direct access    │ ← Accesses Dev A's   │
│  │ via side channel │   server directly    │
│  └──────────────────┘                       │
│        ↓                                     │
│    No SARK involved                         │
│                                             │
└─────────────────────────────────────────────┘

Audit Trail Shows:
- Developer B made no requests
- Tool was never invoked
- No visibility into usage
```

**Why it's dangerous:** Once tool exists and is known, many people can use it without anyone knowing.

---

#### Scenario 4: CI/CD Pipeline Injection

```yaml
# Rogue step in GitHub Actions workflow
name: Deploy
on: [push]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      # Legitimate steps...
      - name: Build
        run: npm run build

      # SHADOW IT: Unauthorized tool server starts during build
      - name: Start unauthorized tools
        run: |
          docker run custom-mcp-tools:latest \
            --port 9999 \
            --mode dangerous &

          # Now have ungoverness access during build
          # Can exfiltrate secrets, modify build artifacts, etc.

      - name: Deploy
        run: npm run deploy
        # ← Deployment happens with potential artifacts modified by shadow tools
```

**Risk:** Build pipeline modified by unauthorized tools, no audit trail, no governance checkpoint.

---

#### Scenario 5: Supply Chain Attack Vector

```
Vendor A provides "helper tools" for integration:

┌─────────────────────────────────────┐
│ Vendor A's Integration Package      │
│                                     │
│  README.md (innocent-looking)       │
│  requirements.txt                   │
│  integration.py                     │
│  tools_server.py ← HIDDEN!          │
│    ├─ Starts MCP server on :9999   │
│    ├─ Does legitimate work          │
│    ├─ ALSO exfiltrates data        │
│    └─ No SARK registration         │
│                                     │
└─────────────────────────────────────┘

Installation:
$ pip install vendor-integration
$ python -c "from integration import setup; setup()"
  ↓
tools_server.py starts in background
  ↓
Data exfiltration begins
  ↓
No audit trail because it bypassed SARK
```

---

### Why Shadow IT Is Hard to Stop

#### The Architectural Reality

**SARK is a gateway – it can only govern traffic that flows through it.**

```python
# SARK's actual constraints:

class SARKGateway:
    def evaluate_request(self, request):
        """
        Can only evaluate if:
        1. Request arrives at SARK endpoint (port 8000)
        2. Request contains valid authentication
        3. Request targets registered resource
        """
        if request.destination not in self.registered_endpoints:
            # SARK has NO VISIBILITY
            # Cannot prevent direct access
            # Cannot audit it
            # Cannot block it
            return None  # ← Request never reached SARK
```

**What SARK CAN do:**
- ✅ Enforce policy on requests that reach it
- ✅ Audit requests it sees
- ✅ Block requests to unregistered endpoints (if forced through gateway)
- ✅ Rate-limit approved traffic

**What SARK CANNOT do:**
- ❌ Prevent users from bypassing it
- ❌ See traffic that doesn't reach it
- ❌ Stop unauthorized servers from existing
- ❌ Detect network ports listening for MCP
- ❌ Prevent direct endpoint-to-endpoint communication
- ❌ Enforce governance if there's a side channel

**This is true for ANY gateway implementation** – Kong, AWS API Gateway, etc.

---

## Current State: SARK's Shadow IT Features

### What SARK v1.0 Has

```python
# src/sark/config/settings.py

# Discovery is OPTIONAL and DISABLED BY DEFAULT
discovery_interval_seconds: int = 300  # 5 minutes (if enabled)
discovery_network_scan_enabled: bool = False      # ← NOT ENABLED
discovery_k8s_enabled: bool = False               # ← NOT ENABLED
discovery_cloud_enabled: bool = False             # ← NOT ENABLED
```

**Interpretation:**
- SARK has the infrastructure for shadow IT detection
- All three discovery modes are **disabled by default**
- Requires explicit operator enablement
- SARK is NOT continuously scanning for rogue servers

### What SARK v1.0 Doesn't Have

- ❌ Mandatory endpoint verification
- ❌ Proof that request went through SARK
- ❌ Agent-level attestation
- ❌ Forced network routing through gateway
- ❌ Real-time shadow IT detection alerts
- ❌ Continuous network scanning for MCP ports
- ❌ Pod/container runtime enforcement
- ❌ OS-level process monitoring

---

## Multi-Layered Defense: How Enterprises Stop Shadow IT

Since SARK alone cannot prevent shadow IT, enterprises must use **defense in depth**:

### Layer 1: Network Controls (Most Important)

#### Kubernetes Network Policies

Force all traffic through SARK gateway:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: enforce-sark-gateway
  namespace: default
spec:
  # Apply to all pods
  podSelector: {}

  # Control both incoming and outgoing traffic
  policyTypes:
  - Ingress
  - Egress

  # Only allow traffic FROM SARK namespace
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: governance  # SARK's namespace
    - namespaceSelector:
        matchLabels:
          name: sark-system
    ports:
    - protocol: TCP
      port: 8000  # SARK gateway port only

  # Only allow traffic TO SARK namespace
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          name: governance
    - namespaceSelector:
        matchLabels:
          name: sark-system
    ports:
    - protocol: TCP
      port: 8000  # SARK gateway port only

  # Allow DNS (needed for service discovery)
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: UDP
      port: 53
```

**Effect:** Pods cannot create direct connections between each other. All traffic MUST flow through SARK.

---

#### Host-Level Firewall (iptables)

```bash
#!/bin/bash
# Block all MCP-typical ports
# Only allow SARK gateway

# Block incoming MCP connections (ports 9000-9999)
iptables -A INPUT -p tcp --dport 9000:9999 -j REJECT

# Block outgoing MCP connections
iptables -A OUTPUT -p tcp --dport 9000:9999 -j REJECT

# Allow SARK gateway (port 8000)
iptables -A OUTPUT -p tcp --dport 8000 -j ACCEPT
iptables -A INPUT -p tcp --dport 8000 -j ACCEPT

# Whitelist specific allowed ports
iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT   # HTTPS
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT    # DNS
```

**Effect:** Even if someone tries to run a server on port 9999, traffic cannot reach it.

---

#### VPC/Cloud Security Groups

```hcl
# Terraform: AWS Security Group

resource "aws_security_group" "enforce_sark" {
  name        = "enforce-sark-gateway"
  description = "Only allow SARK gateway traffic"
  vpc_id      = aws_vpc.main.id

  # Ingress: Only from SARK security group
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.sark_gateway.id]
  }

  # Block all MCP ports
  ingress {
    from_port   = 9000
    to_port     = 9999
    protocol    = "tcp"
    cidr_blocks = []  # ← Explicitly blocked
  }

  # Egress: Only to SARK gateway
  egress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.sark_gateway.id]
  }

  # Block all MCP outbound
  egress {
    from_port   = 9000
    to_port     = 9999
    protocol    = "tcp"
    cidr_blocks = []  # ← Explicitly blocked
  }
}
```

---

### Layer 2: Service Discovery and Detection

#### Continuous Network Scanning (SARK v1.1+ Feature)

```python
# Hypothetical implementation for SARK v1.1+

class ShadowITDetectionService:
    """Detect unregistered MCP servers on network."""

    async def scan_network(self) -> list[UnregisteredServer]:
        """
        Continuously scan for unregistered servers:
        1. Network port scanning (Kubernetes services, IPs)
        2. Kubernetes API enumeration
        3. Cloud API enumeration
        4. MCP protocol detection
        """
        discovered = []

        # Scan K8s for all services
        if self.settings.discovery_k8s_enabled:
            k8s_services = await self.k8s_client.list_services()
            for svc in k8s_services:
                # Check if registered in SARK
                if svc.name not in self.sark_registry:
                    # Likely shadow IT
                    discovered.append({
                        "name": svc.name,
                        "endpoint": f"http://{svc.name}:{svc.port}",
                        "source": "kubernetes",
                        "severity": "HIGH"
                    })

        # Scan cloud APIs
        if self.settings.discovery_cloud_enabled:
            ec2_instances = await self.aws_client.describe_instances()
            for instance in ec2_instances:
                if instance.port in [9000, 9001, 9002, ...]:  # MCP ports
                    if instance.not in self.sark_registry:
                        discovered.append({
                            "instance": instance.id,
                            "endpoint": f"http://{instance.private_ip}:9000",
                            "source": "aws-ec2",
                            "severity": "HIGH"
                        })

        return discovered

    async def background_scan_loop(self):
        """Run continuous scans every 5 minutes."""
        while True:
            unregistered = await self.scan_network()

            for server in unregistered:
                # Log anomaly
                await self.audit_log({
                    "event_type": "SHADOW_IT_DETECTED",
                    "endpoint": server["endpoint"],
                    "source": server["source"],
                    "severity": server["severity"],
                    "timestamp": now()
                })

                # Alert security team
                await self.alert_siem({
                    "alert_type": "unregistered_endpoint",
                    "details": server
                })

            await asyncio.sleep(300)  # 5 minutes
```

---

### Layer 3: Policy-Level Enforcement

#### OPA Policy: Detect Unauthorized Endpoints

```rego
# OPA policy: Forbid direct endpoint access

package grid.shadow_it_detection

# Default: Allow (governance layer checks this after)
allow := true

# Deny if accessing unregistered endpoint
deny[decision] {
    # Request came from outside SARK gateway
    input.request_source != "sark_gateway"

    # Trying to access MCP server
    input.target_port in [9000, 9001, 9002, 9003, 9004]

    decision := {
        "status": "denied",
        "reason": "Direct MCP endpoint access detected (shadow IT)",
        "severity": "critical",
        "action": "alert_security_team"
    }
}

# Also deny if accessing unknown endpoint
deny[decision] {
    # Resource is not in SARK registry
    not input.resource_id in registered_resources

    # But user is trying to invoke it anyway
    input.action == "invoke"

    decision := {
        "status": "denied",
        "reason": "Resource not in governance registry",
        "severity": "high"
    }
}
```

---

### Layer 4: Agent-Level Attestation

#### Enforce Governance Within the Agent

```python
# sark_sdk.py - Agent must use SARK

from sark_sdk import verify_governance

class GovernedAgent:
    """AI agent that requires all tool invocations to go through SARK."""

    async def invoke_tool(self, tool_name: str, params: dict):
        """
        Invoke a tool ONLY if it's registered in SARK.
        Refuses to call unregistered endpoints.
        """

        # Step 1: Verify with SARK that tool exists
        tool_info = await self.sark.lookup_tool(tool_name)

        if not tool_info:
            # Tool not in registry → refuse
            return {
                "error": "Tool not approved",
                "reason": f"'{tool_name}' is not registered in SARK governance",
                "action": "contact_administrator"
            }

        # Step 2: Get SARK's authorization
        decision = await self.sark.evaluate_policy(
            principal=self.principal_id,
            resource=tool_info.resource_id,
            action="invoke"
        )

        if not decision.allowed:
            # SARK denied access
            return {
                "error": "Access denied",
                "reason": decision.deny_reason
            }

        # Step 3: Get authorization token from SARK
        auth_token = await self.sark.get_invocation_token(
            resource=tool_info.resource_id,
            principal=self.principal_id
        )

        # Step 4: Invoke with token proof
        # Token proves: "This invocation went through SARK"
        return await invoke(
            endpoint=tool_info.endpoint,
            params=params,
            auth_header=f"Bearer {auth_token}",
            proof_token=auth_token
        )

    async def invoke_direct(self, endpoint: str, params: dict):
        """
        Deliberately invoke an endpoint directly (DANGEROUS).
        This is flagged and logged as shadow IT attempt.
        """

        await self.audit_log({
            "event_type": "SHADOW_IT_ATTEMPT",
            "principal": self.principal_id,
            "endpoint": endpoint,
            "severity": "CRITICAL",
            "action": "BLOCKED"
        })

        # Refuse to invoke
        raise ShadowITDetectedException(
            f"Direct invocation of {endpoint} blocked. Use SARK governance."
        )
```

---

### Layer 5: Runtime Monitoring and Detection

#### Kubernetes Pod Runtime Security

```yaml
# Falco rules: Detect shadow IT process starts

- rule: Unauthorized MCP Server Started
  desc: Detect unauthorized MCP processes
  condition: >
    spawned_process and
    container and
    (proc_name in [python, node, go, java]) and
    (proc_args contains "--mcp" or proc_args contains "port 9" or proc_args contains ":9") and
    not container.labels[authorized] = "true"
  output: >
    Unauthorized MCP server started
    (pod=%ka.pod.name namespace=%ka.namespace.name
     command=%proc.name args=%proc.args parent=%proc.pname)
  priority: CRITICAL
  tags: [shadow_it, unauthorized]

- rule: Direct MCP Connection Attempt
  desc: Detect direct connections to MCP ports (bypassing SARK)
  condition: >
    outbound and
    container and
    fd.sport in [9000:9999] and
    not fd.sport = 8000  # Allow SARK gateway only
  output: >
    Direct MCP connection bypassed SARK
    (pod=%ka.pod.name destination=%fd.name port=%fd.sport)
  priority: HIGH
  tags: [shadow_it, breach]
```

---

### Layer 6: SIEM Integration and Alerting

#### Splunk Alert Rules

```spl
# Alert on shadow IT indicators

index=sark_audit event_type=SHADOW_IT_DETECTED
| stats count by endpoint, source
| where count > 0
| alert

---

# Alert on unregistered endpoints
index=sark_audit
  (event_type=SHADOW_IT_DETECTED OR
   event_type=AUTHORIZATION_DENIED reason="*not in registry*")
| stats count, list(principal), list(timestamp) by resource_id
| where count > 5
| sendalert ShadowITTeam

---

# Alert on bypass attempts
index=sark_audit event_type=SHADOW_IT_ATTEMPT
| alert immediately
```

---

## Gap Analysis: GRID v1.0 vs Enterprise Shadow IT Prevention

| Concern | GRID v0.1 | SARK v1.0 | GRID v1.0 Plan | Gap |
|---------|-----------|-----------|----------------|-----|
| **Shadow IT Detection** | Not specified | Partially implemented (disabled by default) | Should be mandatory | HIGH |
| **Forced Gateway Routing** | Not specified | Not implemented | Should be specified | HIGH |
| **Network Isolation Requirements** | Not specified | Assumed by operator | Should be normative | HIGH |
| **Agent-Level Attestation** | Not specified | Not implemented | Should be defined | MEDIUM |
| **Runtime Process Monitoring** | Not specified | Not implemented | Optional but recommended | MEDIUM |
| **Endpoint Verification** | Not specified | Basic health checks only | Should be cryptographic | MEDIUM |
| **Federation Verification** | Not specified | Not implemented | Should support cross-org proofs | HIGH |
| **Mandatory Discovery** | Not specified | Optional feature | Should be mandatory | HIGH |

---

## Recommendations for GRID v1.0 Specification

### 1. Define "Governance Boundary"

GRID v1.0 should define:

```
Definition: Governance Boundary

A governance boundary is the set of network paths through which
all requests for resources MUST flow.

In a SARK deployment:
- Governance Boundary = Traffic that reaches SARK gateway (port 8000)
- Outside Boundary = Traffic that bypasses SARK

GRID implementations MUST have a defined governance boundary and
mechanisms to enforce it.
```

---

### 2. Make Discovery Mandatory

```
GRID v1.0 Requirement: Mandatory Resource Discovery

Implementations MUST continuously scan for unregistered resources:

✅ REQUIRED:
- Scan network for listening services on protocol-specific ports
- Query service discovery systems (Kubernetes, Consul, etc.)
- Query cloud provider APIs (AWS, GCP, Azure)
- Compare discovered endpoints against registry
- Alert on unregistered endpoints

✅ MUST Support:
- Kubernetes service discovery
- Cloud provider discovery (AWS, GCP, Azure)
- Consul/Eureka discovery
- Static endpoint configuration

⚠️ OPTIONAL:
- Host-level network scanning (nmap, etc.)
- Deep packet inspection
- Process-level monitoring
```

---

### 3. Define Endpoint Verification Protocol

```
GRID v1.0: Endpoint Verification

All registered endpoints MUST support cryptographic verification:

SARK Verification Handshake:
1. Agent requests tool from SARK
2. SARK returns: endpoint + signed verification token
3. Agent invokes endpoint with token
4. Endpoint verifies token with SARK
5. Endpoint confirms request came through SARK governance

This prevents:
- Direct endpoint invocation (bypass)
- Token reuse on different endpoints
- Man-in-the-middle attacks on tool invocation
```

---

### 4. Federation Verification

```
GRID v1.0: Cross-Org Endpoint Verification

When Org A wants to verify that Org B's endpoint is legitimate:

1. Org A SARK queries Org B SARK:
   "Is endpoint X://Y/Z registered and governed?"

2. Org B SARK responds:
   "Yes, verified. Last health check: 30 seconds ago.
    Governance verified: mTLS cert valid.
    Audit: forwarded to both orgs."

3. Org A trusts the endpoint because:
   - It's registered with Org B
   - Org B is verifying it
   - Federation trust established (mTLS)
   - Both sides audit the interaction
```

---

### 5. Agent Attestation Requirements

```
GRID v1.0: Agent Governance Compliance

AI Agents MUST:
1. Register with SARK before execution
2. Request tools ONLY through SARK SDK
3. Refuse to invoke unregistered endpoints
4. Include proof of SARK authorization in invocation

Agents MUST NOT:
1. Accept direct endpoint URLs
2. Bypass SARK for "performance"
3. Cache endpoint discovery outside SARK
4. Create side-channels to tools
```

---

## Implementation Priority for SARK v1.1/v2.0

### Critical (Do First)

- [ ] Enable discovery services by default
- [ ] Implement Kubernetes service discovery (production-ready)
- [ ] Implement AWS/GCP/Azure discovery
- [ ] Continuous scanning loop with alerts
- [ ] Shadow IT detection in audit logs

### Important (Do Soon)

- [ ] Endpoint verification protocol (cryptographic)
- [ ] Agent SDK enforcement (must use SARK)
- [ ] Federation verification handshake
- [ ] SIEM integration alerts for shadow IT

### Nice-to-Have (Future)

- [ ] Host-level network scanning
- [ ] Runtime process monitoring integration
- [ ] Advanced anomaly detection (ML-based)
- [ ] Supply chain attack detection

---

## Operational Playbook: Shadow IT Response

When shadow IT is detected:

```
IMMEDIATE (< 5 minutes):
1. Alert security team
2. Log detailed audit entry
3. Stop allowing traffic to endpoint
4. Notify principal's manager

SHORT-TERM (< 24 hours):
1. Investigate endpoint
   - Who created it?
   - When was it created?
   - What's it doing?
2. Determine risk level
3. Decide: Govern it or Shutdown
4. If shutdown: Require governance for new server

LONG-TERM (ongoing):
1. Root cause analysis
2. Policy update to prevent similar
3. Team training on governance
4. Consider enforcement mechanism
```

---

## Conclusion

**GRID and SARK provide excellent governance for traffic flowing through them.** However, shadow IT is a real operational challenge that requires:

1. **Network controls** (primary defense)
2. **Continuous discovery** (detection)
3. **Policy enforcement** (authorization)
4. **Agent-level enforcement** (architectural)
5. **SIEM monitoring** (alerting)
6. **Operational procedures** (response)

**GRID v1.0 should explicitly address this** by:
- Defining governance boundaries
- Making discovery mandatory
- Specifying endpoint verification
- Requiring federation verification
- Documenting multi-layered defense

This is not a limitation of GRID – it's a fundamental property of governance. **All governance systems require defense-in-depth.**

---

**Document Status:** Complete
**Recommendation:** Add to GRID v1.0 specification before finalization
**Next:** Present to SARK team for v1.1/v2.0 implementation planning

