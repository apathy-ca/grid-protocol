# GRID Protocol Integration Guide

This document provides guidance on integrating existing systems with the GRID protocol.

## Table of Contents

- [Integration Strategies](#integration-strategies)
- [Migrating from Traditional RBAC](#migrating-from-traditional-rbac)
- [Compatibility Considerations](#compatibility-considerations)
- [Testing Your Integration](#testing-your-integration)

---

## Integration Strategies

### 1. Centralized Gateway

Deploy a centralized GRID gateway and route all traffic to your existing services through it.

**Steps:**

1. Deploy a GRID gateway (e.g., SARK).
2. Configure your network to route all traffic to your services through the gateway.
3. Register your existing services as resources in GRID.
4. Create policies in GRID to govern access to your services.

**Pros:**
- No changes required to your existing services.
- Centralized control and visibility.

**Cons:**
- Single point of failure.
- Can become a performance bottleneck.

### 2. Sidecar Proxy

Deploy a lightweight GRID proxy as a sidecar container alongside each of your existing services.

**Steps:**

1. Deploy a GRID sidecar proxy alongside each of your services.
2. Configure the sidecar to intercept all outbound traffic from your service.
3. Create policies in GRID to govern access to downstream services.

**Pros:**
- Decentralized and scalable.
- No single point of failure.

**Cons:**
- More complex to manage and operate.
- Higher resource overhead.

### 3. SDK Integration

Integrate a GRID SDK directly into your existing services.

**Steps:**

1. Add the GRID SDK to your service's dependencies.
2. Use the SDK to evaluate GRID policies before accessing resources.
3. Use the SDK to record audit events.

**Pros:**
- Fine-grained control over policy evaluation.
- No need for a separate gateway or proxy.

**Cons:**
- Requires code changes to your existing services.
- Can be more complex to implement.

---

## Migrating from Traditional RBAC

### 1. Export Your Existing Roles

Export your existing roles and permissions to a structured format (e.g., CSV, JSON).

### 2. Map Roles to GRID Policies

Map your existing roles to GRID policies. For example, a role with `read` and `write` permissions on a resource can be mapped to a GRID policy that allows `read` and `write` actions on that resource.

### 3. Import Policies into GRID

Use the GRID API to import your new policies into your GRID implementation.

### 4. Test Your Policies

Use the GRID policy evaluation API to test your new policies and ensure they are working as expected.

---

## Compatibility Considerations

### Authentication

GRID supports a variety of authentication methods (OIDC, LDAP, SAML, API keys, etc.). Ensure that your existing authentication system is compatible with your GRID implementation.

### Protocol Adapters

If your existing services use a protocol that is not natively supported by your GRID implementation, you will need to create a protocol adapter. See the [Protocol Adapter Examples](examples/adapters/) for templates and guidance.

---

## Testing Your Integration

### Unit Tests

Write unit tests to verify that your GRID policies are working as expected.

### Integration Tests

Write integration tests to verify that your existing services are correctly integrated with GRID.

### End-to-End Tests

Write end-to-end tests to verify that your entire system is working as expected, from the principal to the resource provider.