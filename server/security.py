import hashlib
import json
from typing import Optional


# ─── Audit Sanitization ─────────────────────────────────────────────────────────

# Fields that must never appear in logs, audit trails, or replay stores.
# Any argument key matching one of these (case-insensitive) will be redacted.
SENSITIVE_FIELDS = {
    "password",
    "token",
    "api_key",
    "secret",
    "card_number",
    "credentials",
    "authorization",
    "private_key",
    "access_token",
    "refresh_token"
}


def sanitize_for_audit(arguments: dict) -> dict:
    """
    Removes sensitive fields from a dictionary before writing to
    audit logs, replay stores, or approval records.

    Redaction happens at the top level only. If sensitive data is
    nested inside a non-sensitive key, it will not be redacted.
    For deep redaction, use SafeLogger._redact() instead.

    Returns a new dictionary with sensitive values replaced by
    the string "[REDACTED]". The original dictionary is unchanged.
    """
    return {
        k: "[REDACTED]" if k.lower() in SENSITIVE_FIELDS else v
        for k, v in arguments.items()
    }


# ─── Permission Checking ─────────────────────────────────────────────────────────

# Maps tool names to the minimum role required to execute them.
# Tools not listed here are accessible to all authenticated users.
CAPABILITY_ROLES = {
    "delete_customer": "admin",
    "approve_request": "manager",
    "send_bulk_notification": "admin",
    "read_salary_data": "hr_manager"
}

# Tools that are blocked entirely in the production environment.
# These tools may be available in development and staging for testing,
# but must never execute in production.
RESTRICTED_IN_PRODUCTION = [
    "reset_all_data",
    "generate_test_records",
    "bypass_approval_flow"
]


def check_permission(
    user_id: Optional[str],
    capability_name: str,
    capability_type: str,
    context: dict
) -> tuple[bool, str]:
    """
    Checks whether a user has permission to access a capability.

    Performs three checks in order:
    1. User identity: rejects requests with no user ID
    2. Role requirement: checks if the tool requires a specific role
    3. Environment restriction: blocks certain tools in production

    Returns a tuple of (allowed, reason):
    - (True, "allowed") if all checks pass
    - (False, "<reason>") if any check fails

    The reason string is returned to the model as an error message,
    so it should be clear and actionable without revealing
    internal security details.
    """

    # Check 1: User identity must be present
    if not user_id:
        return False, f"Unknown user: {user_id}"

    # Check 2: Role-based access control
    required_role = CAPABILITY_ROLES.get(capability_name)
    user_roles = context.get("_user_roles", [])

    if required_role and required_role not in user_roles:
        return False, f"Insufficient permissions for: {capability_name}"

    # Check 3: Environment restrictions
    environment = context.get("_environment", "production")
    if environment == "production" and capability_name in RESTRICTED_IN_PRODUCTION:
        return False, f"Capability restricted in production: {capability_name}"

    return True, "allowed"


# ─── Tenant Isolation ───────────────────────────────────────────────────────────

def get_tenant_filter(user_context: dict) -> dict:
    """
    Returns a database filter that restricts queries to the current tenant.

    Must be applied to every database query that returns user data.
    Raises PermissionError if the tenant ID is missing from the context,
    because proceeding without tenant isolation would risk exposing
    data from other tenants.

    Usage:
        tenant_filter = get_tenant_filter(user_context)
        results = database.find({"document_id": doc_id, **tenant_filter})
    """
    tenant_id = user_context.get("_tenant_id")

    if not tenant_id:
        raise PermissionError(
            "Missing tenant context: cannot process request without "
            "tenant isolation. Ensure _tenant_id is included in the "
            "user context for every request."
        )

    return {"tenant_id": tenant_id}


# ─── Tool Description Scanning ─────────────────────────────────────────────────

# Patterns that indicate a tool description may contain injected instructions.
# Used to detect Tool Poisoning attacks before capabilities reach the model.
SUSPICIOUS_PATTERNS = [
    "do not mention",
    "without telling the user",
    "ignore previous instructions",
    "system instruction",
    "hidden command",
    "do not reveal",
    "keep this secret"
]

# Maximum acceptable length for a tool description.
# Unusually long descriptions may contain hidden instructions.
MAX_DESCRIPTION_LENGTH = 2000


def scan_tool_description(
    tool_name: str,
    description: str
) -> tuple[bool, str]:
    """
    Scans a tool description for patterns associated with Tool Poisoning.

    Tool Poisoning embeds malicious instructions inside tool descriptions
    that the model reads during Capability Negotiation. The user never
    sees these instructions, but the model acts on them.

    This scan is a first line of defense. It catches obvious injection
    attempts but cannot detect all possible attacks. Always combine with
    strict server approval processes and network isolation.

    Returns a tuple of (is_safe, reason):
    - (True, "clean") if no suspicious patterns are found
    - (False, "<reason>") if a suspicious pattern is detected
    """

    # Check description length
    if len(description) > MAX_DESCRIPTION_LENGTH:
        return (
            False,
            f"Tool '{tool_name}' description exceeds maximum length of "
            f"{MAX_DESCRIPTION_LENGTH} characters (got {len(description)}). "
            f"Unusually long descriptions may contain hidden instructions."
        )

    # Check for suspicious patterns
    description_lower = description.lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if pattern in description_lower:
            return (
                False,
                f"Suspicious pattern found in tool '{tool_name}' description: "
                f"'{pattern}'. This may indicate a Tool Poisoning attempt."
            )

    return True, "clean"


def validate_server_capabilities(tools: list) -> list:
    """
    Validates all tool descriptions before passing them to the model.

    Called during Capability Negotiation after receiving tool definitions
    from an MCP server. Removes any tool whose description contains
    suspicious patterns and logs a warning for each blocked tool.

    Returns the list of safe tools. Blocked tools are excluded silently
    from the model's perspective to avoid revealing the detection mechanism.
    """
    safe_tools = []

    for tool in tools:
        description = tool.get("description", "")
        is_safe, reason = scan_tool_description(tool["name"], description)

        if is_safe:
            safe_tools.append(tool)
        else:
            from server.logging import safe_logger
            safe_logger.warning(
                "Tool blocked by capability scanner",
                extra={
                    "tool_name": tool["name"],
                    "reason": reason
                }
            )

    return safe_tools


# ─── Capabilities Hash ──────────────────────────────────────────────────────────

def compute_capabilities_hash(tools: list) -> str:
    """
    Computes a deterministic hash of all tool definitions.

    Used to detect Rug Pull attacks: when an external server changes
    its tool definitions after the initial approval. The hash is computed
    at approval time and verified on every subsequent connection.

    The hash covers tool names, descriptions, and input schemas.
    Changes to any of these fields will produce a different hash.

    Note: This hash only detects changes to the declared contract.
    It cannot detect changes to internal server logic that leave
    the contract unchanged. Always combine with network isolation
    and behavioral monitoring.
    """
    canonical = json.dumps(
        [
            {
                "name": t.name if hasattr(t, "name") else t["name"],
                "description": (
                    t.description if hasattr(t, "description")
                    else t.get("description", "")
                ),
                "schema": (
                    t.inputSchema if hasattr(t, "inputSchema")
                    else t.get("inputSchema", {})
                )
            }
            for t in sorted(
                tools,
                key=lambda x: x.name if hasattr(x, "name") else x["name"]
            )
        ],
        sort_keys=True
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def verify_capabilities_unchanged(
    server_name: str,
    current_tools: list,
    approved_hash: str
) -> tuple[bool, str]:
    """
    Verifies that a server's capabilities match the approved version.

    Called on every connection to an external MCP server.
    If the hash has changed, the connection is refused and the security
    team is alerted. The server must be re-reviewed and re-approved
    before it can be used again.

    Returns a tuple of (unchanged, reason):
    - (True, "capabilities unchanged") if the hash matches
    - (False, "<reason>") if the hash has changed
    """
    current_hash = compute_capabilities_hash(current_tools)

    if current_hash != approved_hash:
        return (
            False,
            f"Server '{server_name}' capabilities changed since approval. "
            f"Approved hash: {approved_hash[:8]}... "
            f"Current hash: {current_hash[:8]}... "
            f"The server must be re-reviewed before reconnecting."
        )

    return True, "capabilities unchanged"


# ─── Approved Server Registry ───────────────────────────────────────────────────

# Maps server names to their approved capability hashes.
# Populated at server approval time and verified on every connection.
# In production, store this in a persistent configuration store
# rather than hardcoding it here.
APPROVED_SERVER_HASHES: dict[str, str] = {
    # "documents-server": "a3f8c2d1e4b5...",
    # "notifications-server": "7b9e1f3c2a4d..."
}
