
import asyncio
import time

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent

from server.approval import approval_gate
from server.concurrency import limiter
from server.logging import safe_logger
from server.metrics import alerting, metrics
from server.replay import replay_store
from server.resources.registry import (
    get_all_resource_definitions,
    read_resource as route_read_resource
)
from server.security import check_permission
from server.tools.registry import execute_tool as route_execute_tool
from server.tools.registry import get_all_tool_definitions
from server.utils import generate_correlation_id


# ─── MCP Server Instance ────────────────────────────────────────────────────────

# Central MCP server instance.
# All tool and resource handlers are registered against this instance.
# The same instance is used by both the STDIO entry point (server.py)
# and the HTTP entry point (server_http.py).
server = Server("mcp-engineering-lab")


# ─── Resource Handlers ──────────────────────────────────────────────────────────

@server.list_resources()
async def list_resources():
    """
    Returns all registered resource definitions.
    Called during Capability Negotiation when a client connects.
    Definitions are loaded from the resource registry.
    """
    return get_all_resource_definitions()


@server.read_resource()
async def read_resource(uri: str):
    """
    Routes a resource read request to the appropriate handler.
    Raises ValueError if no handler is registered for the given URI.
    The error is returned to the model as a protocol-level error.
    """
    return await route_read_resource(uri)


# ─── Tool Handlers ──────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools():
    """
    Returns all registered tool definitions.
    Called during Capability Negotiation when a client connects.
    Definitions are loaded from the tool registry.
    """
    return get_all_tool_definitions()


@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """
    Central handler for all tool calls.

    Executes the following pipeline for every tool call:
    1. Generate or extract Correlation ID for request tracing
    2. Acquire a concurrency slot to prevent resource exhaustion
    3. Check permissions against the security layer
    4. Delegate execution to the tool registry
    5. Record metrics and replay data in the finally block

    The finally block ensures that metrics and replay recording always
    happen, regardless of whether the tool call succeeded or failed.
    This is critical for accurate monitoring and failure analysis.

    Returns isError=True with a clear message if any pipeline step fails.
    Raises exceptions for unexpected infrastructure failures.
    """
    correlation_id = arguments.get(
        "_correlation_id",
        generate_correlation_id()
    )
    start_time = time.time()
    result_text = ""
    is_error = False

    try:
        # Acquire concurrency slot before any work begins
        await limiter.acquire()

        safe_logger.info(
            "Tool call started",
            extra={
                "correlation_id": correlation_id,
                "tool_name": name,
                "user_id": arguments.get("_user_id", "anonymous"),
                "tenant_id": arguments.get("_tenant_id", "unknown")
            }
        )

        # Permission check before any business logic
        allowed, reason = check_permission(
            arguments.get("_user_id", "anonymous"),
            name,
            "tool",
            arguments
        )

        if not allowed:
            metrics.record_permission_denial(name)
            result_text = f"Access denied: {reason}"
            return [TextContent(type="text", text=result_text)], True

        # Delegate to the tool registry
        result = await route_execute_tool(name, arguments)

        # Extract result text for replay recording
        if isinstance(result, tuple):
            result_content, is_error = result[0], result[1] if len(result) > 1 else False
            result_text = result_content[0].text if result_content else ""
        else:
            result_text = result[0].text if result else ""

        return result

    except Exception as e:
        is_error = True
        result_text = str(e)
        safe_logger.error(
            "Tool call raised exception",
            extra={
                "correlation_id": correlation_id,
                "tool_name": name,
                "error": str(e)
            }
        )
        raise

    finally:
        # Always release concurrency slot
        limiter.release()

        duration_ms = (time.time() - start_time) * 1000

        # Record metrics for monitoring and alerting
        metrics.record_tool_call(name, duration_ms, not is_error)
        alerting.check_and_alert(name)

        # Record for replay capability
        replay_store.record(
            tool_name=name,
            arguments=arguments,
            result=result_text,
            is_error=is_error,
            correlation_id=correlation_id
        )

        safe_logger.info(
            "Tool call completed",
            extra={
                "correlation_id": correlation_id,
                "tool_name": name,
                "duration_ms": round(duration_ms, 2),
                "success": not is_error
            }
        )


# ─── STDIO Entry Point ──────────────────────────────────────────────────────────

async def main():
    """
    Entry point for running the MCP server over STDIO transport.

    STDIO transport is used for local development and testing.
    For production deployments, use server_http.py with Streamable HTTP.

    The server runs until the STDIO streams are closed by the client.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
