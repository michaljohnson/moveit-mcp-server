"""Tests for the unified tool registry."""

import pytest
from unittest.mock import MagicMock, AsyncMock

from moveit_mcp.tools.registry import ToolRegistry

try:
    from mcp.types import Tool, TextContent
except ImportError:
    Tool = MagicMock
    TextContent = MagicMock


@pytest.fixture
def registry():
    return ToolRegistry()


@pytest.fixture
def sample_tool():
    return Tool(
        name="test_tool",
        description="A test tool",
        inputSchema={
            "type": "object",
            "properties": {"arg1": {"type": "string"}},
            "required": ["arg1"],
        },
    )


@pytest.fixture
def sample_handler():
    async def handler(arguments):
        return [TextContent(type="text", text=f"Result: {arguments.get('arg1')}")]
    return handler


def test_register_tool(registry, sample_tool, sample_handler):
    """Test registering a single tool."""
    registry.register_tool(sample_tool, sample_handler)
    tools = registry.get_tools()
    assert len(tools) == 1
    assert tools[0].name == "test_tool"


def test_register_multiple_tools(registry):
    """Test registering multiple tools at once."""
    tools = [
        Tool(name="tool1", description="Tool 1", inputSchema={"type": "object", "properties": {}}),
        Tool(name="tool2", description="Tool 2", inputSchema={"type": "object", "properties": {}}),
    ]
    handlers = {
        "tool1": AsyncMock(return_value=[]),
        "tool2": AsyncMock(return_value=[]),
    }
    registry.register_tools(tools, handlers)
    assert len(registry.get_tools()) == 2


def test_register_tools_missing_handler(registry):
    """Test that tools without handlers are skipped."""
    tools = [
        Tool(name="has_handler", description="OK", inputSchema={"type": "object", "properties": {}}),
        Tool(name="no_handler", description="Missing", inputSchema={"type": "object", "properties": {}}),
    ]
    handlers = {"has_handler": AsyncMock(return_value=[])}
    registry.register_tools(tools, handlers)
    assert len(registry.get_tools()) == 1
    assert registry.get_tools()[0].name == "has_handler"


@pytest.mark.asyncio
async def test_handle_tool_call(registry, sample_tool, sample_handler):
    """Test dispatching a tool call."""
    registry.register_tool(sample_tool, sample_handler)
    result = await registry.handle_tool_call("test_tool", {"arg1": "hello"})
    assert len(result) == 1
    assert "hello" in result[0].text


@pytest.mark.asyncio
async def test_handle_unknown_tool(registry):
    """Test handling a call to an unknown tool."""
    result = await registry.handle_tool_call("nonexistent", {})
    assert len(result) == 1
    assert "Unknown tool" in result[0].text


@pytest.mark.asyncio
async def test_handle_tool_error(registry):
    """Test handling a tool that raises an exception."""
    async def bad_handler(arguments):
        raise ValueError("Something went wrong")

    tool = Tool(name="bad_tool", description="Breaks", inputSchema={"type": "object", "properties": {}})
    registry.register_tool(tool, bad_handler)

    result = await registry.handle_tool_call("bad_tool", {})
    assert len(result) == 1
    assert "Error" in result[0].text


def test_setup_server_handlers(registry, sample_tool, sample_handler):
    """Test setting up unified server handlers."""
    registry.register_tool(sample_tool, sample_handler)
    mock_server = MagicMock()
    registry.setup_server_handlers(mock_server)

    # Verify decorators were called
    mock_server.list_tools.assert_called_once()
    mock_server.call_tool.assert_called_once()
