# GRID Policy Example: Time-Based Access Control
#
# This policy demonstrates temporal access control where access
# decisions depend on time-based conditions.
#
# Time-based rules:
# - Business hours restrictions
# - Maintenance windows
# - Emergency access periods
# - Time-limited approvals
# - Scheduled access grants

package grid.authorization

# Default deny - zero-trust principle
default allow := false

# =============================================================================
# BUSINESS HOURS RULES
# =============================================================================

# Low sensitivity resources: Available 24/7
allow if {
    input.resource.sensitivity == "low"
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation in ["read", "execute"]
}

# Medium sensitivity: Business hours only
allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["medium", "high", "critical"]
    is_business_hours
    input.action.operation in ["read", "execute"]
}

# High sensitivity: Strict business hours (9 AM - 5 PM)
allow if {
    input.resource.sensitivity == "high"
    input.principal.clearance in ["high", "critical"]
    is_strict_business_hours
    input.action.operation in ["read", "execute"]
}

# Critical sensitivity: Core business hours + approval
allow if {
    input.resource.sensitivity == "critical"
    input.principal.clearance == "critical"
    is_core_business_hours
    has_time_limited_approval
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# WRITE OPERATIONS (More Time-Restrictive)
# =============================================================================

# Write to medium sensitivity: Business hours only
allow if {
    input.resource.sensitivity == "medium"
    input.principal.clearance in ["high", "critical"]
    is_business_hours
    input.action.operation == "write"
}

# Write to high/critical: Core hours + change window
allow if {
    input.resource.sensitivity in ["high", "critical"]
    input.principal.clearance == "critical"
    is_in_change_window
    has_change_approval
    input.action.operation == "write"
}

# =============================================================================
# MAINTENANCE WINDOWS
# =============================================================================

# During maintenance window: Only platform team
allow if {
    is_maintenance_window
    "platform" in input.principal.teams
    input.action.operation in ["read", "write", "execute", "manage"]
}

# Block non-maintenance operations during maintenance
deny if {
    is_maintenance_window
    not ("platform" in input.principal.teams)
    input.action.operation in ["write", "delete", "manage"]
}

# =============================================================================
# EMERGENCY ACCESS
# =============================================================================

# Emergency access: Admins can access critical resources 24/7
allow if {
    input.principal.role == "admin"
    is_emergency_declared
    input.resource.sensitivity in ["high", "critical"]
    input.action.operation in ["read", "write", "execute"]
}

# On-call engineers during incidents
allow if {
    input.principal.on_call == true
    is_incident_active
    input.resource.type in ["infrastructure", "service"]
    input.action.operation in ["read", "execute", "write"]
}

# =============================================================================
# SCHEDULED ACCESS GRANTS
# =============================================================================

# Time-limited access grants (e.g., contractor access)
allow if {
    has_active_time_grant
    input.action.operation in ["read", "execute"]
}

# Temporary elevated access (break-glass)
allow if {
    has_break_glass_access
    is_within_break_glass_window
    input.action.operation in ["read", "write", "execute"]
}

# =============================================================================
# WEEKEND AND HOLIDAY RESTRICTIONS
# =============================================================================

# Weekends: Only read access for non-critical
allow if {
    is_weekend
    input.resource.sensitivity in ["low", "medium"]
    input.principal.clearance in ["medium", "high", "critical"]
    input.action.operation == "read"
}

# Holidays: Restricted access
deny if {
    is_holiday
    input.resource.sensitivity in ["high", "critical"]
    input.action.operation in ["write", "delete"]
    not input.principal.role == "admin"
}

# =============================================================================
# RATE LIMITING BY TIME
# =============================================================================

# Limit high-frequency operations during peak hours
deny if {
    is_peak_hours
    input.resource.type == "database"
    input.action.operation == "write"
    exceeds_peak_hour_rate_limit
}

# =============================================================================
# TIMEZONE-AWARE RULES
# =============================================================================

# Regional access based on local business hours
allow if {
    input.resource.data_region != null
    is_business_hours_in_region(input.resource.data_region)
    input.principal.region == input.resource.data_region
    input.action.operation in ["read", "execute"]
}

# =============================================================================
# HELPER FUNCTIONS - TIME CHECKS
# =============================================================================

# Standard business hours: 9 AM - 6 PM, Monday-Friday
is_business_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 9
    hour < 18
    day := time.weekday(input.context.timestamp)
    day not in [0, 6]  # Not Saturday or Sunday
}

# Strict business hours: 9 AM - 5 PM, Monday-Friday
is_strict_business_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 9
    hour < 17
    day := time.weekday(input.context.timestamp)
    day not in [0, 6]
}

# Core business hours: 10 AM - 4 PM, Monday-Friday
is_core_business_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 10
    hour < 16
    day := time.weekday(input.context.timestamp)
    day not in [0, 6]
}

# Check if current time is weekend
is_weekend if {
    day := time.weekday(input.context.timestamp)
    day in [0, 6]  # Saturday or Sunday
}

# Check if current date is a holiday
is_holiday if {
    # Parse date from timestamp
    date_parts := time.parse_rfc3339_ns(input.context.timestamp)
    date_str := sprintf("%d-%02d-%02d", [date_parts[0], date_parts[1], date_parts[2]])
    
    # Check against holiday list
    date_str in input.context.holidays
}

# Check if in maintenance window
is_maintenance_window if {
    input.context.maintenance_window != null
    input.context.timestamp >= input.context.maintenance_window.start
    input.context.timestamp <= input.context.maintenance_window.end
}

# Check if in approved change window
is_in_change_window if {
    input.context.change_window != null
    input.context.timestamp >= input.context.change_window.start
    input.context.timestamp <= input.context.change_window.end
}

# Check if emergency is declared
is_emergency_declared if {
    input.context.emergency_status == "active"
}

# Check if incident is active
is_incident_active if {
    input.context.incident_status == "active"
}

# Check if during peak hours (8 AM - 10 AM, 5 PM - 7 PM)
is_peak_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 8
    hour < 10
}

is_peak_hours if {
    hour := time.clock([input.context.timestamp])[0]
    hour >= 17
    hour < 19
}

# =============================================================================
# HELPER FUNCTIONS - APPROVAL CHECKS
# =============================================================================

# Check if principal has time-limited approval
has_time_limited_approval if {
    some approval in input.principal.approvals
    approval.resource_id == input.resource.id
    approval.status == "approved"
    input.context.timestamp >= approval.valid_from
    input.context.timestamp <= approval.valid_until
}

# Check if principal has active time grant
has_active_time_grant if {
    some grant in input.principal.time_grants
    grant.resource_id == input.resource.id
    input.context.timestamp >= grant.start_time
    input.context.timestamp <= grant.end_time
}

# Check if principal has break-glass access
has_break_glass_access if {
    input.principal.break_glass_token != null
    input.principal.break_glass_token.status == "active"
}

# Check if within break-glass time window (typically 1-4 hours)
is_within_break_glass_window if {
    input.principal.break_glass_token != null
    token_age := time.diff(
        input.context.timestamp,
        input.principal.break_glass_token.issued_at
    )
    # Token valid for 4 hours (14400 seconds)
    token_age[0] < 14400
}

# Check if has change approval
has_change_approval if {
    input.context.change_ticket != null
    input.context.change_ticket.status == "approved"
}

# Check if exceeds rate limit during peak hours
exceeds_peak_hour_rate_limit if {
    input.context.request_count_last_hour > 100
}

# Check business hours in specific region
is_business_hours_in_region(region) if {
    # This would need timezone data for each region
    # Simplified example for US regions
    region == "us-east"
    hour := time.clock([input.context.timestamp])[0]
    hour >= 9
    hour < 18
}

# =============================================================================
# DECISION METADATA
# =============================================================================

reason := "Access granted during business hours" if {
    allow
    is_business_hours
}

reason := "Access granted: Emergency access active" if {
    allow
    is_emergency_declared
}

reason := "Access granted: Break-glass access used" if {
    allow
    has_break_glass_access
}

reason := "Access denied: Outside business hours" if {
    not allow
    not is_business_hours
    input.resource.sensitivity in ["medium", "high", "critical"]
}

reason := "Access denied: Maintenance window active" if {
    deny
    is_maintenance_window
}

reason := "Access denied: Holiday restrictions" if {
    deny
    is_holiday
}

reason := "Access denied: Peak hour rate limit exceeded" if {
    deny
    exceeds_peak_hour_rate_limit
}