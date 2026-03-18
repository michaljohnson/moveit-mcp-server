"""Tests for planning scene tool implementations."""

import pytest
from unittest.mock import MagicMock

from moveit_mcp.tools.scene import get_scene_tools


@pytest.fixture
def scene_tools(mock_moveit_wrapper, mock_server_instance):
    """Get scene tools and handlers."""
    tools, handlers = get_scene_tools(
        mock_moveit_wrapper, server_instance=mock_server_instance
    )
    return tools, handlers


@pytest.fixture
def tools(scene_tools):
    return scene_tools[0]


@pytest.fixture
def handlers(scene_tools):
    return scene_tools[1]


def test_scene_tools_count(tools):
    """Test that all 6 scene tools are registered."""
    assert len(tools) == 6


def test_scene_tool_names(tools):
    """Test scene tool names."""
    names = {t.name for t in tools}
    assert names == {
        "add_collision_box", "add_collision_sphere", "remove_collision_object",
        "clear_planning_scene", "list_collision_objects", "check_state_collision",
    }


def test_scene_handlers_match_tools(tools, handlers):
    """Test that every tool has a matching handler."""
    for tool in tools:
        assert tool.name in handlers


@pytest.mark.asyncio
async def test_add_collision_box(handlers, mock_moveit_wrapper):
    """Test adding a collision box."""
    result = await handlers["add_collision_box"]({
        "object_id": "table",
        "position": [0.5, 0.0, 0.2],
        "dimensions": [0.6, 1.0, 0.02],
    })
    assert "Successfully added" in result[0].text
    assert "table" in result[0].text
    mock_moveit_wrapper.add_collision_box.assert_called_once()


@pytest.mark.asyncio
async def test_add_collision_box_invalid_position(handlers):
    """Test add_collision_box rejects invalid position."""
    result = await handlers["add_collision_box"]({
        "object_id": "bad_box",
        "position": [0.5, 0.0],  # Only 2 elements
        "dimensions": [0.1, 0.1, 0.1],
    })
    assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_add_collision_box_invalid_dimensions(handlers):
    """Test add_collision_box rejects invalid dimensions."""
    result = await handlers["add_collision_box"]({
        "object_id": "bad_box",
        "position": [0.5, 0.0, 0.5],
        "dimensions": [0.1, 0.1],  # Only 2 elements
    })
    assert "Error" in result[0].text


@pytest.mark.asyncio
async def test_add_collision_sphere(handlers, mock_moveit_wrapper):
    """Test adding a collision sphere."""
    result = await handlers["add_collision_sphere"]({
        "object_id": "ball",
        "position": [0.3, 0.2, 0.4],
        "radius": 0.05,
    })
    assert "Successfully added" in result[0].text
    assert "ball" in result[0].text
    mock_moveit_wrapper.add_collision_sphere.assert_called_once()


@pytest.mark.asyncio
async def test_remove_collision_object(handlers, mock_moveit_wrapper):
    """Test removing a collision object."""
    result = await handlers["remove_collision_object"]({"object_id": "table"})
    assert "Successfully removed" in result[0].text
    mock_moveit_wrapper.remove_collision_object.assert_called_once_with("table")


@pytest.mark.asyncio
async def test_clear_planning_scene(handlers, mock_moveit_wrapper):
    """Test clearing the planning scene."""
    result = await handlers["clear_planning_scene"]({})
    assert "Successfully cleared" in result[0].text
    mock_moveit_wrapper.clear_planning_scene.assert_called_once()


@pytest.mark.asyncio
async def test_list_collision_objects_empty(handlers, mock_moveit_wrapper):
    """Test listing collision objects when scene is empty."""
    mock_moveit_wrapper.get_planning_scene_objects.return_value = []
    result = await handlers["list_collision_objects"]({})
    assert "No collision objects" in result[0].text


@pytest.mark.asyncio
async def test_list_collision_objects_with_items(handlers, mock_moveit_wrapper):
    """Test listing collision objects with objects present."""
    mock_moveit_wrapper.get_planning_scene_objects.return_value = ["table", "box1"]
    result = await handlers["list_collision_objects"]({})
    assert "table" in result[0].text
    assert "box1" in result[0].text
    assert "2" in result[0].text


@pytest.mark.asyncio
async def test_check_state_collision_free(handlers, mock_moveit_wrapper):
    """Test collision check for collision-free state."""
    mock_moveit_wrapper.check_collision.return_value = False
    result = await handlers["check_state_collision"]({
        "group": "panda_arm",
        "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    })
    assert "collision-free" in result[0].text


@pytest.mark.asyncio
async def test_check_state_in_collision(handlers, mock_moveit_wrapper):
    """Test collision check for state in collision."""
    mock_moveit_wrapper.check_collision.return_value = True
    result = await handlers["check_state_collision"]({
        "group": "panda_arm",
        "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
    })
    assert "in collision" in result[0].text
