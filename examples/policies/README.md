# GRID Policy Examples

This directory contains example policies written in Rego (Open Policy Agent language).

## Policy Categories

### Basic Policies
- **rbac-basic.rego** - Simple role-based access control
- **rbac-team-based.rego** - Team membership-based access

### Advanced Policies
- **abac-sensitivity.rego** - Attribute-based with data sensitivity
- **time-based-access.rego** - Temporal restrictions (business hours, etc.)

## Policy Structure

All GRID policies follow this structure:

```rego
package grid.authorization

# Default deny (zero-trust)
default allow := false

# Allow rules (conditions when access is granted)
allow if {
    # Conditions here
}

# Deny rules (explicit denials, override allows)
deny if {
    # Conditions here
}

# Helper functions
helper_function if {
    # Reusable logic
}
```

## Testing Policies

### Using OPA CLI

```bash
# Test all policies
opa test examples/policies/

# Test specific policy
opa test examples/policies/rbac-basic.rego

# Evaluate with input
echo '{"principal": {"role": "developer"}, "resource": {"sensitivity": "medium"}}' | \
  opa eval -d examples/policies/rbac-basic.rego \
  -I "data.grid.authorization.allow"
```

### Using SARK

If you have SARK deployed:

```bash
# Upload policy
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -d @rbac-basic.rego

# Test evaluation
curl -X POST http://localhost:8000/api/v1/policy/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "principal_id": "alice@company.com",
    "resource_id": "jira-server",
    "action": "execute"
  }'
```

## Policy Best Practices

1. **Always start with `default allow := false`** - Zero-trust principle
2. **Use explicit deny rules** - Deny overrides allow
3. **Document your policies** - Add comments explaining logic
4. **Test thoroughly** - Include test cases
5. **Version your policies** - Track changes over time
6. **Keep policies simple** - Complex logic should be in helper functions

## Common Patterns

### Role-Based Access
```rego
allow if {
    input.principal.role == "admin"
}
```

### Team-Based Access
```rego
allow if {
    some team in input.principal.teams
    team in input.resource.managers
}
```

### Sensitivity-Based Access
```rego
allow if {
    input.resource.sensitivity == "low"
}

allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["medium", "high", "critical"]
}
```

### Time-Based Access
```rego
allow if {
    is_business_hours
    input.resource.sensitivity != "critical"
}

is_business_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 9
    hour < 18
}
```

## Input Schema

Policies receive this input structure:

```json
{
  "principal": {
    "id": "alice@company.com",
    "type": "human",
    "role": "developer",
    "teams": ["backend", "security"],
    "attributes": {
      "department": "Engineering",
      "clearance": "high"
    }
  },
  "resource": {
    "id": "jira-server-1",
    "type": "tool",
    "sensitivity": "medium",
    "managers": ["backend"]
  },
  "action": {
    "operation": "execute",
    "parameters": {}
  },
  "context": {
    "timestamp": "2025-11-27T19:00:00Z",
    "ip_address": "10.1.2.3",
    "environment": "production"
  }
}
```

## Contributing

See [CONTRIBUTING.md](../../CONTRIBUTING.md) for guidelines on contributing new policy examples.

---

**Questions?** See the [GRID Specification](../../GRID_PROTOCOL_SPECIFICATION_v0.1.md) §5 for complete policy documentation.