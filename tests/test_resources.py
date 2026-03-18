"""Tests for MCP resource providers."""

import json

import pytest
from unittest.mock import MagicMock, AsyncMock

from moveit_mcp.resources.providers import register_resources


@pytest.fixture
def resource_server(mock_moveit_wrapper, op_manager):
    """Create a mock MCP server and register resources."""
    server = MagicMock()

    list_handler = None
    read_handler = None

    def capture_list():
        def decorator(fn):
            nonlocal list_handler
            list_handler = fn
            return fn
        return decorator

    def capture_read():
        def decorator(fn):
            nonlocal read_handler
            read_handler = fn
            return fn
        return decorator

    server.list_resources = capture_list
    server.read_resource = capture_read

    register_resources(server, mock_moveit_wrapper, op_manager)

    return list_handler, read_handler, mock_moveit_wrapper, op_manager


@pytest.mark.asyncio
async def test_list_resources(resource_server):
    """Test listing available resources."""
    list_handler, _, _, _ = resource_server
    resources = await list_handler()

    assert len(resources) == 4
    uris = {str(r.uri) for r in resources}
    assert "moveit://planning_groups" in uris
    assert "moveit://joint_states/panda_arm" in uris
    assert "moveit://planning_scene" in uris
    assert "moveit://active_operations" in uris


@pytest.mark.asyncio
async def test_read_planning_groups(resource_server):
    """Test reading planning groups resource."""
    _, read_handler, wrapper, _ = resource_server
    wrapper.get_planning_groups.return_value = ["panda_arm", "panda_hand"]

    result = await read_handler("moveit://planning_groups")
    data = json.loads(result)
    assert "planning_groups" in data
    assert "panda_arm" in data["planning_groups"]
    assert "panda_hand" in data["planning_groups"]


@pytest.mark.asyncio
async def test_read_joint_states(resource_server):
    """Test reading joint states resource."""
    _, read_handler, wrapper, _ = resource_server
    result = await read_handler("moveit://joint_states/panda_arm")
    data = json.loads(result)
    assert "joint_names" in data
    assert "joint_positions" in data
    assert len(data["joint_names"]) == 7


@pytest.mark.asyncio
async def test_read_planning_scene(resource_server):
    """Test reading planning scene resource."""
    _, read_handler, wrapper, _ = resource_server
    wrapper.get_planning_scene_objects.return_value = ["table", "box1"]

    result = await read_handler("moveit://planning_scene")
    data = json.loads(result)
    assert "collision_objects" in data
    assert "table" in data["collision_objects"]


@pytest.mark.asyncio
async def test_read_active_operations(resource_server):
    """Test reading active operations resource."""
    _, read_handler, _, op_manager = resource_server
    await op_manager.start()
    try:
        result = await read_handler("moveit://active_operations")
        data = json.loads(result)
        assert "operations" in data
        assert isinstance(data["operations"], list)
    finally:
        await op_manager.stop()


@pytest.mark.asyncio
async def test_read_unknown_resource(resource_server):
    """Test reading an unknown resource URI."""
    _, read_handler, _, _ = resource_server
    result = await read_handler("moveit://nonexistent")
    data = json.loads(result)
    assert "error" in data
