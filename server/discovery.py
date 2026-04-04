from aiohttp import web


# Static Server Card document describing this server's capabilities.
# Update this document whenever tools or resources are added or removed.
# The card is served at /.well-known/mcp-server-card.json following
# the .well-known URI convention defined in RFC 8615.
SERVER_CARD = {
    "name": "mcp-engineering-lab",
    "version": "1.0.0",
    "description": (
        "MCP server companion for the book "
        "MCP Systems Engineering by Tomer Kedem"
    ),
    "transport": {
        "type": "streamable-http",
        "endpoint": "/mcp"
    },
    "capabilities": {
        "tools": True,
        "resources": True,
        "prompts": False
    },
    "tools": [
        {
            "name": "search_documents",
            "description": "Search documents by a text query",
            "version": "2"
        },
        {
            "name": "get_server_metrics",
            "description": "Returns server metrics summary"
        }
    ],
    "resources": [
        {
            "uri_prefix": "document://",
            "description": "Read documents by ID"
        }
    ],
    "contact": {
        "name": "Tomer Kedem",
        "url": "https://github.com/tomerkedem/mcp-engineering-lab"
    }
}


async def handle_server_card(request: web.Request) -> web.Response:
    """
    Returns the MCP Server Card for this server.

    The Server Card is a static JSON document that describes the server's
    capabilities, transport, and contact information.

    Used by discovery tools and host applications to learn about
    this server's capabilities without establishing a full MCP connection.
    """
    return web.json_response(SERVER_CARD)
