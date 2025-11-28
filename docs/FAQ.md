# GRID Protocol FAQ

This document answers frequently asked questions about the GRID protocol.

## Table of Contents

- [General](#general)
- [Technical](#technical)
- [Comparison](#comparison)
- [Community](#community)

---

## General

### What is GRID?

GRID (Governed Resource Interaction Definition) is a universal governance protocol for machine-to-machine interactions. It standardizes how one computational system (a "principal") requests access to capabilities or resources provided by another (a "resource provider").

### What is the difference between GRID and SARK?

- **GRID** is the specification.
- **SARK** is the reference implementation of the GRID specification.

Think of it like this: GRID is to SARK as DNS is to BIND.

### What is the current status of GRID?

The current version of the GRID specification is v0.1. The SARK reference implementation is production-ready for MCP governance.

### When is v1.0 planned?

GRID v1.0 is planned for 2026 Q1-Q2. It will include support for federation and multiple protocols.

---

## Technical

### Is GRID just for MCP/AI?

No. GRID is protocol-agnostic and can be used to govern any machine-to-machine interaction, including HTTP, gRPC, and custom protocols.

### What is the performance impact of GRID?

GRID is designed for high performance. Policy evaluation decisions are cached to minimize latency.

- **Cache hits:** <5ms
- **Cache misses:** ~50ms

In production, SARK achieves a cache hit rate of 80-95%.

### What about shadow IT?

GRID can only govern traffic that flows through it. To prevent "shadow IT" (unauthorized services running outside of GRID's governance), you must use defense-in-depth strategies, such as network controls and service discovery.

For more information, see the [GRID Shadow IT and Governance Gaps](GRID_SHADOW_IT_AND_GOVERNANCE_GAPS.md) document.

---

## Comparison

### How does GRID compare to OAuth/OIDC?

OAuth and OIDC are primarily focused on authentication and user consent. GRID is focused on fine-grained authorization and policy enforcement.

GRID can be used in conjunction with OAuth/OIDC. For example, you can use OIDC to authenticate a user and then use GRID to authorize their access to resources.

### How does GRID compare to traditional RBAC?

Traditional RBAC systems are often hard-coded and difficult to change. GRID uses a policy-first approach, with declarative policies that are easy to read, write, and test.

GRID also supports attribute-based access control (ABAC) and other advanced authorization models.

### How does GRID compare to API Gateway solutions?

API gateways are primarily focused on routing, rate limiting, and authentication. GRID is focused on fine-grained authorization and policy enforcement.

GRID can be used in conjunction with an API gateway. For example, you can use an API gateway to handle authentication and then use GRID to handle authorization.

### How does GRID compare to a service mesh (Istio, Linkerd)?

A service mesh is focused on managing service-to-service communication, including routing, load balancing, and observability. GRID is focused on fine-grained authorization and policy enforcement.

GRID can be used in conjunction with a service mesh. For example, you can use a service mesh to handle routing and then use GRID to handle authorization.

---

## Community

### How can I contribute?

We welcome contributions from everyone! Please see the [Contribution Guidelines](CONTRIBUTING.md) for more information.

### Where can I ask questions?

- **General questions:** [GitHub Discussions](https://github.com/anthropics/grid-protocol/discussions)
- **Bug reports:** [GitHub Issues](https://github.com/anthropics/grid-protocol/issues)
- **Specification questions:** Reference the spec or ask in Discussions