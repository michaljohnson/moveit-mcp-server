"""Tests for ToolRegistry."""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Mock MCP imports
import sys
sys.modules['mcp'] = MagicMock()
sys.modules['mcp.server'] = MagicMock()
sys.modules['mcp.types'] = MagicMock()

from moveit_mcp.tools.registry import ToolRegistry


@pytest.fixture
def registry():
    """Create a ToolRegistry for testing."""
    return ToolRegistry()


@pytest.fixture
def mock_tool():
    """Create a mock MCP Tool."""
    from mcp.types import Tool
    tool = MagicMock()
    tool.name = "test_tool"
    tool.description = "Test tool"
    tool.inputSchema = {"type": "object"}
    return tool


@pytest.mark.asyncio
async def test_register_tool(registry, mock_tool):
    """Test registering a single tool."""
    async def test_handler(arguments):
        return [{"type": "text", "text": "success"}]

    registry.register_tool(mock_tool, test_handler)

    assert len(registry.get_tools()) == 1
    assert mock_tool in registry.get_tools()
    assert "test_tool" in registry._handlers


@pytest.mark.asyncio
async def test_register_multiple_tools(registry):
    """Test registering multiple tools at once."""
    # Create mock tools
    tool1 = MagicMock()
    tool1.name = "tool1"
    tool2 = MagicMock()
    tool2.name = "tool2"

    async def handler1(args):
        return [{"type": "text", "text": "handler1"}]

    async def handler2(args):
        return [{"type": "text", "text": "handler2"}]

    tools = [tool1, tool2]
    handlers = {"tool1": handler1, "tool2": handler2}

    registry.register_tools(tools, handlers)

    assert len(registry.get_tools()) == 2
    assert "tool1" in registry._handlers
    assert "tool2" in registry._handlers


@pytest.mark.asyncio
async def test_handle_tool_call(registry, mock_tool):
    """Test dispatching tool calls."""
    result_value = [{"type": "text", "text": "success"}]

    async def test_handler(arguments):
        return result_value

    registry.register_tool(mock_tool, test_handler)

    result = await registry.handle_tool_call("test_tool", {"arg": "value"})
    assert result == result_value


@pytest.mark.asyncio
async def test_handle_unknown_tool(registry):
    """Test handling call to unknown tool."""
    result = await registry.handle_tool_call("unknown_tool", {})

    # Should return error message
    assert len(result) == 1
    # Just verify we got a non-None result (since TextContent is mocked)
    assert result[0] is not None


@pytest.mark.asyncio
async def test_handle_tool_exception(registry, mock_tool):
    """Test handling exceptions in tool handlers."""
    async def failing_handler(arguments):
        raise ValueError("Test error")

    registry.register_tool(mock_tool, failing_handler)

    result = await registry.handle_tool_call("test_tool", {})

    # Should return error message
    assert len(result) == 1


def test_setup_server_handlers(registry, mock_tool):
    """Test setting up server handlers."""
    mock_server = MagicMock()

    # Create a list to store the decorated functions
    list_tools_fn = None
    call_tool_fn = None

    def list_tools_decorator():
        def wrapper(fn):
            nonlocal list_tools_fn
            list_tools_fn = fn
            return fn
        return wrapper

    def call_tool_decorator():
        def wrapper(fn):
            nonlocal call_tool_fn
            call_tool_fn = fn
            return fn
        return wrapper

    mock_server.list_tools = list_tools_decorator
    mock_server.call_tool = call_tool_decorator

    async def test_handler(args):
        return []

    registry.register_tool(mock_tool, test_handler)
    registry.setup_server_handlers(mock_server)

    # Verify decorators were called
    assert list_tools_fn is not None
    assert call_tool_fn is not None


@pytest.mark.asyncio
async def test_register_tool_without_handler(registry):
    """Test registering tools when handler is missing."""
    tool = MagicMock()
    tool.name = "missing_handler_tool"

    # Register tools with missing handler
    registry.register_tools([tool], {})

    # Tool should not be registered
    assert len(registry.get_tools()) == 0
