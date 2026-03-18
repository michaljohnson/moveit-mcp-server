"""Tests for MCP prompt definitions."""

import pytest
from unittest.mock import MagicMock

from moveit_mcp.prompts.definitions import register_prompts


@pytest.fixture
def prompt_server():
    """Create a mock MCP server and register prompts."""
    server = MagicMock()

    # Capture the decorated functions
    list_handler = None
    get_handler = None

    def capture_list():
        def decorator(fn):
            nonlocal list_handler
            list_handler = fn
            return fn
        return decorator

    def capture_get():
        def decorator(fn):
            nonlocal get_handler
            get_handler = fn
            return fn
        return decorator

    server.list_prompts = capture_list
    server.get_prompt = capture_get

    register_prompts(server)

    return list_handler, get_handler


@pytest.mark.asyncio
async def test_list_prompts(prompt_server):
    """Test listing all available prompts."""
    list_handler, _ = prompt_server
    prompts = await list_handler()

    assert len(prompts) == 5
    names = {p.name for p in prompts}
    assert names == {
        "move_robot_to_pose",
        "pick_and_place",
        "inspect_robot_state",
        "setup_collision_scene",
        "plan_cartesian_path",
    }


@pytest.mark.asyncio
async def test_all_prompts_have_descriptions(prompt_server):
    """Test that all prompts have descriptions."""
    list_handler, _ = prompt_server
    prompts = await list_handler()
    for prompt in prompts:
        assert prompt.description is not None
        assert len(prompt.description) > 10


@pytest.mark.asyncio
async def test_all_prompts_have_arguments(prompt_server):
    """Test that all prompts have at least one argument."""
    list_handler, _ = prompt_server
    prompts = await list_handler()
    for prompt in prompts:
        assert len(prompt.arguments) >= 1


@pytest.mark.asyncio
async def test_get_move_robot_to_pose(prompt_server):
    """Test the move_robot_to_pose prompt."""
    _, get_handler = prompt_server
    messages = await get_handler("move_robot_to_pose", {
        "group": "panda_arm",
        "x": "0.3",
        "y": "0.1",
        "z": "0.5",
    })
    assert len(messages) == 1
    assert messages[0].role == "user"
    assert "panda_arm" in messages[0].content.text
    assert "get_current_pose" in messages[0].content.text
    assert "plan_to_pose" in messages[0].content.text


@pytest.mark.asyncio
async def test_get_pick_and_place(prompt_server):
    """Test the pick_and_place prompt."""
    _, get_handler = prompt_server
    messages = await get_handler("pick_and_place", {
        "arm_group": "panda_arm",
        "gripper_group": "panda_hand",
    })
    assert len(messages) == 1
    assert "panda_arm" in messages[0].content.text
    assert "panda_hand" in messages[0].content.text
    assert "Pick Phase" in messages[0].content.text
    assert "Place Phase" in messages[0].content.text


@pytest.mark.asyncio
async def test_get_inspect_robot_state(prompt_server):
    """Test the inspect_robot_state prompt."""
    _, get_handler = prompt_server
    messages = await get_handler("inspect_robot_state", {"group": "arm"})
    assert len(messages) == 1
    text = messages[0].content.text
    assert "arm" in text
    assert "get_current_joint_state" in text
    assert "get_current_pose" in text
    assert "list_collision_objects" in text


@pytest.mark.asyncio
async def test_get_setup_collision_scene_table(prompt_server):
    """Test setup_collision_scene prompt with table type."""
    _, get_handler = prompt_server
    messages = await get_handler("setup_collision_scene", {"scene_type": "table"})
    assert "table" in messages[0].content.text.lower()
    assert "clear_planning_scene" in messages[0].content.text


@pytest.mark.asyncio
async def test_get_setup_collision_scene_walls(prompt_server):
    """Test setup_collision_scene prompt with walls type."""
    _, get_handler = prompt_server
    messages = await get_handler("setup_collision_scene", {"scene_type": "walls"})
    assert "wall" in messages[0].content.text.lower()


@pytest.mark.asyncio
async def test_get_setup_collision_scene_obstacles(prompt_server):
    """Test setup_collision_scene prompt with obstacles type."""
    _, get_handler = prompt_server
    messages = await get_handler("setup_collision_scene", {"scene_type": "obstacles"})
    assert "obstacle" in messages[0].content.text.lower()


@pytest.mark.asyncio
async def test_get_setup_collision_scene_custom(prompt_server):
    """Test setup_collision_scene prompt with custom type."""
    _, get_handler = prompt_server
    messages = await get_handler("setup_collision_scene", {"scene_type": "custom"})
    assert "custom" in messages[0].content.text.lower()


@pytest.mark.asyncio
async def test_get_plan_cartesian_path(prompt_server):
    """Test the plan_cartesian_path prompt."""
    _, get_handler = prompt_server
    messages = await get_handler("plan_cartesian_path", {
        "group": "panda_arm",
        "num_waypoints": "4",
    })
    text = messages[0].content.text
    assert "panda_arm" in text
    assert "4" in text
    assert "compute_ik" in text


@pytest.mark.asyncio
async def test_get_unknown_prompt(prompt_server):
    """Test that unknown prompt raises ValueError."""
    _, get_handler = prompt_server
    with pytest.raises(ValueError, match="Unknown prompt"):
        await get_handler("nonexistent_prompt", {})


@pytest.mark.asyncio
async def test_prompts_with_default_arguments(prompt_server):
    """Test prompts work with empty arguments (use defaults)."""
    _, get_handler = prompt_server
    # All prompts should handle missing arguments gracefully
    messages = await get_handler("move_robot_to_pose", {})
    assert len(messages) == 1
    assert "panda_arm" in messages[0].content.text  # default group

    messages = await get_handler("inspect_robot_state", {})
    assert len(messages) == 1
