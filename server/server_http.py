# Session management for HTTP transport
from mcp.server.streamable_http import MCP_SESSION_ID_HEADER
import uuid

active_sessions = {}

async def handle_mcp(request: web.Request) -> web.Response:
    """
    Handles MCP requests with session management.
    """
    session_id = request.headers.get(MCP_SESSION_ID_HEADER)

    if not session_id:
        # New session
        session_id = str(uuid.uuid4())

    if session_id not in active_sessions:
        active_sessions[session_id] = {
            "created_at": datetime.datetime.utcnow().isoformat(),
            "request_count": 0
        }

    active_sessions[session_id]["request_count"] += 1

    transport = StreamableHTTPServerTransport(
        request,
        session_id=session_id
    )
    await server.connect(transport)
    return transport.response
