# This package contains all MCP resource definitions and their read logic.
# Each module in this package is responsible for one resource domain.
#
# Resources are read-only by definition. A resource module must never
# modify system state. If a capability requires modifying state,
# it belongs in server/tools/ as a Tool, not here.
#
# Adding a new resource:
# 1. Create a new module in this package (e.g., resources/customers.py)
# 2. Define the Resource object and the read function
# 3. Register both in server/resources/registry.py
#
# Resource modules must not import from server.py to avoid circular imports.
# All shared utilities are imported from their dedicated modules:
#   - server.security   for tenant isolation and permission checking
#   - server.logging    for safe logging
