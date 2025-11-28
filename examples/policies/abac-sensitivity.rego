# GRID Policy Example: Attribute-Based Access Control (ABAC) with Sensitivity Levels
#
# This policy demonstrates attribute-based access control where access
# decisions are based on attributes of the principal, resource, and context.
#
# Key Attributes:
# - Principal: clearance_level, department, region
# - Resource: sensitivity_level, classification, data_category
# - Context: environment, time, location

package grid.authorization

# Default deny - zero-trust principle
default allow := false

# =============================================================================
# SENSITIVITY LEVEL RULES
# =============================================================================

# Public/Low sensitivity: Anyone authenticated can access
allow if {
    input.resource.sensitivity == "low"
    input.principal.id != null  # Must be authenticated
    input.action.operation in ["read", "execute"]
}

# Medium sensitivity: Requires medium clearance or higher
allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation in ["read", "execute"]
}

# High sensitivity: Requires high clearance or higher
allow if {
    input.resource.sensitivity == "high"
    input.principal.clearance in ["high", "critical"]
    input.action.operation in ["read", "execute"]
}

# Critical sensitivity: Requires critical clearance + additional checks
allow if {
    input.resource.sensitivity == "critical"
    input.principal.clearance == "critical"
    is_business_hours
    is_secure_environment
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# DATA CLASSIFICATION RULES
# =============================================================================

# Public data: No restrictions
allow if {
    input.resource.classification == "public"
    input.action.operation == "read"
}

# Internal data: Must be employee
allow if {
    input.resource.classification == "internal"
    input.principal.type in ["human", "service"]
    input.principal.attributes.employee == true
    input.action.operation in ["read", "execute"]
}

# Confidential data: Requires clearance + department match
allow if {
    input.resource.classification == "confidential"
    input.principal.clearance in ["high", "critical"]
    department_has_access
    input.action.operation in ["read", "execute"]
}

# Secret data: Requires critical clearance + explicit approval
allow if {
    input.resource.classification == "secret"
    input.principal.clearance == "critical"
    has_explicit_approval
    is_business_hours
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# WRITE OPERATIONS (More Restrictive)
# =============================================================================

# Write to low sensitivity: Requires medium clearance
allow if {
    input.resource.sensitivity == "low"
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation == "write"
}

# Write to medium sensitivity: Requires high clearance
allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["high", "critical"]
    input.action.operation == "write"
    is_business_hours
}

# Write to high/critical: Requires critical clearance + approval
allow if {
    input.resource.sensitivity in ["high", "critical"]
    input.principal.clearance == "critical"
    has_explicit_approval
    is_business_hours
    is_secure_environment
    input.action.operation == "write"
}

# =============================================================================
# DEPARTMENT-BASED ACCESS
# =============================================================================

# Engineering can access technical resources
allow if {
    input.principal.department == "engineering"
    input.resource.data_category in ["code", "infrastructure", "technical"]
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation in ["read", "execute"]
}

# Finance can access financial resources
allow if {
    input.principal.department == "finance"
    input.resource.data_category in ["financial", "accounting"]
    input.principal.clearance in ["high", "critical"]
    input.action.operation in ["read", "execute", "write"]
}

# HR can access personnel resources
allow if {
    input.principal.department == "hr"
    input.resource.data_category in ["personnel", "payroll"]
    input.principal.clearance in ["high", "critical"]
    input.action.operation in ["read", "execute", "write"]
}

# Legal can access all resources for compliance
allow if {
    input.principal.department == "legal"
    input.principal.clearance in ["high", "critical"]
    input.action.operation in ["read", "audit"]
}

# =============================================================================
# REGION-BASED ACCESS (Data Residency)
# =============================================================================

# Data must be accessed from same region (GDPR, data residency)
allow if {
    input.resource.data_region != null
    input.principal.region == input.resource.data_region
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation in ["read", "execute"]
}

# Cross-region access requires explicit approval
allow if {
    input.resource.data_region != null
    input.principal.region != input.resource.data_region
    has_cross_region_approval
    input.principal.clearance in ["high", "critical"]
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# CONTEXT-BASED RULES
# =============================================================================

# Production environment: Higher restrictions
allow if {
    input.context.environment == "production"
    input.principal.clearance in ["high", "critical"]
    input.resource.sensitivity in ["low", "medium"]
    is_business_hours
    input.action.operation in ["read", "execute"]
}

# Development environment: More permissive
allow if {
    input.context.environment in ["dev", "staging"]
    input.principal.clearance in ["medium", "high", "critical"]
    input.resource.sensitivity in ["low", "medium", "high"]
    input.action.operation in ["read", "write", "execute"]
}

# =============================================================================
# EXPLICIT DENY RULES
# =============================================================================

# Deny critical operations outside business hours
deny if {
    input.resource.sensitivity == "critical"
    not is_business_hours
}

# Deny access from untrusted networks
deny if {
    input.context.network_zone == "untrusted"
    input.resource.sensitivity in ["high", "critical"]
}

# Deny cross-region access to PII without approval
deny if {
    input.resource.data_category == "pii"
    input.principal.region != input.resource.data_region
    not has_cross_region_approval
}

# Deny write operations in production without change approval
deny if {
    input.context.environment == "production"
    input.action.operation in ["write", "delete"]
    not has_change_approval
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Check if current time is during business hours
is_business_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 9
    hour < 18
    day := time.weekday(input.context.timestamp)
    day not in [0, 6]
}

# Check if environment is secure (not public network)
is_secure_environment if {
    input.context.network_zone in ["corporate", "vpn", "trusted"]
}

# Check if principal's department has access to resource category
department_has_access if {
    # Engineering can access technical resources
    input.principal.department == "engineering"
    input.resource.data_category in ["code", "infrastructure", "technical"]
}

department_has_access if {
    # Finance can access financial resources
    input.principal.department == "finance"
    input.resource.data_category in ["financial", "accounting"]
}

department_has_access if {
    # HR can access personnel resources
    input.principal.department == "hr"
    input.resource.data_category in ["personnel", "payroll"]
}

# Check if principal has explicit approval for this resource
has_explicit_approval if {
    some approval in input.principal.approvals
    approval.resource_id == input.resource.id
    approval.status == "approved"
    approval.expires_at > input.context.timestamp
}

# Check if principal has cross-region access approval
has_cross_region_approval if {
    some approval in input.principal.approvals
    approval.type == "cross_region_access"
    approval.status == "approved"
    approval.expires_at > input.context.timestamp
}

# Check if there's a change approval for production writes
has_change_approval if {
    input.context.change_ticket != null
    input.context.change_ticket.status == "approved"
}

# =============================================================================
# DECISION METADATA
# =============================================================================

reason := sprintf("Access granted: %s clearance for %s sensitivity resource", 
    [input.principal.clearance, input.resource.sensitivity]) if {
    allow
}

reason := "Access denied: Insufficient clearance level" if {
    not allow
    input.principal.clearance == "low"
    input.resource.sensitivity in ["medium", "high", "critical"]
}

reason := "Access denied: Critical resources require business hours" if {
    deny
    input.resource.sensitivity == "critical"
    not is_business_hours
}

reason := "Access denied: Untrusted network for sensitive resource" if {
    deny
    input.context.network_zone == "untrusted"
}

reason := "Access denied: Cross-region access requires approval" if {
    deny
    input.principal.region != input.resource.data_region
    not has_cross_region_approval
}