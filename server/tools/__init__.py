# This package contains all MCP tool definitions and their execution logic.
# Each module in this package is responsible for one tool or a closely
# related group of tools that share the same domain.
#
# Adding a new tool:
# 1. Create a new module in this package (e.g., tools/orders.py)
# 2. Define the Tool object and the execution function
# 3. Register both in server/tools/registry.py
#
# Tool modules must not import from server.py to avoid circular imports.
# All shared utilities are imported from their dedicated modules:
#   - server.security   for permission checking and sanitization
#   - server.logging    for safe logging
#   - server.metrics    for recording call outcomes
