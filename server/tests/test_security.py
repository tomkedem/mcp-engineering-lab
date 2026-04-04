import pytest
from server import check_permission, get_tenant_filter, sanitize_for_audit

def test_permission_denied_for_unknown_user():
    """Unknown user is denied access to any tool."""
    allowed, reason = check_permission(
        user_id="unknown_user",
        capability_name="search_documents",
        capability_type="tool",
        context={}
    )
    assert not allowed
    assert "unknown" in reason.lower()

def test_tenant_filter_raises_without_tenant():
    """Missing tenant context raises an error."""
    with pytest.raises(PermissionError):
        get_tenant_filter({})

def test_tenant_filter_returns_correct_tenant():
    """Tenant filter includes the correct tenant ID."""
    result = get_tenant_filter({"tenant_id": "tenant_123"})
    assert result["tenant_id"] == "tenant_123"

def test_sensitive_fields_redacted_in_audit():
    """Sensitive fields are redacted before audit logging."""
    arguments = {
        "query": "sample",
        "password": "secret123",
        "api_key": "key_abc"
    }
    safe = sanitize_for_audit(arguments)
    assert safe["query"] == "sample"
    assert safe["password"] == "[REDACTED]"
    assert safe["api_key"] == "[REDACTED]"

def test_admin_tool_blocked_in_production():
    """Admin tools are blocked in production environment."""
    allowed, reason = check_permission(
        user_id="admin_user",
        capability_name="reset_all_data",
        capability_type="tool",
        context={"environment": "production"}
    )
    assert not allowed
    assert "production" in reason.lower()
