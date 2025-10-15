#!/bin/bash
# Start the MCP server with HTTP/SSE transport for Claude Code integration

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

# Parse command line arguments
PORT=${1:-8000}
HOST=${2:-0.0.0.0}

echo "============================================"
echo "MoveIt MCP Server - HTTP/SSE Mode"
echo "============================================"
echo "Starting server on ${HOST}:${PORT}"
echo ""
echo "Make sure the robot demo is running in another terminal:"
echo "  ros2 launch /workspace/moveit2-mcp-server/launch/panda_demo_fixed.launch.py"
echo ""
echo "Configure Claude Code to connect to:"
echo "  http://localhost:${PORT}/sse"
echo "============================================"
echo ""

# Run the MCP server with SSE transport
exec python3 -m moveit_mcp.server --transport sse --host ${HOST} --port ${PORT}
