# GRID Protocol API Reference

This document provides a reference for the GRID Protocol API. This API is used to evaluate policies, manage resources, and query the audit log.

## Table of Contents

- [Authentication](#authentication)
- [Policy API](#policy-api)
- [Resource API](#resource-api)
- [Audit API](#audit-api)
- [Error Handling](#error-handling)

---

## Authentication

All API requests must be authenticated using a bearer token. The token should be included in the `Authorization` header:

```
Authorization: Bearer <your-token>
```

Tokens can be obtained through the authentication methods supported by your GRID implementation (e.g., OIDC, LDAP, SAML).

---

## Policy API

### Evaluate a Policy

Evaluates a policy and returns an authorization decision.

- **Endpoint:** `POST /api/v1/policy/evaluate`
- **Permissions:** Any authenticated principal

**Request Body:**

```json
{
  "principal_id": "alice@company.com",
  "resource_id": "jira-server",
  "action": "execute",
  "context": {
    "ip_address": "10.1.2.3",
    "timestamp": "2025-11-27T19:00:00Z"
  }
}
```

**Response (200 OK):**

```json
{
  "allowed": true,
  "reason": "Developer can execute medium sensitivity tools",
  "policy_id": "rbac-default",
  "audit_id": "event-123"
}
```

**Response (403 Forbidden):**

```json
{
  "allowed": false,
  "reason": "Access denied: Critical resources require business hours",
  "policy_id": "time-based-access",
  "audit_id": "event-124"
}
```

---

## Resource API

### List Resources

Lists all registered resources.

- **Endpoint:** `GET /api/v1/resources`
- **Permissions:** `resource:read`

**Query Parameters:**

- `type`: Filter by resource type (e.g., `tool`, `data`, `service`)
- `sensitivity`: Filter by sensitivity level (e.g., `low`, `medium`, `high`, `critical`)

**Response (200 OK):**

```json
[
  {
    "id": "jira-server",
    "type": "tool",
    "name": "Jira Server",
    "sensitivity": "medium"
  },
  {
    "id": "postgres-prod-db",
    "type": "data",
    "name": "Production Database",
    "sensitivity": "critical"
  }
]
```

### Register a Resource

Registers a new resource with GRID.

- **Endpoint:** `POST /api/v1/resources`
- **Permissions:** `resource:write`

**Request Body:**

```json
{
  "id": "my-new-tool",
  "type": "tool",
  "name": "My New Tool",
  "sensitivity": "medium"
}
```

**Response (201 Created):**

```json
{
  "id": "my-new-tool",
  "type": "tool",
  "name": "My New Tool",
  "sensitivity": "medium"
}
```

---

## Audit API

### Query Audit Log

Queries the audit log for security events.

- **Endpoint:** `GET /api/v1/audit`
- **Permissions:** `audit:read`

**Query Parameters:**

- `from_timestamp`: Start of the time range (ISO 8601)
- `to_timestamp`: End of the time range (ISO 8601)
- `principal_id`: Filter by principal ID
- `resource_id`: Filter by resource ID
- `decision`: Filter by decision (`allow`, `deny`, `error`)

**Response (200 OK):**

```json
[
  {
    "id": "event-123",
    "timestamp": "2025-11-27T19:00:00Z",
    "principal_id": "alice@company.com",
    "resource_id": "jira-server",
    "action": "execute",
    "decision": "allow",
    "reason": "Developer can execute medium sensitivity tools"
  },
  {
    "id": "event-124",
    "timestamp": "2025-11-27T23:00:00Z",
    "principal_id": "bob@company.com",
    "resource_id": "postgres-prod-db",
    "action": "write",
    "decision": "deny",
    "reason": "Critical sensitivity database access denied outside work hours"
  }
]
```

---

## Error Handling

The API uses standard HTTP status codes to indicate the success or failure of a request.

- **2xx:** Success
- **4xx:** Client error (e.g., invalid request, authentication failure)
- **5xx:** Server error

All error responses include a JSON body with a descriptive error message:

```json
{
  "error": "Invalid request",
  "message": "Missing required field: principal_id"
}