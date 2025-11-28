# GRID Policy Example: Team-Based Access Control
#
# This policy demonstrates team-based access control where access
# is granted based on team membership and resource ownership.
#
# Concepts:
# - Team membership determines access
# - Resources are owned/managed by teams
# - Cross-team collaboration with explicit grants
# - Team leads have elevated permissions

package grid.authorization

# Default deny - zero-trust principle
default allow := false

# =============================================================================
# ADMIN RULES (Override all team restrictions)
# =============================================================================

# Admins bypass all team restrictions
allow if {
    input.principal.role == "admin"
}

# =============================================================================
# TEAM MEMBER RULES
# =============================================================================

# Team members can access resources managed by their team
allow if {
    # Check if principal is in any team
    some team_id in input.principal.teams
    
    # Check if that team manages the resource
    team_id in input.resource.managers
    
    # Allow read and execute operations
    input.action.operation in ["read", "execute"]
}

# Team members can write to resources owned by their team
# (but only if sensitivity is not critical)
allow if {
    some team_id in input.principal.teams
    team_id in input.resource.managers
    input.action.operation == "write"
    input.resource.sensitivity != "critical"
}

# =============================================================================
# TEAM LEAD RULES
# =============================================================================

# Team leads can manage resources for their teams
allow if {
    # Check if principal is a team lead
    some team_id in input.principal.teams
    input.principal.is_team_lead[team_id] == true
    
    # Check if managing their team's resource
    team_id in input.resource.managers
    
    # Allow management operations
    input.action.operation in ["read", "write", "execute", "manage"]
}

# Team leads can create new resources for their team
allow if {
    some team_id in input.principal.teams
    input.principal.is_team_lead[team_id] == true
    input.action.operation == "create"
    input.resource.type in ["tool", "service", "data"]
}

# Team leads can grant access to external teams
allow if {
    some team_id in input.principal.teams
    input.principal.is_team_lead[team_id] == true
    team_id in input.resource.managers
    input.action.operation == "grant_access"
}

# =============================================================================
# CROSS-TEAM COLLABORATION
# =============================================================================

# Allow access if resource explicitly grants access to principal's team
allow if {
    # Check if any of principal's teams are in allowed_teams
    some team_id in input.principal.teams
    team_id in input.resource.allowed_teams
    
    # Only read and execute for cross-team access
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# SPECIAL TEAM RULES
# =============================================================================

# Security team can audit all resources
allow if {
    "security" in input.principal.teams
    input.action.operation == "audit"
}

# Security team can read all resources (for security reviews)
allow if {
    "security" in input.principal.teams
    input.action.operation == "read"
}

# Platform team can manage infrastructure resources
allow if {
    "platform" in input.principal.teams
    input.resource.type in ["infrastructure", "service"]
    input.action.operation in ["read", "write", "execute", "manage"]
}

# =============================================================================
# EXPLICIT DENY RULES
# =============================================================================

# Deny critical resource modifications outside business hours
# (even for team leads, except admins)
deny if {
    input.resource.sensitivity == "critical"
    input.action.operation in ["write", "delete", "manage"]
    not is_business_hours
    input.principal.role != "admin"
}

# Deny cross-team write access (must be same team)
deny if {
    input.action.operation in ["write", "delete"]
    not has_team_overlap(input.principal.teams, input.resource.managers)
    input.principal.role != "admin"
}

# Deny access to archived resources
deny if {
    input.resource.status == "archived"
    input.action.operation != "read"
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

# Check if there's any overlap between two sets of teams
has_team_overlap(principal_teams, resource_teams) if {
    some team in principal_teams
    team in resource_teams
}

# Check if principal is a team lead for any of their teams
is_any_team_lead if {
    some team_id in input.principal.teams
    input.principal.is_team_lead[team_id] == true
}

# =============================================================================
# DECISION METADATA
# =============================================================================

reason := "Admin has full access" if {
    input.principal.role == "admin"
}

reason := "Team member accessing team-managed resource" if {
    some team_id in input.principal.teams
    team_id in input.resource.managers
}

reason := "Team lead managing team resource" if {
    is_any_team_lead
    has_team_overlap(input.principal.teams, input.resource.managers)
}

reason := "Cross-team collaboration allowed" if {
    some team_id in input.principal.teams
    team_id in input.resource.allowed_teams
}

reason := "Security team audit access" if {
    "security" in input.principal.teams
    input.action.operation == "audit"
}

reason := "Access denied: Not a member of resource's team" if {
    not allow
    not has_team_overlap(input.principal.teams, input.resource.managers)
}

reason := "Access denied: Critical resource outside business hours" if {
    deny
    input.resource.sensitivity == "critical"
    not is_business_hours
}