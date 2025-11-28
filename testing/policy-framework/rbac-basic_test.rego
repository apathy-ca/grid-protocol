# Test cases for rbac-basic.rego
package grid.authorization

# =============================================================================
# ADMIN TESTS
# =============================================================================

test_admin_can_do_anything if {
    allow with input as {
        "principal": {"role": "admin"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "critical"}
    }
}

# =============================================================================
# DEVELOPER TESTS
# =============================================================================

test_developer_can_execute_medium_sensitivity if {
    allow with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "medium"}
    }
}

test_developer_cannot_execute_critical_sensitivity if {
    not allow with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "critical"}
    }
}

test_developer_can_read_any_resource if {
    allow with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "read"},
        "resource": {"sensitivity": "high"}
    }
}

test_developer_can_write_low_sensitivity if {
    allow with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "write"},
        "resource": {"sensitivity": "low"}
    }
}

test_developer_cannot_write_high_sensitivity if {
    not allow with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "write"},
        "resource": {"sensitivity": "high"}
    }
}

# =============================================================================
# VIEWER TESTS
# =============================================================================

test_viewer_can_read_low_sensitivity if {
    allow with input as {
        "principal": {"role": "viewer"},
        "action": {"operation": "read"},
        "resource": {"sensitivity": "low"}
    }
}

test_viewer_cannot_read_high_sensitivity if {
    not allow with input as {
        "principal": {"role": "viewer"},
        "action": {"operation": "read"},
        "resource": {"sensitivity": "high"}
    }
}

test_viewer_cannot_write if {
    not allow with input as {
        "principal": {"role": "viewer"},
        "action": {"operation": "write"},
        "resource": {"sensitivity": "low"}
    }
}

# =============================================================================
# DENY RULE TESTS
# =============================================================================

test_deny_critical_outside_business_hours if {
    # This timestamp is outside business hours
    ts := "2025-11-28T20:00:00Z"
    deny with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "critical"},
        "context": {"timestamp": ts}
    }
}

test_allow_critical_during_business_hours if {
    # This timestamp is during business hours
    ts := "2025-11-28T14:00:00Z"
    # Need to mock time.now() or pass it in context
    # For this policy, we pass it in the context
    not deny with input as {
        "principal": {"role": "developer"},
        "action": {"operation": "execute"},
        "resource": {"sensitivity": "critical"},
        "context": {"timestamp": ts}
    }
}
