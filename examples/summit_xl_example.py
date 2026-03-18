#!/usr/bin/env python3
"""
Example MCP client for the Summit XL mobile manipulator.

Demonstrates how to interact with the MoveIt MCP server programmatically
using the Summit XL robot with arm and gripper planning groups.

Prerequisites:
    Terminal 1: ros2 launch icclab_summit_xl_move_it_config demo.launch.py
    Terminal 2: moveit-mcp-server --config config/summit_xl_mcp_server.yaml

Usage:
    python examples/summit_xl_example.py
"""

import asyncio
import json

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client, StdioServerParameters
except ImportError:
    print("Error: MCP SDK not installed. Run: pip install mcp")
    exit(1)


async def run_summit_xl_example():
    """Demonstrate MCP server interaction with the Summit XL robot."""

    server_params = StdioServerParameters(
        command="moveit-mcp-server",
        args=["--config", "config/summit_xl_mcp_server.yaml"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to MoveIt MCP Server (Summit XL)\n")

            # --- Discover capabilities ---
            print("=" * 60)
            print("DISCOVERING SERVER CAPABILITIES")
            print("=" * 60)

            tools_result = await session.list_tools()
            print(f"\nAvailable tools ({len(tools_result.tools)}):")
            for tool in tools_result.tools:
                print(f"  - {tool.name}")

            resources_result = await session.list_resources()
            print(f"\nAvailable resources ({len(resources_result.resources)}):")
            for resource in resources_result.resources:
                print(f"  - {resource.name} ({resource.uri})")

            prompts_result = await session.list_prompts()
            print(f"\nAvailable prompts ({len(prompts_result.prompts)}):")
            for prompt in prompts_result.prompts:
                print(f"  - {prompt.name}: {prompt.description}")

            # --- Query robot state ---
            print("\n" + "=" * 60)
            print("QUERYING SUMMIT XL STATE")
            print("=" * 60)

            # Get planning groups (expect: arm, gripper)
            print("\nPlanning Groups:")
            result = await session.call_tool("list_planning_groups", {})
            print(f"  {result.content[0].text}")

            # Get arm joint state
            print("\nCurrent Arm Joint State:")
            result = await session.call_tool(
                "get_current_joint_state", {"group": "arm"}
            )
            print(f"  {result.content[0].text}")

            # Get gripper joint state
            print("Current Gripper Joint State:")
            result = await session.call_tool(
                "get_current_joint_state", {"group": "gripper"}
            )
            print(f"  {result.content[0].text}")

            # Get arm end-effector pose
            print("Arm End-Effector Pose:")
            result = await session.call_tool(
                "get_current_pose", {"group": "arm"}
            )
            print(f"  {result.content[0].text}")

            # --- Arm motion planning ---
            print("\n" + "=" * 60)
            print("ARM MOTION PLANNING")
            print("=" * 60)

            # Plan to home state
            print("\nPlanning arm to 'home' state...")
            result = await session.call_tool(
                "plan_to_named_state",
                {"group": "arm", "state_name": "home"},
            )
            response_text = result.content[0].text
            print(f"  {response_text}")

            if "Operation ID:" in response_text:
                operation_id = response_text.split("Operation ID: ")[1].split("\n")[0]

                # Check plan result
                await asyncio.sleep(2)
                result = await session.call_tool(
                    "get_plan_result", {"operation_id": operation_id}
                )
                print(f"  Plan result: {result.content[0].text}")

                # Execute
                print("\nExecuting arm plan...")
                result = await session.call_tool(
                    "execute_plan", {"operation_id": operation_id}
                )
                print(f"  {result.content[0].text}")

                exec_text = result.content[0].text
                if "Operation ID:" in exec_text:
                    exec_id = exec_text.split("Operation ID: ")[1].split("\n")[0]
                    await asyncio.sleep(3)
                    result = await session.call_tool(
                        "get_execution_status", {"operation_id": exec_id}
                    )
                    print(f"  Execution status: {result.content[0].text}")

            # --- Gripper control ---
            print("\n" + "=" * 60)
            print("GRIPPER CONTROL")
            print("=" * 60)

            # Open gripper
            print("\nPlanning gripper to 'open' state...")
            result = await session.call_tool(
                "plan_to_named_state",
                {"group": "gripper", "state_name": "open"},
            )
            response_text = result.content[0].text
            print(f"  {response_text}")

            if "Operation ID:" in response_text:
                operation_id = response_text.split("Operation ID: ")[1].split("\n")[0]
                await asyncio.sleep(2)
                result = await session.call_tool(
                    "get_plan_result", {"operation_id": operation_id}
                )
                print(f"  Plan result: {result.content[0].text}")

            # --- Scene management ---
            print("\n" + "=" * 60)
            print("COLLISION SCENE MANAGEMENT")
            print("=" * 60)

            # Add a table in front of the robot
            print("\nAdding table obstacle...")
            result = await session.call_tool(
                "add_collision_box",
                {
                    "object_id": "worktable",
                    "position": [0.6, 0.0, 0.35],
                    "dimensions": [0.5, 0.8, 0.02],
                },
            )
            print(f"  {result.content[0].text}")

            # Add an object on the table
            print("\nAdding object on table...")
            result = await session.call_tool(
                "add_collision_box",
                {
                    "object_id": "box_object",
                    "position": [0.6, 0.1, 0.41],
                    "dimensions": [0.05, 0.05, 0.1],
                },
            )
            print(f"  {result.content[0].text}")

            # List objects
            print("\nCollision objects:")
            result = await session.call_tool("list_collision_objects", {})
            print(f"  {result.content[0].text}")

            # --- Kinematics ---
            print("\n" + "=" * 60)
            print("KINEMATICS")
            print("=" * 60)

            # Compute IK for a target above the table
            print("\nComputing IK for target above table [0.5, 0.0, 0.55]...")
            result = await session.call_tool(
                "compute_ik",
                {
                    "group": "arm",
                    "position": [0.5, 0.0, 0.55],
                    "orientation": [0.0, 1.0, 0.0, 0.0],
                },
            )
            print(f"  {result.content[0].text}")

            # --- Combined plan and execute ---
            print("\n" + "=" * 60)
            print("COMBINED PLAN AND EXECUTE")
            print("=" * 60)

            print("\nUsing plan_and_execute for arm to named state...")
            result = await session.call_tool(
                "plan_and_execute",
                {
                    "group": "arm",
                    "target_type": "named_state",
                    "target": {"state_name": "home"},
                },
            )
            response_text = result.content[0].text
            print(f"  {response_text}")

            if "Operation ID:" in response_text:
                op_id = response_text.split("Operation ID: ")[1].split("\n")[0]
                await asyncio.sleep(5)
                result = await session.call_tool(
                    "get_execution_status", {"operation_id": op_id}
                )
                print(f"  Status: {result.content[0].text}")

            # --- Cleanup ---
            print("\n" + "=" * 60)
            print("CLEANUP")
            print("=" * 60)

            print("\nClearing planning scene...")
            result = await session.call_tool("clear_planning_scene", {})
            print(f"  {result.content[0].text}")

            print("\nSummit XL example complete!")


if __name__ == "__main__":
    try:
        asyncio.run(run_summit_xl_example())
    except KeyboardInterrupt:
        print("\nExample interrupted")
    except Exception as e:
        print(f"Error: {e}")
