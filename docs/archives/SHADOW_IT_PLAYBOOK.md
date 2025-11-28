# GRID Shadow IT Playbook

This document provides an operational playbook for detecting, responding to, and preventing "shadow IT" in a GRID-governed environment.

## Table of Contents

- [What is Shadow IT?](#what-is-shadow-it)
- [Detection Strategies](#detection-strategies)
- [Response Procedures](#response-procedures)
- [Prevention Strategies](#prevention-strategies)
- [Monitoring and Alerting](#monitoring-and-alerting)

---

## What is Shadow IT?

In the context of GRID, "shadow IT" refers to any computational capabilities (MCP servers, tools, APIs, etc.) that exist on the network but are not registered in the GRID resource registry and therefore bypass all GRID governance.

For a detailed analysis of this issue, see the [GRID Shadow IT and Governance Gaps](GRID_SHADOW_IT_AND_GOVERNANCE_GAPS.md) document.

---

## Detection Strategies

### 1. Network Scanning

- **Continuous Port Scanning:** Regularly scan your network for open ports commonly used by MCP servers (e.g., 9000-9999).
- **Service Discovery:** Use tools like Consul, Eureka, or Kubernetes service discovery to identify all running services and compare them against the GRID resource registry.
- **Cloud Provider APIs:** Use cloud provider APIs (e.g., AWS EC2 `describe-instances`) to discover all running instances and their open ports.

### 2. Policy-Level Detection

- **OPA Policies:** Use Open Policy Agent (OPA) policies to detect and block requests to unregistered endpoints.
- **Agent-Level Attestation:** Require all agents to use a GRID SDK that refuses to call unregistered endpoints.

### 3. Runtime Monitoring

- **Process Monitoring:** Use tools like Falco or osquery to monitor for the startup of unauthorized processes.
- **Network Flow Analysis:** Analyze network traffic to identify direct connections between services that are not flowing through the GRID gateway.

---

## Response Procedures

When a potential shadow IT instance is detected, follow these steps:

### Immediate Response (< 5 minutes)

1. **Alert:** Trigger an alert to the security team.
2. **Log:** Create a detailed audit entry with all available information about the instance.
3. **Block:** If possible, block all traffic to and from the instance at the network level.
4. **Notify:** Notify the manager of the principal who created the instance.

### Short-Term Response (< 24 hours)

1. **Investigate:**
   - Who created the instance?
   - When was it created?
   - What is it doing?
   - What data is it accessing?
2. **Assess Risk:** Determine the risk level of the instance (e.g., low, medium, high, critical).
3. **Decide:**
   - **Govern It:** If the instance is a legitimate business tool, register it with GRID and bring it under governance.
   - **Shut It Down:** If the instance is unauthorized or malicious, shut it down immediately.

### Long-Term Response (Ongoing)

1. **Root Cause Analysis:** Determine the root cause of the shadow IT instance.
2. **Policy Update:** Update your GRID policies to prevent similar instances in the future.
3. **Training:** Provide training to the team on the importance of GRID governance.
4. **Enforcement:** Implement technical enforcement mechanisms to prevent shadow IT.

---

## Prevention Strategies

### 1. Network Controls

- **Force all traffic through the GRID gateway:** Use Kubernetes network policies, host-level firewalls, and VPC security groups to block all direct service-to-service communication.
- **Default deny:** Block all outbound traffic by default and only allow traffic to known, trusted endpoints.

### 2. Agent-Level Enforcement

- **Require all agents to use a GRID SDK:** The SDK should enforce that all tool invocations go through the GRID gateway.
- **Agent Attestation:** Use agent-level attestation to verify that all agents are running an approved version of the SDK.

### 3. Education and Training

- **Train developers on the importance of GRID governance.**
- **Make it easy to register new resources with GRID.**
- **Provide a sandbox environment for experimentation.**

---

## Monitoring and Alerting

### SIEM Integration

- **Forward all shadow IT detection events to your SIEM.**
- **Create dashboards to visualize shadow IT activity.**
- **Configure alerts for high-severity events.**

### Alert Rules

Create alert rules for the following events:

- **Unregistered endpoint detected.**
- **Direct connection to an MCP port detected.**
- **Unauthorized process started.**
- **Agent attempts to bypass GRID governance.**