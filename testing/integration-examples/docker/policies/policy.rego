package grid.authz

default allow = false

allow {
    input.principal.role == "admin"
}