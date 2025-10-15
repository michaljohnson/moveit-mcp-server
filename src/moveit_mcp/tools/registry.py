"""Unified tool registry for MCP server.

This module provides a centralized registry for all MCP tools.
Since MCP only allows ONE @server.list_tools() and ONE @server.call_tool() handler,
we need to aggregate all tools from different modules into single handlers.
"""

import logging
from typing import Dict, Callable, Awaitable, List

try:
    from mcp.server import Server
    from mcp.types import Tool, TextContent
except ImportError:
    pass

logger = logging.getLogger(__name__)


class ToolRegistry:
    """Central registry for all MCP tools."""

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: List[Tool] = []
        self._handlers: Dict[str, Callable] = {}

    def register_tool(self, tool: Tool, handler: Callable[[dict], Awaitable[list]]):
        """
        Register a tool and its handler.

        Args:
            tool: MCP Tool definition
            handler: Async function that handles the tool call
        """
        self._tools.append(tool)
        self._handlers[tool.name] = handler
        logger.debug(f"Registered tool: {tool.name}")

    def register_tools(self, tools: List[Tool], handlers: Dict[str, Callable]):
        """
        Register multiple tools and their handlers.

        Args:
            tools: List of MCP Tool definitions
            handlers: Dictionary mapping tool names to handler functions
        """
        for tool in tools:
            if tool.name not in handlers:
                logger.warning(f"No handler found for tool: {tool.name}")
                continue
            self.register_tool(tool, handlers[tool.name])

    def get_tools(self) -> List[Tool]:
        """Get all registered tools."""
        return self._tools

    async def handle_tool_call(self, name: str, arguments: dict) -> list:
        """
        Dispatch tool call to the appropriate handler.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result
        """
        handler = self._handlers.get(name)
        if handler:
            try:
                return await handler(arguments)
            except Exception as e:
                logger.error(f"Error handling tool '{name}': {e}", exc_info=True)
                return [TextContent(type="text", text=f"Error: {str(e)}")]
        else:
            logger.warning(f"Unknown tool: {name}")
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    def setup_server_handlers(self, server: "Server"):
        """
        Register the unified handlers with the MCP server.

        This should be called ONCE after all tools have been registered.

        Args:
            server: MCP Server instance
        """
        registry = self  # Capture self for closures

        @server.list_tools()
        async def list_all_tools() -> List[Tool]:
            """List all registered tools."""
            logger.debug(f"Listing {len(registry._tools)} tools")
            return registry.get_tools()

        @server.call_tool()
        async def handle_all_tools(name: str, arguments: dict) -> list:
            """Handle all tool calls."""
            logger.debug(f"Handling tool call: {name}")
            return await registry.handle_tool_call(name, arguments)

        logger.info(f"Registered unified handlers for {len(self._tools)} tools")
