const runButton = document.getElementById('run-button');
const rawOutput = document.getElementById('raw-output');
const decisionBox = document.getElementById('decision-box');

let policyEditor, inputEditor;

const initialPolicy = `# GRID Policy Example: Basic Role-Based Access Control (RBAC)
#
# This policy demonstrates simple role-based access control where
# different roles have different levels of access to resources.
#
# Roles:
# - admin: Full access to all resources
# - developer: Can execute low/medium sensitivity tools
# - viewer: Read-only access to low sensitivity resources
# - service: Service accounts with limited access

package grid.authorization

# Default deny - zero-trust principle
# All access is denied unless explicitly allowed
default allow := false

# =============================================================================
# ADMIN RULES
# =============================================================================

# Admins have unrestricted access to all resources
allow if {
    input.principal.role == "admin"
}

# =============================================================================
# DEVELOPER RULES
# =============================================================================

# Developers can execute tools with low or medium sensitivity
allow if {
    input.principal.role == "developer"
    input.action.operation == "execute"
    input.resource.sensitivity in ["low", "medium"]
}

# Developers can read any resource (but not write)
allow if {
    input.principal.role == "developer"
    input.action.operation == "read"
}

# Developers can write to low sensitivity resources only
allow if {
    input.principal.role == "developer"
    input.action.operation == "write"
    input.resource.sensitivity == "low"
}

# =============================================================================
# VIEWER RULES
# =============================================================================

# Viewers can only read low sensitivity resources
allow if {
    input.principal.role == "viewer"
    input.action.operation == "read"
    input.resource.sensitivity == "low"
}

# =============================================================================
# SERVICE ACCOUNT RULES
# =============================================================================

# Service accounts can execute tools they own
allow if {
    input.principal.role == "service"
    input.action.operation == "execute"
    input.resource.owner == input.principal.id
}

# Service accounts can read resources in their scope
allow if {
    input.principal.role == "service"
    input.action.operation == "read"
    input.resource.sensitivity in ["low", "medium"]
}

# =============================================================================
# EXPLICIT DENY RULES (Override allows)
# =============================================================================

# Deny all access to critical resources outside business hours
# (except for admins)
deny if {
    input.resource.sensitivity == "critical"
    not is_business_hours
    input.principal.role != "admin"
}

# Deny write operations to production environment for non-admins
deny if {
    input.action.operation == "write"
    input.context.environment == "production"
    input.principal.role != "admin"
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Check if current time is during business hours (9 AM - 6 PM, Mon-Fri)
is_business_hours if {
    # Parse the timestamp string into nanoseconds
    ns := time.parse_rfc3339_ns(input.context.timestamp)

    # Extract hour from nanoseconds
    hour := time.clock(ns)[0]

    # Check if between 9 AM and 6 PM UTC
    hour >= 9
    hour < 18

    # Check if weekday (not Saturday or Sunday)
    day := time.weekday(ns)
    day != "Saturday"
    day != "Sunday"
}

# =============================================================================
# DECISION METADATA
# =============================================================================

# Provide reason for the decision (useful for audit logs)
reason := "Admin has full access" if {
    input.principal.role == "admin"
}

reason := "Developer can execute low/medium sensitivity tools" if {
    input.principal.role == "developer"
    input.action.operation == "execute"
    input.resource.sensitivity in ["low", "medium"]
}

reason := "Viewer can only read low sensitivity resources" if {
    input.principal.role == "viewer"
    input.action.operation == "read"
    input.resource.sensitivity == "low"
}

reason := "Access denied: Critical resources require business hours" if {
    input.resource.sensitivity == "critical"
    not is_business_hours
    input.principal.role != "admin"
}

reason := "Access denied: Production writes require admin role" if {
    input.action.operation == "write"
    input.context.environment == "production"
    input.principal.role != "admin"
}

reason := "Access denied by default policy" if {
    not allow
}
`;

const initialInput = `{
    "principal": {
        "id": "user123",
        "role": "developer"
    },
    "action": {
        "operation": "execute"
    },
    "resource": {
        "id": "tool-abc",
        "sensitivity": "medium"
    },
    "context": {
        "timestamp": "2025-11-28T14:00:00Z"
    }
}`;

require.config({ paths: { 'vs': 'https://cdnjs.cloudflare.com/ajax/libs/monaco-editor/0.26.1/min/vs' }});
require(['vs/editor/editor.main'], function() {
    policyEditor = monaco.editor.create(document.getElementById('policy-editor'), {
        value: initialPolicy,
        language: 'go' // Rego is not supported, but Go is close enough for highlighting
    });
    inputEditor = monaco.editor.create(document.getElementById('input-editor'), {
        value: initialInput,
        language: 'json'
    });
});

runButton.addEventListener('click', async () => {
    const policy = policyEditor.getValue();
    const input = JSON.parse(inputEditor.getValue());

    try {
        const opa = await window.OpaWasm.loadPolicy(policy);
        const result = opa.evaluate(input);
        
        const decision = result[0].result;
        const allow = decision.allow === true && decision.deny !== true;
        
        decisionBox.textContent = `Decision: ${allow ? 'Allow' : 'Deny'}`;
        decisionBox.className = `decision ${allow ? 'allow' : 'deny'}`;
        
        if (decision.reason) {
            decisionBox.textContent += ` - Reason: ${decision.reason}`;
        }

        rawOutput.textContent = JSON.stringify(result, null, 2);
    } catch (err) {
        rawOutput.textContent = `Error: ${err}`;
    }
});