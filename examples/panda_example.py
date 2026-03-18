#!/usr/bin/env python3
"""
Example MCP client for the Panda robot arm.

Demonstrates how to interact with the MoveIt MCP server programmatically
using the Franka Emika Panda 7-DOF robot arm.

Prerequisites:
    Terminal 1: ros2 launch moveit_resources_panda_moveit_config demo.launch.py
    Terminal 2: moveit-mcp-server --config config/panda_mcp_server.yaml

Usage:
    python examples/panda_example.py
"""

import asyncio
import json

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
except ImportError:
    print("Error: MCP SDK not installed. Run: pip install mcp")
    exit(1)


async def run_panda_example():
    """Demonstrate MCP server interaction with the Panda robot arm."""

    server_params = StdioServerParameters(
        command="moveit-mcp-server",
        args=["--config", "config/panda_mcp_server.yaml"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MoveIt MCP Server (Panda)\n")

            # --- Discover capabilities ---
            print("=" * 60)
            print("DISCOVERING SERVER CAPABILITIES")
            print("=" * 60)

            # List tools
            tools_result = await session.list_tools()
            print(f"\nAvailable tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  - {tool.name}: {tool.description}")

            # List resources
            resources_result = await session.list_resources()
            print(f"\nAvailable resources ({len(resources_result.resources)}):")
            for resource in resources_result.resources:
                print(f"  - {resource.name} ({resource.uri})")

            # List prompts
            prompts_result = await session.list_prompts()
            print(f"\nAvailable prompts ({len(prompts_result.prompts)}):")
            for prompt in prompts_result.prompts:
                print(f"  - {prompt.name}: {prompt.description}")

            # --- Query robot state ---
            print("\n" + "=" * 60)
            print("QUERYING ROBOT STATE")
            print("=" * 60)

            # Get planning groups
            print("\nPlanning Groups:")
            result = await session.call_tool("list_planning_groups", {})
            print(f"  {result.content[0].text}")

            # Get current joint state
            print("\nCurrent Joint State (panda_arm):")
            result = await session.call_tool(
                "get_current_joint_state", {"group": "panda_arm"}
            )
            print(f"  {result.content[0].text}")

            # Get current end-effector pose
            print("Current End-Effector Pose:")
            result = await session.call_tool(
                "get_current_pose", {"group": "panda_arm"}
            )
            print(f"  {result.content[0].text}")

            # --- Read resources ---
            print("\n" + "=" * 60)
            print("READING RESOURCES")
            print("=" * 60)

            # Planning groups resource
            result = await session.read_resource("moveit://planning_groups")
            groups = json.loads(result.contents[0].text)
            print(f"\nmoveit://planning_groups: {json.dumps(groups, indent=2)}")

            # Joint states resource
            result = await session.read_resource("moveit://joint_states/panda_arm")
            state = json.loads(result.contents[0].text)
            print(f"\nmoveit://joint_states/panda_arm: {json.dumps(state, indent=2)}")

            # --- Motion planning ---
            print("\n" + "=" * 60)
            print("MOTION PLANNING")
            print("=" * 60)

            # Plan to named state 'ready'
            print("\nPlanning to 'ready' state...")
            result = await session.call_tool(
                "plan_to_named_state",
                {"group": "panda_arm", "state_name": "ready"},
            )
            response_text = result.content[0].text
            print(f"  {response_text}")

            # Extract operation ID
            operation_id = response_text.split("Operation ID: ")[1].split("\n")[0]

            # Wait and check result
            await asyncio.sleep(2)
            result = await session.call_tool(
                "get_plan_result", {"operation_id": operation_id}
            )
            print(f"  Plan result: {result.content[0].text}")

            # Execute the plan
            print("\nExecuting plan...")
            result = await session.call_tool(
                "execute_plan", {"operation_id": operation_id}
            )
            print(f"  {result.content[0].text}")

            # Wait for execution
            exec_text = result.content[0].text
            if "Operation ID:" in exec_text:
                exec_id = exec_text.split("Operation ID: ")[1].split("\n")[0]
                await asyncio.sleep(3)
                result = await session.call_tool(
                    "get_execution_status", {"operation_id": exec_id}
                )
                print(f"  Execution status: {result.content[0].text}")

            # --- Collision scene management ---
            print("\n" + "=" * 60)
            print("COLLISION SCENE MANAGEMENT")
            print("=" * 60)

            # Add a table
            print("\nAdding table collision object...")
            result = await session.call_tool(
                "add_collision_box",
                {
                    "object_id": "table",
                    "position": [0.5, 0.0, 0.2],
                    "dimensions": [0.6, 1.0, 0.02],
                },
            )
            print(f"  {result.content[0].text}")

            # Add an obstacle
            print("\nAdding sphere obstacle...")
            result = await session.call_tool(
                "add_collision_sphere",
                {
                    "object_id": "obstacle_sphere",
                    "position": [0.3, 0.2, 0.4],
                    "radius": 0.05,
                },
            )
            print(f"  {result.content[0].text}")

            # List collision objects
            print("\nCollision objects in scene:")
            result = await session.call_tool("list_collision_objects", {})
            print(f"  {result.content[0].text}")

            # --- Kinematics ---
            print("\n" + "=" * 60)
            print("KINEMATICS")
            print("=" * 60)

            # Compute IK
            print("\nComputing IK for position [0.3, 0.0, 0.5]...")
            result = await session.call_tool(
                "compute_ik",
                {
                    "group": "panda_arm",
                    "position": [0.3, 0.0, 0.5],
                    "orientation": [0.0, 1.0, 0.0, 0.0],
                },
            )
            print(f"  {result.content[0].text}")

            # Compute FK with specific joint positions
            print("Computing FK for zero joint positions...")
            result = await session.call_tool(
                "compute_fk",
                {
                    "group": "panda_arm",
                    "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                },
            )
            print(f"  {result.content[0].text}")

            # Check collision
            print("Checking collision for zero joint state...")
            result = await session.call_tool(
                "check_state_collision",
                {
                    "group": "panda_arm",
                    "joint_positions": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                },
            )
            print(f"  {result.content[0].text}")

            # --- Cleanup ---
            print("\n" + "=" * 60)
            print("CLEANUP")
            print("=" * 60)

            print("\nClearing planning scene...")
            result = await session.call_tool("clear_planning_scene", {})
            print(f"  {result.content[0].text}")

            print("\nPanda example complete!")


if __name__ == "__main__":
    try:
        asyncio.run(run_panda_example())
    except KeyboardInterrupt:
        print("\nExample interrupted")
    except Exception as e:
        print(f"Error: {e}")
