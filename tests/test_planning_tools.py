"""Tests for planning tool implementations."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from moveit_mcp.tools.planning import get_planning_tools


@pytest.fixture
def planning_tools(mock_moveit_wrapper, op_manager, mock_server_instance):
    """Get planning tools and handlers."""
    tools, handlers = get_planning_tools(
        mock_moveit_wrapper, op_manager, server_instance=mock_server_instance
    )
    return tools, handlers


@pytest.fixture
def tools(planning_tools):
    return planning_tools[0]


@pytest.fixture
def handlers(planning_tools):
    return planning_tools[1]


def test_planning_tools_count(tools):
    """Test that all 4 planning tools are registered."""
    assert len(tools) == 4


def test_planning_tool_names(tools):
    """Test planning tool names."""
    names = {t.name for t in tools}
    assert names == {"plan_to_pose", "plan_to_joint_state", "plan_to_named_state", "get_plan_result"}


def test_planning_handlers_match_tools(tools, handlers):
    """Test that every tool has a matching handler."""
    for tool in tools:
        assert tool.name in handlers


def test_plan_to_pose_schema(tools):
    """Test plan_to_pose input schema has required fields."""
    tool = next(t for t in tools if t.name == "plan_to_pose")
    schema = tool.inputSchema
    assert "group" in schema["properties"]
    assert "position" in schema["properties"]
    assert "orientation" in schema["properties"]
    assert set(schema["required"]) == {"group", "position", "orientation"}


@pytest.mark.asyncio
async def test_plan_to_pose_handler(handlers, op_manager):
    """Test plan_to_pose handler submits an operation."""
    await op_manager.start()
    try:
        result = await handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": [0.3, 0.0, 0.5],
            "orientation": [0.0, 1.0, 0.0, 0.0],
        })
        assert len(result) == 1
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_to_pose_invalid_position(handlers, op_manager):
    """Test plan_to_pose rejects invalid position."""
    await op_manager.start()
    try:
        result = await handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": [0.3, 0.0],  # Only 2 elements
            "orientation": [0.0, 1.0, 0.0, 0.0],
        })
        assert "Error" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_to_joint_state_handler(handlers, op_manager):
    """Test plan_to_joint_state handler."""
    await op_manager.start()
    try:
        result = await handlers["plan_to_joint_state"]({
            "group": "panda_arm",
            "joint_positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
        })
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_to_named_state_handler(handlers, op_manager):
    """Test plan_to_named_state handler."""
    await op_manager.start()
    try:
        result = await handlers["plan_to_named_state"]({
            "group": "panda_arm",
            "state_name": "ready",
        })
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_get_plan_result_not_found(handlers, op_manager):
    """Test get_plan_result with non-existent operation."""
    await op_manager.start()
    try:
        result = await handlers["get_plan_result"]({"operation_id": "nonexistent"})
        assert "not found" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_server_not_initialized(mock_moveit_wrapper, op_manager):
    """Test that handlers check server initialization."""
    server = MagicMock()
    server.is_initialized = MagicMock(return_value=False)

    tools, handlers = get_planning_tools(mock_moveit_wrapper, op_manager, server_instance=server)

    await op_manager.start()
    try:
        result = await handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": [0.3, 0.0, 0.5],
            "orientation": [0.0, 0.0, 0.0, 1.0],
        })
        assert len(result) == 1
        assert "Error" in result[0].text
        assert "not fully initialized" in result[0].text
    finally:
        await op_manager.stop()
