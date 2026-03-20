"""Full end-to-end integration tests for the MCP server."""

import asyncio
import re

import pytest

from moveit_mcp.tools.planning import get_planning_tools
from moveit_mcp.tools.queries import get_query_tools
from moveit_mcp.tools.scene import get_scene_tools


@pytest.mark.integration
@pytest.mark.slow
class TestMCPServerEndToEnd:
    """End-to-end tests for the complete MCP server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mcp_server):
        """Test that the MCP server initializes with real MoveIt."""
        assert mcp_server.is_initialized()
        assert mcp_server.moveit is not None
        assert mcp_server.op_manager is not None

    @pytest.mark.asyncio
    async def test_planning_tools_with_server(self, mcp_server, sample_pose):
        """Test planning tools through the server."""
        _, handlers = get_planning_tools(mcp_server.moveit, mcp_server.op_manager, mcp_server)

        result = await handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": sample_pose['position'],
            "orientation": sample_pose['orientation'],
            "frame_id": "world",
            "timeout": 5.0,
        })
        assert len(result) == 1
        assert "Operation ID" in result[0].text

        match = re.search(r'Operation ID: ([a-f0-9-]+)', result[0].text)
        if match:
            await asyncio.sleep(1.0)
            result = await handlers["get_plan_result"]({"operation_id": match.group(1)})
            assert len(result) == 1

    @pytest.mark.asyncio
    async def test_query_tools_with_server(self, mcp_server):
        """Test query tools through the server."""
        _, handlers = get_query_tools(mcp_server.moveit, mcp_server)

        result = await handlers["list_planning_groups"]({})
        assert "panda_arm" in result[0].text

        result = await handlers["get_current_joint_state"]({"group": "panda_arm"})
        assert "joint" in result[0].text.lower()

        result = await handlers["get_current_pose"]({"group": "panda_arm"})
        assert "Position" in result[0].text

    @pytest.mark.asyncio
    async def test_scene_tools_with_server(self, mcp_server):
        """Test planning scene tools through the server."""
        _, handlers = get_scene_tools(mcp_server.moveit, mcp_server)

        result = await handlers["add_collision_box"]({
            "object_id": "test_box_e2e",
            "position": [0.5, 0.0, 0.0],
            "orientation": [0.0, 0.0, 0.0, 1.0],
            "dimensions": [0.1, 0.1, 0.1],
        })
        assert "Successfully added" in result[0].text

        result = await handlers["list_collision_objects"]({})
        assert "test_box_e2e" in result[0].text

        result = await handlers["remove_collision_object"]({"object_id": "test_box_e2e"})
        assert "Successfully removed" in result[0].text

    @pytest.mark.asyncio
    async def test_resources_with_server(self, mcp_server):
        """Test that server resources are accessible."""
        assert len(mcp_server.moveit.get_planning_groups()) > 0
        state = mcp_server.moveit.get_current_state("panda_arm")
        assert "joint_names" in state
        assert isinstance(mcp_server.moveit.get_planning_scene_objects(), list)


@pytest.mark.integration
@pytest.mark.slow
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_typical_workflow(self, mcp_server):
        """Test a typical workflow: query state, add obstacle, plan, check result."""
        _, query_handlers = get_query_tools(mcp_server.moveit, mcp_server)
        _, scene_handlers = get_scene_tools(mcp_server.moveit, mcp_server)
        _, plan_handlers = get_planning_tools(mcp_server.moveit, mcp_server.op_manager, mcp_server)

        await query_handlers["get_current_joint_state"]({"group": "panda_arm"})

        await scene_handlers["add_collision_box"]({
            "object_id": "table",
            "position": [0.5, 0.0, -0.1],
            "dimensions": [0.8, 1.2, 0.05],
        })

        result = await plan_handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": [0.4, 0.0, 0.4],
            "orientation": [0.0, 0.0, 0.0, 1.0],
            "timeout": 5.0,
        })

        match = re.search(r'Operation ID: ([a-f0-9-]+)', result[0].text)
        if match:
            await asyncio.sleep(2.0)
            await plan_handlers["get_plan_result"]({"operation_id": match.group(1)})

        await scene_handlers["remove_collision_object"]({"object_id": "table"})
