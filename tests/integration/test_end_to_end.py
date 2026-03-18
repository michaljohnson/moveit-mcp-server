"""Full end-to-end integration tests for the MCP server.

These tests verify the complete MCP server functionality with real ROS/MoveIt.
"""

import pytest
import asyncio
import time

from .conftest import (
    ros_available,
    moveit_available,
    demo_running,
    is_ros_available,
    is_moveit_available,
    is_demo_running,
)


@pytest.mark.integration
@pytest.mark.slow
@moveit_available
class TestMCPServerEndToEnd:
    """End-to-end tests for the complete MCP server."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, wait_for_initialization):
        """Test that the MCP server can initialize with real MoveIt."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer

        # Create server
        server = MoveItMCPServer()

        wait_for_initialization(2.0)

        # Start server (but don't run transport)
        await server.start()

        # Verify initialization
        assert server.is_initialized()
        assert server.moveit is not None
        assert server.op_manager is not None

        # Cleanup
        await server.stop()

        print("✓ MCP server initialized successfully with real MoveIt")

    @pytest.mark.asyncio
    async def test_planning_tools_with_server(self, wait_for_initialization, sample_pose):
        """Test planning tools through the server."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer
        from moveit_mcp.tools.planning import get_planning_tools

        # Create and start server
        server = MoveItMCPServer()
        wait_for_initialization(2.0)
        await server.start()

        # Get planning tools
        tools, handlers = get_planning_tools(
            server.moveit,
            server.op_manager,
            server
        )

        # Test plan_to_pose
        arguments = {
            "group": "panda_arm",
            "position": sample_pose['position'],
            "orientation": sample_pose['orientation'],
            "frame_id": "world",
            "timeout": 5.0
        }

        result = await handlers["plan_to_pose"](arguments)

        # Should return operation ID
        assert len(result) == 1
        assert "Operation ID" in result[0].text

        # Extract operation ID
        text = result[0].text
        import re
        match = re.search(r'Operation ID: ([a-f0-9-]+)', text)
        if match:
            operation_id = match.group(1)

            # Wait a bit for planning
            await asyncio.sleep(1.0)

            # Check result
            result = await handlers["get_plan_result"]({"operation_id": operation_id})
            assert len(result) == 1
            print(f"Planning result: {result[0].text}")

        # Cleanup
        await server.stop()

        print("✓ Planning tools work through MCP server")

    @pytest.mark.asyncio
    async def test_query_tools_with_server(self, wait_for_initialization):
        """Test query tools through the server."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer
        from moveit_mcp.tools.queries import get_query_tools

        # Create and start server
        server = MoveItMCPServer()
        wait_for_initialization(2.0)
        await server.start()

        # Get query tools
        tools, handlers = get_query_tools(server.moveit, server)

        # Test list_planning_groups
        result = await handlers["list_planning_groups"]({})
        assert len(result) == 1
        assert "panda_arm" in result[0].text

        # Test get_current_joint_state
        result = await handlers["get_current_joint_state"]({"group": "panda_arm"})
        assert len(result) == 1
        assert "joint" in result[0].text.lower()

        # Test get_current_pose
        result = await handlers["get_current_pose"]({"group": "panda_arm"})
        assert len(result) == 1
        assert "Position" in result[0].text

        # Cleanup
        await server.stop()

        print("✓ Query tools work through MCP server")

    @pytest.mark.asyncio
    async def test_scene_tools_with_server(self, wait_for_initialization):
        """Test planning scene tools through the server."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer
        from moveit_mcp.tools.scene import get_scene_tools

        # Create and start server
        server = MoveItMCPServer()
        wait_for_initialization(2.0)
        await server.start()

        # Get scene tools
        tools, handlers = get_scene_tools(server.moveit, server)

        # Add collision box
        result = await handlers["add_collision_box"]({
            "object_id": "test_box",
            "position": [0.5, 0.0, 0.0],
            "orientation": [0.0, 0.0, 0.0, 1.0],
            "dimensions": [0.1, 0.1, 0.1]
        })
        assert len(result) == 1
        assert "Successfully added" in result[0].text

        # List objects
        result = await handlers["list_collision_objects"]({})
        assert len(result) == 1
        assert "test_box" in result[0].text

        # Remove object
        result = await handlers["remove_collision_object"]({"object_id": "test_box"})
        assert len(result) == 1
        assert "Successfully removed" in result[0].text

        # Cleanup
        await server.stop()

        print("✓ Scene tools work through MCP server")

    @pytest.mark.asyncio
    async def test_resources_with_server(self, wait_for_initialization):
        """Test MCP resources with the server."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer
        import json

        # Create and start server
        server = MoveItMCPServer()
        wait_for_initialization(2.0)
        await server.start()

        # We can't directly call resource handlers without the MCP framework,
        # but we can verify they're registered
        assert server.moveit is not None
        assert server.op_manager is not None

        # Test that wrapper methods work (resources use these)
        groups = server.moveit.get_planning_groups()
        assert len(groups) > 0

        state = server.moveit.get_current_state("panda_arm")
        assert "joint_names" in state

        objects = server.moveit.get_planning_scene_objects()
        assert isinstance(objects, list)

        # Cleanup
        await server.stop()

        print("✓ Server initialized with resource providers")


@pytest.mark.integration
@pytest.mark.slow
class TestRealWorldScenarios:
    """Test real-world usage scenarios."""

    @pytest.mark.asyncio
    async def test_typical_workflow(self, wait_for_initialization):
        """Test a typical workflow: query state, add obstacle, plan, check result."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.server import MoveItMCPServer
        from moveit_mcp.tools.queries import get_query_tools
        from moveit_mcp.tools.scene import get_scene_tools
        from moveit_mcp.tools.planning import get_planning_tools

        # Initialize server
        server = MoveItMCPServer()
        wait_for_initialization(2.0)
        await server.start()

        # Get tools
        query_tools, query_handlers = get_query_tools(server.moveit, server)
        scene_tools, scene_handlers = get_scene_tools(server.moveit, server)
        plan_tools, plan_handlers = get_planning_tools(server.moveit, server.op_manager, server)

        # Step 1: Query current state
        print("\n1. Querying current robot state...")
        result = await query_handlers["get_current_joint_state"]({"group": "panda_arm"})
        print(f"   Current state retrieved: {result[0].text[:100]}...")

        # Step 2: Add obstacle
        print("\n2. Adding collision object...")
        result = await scene_handlers["add_collision_box"]({
            "object_id": "table",
            "position": [0.5, 0.0, -0.1],
            "dimensions": [0.8, 1.2, 0.05]
        })
        print(f"   {result[0].text}")

        # Step 3: Plan motion
        print("\n3. Planning motion...")
        result = await plan_handlers["plan_to_pose"]({
            "group": "panda_arm",
            "position": [0.4, 0.0, 0.4],
            "orientation": [0.0, 0.0, 0.0, 1.0],
            "timeout": 5.0
        })
        print(f"   {result[0].text}")

        # Step 4: Check plan result
        import re
        match = re.search(r'Operation ID: ([a-f0-9-]+)', result[0].text)
        if match:
            operation_id = match.group(1)
            await asyncio.sleep(2.0)  # Wait for planning

            print("\n4. Checking plan result...")
            result = await plan_handlers["get_plan_result"]({"operation_id": operation_id})
            print(f"   {result[0].text}")

        # Step 5: Clean up obstacle
        print("\n5. Cleaning up...")
        result = await scene_handlers["remove_collision_object"]({"object_id": "table"})
        print(f"   {result[0].text}")

        # Cleanup server
        await server.stop()

        print("\n✓ Complete workflow executed successfully!")
