"""Integration tests for MoveIt MCP Server.

These tests require ROS2 and MoveIt2 to be installed and properly configured.
They test actual functionality rather than mocked behavior.

To run these tests:
1. Ensure ROS2 and MoveIt2 are installed
2. Source ROS2 setup: source /opt/ros/$ROS_DISTRO/setup.bash
3. Launch the demo: ros2 launch moveit_resources_panda_moveit_config demo.launch.py
4. Run tests: pytest tests/integration/ -v -m integration

Tests will be skipped if ROS is not available.
"""
