# GRID Protocol Tutorial: Build Your First Governance Policy

**Time:** 30 minutes  
**Level:** Beginner  
**Prerequisites:** Basic understanding of access control concepts

---

## What You'll Learn

By the end of this tutorial, you'll be able to:
1. Understand GRID's core abstractions
2. Write a basic governance policy in Rego
3. Test your policy with sample data
4. Deploy your policy to a GRID implementation

---

## Step 1: Understanding the Basics (5 minutes)

### The Five Core Abstractions

Every GRID governance decision involves these five elements:

```
┌─────────────┐
│  Principal  │ ← Who is making the request?
└─────────────┘   (alice@company.com, AI agent, service)
       ↓
┌─────────────┐
│   Action    │ ← What do they want to do?
└─────────────┘   (read, write, execute)
       ↓
┌─────────────┐
│  Resource   │ ← What are they accessing?
└─────────────┘   (database, API, tool)
       ↓
┌─────────────┐
│   Policy    │ ← Is it allowed?
└─────────────┘   (rules that decide)
       ↓
┌─────────────┐
│    Audit    │ ← Record what happened
└─────────────┘   (immutable log)
```

### Example Scenario

**Scenario:** Alice (a developer) wants to query the Jira API.

- **Principal:** alice@company.com (role: developer)
- **Resource:** jira-api (sensitivity: medium)
- **Action:** execute (query tickets)
- **Policy:** "Developers can execute medium sensitivity tools"
- **Audit:** Log the access attempt and decision

---

## Step 2: Write Your First Policy (10 minutes)

Let's create a simple policy that allows developers to access development tools.

### Create the Policy File

Create a file named `my-first-policy.rego`:

```rego
# My First GRID Policy
package grid.authorization

# Default deny - zero-trust principle
# Nothing is allowed unless explicitly permitted
default allow := false

# Rule 1: Admins can do anything
allow if {
    input.principal.role == "admin"
}

# Rule 2: Developers can execute low/medium sensitivity tools
allow if {
    input.principal.role == "developer"
    input.action.operation == "execute"
    input.resource.sensitivity in ["low", "medium"]
}

# Rule 3: Everyone can read low sensitivity resources
allow if {
    input.resource.sensitivity == "low"
    input.action.operation == "read"
}
```

### Understanding the Policy

**Line by line:**

1. `package grid.authorization` - Declares this is a GRID authorization policy
2. `default allow := false` - **Zero-trust**: Deny everything by default
3. `allow if { ... }` - Rules that grant access when conditions are met
4. `input.principal.role` - Access the principal's role attribute
5. `input.resource.sensitivity` - Access the resource's sensitivity level

---

## Step 3: Test Your Policy (10 minutes)

### Install OPA (Open Policy Agent)

```bash
# macOS
brew install opa

# Linux
curl -L -o opa https://openpolicyagent.org/downloads/latest/opa_linux_amd64
chmod +x opa

# Windows
# Download from https://www.openpolicyagent.org/downloads/
```

### Create Test Input

Create `test-input.json`:

```json
{
  "principal": {
    "id": "alice@company.com",
    "role": "developer",
    "teams": ["backend"]
  },
  "resource": {
    "id": "jira-api",
    "type": "tool",
    "sensitivity": "medium"
  },
  "action": {
    "operation": "execute"
  },
  "context": {
    "timestamp": "2025-11-27T19:00:00Z",
    "environment": "production"
  }
}
```

### Test the Policy

```bash
# Evaluate the policy
opa eval -d my-first-policy.rego \
  -i test-input.json \
  "data.grid.authorization.allow"

# Expected output:
# {
#   "result": [
#     {
#       "expressions": [
#         {
#           "value": true,  ← Access allowed!
#           "text": "data.grid.authorization.allow"
#         }
#       ]
#     }
#   ]
# }
```

### Test Different Scenarios

**Test 1: Viewer trying to write (should be denied)**

```json
{
  "principal": {
    "id": "bob@company.com",
    "role": "viewer"
  },
  "resource": {
    "sensitivity": "high"
  },
  "action": {
    "operation": "write"
  }
}
```

```bash
opa eval -d my-first-policy.rego -i test-input.json \
  "data.grid.authorization.allow"
# Result: false (denied)
```

**Test 2: Admin accessing critical resource (should be allowed)**

```json
{
  "principal": {
    "id": "admin@company.com",
    "role": "admin"
  },
  "resource": {
    "sensitivity": "critical"
  },
  "action": {
    "operation": "write"
  }
}
```

```bash
opa eval -d my-first-policy.rego -i test-input.json \
  "data.grid.authorization.allow"
# Result: true (allowed)
```

---

## Step 4: Add Business Logic (5 minutes)

Let's make the policy more realistic by adding business hours restrictions.

### Enhanced Policy

```rego
package grid.authorization

default allow := false

# Admins: Full access 24/7
allow if {
    input.principal.role == "admin"
}

# Developers: Execute tools during business hours
allow if {
    input.principal.role == "developer"
    input.action.operation == "execute"
    input.resource.sensitivity in ["low", "medium"]
    is_business_hours
}

# Everyone: Read low sensitivity anytime
allow if {
    input.resource.sensitivity == "low"
    input.action.operation == "read"
}

# Helper function: Check business hours
is_business_hours if {
    # Extract hour from timestamp
    hour := time.clock([input.context.timestamp])[0]
    
    # Between 9 AM and 6 PM
    hour >= 9
    hour < 18
    
    # Monday through Friday
    day := time.weekday(input.context.timestamp)
    day not in [0, 6]  # 0=Sunday, 6=Saturday
}
```

### Test Business Hours

```bash
# Test during business hours (2 PM on a Tuesday)
echo '{
  "principal": {"role": "developer"},
  "resource": {"sensitivity": "medium"},
  "action": {"operation": "execute"},
  "context": {"timestamp": "2025-11-25T14:00:00Z"}
}' | opa eval -d my-first-policy.rego -I \
  "data.grid.authorization.allow"
# Result: true

# Test outside business hours (8 PM)
echo '{
  "principal": {"role": "developer"},
  "resource": {"sensitivity": "medium"},
  "action": {"operation": "execute"},
  "context": {"timestamp": "2025-11-25T20:00:00Z"}
}' | opa eval -d my-first-policy.rego -I \
  "data.grid.authorization.allow"
# Result: false
```

---

## Step 5: Deploy to SARK (Optional)

If you have SARK deployed, you can upload your policy:

```bash
# Upload policy
curl -X POST http://localhost:8000/api/v1/policies \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "my-first-policy",
    "type": "authorization",
    "content": "'"$(cat my-first-policy.rego)"'"
  }'

# Test via SARK API
curl -X POST http://localhost:8000/api/v1/policy/evaluate \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "principal_id": "alice@company.com",
    "resource_id": "jira-api",
    "action": "execute"
  }'
```

---

## Next Steps

### Learn More

1. **Advanced Policies**
   - [`examples/policies/rbac-team-based.rego`](examples/policies/rbac-team-based.rego) - Team-based access
   - [`examples/policies/abac-sensitivity.rego`](examples/policies/abac-sensitivity.rego) - Attribute-based
   - [`examples/policies/time-based-access.rego`](examples/policies/time-based-access.rego) - Temporal rules

2. **Protocol Adapters**
   - [`examples/adapters/http-adapter-template.py`](examples/adapters/http-adapter-template.py) - HTTP/REST
   - [`examples/adapters/grpc-adapter-template.py`](examples/adapters/grpc-adapter-template.py) - gRPC

3. **Full Specification**
   - [GRID Protocol Specification](GRID_PROTOCOL_SPECIFICATION_v0.1.md) - Complete technical spec
   - [Gap Analysis](GRID_GAP_ANALYSIS_AND_IMPLEMENTATION_NOTES.md) - SARK compliance

### Common Patterns

**Pattern 1: Role-Based Access**
```rego
allow if {
    input.principal.role in ["admin", "developer"]
    input.action.operation == "read"
}
```

**Pattern 2: Team-Based Access**
```rego
allow if {
    some team in input.principal.teams
    team in input.resource.managers
}
```

**Pattern 3: Sensitivity-Based Access**
```rego
allow if {
    input.resource.sensitivity == "low"
}

allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["medium", "high"]
}
```

---

## Troubleshooting

### Policy Not Working?

1. **Check syntax:**
   ```bash
   opa check my-first-policy.rego
   ```

2. **Debug evaluation:**
   ```bash
   opa eval -d my-first-policy.rego -i test-input.json \
     --explain=full "data.grid.authorization.allow"
   ```

3. **Common mistakes:**
   - Forgot `default allow := false`
   - Typo in field names (`input.principal.role` not `input.user.role`)
   - Missing package declaration
   - Incorrect timestamp format

### Need Help?

- [OPA Documentation](https://www.openpolicyagent.org/docs/)
- [GRID Specification](GRID_PROTOCOL_SPECIFICATION_v0.1.md)
- [Example Policies](examples/policies/)

---

## Summary

You've learned:
- ✅ GRID's five core abstractions
- ✅ How to write a basic policy in Rego
- ✅ How to test policies with OPA
- ✅ How to add business logic (time-based rules)
- ✅ How to deploy to SARK (optional)

**Next:** Explore [advanced policy examples](examples/policies/) or read the [full specification](GRID_PROTOCOL_SPECIFICATION_v0.1.md).

---

**Happy governing! 🚀**