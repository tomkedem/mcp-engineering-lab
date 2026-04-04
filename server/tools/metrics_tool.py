import json

from mcp.types import TextContent, Tool

from server.metrics import metrics


# ─── Tool Definition ────────────────────────────────────────────────────────────

GET_SERVER_METRICS_TOOL = Tool(
    name="get_server_metrics",
    description="""Returns a summary of current server metrics.

    Includes per-tool statistics:
    - Total call count
    - Error count and error rate percentage
    - Average response duration in milliseconds
    - Validation failure count
    - Permission denial count

    Intended for monitoring and debugging purposes only.
    Should not be called as part of normal user workflows.

    Side effects: None. This tool is read-only.
    Safe to call multiple times with the same arguments.
    """,
    inputSchema={
        "type": "object",
        "properties": {},
        "required": []
    }
)


# ─── Execution ──────────────────────────────────────────────────────────────────

async def execute_get_server_metrics(arguments: dict) -> list:
    """
    Returns the current metrics summary from the metrics singleton.

    No validation required as this tool accepts no input parameters.
    The metrics summary is serialized to JSON and returned as a
    TextContent block for the model to read.

    In production, consider restricting this tool to admin users only
    by adding it to CAPABILITY_ROLES in server/security.py:
        "get_server_metrics": "admin"
    """
    summary = metrics.get_summary()

    return [
        TextContent(
            type="text",
            text=json.dumps(summary, indent=2)
        )
    ]
