import datetime
import uuid

from aiohttp import web
from mcp.server.streamable_http import (
    MCP_SESSION_ID_HEADER,
    StreamableHTTPServerTransport
)

from server.config import config
from server.logging import safe_logger
from server.metrics import metrics
from server.server import server
from server.discovery import handle_server_card


# ─── Session Management ─────────────────────────────────────────────────────────

# In-memory session store for tracking active connections.
# Each entry maps a session ID to basic session metadata.
#
# Limitations of in-memory storage:
# - Sessions are lost when the server restarts
# - Sessions cannot be shared across multiple server instances
#
# For production deployments with multiple instances or high availability
# requirements, replace this with an external store such as Redis.
# See section 12.4 for details on the Stateful Sessions vs Load Balancer
# problem and the available solutions.
active_sessions: dict[str, dict] = {}


def create_session(session_id: str) -> dict:
    """
    Creates a new session entry in the session store.

    Called when a request arrives without a recognized session ID,
    indicating that this is the start of a new client connection.

    Returns the newly created session metadata dictionary.
    """
    session = {
        "session_id": session_id,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "request_count": 0,
        "last_seen_at": datetime.datetime.utcnow().isoformat()
    }
    active_sessions[session_id] = session
    safe_logger.info(
        "New session created",
        extra={"session_id": session_id}
    )
    return session


def update_session(session_id: str):
    """
    Updates the request count and last seen timestamp for an existing session.

    Called on every request to track session activity.
    Used for monitoring and for identifying idle sessions to clean up.
    """
    if session_id in active_sessions:
        active_sessions[session_id]["request_count"] += 1
        active_sessions[session_id]["last_seen_at"] = (
            datetime.datetime.utcnow().isoformat()
        )


# ─── MCP Request Handler ────────────────────────────────────────────────────────

async def handle_mcp(request: web.Request) -> web.Response:
    """
    Handles incoming MCP requests over Streamable HTTP transport.

    Streamable HTTP is the recommended transport for production deployments.
    Unlike STDIO, it supports multiple concurrent sessions, network-based
    communication, and standard HTTP infrastructure such as load balancers,
    reverse proxies, and API gateways.

    Session management:
    - Reads the session ID from the MCP-Session-Id request header
    - Creates a new session if none is found
    - Updates session metadata on every request

    Each request creates a new StreamableHTTPServerTransport instance
    and connects it to the shared MCP server. The server instance is
    shared across all requests and defined in server.py.
    """
    session_id = request.headers.get(MCP_SESSION_ID_HEADER)

    if not session_id:
        # No session ID in the request: this is a new connection
        session_id = str(uuid.uuid4())
        create_session(session_id)
    elif session_id not in active_sessions:
        # Session ID present but not recognized: treat as new session
        create_session(session_id)

    update_session(session_id)

    safe_logger.info(
        "MCP request received",
        extra={
            "session_id": session_id,
            "request_count": active_sessions[session_id]["request_count"],
            "method": request.method,
            "path": request.path
        }
    )

    # Create a new transport instance for this request
    # and connect it to the shared server
    transport = StreamableHTTPServerTransport(
        request,
        session_id=session_id
    )
    await server.connect(transport)
    return transport.response


# ─── Health Check Handler ────────────────────────────────────────────────────────

async def handle_health(request: web.Request) -> web.Response:
    """
    Returns the current health status of the server.

    Used by monitoring systems, load balancers, and container orchestrators
    to determine whether the server is healthy and ready to accept requests.

    Response includes:
    - status: always "healthy" if the server is responding
    - timestamp: current UTC time in ISO format
    - environment: the current deployment environment
    - active_sessions: number of currently tracked sessions
    - metrics: per-tool call statistics

    A 200 response indicates the server is healthy.
    If this endpoint is unreachable, the server should be considered down.
    """
    return web.json_response({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "active_sessions": len(active_sessions),
        "metrics": metrics.get_summary()
    })


# ─── Approval Handlers ──────────────────────────────────────────────────────────

async def handle_approve(request: web.Request) -> web.Response:
    """
    Approves a pending approval request.

    Called by an authorized approver after reviewing the pending operation.
    The request ID is extracted from the URL path.

    Returns 200 if the approval was recorded successfully.
    Returns 404 if the request ID is not found.
    """
    from server.approval import approval_gate

    request_id = request.match_info.get("request_id")

    try:
        approval_gate.approve(request_id)
        return web.json_response({
            "status": "approved",
            "request_id": request_id,
            "approved_at": datetime.datetime.utcnow().isoformat()
        })
    except ValueError as e:
        return web.json_response(
            {"error": str(e)},
            status=404
        )


async def handle_reject(request: web.Request) -> web.Response:
    """
    Rejects a pending approval request.

    Called by an authorized approver after reviewing the pending operation.
    Accepts an optional JSON body with a "reason" field.

    Returns 200 if the rejection was recorded successfully.
    Returns 404 if the request ID is not found.
    """
    from server.approval import approval_gate

    request_id = request.match_info.get("request_id")
    body = await request.json() if request.can_read_body else {}
    reason = body.get("reason", "No reason provided")

    try:
        approval_gate.reject(request_id, reason)
        return web.json_response({
            "status": "rejected",
            "request_id": request_id,
            "reason": reason,
            "rejected_at": datetime.datetime.utcnow().isoformat()
        })
    except ValueError as e:
        return web.json_response(
            {"error": str(e)},
            status=404
        )


    return app
# ─── Application Setup ──────────────────────────────────────────────────────────

def create_app() -> web.Application:
    """
    Creates and configures the aiohttp web application.

    Registers all route handlers:
    - POST /mcp         MCP protocol endpoint
    - GET  /health      Health check for monitoring
    - POST /approvals/{request_id}/approve   Approve a pending operation
    - POST /approvals/{request_id}/reject    Reject a pending operation

    Returns the configured application instance.
    Called by the entry point below and by test fixtures.
    """
    app = web.Application()

    app.router.add_post("/mcp", handle_mcp)
    app.router.add_get("/health", handle_health)
    app.router.add_get(
        "/.well-known/mcp-server-card.json",
        handle_server_card
    )
    app.router.add_post(
        "/approvals/{request_id}/approve",
        handle_approve
    )
    app.router.add_post(
        "/approvals/{request_id}/reject",
        handle_reject
    )

    return app


# ─── HTTP Entry Point ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    """
    Entry point for running the MCP server over Streamable HTTP transport.

    Validates production configuration before starting to fail fast
    if any required environment variables are missing.

    The server listens on 0.0.0.0 to accept connections from all
    network interfaces, which is required for container deployments.
    The port is configured via the PORT environment variable.
    """
    config.validate_production()

    safe_logger.info(
        "Starting MCP server (HTTP transport)",
        extra={
            "environment": config.ENVIRONMENT,
            "port": config.PORT
        }
    )

    app = create_app()
    web.run_app(app, host="0.0.0.0", port=config.PORT)
    
