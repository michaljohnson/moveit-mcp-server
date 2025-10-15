"""Resource providers for MCP server."""

import json
import logging
from typing import Any, Dict

from ..async_ops import AsyncOperationManager
from ..moveit_wrapper import MoveItWrapper

try:
    from mcp.server import Server
    from mcp.types import Resource, TextContent
except ImportError:
    pass

logger = logging.getLogger(__name__)


def register_resources(
    server: "Server", moveit: MoveItWrapper, op_manager: AsyncOperationManager
):
    """Register MCP resource providers."""

    @server.list_resources()
    async def list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="moveit://planning_groups",
                name="Planning Groups",
                mimeType="application/json",
                description="List of available robot planning groups",
            ),
            Resource(
                uri="moveit://joint_states/panda_arm",
                name="Panda Arm Joint States",
                mimeType="application/json",
                description="Current joint states for panda_arm group",
            ),
            Resource(
                uri="moveit://planning_scene",
                name="Planning Scene",
                mimeType="application/json",
                description="Current planning scene with collision objects",
            ),
            Resource(
                uri="moveit://active_operations",
                name="Active Operations",
                mimeType="application/json",
                description="List of active async operations",
            ),
        ]

    @server.read_resource()
    async def read_resource(uri) -> str:
        """Read a resource by URI."""
        try:
            # Convert AnyUrl to string if needed
            uri_str = str(uri) if not isinstance(uri, str) else uri

            if uri_str == "moveit://planning_groups":
                groups = moveit.get_planning_groups()
                return json.dumps({"planning_groups": groups}, indent=2)

            elif uri_str.startswith("moveit://joint_states/"):
                group_name = uri_str.split("/")[-1]
                state = moveit.get_current_state(group_name)
                return json.dumps(state, indent=2)

            elif uri_str == "moveit://planning_scene":
                objects = moveit.get_planning_scene_objects()
                return json.dumps({"collision_objects": objects}, indent=2)

            elif uri_str == "moveit://active_operations":
                operations = await op_manager.list_operations()
                # Filter to only show relevant info
                simplified = [
                    {
                        "operation_id": op["operation_id"],
                        "type": op["type"],
                        "status": op["status"],
                        "progress": op["progress"],
                    }
                    for op in operations
                ]
                return json.dumps({"operations": simplified}, indent=2)

            else:
                raise ValueError(f"Unknown resource URI: {uri_str}")

        except Exception as e:
            logger.error(f"Error reading resource {uri}: {e}", exc_info=True)
            return json.dumps({"error": str(e)})
