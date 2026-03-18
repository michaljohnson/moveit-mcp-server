"""Tests for query tool implementations."""

import pytest
from unittest.mock import MagicMock

from moveit_mcp.tools.queries import get_query_tools


@pytest.fixture
def query_tools(mock_moveit_wrapper, mock_server_instance):
    """Get query tools and handlers."""
    tools, handlers = get_query_tools(
        mock_moveit_wrapper, server_instance=mock_server_instance
    )
    return tools, handlers


@pytest.fixture
def tools(query_tools):
    return query_tools[0]


@pytest.fixture
def handlers(query_tools):
    return query_tools[1]


def test_query_tools_count(tools):
    """Test that all 5 query tools are registered."""
    assert len(tools) == 5


def test_query_tool_names(tools):
    """Test query tool names."""
    names = {t.name for t in tools}
    assert names == {
        "get_current_joint_state", "get_current_pose", "compute_fk",
        "compute_ik", "list_planning_groups",
    }


def test_query_handlers_match_tools(tools, handlers):
    """Test that every tool has a matching handler."""
    for tool in tools:
        assert tool.name in handlers


@pytest.mark.asyncio
async def test_get_current_joint_state(handlers, mock_moveit_wrapper):
    """Test getting current joint state."""
    result = await handlers["get_current_joint_state"]({"group": "panda_arm"})
    text = result[0].text
    assert "panda_arm" in text
    assert "panda_joint1" in text
    mock_moveit_wrapper.get_current_state.assert_called_once_with("panda_arm")


@pytest.mark.asyncio
async def test_get_current_pose(handlers, mock_moveit_wrapper):
    """Test getting current end-effector pose."""
    result = await handlers["get_current_pose"]({"group": "panda_arm"})
    text = result[0].text
    assert "panda_arm" in text
    assert "Position" in text
    assert "Orientation" in text


@pytest.mark.asyncio
async def test_get_current_pose_with_link(handlers, mock_moveit_wrapper):
    """Test getting pose for a specific link."""
    result = await handlers["get_current_pose"]({
        "group": "panda_arm",
        "link_name": "panda_link8",
    })
    mock_moveit_wrapper.get_current_pose.assert_called_once_with("panda_arm", "panda_link8")


@pytest.mark.asyncio
async def test_compute_fk(handlers, mock_moveit_wrapper):
    """Test forward kinematics computation."""
    result = await handlers["compute_fk"]({
        "group": "panda_arm",
        "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    })
    text = result[0].text
    assert "Forward kinematics" in text
    assert "Position" in text


@pytest.mark.asyncio
async def test_compute_ik_success(handlers, mock_moveit_wrapper):
    """Test successful inverse kinematics computation."""
    result = await handlers["compute_ik"]({
        "group": "panda_arm",
        "position": [0.3, 0.0, 0.5],
        "orientation": [0.0, 1.0, 0.0, 0.0],
    })
    text = result[0].text
    assert "Inverse kinematics solution" in text
    assert "panda_joint1" in text


@pytest.mark.asyncio
async def test_compute_ik_failure(handlers, mock_moveit_wrapper):
    """Test IK failure case."""
    mock_moveit_wrapper.compute_ik.return_value = None
    result = await handlers["compute_ik"]({
        "group": "panda_arm",
        "position": [10.0, 10.0, 10.0],  # Unreachable
        "orientation": [0.0, 1.0, 0.0, 0.0],
    })
    assert "IK failed" in result[0].text


@pytest.mark.asyncio
async def test_compute_ik_invalid_position(handlers):
    """Test IK with invalid position length."""
    result = await handlers["compute_ik"]({
        "group": "panda_arm",
        "position": [0.3, 0.0],  # Only 2 elements
        "orientation": [0.0, 1.0, 0.0, 0.0],
    })
    assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_compute_ik_invalid_orientation(handlers):
    """Test IK with invalid orientation length."""
    result = await handlers["compute_ik"]({
        "group": "panda_arm",
        "position": [0.3, 0.0, 0.5],
        "orientation": [0.0, 1.0, 0.0],  # Only 3 elements
    })
    assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_list_planning_groups(handlers, mock_moveit_wrapper):
    """Test listing planning groups."""
    result = await handlers["list_planning_groups"]({})
    text = result[0].text
    assert "panda_arm" in text
    assert "panda_hand" in text
    assert "2" in text


def test_compute_ik_schema(tools):
    """Test compute_ik schema has all expected fields."""
    tool = next(t for t in tools if t.name == "compute_ik")
    props = tool.inputSchema["properties"]
    assert "group" in props
    assert "position" in props
    assert "orientation" in props
    assert "timeout" in props
    assert "attempts" in props


def test_list_planning_groups_schema(tools):
    """Test list_planning_groups has no required inputs."""
    tool = next(t for t in tools if t.name == "list_planning_groups")
    assert "required" not in tool.inputSchema or len(tool.inputSchema.get("required", [])) == 0
