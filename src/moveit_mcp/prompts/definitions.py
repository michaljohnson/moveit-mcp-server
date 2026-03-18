"""Prompt definitions for guided MoveIt2 workflows."""

import logging

try:
    from mcp.server import Server
    from mcp.types import Prompt, PromptArgument, PromptMessage, TextContent
except ImportError:
    pass

logger = logging.getLogger(__name__)


def register_prompts(server: "Server"):
    """Register MCP prompt providers."""

    @server.list_prompts()
    async def list_prompts() -> list[Prompt]:
        """List available prompts."""
        return [
            Prompt(
                name="move_robot_to_pose",
                description=(
                    "Guided workflow to move the robot end-effector to a target pose. "
                    "Walks through querying current state, planning, and executing."
                ),
                arguments=[
                    PromptArgument(
                        name="group",
                        description="Planning group name (e.g., 'panda_arm' or 'arm')",
                        required=True,
                    ),
                    PromptArgument(
                        name="x",
                        description="Target X position in meters",
                        required=True,
                    ),
                    PromptArgument(
                        name="y",
                        description="Target Y position in meters",
                        required=True,
                    ),
                    PromptArgument(
                        name="z",
                        description="Target Z position in meters",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="pick_and_place",
                description=(
                    "Guided workflow for a pick-and-place operation. "
                    "Walks through moving to pick pose, grasping, moving to place pose, and releasing."
                ),
                arguments=[
                    PromptArgument(
                        name="arm_group",
                        description="Arm planning group name (e.g., 'panda_arm' or 'arm')",
                        required=True,
                    ),
                    PromptArgument(
                        name="gripper_group",
                        description="Gripper planning group name (e.g., 'panda_hand' or 'gripper')",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="inspect_robot_state",
                description=(
                    "Guided workflow to inspect the current robot state. "
                    "Queries joint states, end-effector pose, and planning scene."
                ),
                arguments=[
                    PromptArgument(
                        name="group",
                        description="Planning group name (e.g., 'panda_arm' or 'arm')",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="setup_collision_scene",
                description=(
                    "Guided workflow to set up collision objects in the planning scene. "
                    "Helps add tables, walls, and obstacles for safe motion planning."
                ),
                arguments=[
                    PromptArgument(
                        name="scene_type",
                        description="Type of scene: 'table', 'walls', 'obstacles', or 'custom'",
                        required=True,
                    ),
                ],
            ),
            Prompt(
                name="plan_cartesian_path",
                description=(
                    "Guided workflow to plan a multi-waypoint Cartesian path. "
                    "Walks through defining waypoints, planning, and executing the path."
                ),
                arguments=[
                    PromptArgument(
                        name="group",
                        description="Planning group name (e.g., 'panda_arm' or 'arm')",
                        required=True,
                    ),
                    PromptArgument(
                        name="num_waypoints",
                        description="Number of waypoints in the path",
                        required=True,
                    ),
                ],
            ),
        ]

    @server.get_prompt()
    async def get_prompt(name: str, arguments: dict | None = None) -> list[PromptMessage]:
        """Get a prompt by name."""
        arguments = arguments or {}

        if name == "move_robot_to_pose":
            return _move_robot_to_pose_prompt(arguments)
        elif name == "pick_and_place":
            return _pick_and_place_prompt(arguments)
        elif name == "inspect_robot_state":
            return _inspect_robot_state_prompt(arguments)
        elif name == "setup_collision_scene":
            return _setup_collision_scene_prompt(arguments)
        elif name == "plan_cartesian_path":
            return _plan_cartesian_path_prompt(arguments)
        else:
            raise ValueError(f"Unknown prompt: {name}")


def _move_robot_to_pose_prompt(arguments: dict) -> list:
    group = arguments.get("group", "panda_arm")
    x = arguments.get("x", "0.3")
    y = arguments.get("y", "0.0")
    z = arguments.get("z", "0.5")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"I want to move the robot to a target position. Please follow these steps:\n\n"
                    f"1. First, use `get_current_pose` to check the current end-effector position "
                    f"for planning group '{group}'.\n"
                    f"2. Then use `compute_ik` to verify the target pose "
                    f"(position=[{x}, {y}, {z}], orientation=[0, 1, 0, 0]) is reachable.\n"
                    f"3. If reachable, use `plan_to_pose` to plan the motion for group '{group}'.\n"
                    f"4. Check the plan result with `get_plan_result`.\n"
                    f"5. If planning succeeded, use `execute_plan` to move the robot.\n"
                    f"6. Finally, verify the new pose with `get_current_pose`.\n\n"
                    f"Report the results at each step."
                ),
            ),
        ),
    ]


def _pick_and_place_prompt(arguments: dict) -> list:
    arm_group = arguments.get("arm_group", "panda_arm")
    gripper_group = arguments.get("gripper_group", "panda_hand")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"I want to perform a pick-and-place operation. Please follow these steps:\n\n"
                    f"**Setup:**\n"
                    f"1. Use `list_planning_groups` to confirm '{arm_group}' and "
                    f"'{gripper_group}' are available.\n"
                    f"2. Use `get_current_joint_state` for both groups to check the starting state.\n\n"
                    f"**Pick Phase:**\n"
                    f"3. Plan the arm to a pre-grasp position above the object using `plan_to_pose` "
                    f"for group '{arm_group}'.\n"
                    f"4. Execute the plan with `execute_plan`.\n"
                    f"5. Plan the arm down to the grasp position.\n"
                    f"6. Execute, then close the gripper using `plan_to_named_state` on "
                    f"'{gripper_group}' with state 'close'.\n\n"
                    f"**Place Phase:**\n"
                    f"7. Plan the arm to lift the object (move up in Z).\n"
                    f"8. Plan and execute to the place position.\n"
                    f"9. Open the gripper using `plan_to_named_state` on '{gripper_group}' "
                    f"with state 'open'.\n"
                    f"10. Retreat the arm to a safe position.\n\n"
                    f"Ask me for the pick and place coordinates before starting."
                ),
            ),
        ),
    ]


def _inspect_robot_state_prompt(arguments: dict) -> list:
    group = arguments.get("group", "panda_arm")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Please give me a complete inspection of the robot's current state:\n\n"
                    f"1. Use `list_planning_groups` to show all available groups.\n"
                    f"2. Use `get_current_joint_state` for group '{group}' and display "
                    f"each joint name with its position in both radians and degrees.\n"
                    f"3. Use `get_current_pose` for group '{group}' to show the end-effector "
                    f"position (x, y, z in meters) and orientation (quaternion and Euler angles).\n"
                    f"4. Use `list_collision_objects` to show what's in the planning scene.\n"
                    f"5. Read the `moveit://active_operations` resource to check for any "
                    f"running operations.\n\n"
                    f"Format the results in a clear summary table."
                ),
            ),
        ),
    ]


def _setup_collision_scene_prompt(arguments: dict) -> list:
    scene_type = arguments.get("scene_type", "table")

    scene_instructions = {
        "table": (
            "Set up a table scene:\n"
            "- Add a table surface at position [0.5, 0.0, 0.2] with dimensions [0.6, 1.0, 0.02]\n"
            "- Add table legs if desired"
        ),
        "walls": (
            "Set up a walled workspace:\n"
            "- Add a back wall at [0.8, 0.0, 0.5] with dimensions [0.02, 1.0, 1.0]\n"
            "- Add left wall at [0.4, -0.5, 0.5] with dimensions [0.8, 0.02, 1.0]\n"
            "- Add right wall at [0.4, 0.5, 0.5] with dimensions [0.8, 0.02, 1.0]"
        ),
        "obstacles": (
            "Set up a scene with obstacles:\n"
            "- Add a box obstacle at [0.4, 0.2, 0.3] with dimensions [0.1, 0.1, 0.3]\n"
            "- Add a sphere obstacle at [0.3, -0.2, 0.4] with radius 0.05\n"
            "- Add a tall pillar at [0.5, 0.0, 0.25] with dimensions [0.05, 0.05, 0.5]"
        ),
        "custom": (
            "I'd like to set up a custom collision scene. Ask me for:\n"
            "- The number and types of objects (boxes, spheres)\n"
            "- Position, dimensions/radius for each object\n"
            "- Object names/IDs"
        ),
    }

    instructions = scene_instructions.get(scene_type, scene_instructions["custom"])

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"Please set up the planning scene with collision objects.\n\n"
                    f"{instructions}\n\n"
                    f"Steps:\n"
                    f"1. First, use `clear_planning_scene` to start fresh.\n"
                    f"2. Add each collision object using `add_collision_box` or "
                    f"`add_collision_sphere`.\n"
                    f"3. Use `list_collision_objects` to confirm all objects were added.\n"
                    f"4. Optionally use `check_state_collision` to verify the robot's "
                    f"current state is collision-free.\n\n"
                    f"Report the results at each step."
                ),
            ),
        ),
    ]


def _plan_cartesian_path_prompt(arguments: dict) -> list:
    group = arguments.get("group", "panda_arm")
    num_waypoints = arguments.get("num_waypoints", "3")

    return [
        PromptMessage(
            role="user",
            content=TextContent(
                type="text",
                text=(
                    f"I want to plan a multi-waypoint path for planning group '{group}' "
                    f"with {num_waypoints} waypoints.\n\n"
                    f"Please follow these steps:\n"
                    f"1. Use `get_current_pose` to get the starting position.\n"
                    f"2. Ask me for the {num_waypoints} waypoint positions (x, y, z) "
                    f"and orientations.\n"
                    f"3. For each waypoint, use `compute_ik` to verify it's reachable.\n"
                    f"4. Plan to each waypoint sequentially using `plan_to_pose`, checking "
                    f"results with `get_plan_result` after each plan.\n"
                    f"5. Execute each segment with `execute_plan`, waiting for completion "
                    f"with `get_execution_status`.\n"
                    f"6. After all waypoints, use `get_current_pose` to verify the "
                    f"final position.\n\n"
                    f"If any waypoint is unreachable or planning fails, suggest an "
                    f"alternative position and ask for confirmation."
                ),
            ),
        ),
    ]
