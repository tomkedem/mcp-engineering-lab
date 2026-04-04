import datetime
import json
from typing import Optional

from mcp.types import TextContent, Tool

from server.logging import safe_logger


# ─── Tool Definitions ───────────────────────────────────────────────────────────

SEARCH_DOCUMENTS_TOOL = Tool(
    name="search_documents",
    description="""Searches documents by a text query. Current version: v2.

    Changes from v1: 'filters' parameter added for advanced filtering.
    v1 (search_documents_v1) remains available until 2026-06-01.

    Side effects: None. This tool is read-only and does not modify any data.
    Safe to call multiple times with the same arguments.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "The search query. Must be a non-empty string. "
                    "Maximum 200 characters."
                ),
                "maxLength": 200
            },
            "max_results": {
                "type": "integer",
                "description": (
                    "Maximum number of results to return. "
                    "Must be between 1 and 20. Defaults to 10."
                ),
                "minimum": 1,
                "maximum": 20,
                "default": 10
            },
            "filters": {
                "type": "object",
                "description": (
                    "Optional filters to narrow the search results. "
                    "Added in v2. All filter fields are optional."
                ),
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter results by document category."
                    },
                    "date_from": {
                        "type": "string",
                        "format": "date",
                        "description": (
                            "Filter results to documents created on or after "
                            "this date. Format: YYYY-MM-DD."
                        )
                    }
                }
            }
        },
        "required": ["query"]
    }
)

SEARCH_DOCUMENTS_V1_TOOL = Tool(
    name="search_documents_v1",
    description="""DEPRECATED. Use search_documents (v2) instead.

    This tool will be removed on 2026-06-01.
    Migrate by switching to search_documents and optionally adding the
    'filters' parameter for advanced filtering.

    Side effects: None.
    """,
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query. Maximum 200 characters.",
                "maxLength": 200
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results. Between 1 and 20.",
                "minimum": 1,
                "maximum": 20,
                "default": 10
            }
        },
        "required": ["query"]
    }
)


# ─── Validation ─────────────────────────────────────────────────────────────────

def validate_search_input(arguments: dict) -> Optional[str]:
    """
    Validates the input arguments for search_documents and search_documents_v1.

    Validation is performed before any business logic to ensure the model
    receives a clear, actionable error message when input is invalid.
    This prevents the model from proceeding with incorrect assumptions.

    Returns an error message string if validation fails, None if valid.
    Checks are performed in order: presence, type, content, range.
    """
    query = arguments.get("query")
    max_results = arguments.get("max_results", 10)

    # Check presence before type to give a more specific error message
    if query is None:
        return "Missing required parameter: query"

    if not isinstance(query, str):
        return "Parameter 'query' must be a string"

    if len(query.strip()) == 0:
        return "Parameter 'query' cannot be empty"

    if len(query) > 200:
        return (
            f"Parameter 'query' exceeds maximum length of 200 characters "
            f"(got {len(query)})"
        )

    if not isinstance(max_results, int):
        return "Parameter 'max_results' must be an integer"

    if max_results < 1 or max_results > 20:
        return (
            f"Parameter 'max_results' must be between 1 and 20 "
            f"(got {max_results})"
        )

    return None


# ─── Execution ──────────────────────────────────────────────────────────────────

async def _run_search(
    query: str,
    max_results: int,
    filters: Optional[dict]
) -> list:
    """
    Core search execution logic shared by v1 and v2.

    Currently returns a static sample result for demonstration.
    In production, replace this with a real search implementation
    that queries your document store and applies the provided filters.

    The result format is intentionally simple and stable.
    Any changes to the result schema are considered breaking changes
    and require a new tool version.
    """
    # Sample result for demonstration purposes.
    # Replace with actual database or search engine query.
    results = [
        {
            "id": "1",
            "title": "Sample Document",
            "score": 0.95,
            "category": "general",
            "created_at": "2026-01-01"
        }
    ]

    # Apply category filter if provided
    if filters and filters.get("category"):
        results = [
            r for r in results
            if r.get("category") == filters["category"]
        ]

    # Apply date filter if provided
    if filters and filters.get("date_from"):
        date_from = filters["date_from"]
        results = [
            r for r in results
            if r.get("created_at", "") >= date_from
        ]

    # Respect max_results limit
    results = results[:max_results]

    return [
        TextContent(
            type="text",
            text=json.dumps(results, indent=2)
        )
    ]


async def execute_search_documents(arguments: dict) -> list:
    """
    Executes search_documents v2.

    Validates input, then delegates to the core search logic.
    Returns isError=True with a clear message if validation fails.
    """
    error = validate_search_input(arguments)
    if error:
        return [
            TextContent(type="text", text=f"Validation error: {error}")
        ], True

    query = arguments["query"].strip()
    max_results = arguments.get("max_results", 10)
    filters = arguments.get("filters")

    return await _run_search(query, max_results, filters)


async def execute_search_documents_v1(arguments: dict) -> list:
    """
    Executes the deprecated search_documents v1.

    Logs a deprecation warning on every call to track migration progress.
    Delegates to the core search logic without filters, since v1 does
    not support the filters parameter.

    Remove this function and its registry entry on 2026-06-01.
    """
    safe_logger.warning(
        "Deprecated tool called",
        extra={
            "tool": "search_documents_v1",
            "migration_deadline": "2026-06-01",
            "migration_target": "search_documents"
        }
    )

    error = validate_search_input(arguments)
    if error:
        return [
            TextContent(type="text", text=f"Validation error: {error}")
        ], True

    query = arguments["query"].strip()
    max_results = arguments.get("max_results", 10)

    # v1 does not support filters
    return await _run_search(query, max_results, filters=None)
