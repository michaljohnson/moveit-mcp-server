"""Tests for execution tool implementations."""

import asyncio

import pytest
from unittest.mock import MagicMock

from moveit_mcp.tools.execution import get_execution_tools


@pytest.fixture
def execution_tools(mock_moveit_wrapper, op_manager, mock_server_instance):
    """Get execution tools and handlers."""
    tools, handlers = get_execution_tools(
        mock_moveit_wrapper, op_manager, server_instance=mock_server_instance
    )
    return tools, handlers


@pytest.fixture
def tools(execution_tools):
    return execution_tools[0]


@pytest.fixture
def handlers(execution_tools):
    return execution_tools[1]


def test_execution_tools_count(tools):
    """Test that all 4 execution tools are registered."""
    assert len(tools) == 4


def test_execution_tool_names(tools):
    """Test execution tool names."""
    names = {t.name for t in tools}
    assert names == {"execute_plan", "get_execution_status", "stop_execution", "plan_and_execute"}


def test_execution_handlers_match_tools(tools, handlers):
    """Test that every tool has a matching handler."""
    for tool in tools:
        assert tool.name in handlers


@pytest.mark.asyncio
async def test_execute_plan_no_trajectory(handlers, op_manager):
    """Test execute_plan when no trajectory is available."""
    await op_manager.start()
    try:
        result = await handlers["execute_plan"]({})
        assert "No trajectory available" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_get_execution_status_not_found(handlers, op_manager):
    """Test get_execution_status with non-existent operation."""
    await op_manager.start()
    try:
        result = await handlers["get_execution_status"]({"operation_id": "nonexistent"})
        assert "not found" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_stop_execution_not_found(handlers, op_manager):
    """Test stop_execution with non-existent operation."""
    await op_manager.start()
    try:
        result = await handlers["stop_execution"]({"operation_id": "nonexistent"})
        assert "Could not stop" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_and_execute_named_state(handlers, op_manager):
    """Test plan_and_execute with named state target."""
    await op_manager.start()
    try:
        result = await handlers["plan_and_execute"]({
            "group": "panda_arm",
            "target_type": "named_state",
            "target": {"state_name": "ready"},
        })
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_and_execute_pose(handlers, op_manager):
    """Test plan_and_execute with pose target."""
    await op_manager.start()
    try:
        result = await handlers["plan_and_execute"]({
            "group": "panda_arm",
            "target_type": "pose",
            "target": {
                "position": [0.3, 0.0, 0.5],
                "orientation": [0.0, 0.0, 0.0, 1.0],
            },
            "timeout": 5.0,
        })
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_and_execute_joint_state(handlers, op_manager):
    """Test plan_and_execute with joint state target."""
    await op_manager.start()
    try:
        result = await handlers["plan_and_execute"]({
            "group": "panda_arm",
            "target_type": "joint_state",
            "target": {
                "joint_positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
            },
        })
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_plan_and_execute_invalid_target_type(handlers, op_manager):
    """Test plan_and_execute with invalid target type."""
    await op_manager.start()
    try:
        result = await handlers["plan_and_execute"]({
            "group": "panda_arm",
            "target_type": "invalid_type",
            "target": {},
        })
        # The operation is submitted async, so we get an operation ID
        assert "Operation ID" in result[0].text
    finally:
        await op_manager.stop()


def test_plan_and_execute_schema(tools):
    """Test plan_and_execute input schema."""
    tool = next(t for t in tools if t.name == "plan_and_execute")
    schema = tool.inputSchema
    assert set(schema["required"]) == {"group", "target_type", "target"}
    assert schema["properties"]["target_type"]["enum"] == ["pose", "joint_state", "named_state"]
