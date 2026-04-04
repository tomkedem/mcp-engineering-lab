# server/server_http.py
import asyncio
import datetime
import json
import uuid
import os

from aiohttp import web
from mcp.server import Server
from mcp.server.streamable_http import StreamableHTTPServerTransport, MCP_SESSION_ID_HEADER
from mcp.types import Tool, TextContent

from policy import policy_layer
from server import (
    safe_logger,
    metrics,
    replay_store,
    approval_gate,
    limiter,
    alerting,
    generate_correlation_id,
    validate_input,
    check_permission,
    execute_tool,
    get_all_tools,
    sanitize_for_audit
)

# Configuration
class Config:
    ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
    PORT = int(os.environ.get("PORT", 8080))
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    DATABASE_TIMEOUT_SECONDS = float(os.environ.get("DATABASE_TIMEOUT_SECONDS", 5.0))
    MAX_REQUESTS_PER_MINUTE = int(os.environ.get("MAX_REQUESTS_PER_MINUTE", 100))

    @classmethod
    def validate_production(cls):
        if cls.ENVIRONMENT == "production":
            required = ["DATABASE_PASSWORD", "API_KEY", "REDIS_URL"]
            missing = [var for var in required if not os.environ.get(var)]
            if missing:
                raise RuntimeError(
                    f"Missing required environment variables: {missing}"
                )

config = Config()

# Deprecated tools registry
DEPRECATED_TOOLS = {
    "search_documents_v1": datetime.date(2026, 6, 1)
}

# Active sessions
active_sessions = {}

# MCP Server
server = Server("mcp-engineering-lab")

@server.list_tools()
async def list_tools():
    today = datetime.date.today()
    tools = get_all_tools()

    active_tools = []
    for tool in tools:
        removal_date = DEPRECATED_TOOLS.get(tool.name)
        if removal_date and today >= removal_date:
            safe_logger.info(
                "Deprecated tool removed from capabilities",
                extra={"tool": tool.name, "removal_date": str(removal_date)}
            )
            continue
        active_tools.append(tool)

    return active_tools

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    correlation_id = arguments.get("_correlation_id", generate_correlation_id())
    start_time = asyncio.get_event_loop().time()
    result_text = ""
    is_error = False

    try:
        await limiter.acquire()

        # Validate input
        error = validate_input(name, arguments)
        if error:
            metrics.record_validation_failure(name)
            result_text = f"Validation error: {error}"
            return [TextContent(type="text", text=result_text)], True

        # Check permissions
        allowed, reason = check_permission(
            arguments.get("_user_id"),
            name,
            "tool",
            arguments
        )
        if not allowed:
            metrics.record_permission_denial(name)
            result_text = f"Access denied: {reason}"
            return [TextContent(type="text", text=result_text)], True

        # Enforce policies
        policy_allowed, policy_reason = policy_layer.evaluate(
            name, arguments, arguments
        )
        if not policy_allowed:
            result_text = f"Policy violation: {policy_reason}"
            return [TextContent(type="text", text=result_text)], True

        # Execute tool
        result = await execute_tool(name, arguments)
        result_text = result[0].text if result else ""
        return result

    except Exception as e:
        is_error = True
        result_text = str(e)
        raise

    finally:
        limiter.release()
        duration_ms = (asyncio.get_event_loop().time() - start_time) * 1000
        metrics.record_tool_call(name, duration_ms, not is_error)
        alerting.check_and_alert(name)

        safe_logger.info(
            "Tool call completed",
            extra={
                "correlation_id": correlation_id,
                "tool_name": name,
                "duration_ms": round(duration_ms, 2),
                "success": not is_error
            }
        )

        replay_store.record(
            tool_name=name,
            arguments=arguments,
            result=result_text,
            is_error=is_error,
            correlation_id=correlation_id
        )

# HTTP handlers
async def handle_mcp(request: web.Request) -> web.Response:
    """Handles MCP requests with session management."""
    session_id = request.headers.get(MCP_SESSION_ID_HEADER)

    if not session_id:
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

async def handle_health(request: web.Request) -> web.Response:
    """Health check endpoint for monitoring systems."""
    return web.json_response({
        "status": "healthy",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "environment": config.ENVIRONMENT,
        "metrics": metrics.get_summary()
    })

# Application setup
app = web.Application()
app.router.add_post("/mcp", handle_mcp)
app.router.add_get("/health", handle_health)

if __name__ == "__main__":
    config.validate_production()
    safe_logger.info(
        "Starting MCP server",
        extra={
            "environment": config.ENVIRONMENT,
            "port": config.PORT
        }
    )
    web.run_app(app, host="0.0.0.0", port=config.PORT)
