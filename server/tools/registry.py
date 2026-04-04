from mcp.types import Tool

from server.tools.search import (
    SEARCH_DOCUMENTS_TOOL,
    SEARCH_DOCUMENTS_V1_TOOL,
    execute_search_documents,
    execute_search_documents_v1
)
from server.tools.metrics_tool import (
    GET_SERVER_METRICS_TOOL,
    execute_get_server_metrics
)


# Registry of all available tools.
# Maps tool names to their Tool definition and execution function.
# Add new tools here after creating their module.
TOOL_REGISTRY: dict[str, dict] = {
    "search_documents": {
        "definition": SEARCH_DOCUMENTS_TOOL,
        "handler": execute_search_documents
    },
    "search_documents_v1": {
        "definition": SEARCH_DOCUMENTS_V1_TOOL,
        "handler": execute_search_documents_v1
    },
    "get_server_metrics": {
        "definition": GET_SERVER_METRICS_TOOL,
        "handler": execute_get_server_metrics
    }
}


def get_all_tool_definitions() -> list[Tool]:
    """
    Returns all tool definitions from the registry.
    Called by the list_tools handler in server.py.
    """
    return [entry["definition"] for entry in TOOL_REGISTRY.values()]


async def execute_tool(name: str, arguments: dict) -> list:
    """
    Routes a tool call to the appropriate handler.
    Called by the call_tool handler in server.py.

    Raises ValueError if the tool name is not found in the registry.
    This error is caught by the call_tool handler and returned to
    the model as a protocol-level error.
    """
    entry = TOOL_REGISTRY.get(name)

    if not entry:
        raise ValueError(f"Tool not found: {name}")

    return await entry["handler"](arguments)
