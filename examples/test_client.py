#!/usr/bin/env python3
"""
Example test client for MoveIt MCP Server.

This demonstrates how to interact with the MCP server programmatically.
"""

import asyncio
import json

try:
    from mcp import ClientSession
    from mcp.client.stdio import stdio_client
except ImportError:
    print("Error: MCP SDK not installed")
    exit(1)


async def test_moveit_mcp_server():
    """Test the MoveIt MCP server functionality."""

    # Connect to the server via stdio
    server_params = {
        "command": "moveit-mcp-server",
        "args": [],
    }

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            print("Connected to MoveIt MCP Server\n")

            # List available tools
            print("=== Available Tools ===")
            tools = await session.list_tools()
            for tool in tools:
                print(f"  - {tool.name}: {tool.description}")
            print()

            # List available resources
            print("=== Available Resources ===")
            resources = await session.list_resources()
            for resource in resources:
                print(f"  - {resource.name} ({resource.uri})")
            print()

            # Get planning groups
            print("=== Planning Groups ===")
            result = await session.read_resource("moveit://planning_groups")
            groups = json.loads(result.contents[0].text)
            print(json.dumps(groups, indent=2))
            print()

            # Get current joint state
            print("=== Current Joint State ===")
            result = await session.call_tool("get_current_joint_state", {"group": "panda_arm"})
            print(result.content[0].text)
            print()

            # Plan to a named state
            print("=== Planning to 'ready' state ===")
            result = await session.call_tool(
                "plan_to_named_state",
                {"group": "panda_arm", "state_name": "ready"}
            )
            print(result.content[0].text)

            # Extract operation ID from result
            operation_id = result.content[0].text.split("Operation ID: ")[1].split("\n")[0]
            print(f"Got operation ID: {operation_id}\n")

            # Wait for planning to complete
            print("=== Checking Planning Result ===")
            await asyncio.sleep(2)  # Give it time to plan
            result = await session.call_tool(
                "get_plan_result",
                {"operation_id": operation_id}
            )
            print(result.content[0].text)
            print()

            # Add a collision box
            print("=== Adding Collision Box ===")
            result = await session.call_tool(
                "add_collision_box",
                {
                    "object_id": "test_box",
                    "position": [0.5, 0.0, 0.5],
                    "dimensions": [0.1, 0.1, 0.1],
                }
            )
            print(result.content[0].text)
            print()

            # List collision objects
            print("=== Collision Objects ===")
            result = await session.call_tool("list_collision_objects", {})
            print(result.content[0].text)
            print()

            # Compute IK
            print("=== Computing IK ===")
            result = await session.call_tool(
                "compute_ik",
                {
                    "group": "panda_arm",
                    "position": [0.3, 0.0, 0.5],
                    "orientation": [0, 1, 0, 0],  # 180 deg rotation around Y
                }
            )
            print(result.content[0].text)
            print()

            # Clean up - remove collision object
            print("=== Removing Collision Box ===")
            result = await session.call_tool(
                "remove_collision_object",
                {"object_id": "test_box"}
            )
            print(result.content[0].text)


if __name__ == "__main__":
    try:
        asyncio.run(test_moveit_mcp_server())
    except KeyboardInterrupt:
        print("\nTest interrupted")
    except Exception as e:
        print(f"Error: {e}")
