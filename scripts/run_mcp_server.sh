#!/bin/bash
# Wrapper script to run MCP server with ROS 2 environment sourced

# Source ROS 2 setup
if [ -f /opt/ros/${ROS_DISTRO}/setup.bash ]; then
    source /opt/ros/${ROS_DISTRO}/setup.bash
fi

# Source MoveIt workspace if it exists
if [ -f ~/ws_moveit/install/setup.bash ]; then
    source ~/ws_moveit/install/setup.bash
fi

# Activate virtual environment
if [ -f /opt/mcp-venv/bin/activate ]; then
    source /opt/mcp-venv/bin/activate
fi

# Run the MCP server
exec python3 -m moveit_mcp.server "$@"
