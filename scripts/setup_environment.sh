#!/bin/bash
# Setup script for MoveIt2 MCP Server environment

set -e

echo "=== MoveIt2 MCP Server Setup ==="
echo

# Check ROS2 installation
if [ -z "$ROS_DISTRO" ]; then
    echo "❌ ROS2 not detected. Please source your ROS2 installation:"
    echo "   source /opt/ros/jazzy/setup.bash"
    echo "   (or use your installed ROS2 distro: rolling, etc.)"
    exit 1
fi

echo "✓ ROS2 detected: $ROS_DISTRO"

# Recommend Jazzy or Rolling
if [ "$ROS_DISTRO" != "jazzy" ] && [ "$ROS_DISTRO" != "rolling" ]; then
    echo "⚠ Warning: This project is tested with ROS2 Jazzy and Rolling"
    echo "   You are using: $ROS_DISTRO"
    echo "   Consider using Jazzy (recommended) or Rolling for best compatibility"
fi

# Check for MoveIt2
if ! dpkg -l | grep -q "ros-$ROS_DISTRO-moveit"; then
    echo "❌ MoveIt2 not installed"
    echo "   Install with: sudo apt install ros-$ROS_DISTRO-moveit"
    exit 1
fi

echo "✓ MoveIt2 installed"

# Check for moveit_py
if ! dpkg -l | grep -q "ros-$ROS_DISTRO-moveit-py"; then
    echo "❌ MoveIt Python bindings not installed"
    echo "   Install with: sudo apt install ros-$ROS_DISTRO-moveit-py"
    exit 1
fi

echo "✓ MoveIt Python bindings installed"

# Check for Panda config
if ! dpkg -l | grep -q "ros-$ROS_DISTRO-moveit-resources-panda-moveit-config"; then
    echo "⚠ Panda MoveIt config not installed (recommended for demos)"
    echo "   Install with: sudo apt install ros-$ROS_DISTRO-moveit-resources-panda-moveit-config"
else
    echo "✓ Panda MoveIt config installed"
fi

# Check Python version
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
REQUIRED_VERSION="3.10"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "✓ Python version: $PYTHON_VERSION"

# Install Python dependencies
echo
echo "Installing Python dependencies..."
pip install -e . --quiet

if [ $? -eq 0 ]; then
    echo "✓ Python dependencies installed"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

# Check if server can be executed
if command -v moveit-mcp-server &> /dev/null; then
    echo "✓ moveit-mcp-server command available"
else
    echo "❌ moveit-mcp-server command not found"
    echo "   Try: pip install -e ."
    exit 1
fi

# Create config directory if it doesn't exist
mkdir -p ~/.config/moveit_mcp/
if [ ! -f ~/.config/moveit_mcp/config.yaml ]; then
    cp config/panda_mcp_server.yaml ~/.config/moveit_mcp/config.yaml
    echo "✓ Config file created at ~/.config/moveit_mcp/config.yaml"
fi

echo
echo "=== Setup Complete ==="
echo
echo "Next steps:"
echo "1. Start MoveIt demo:"
echo "   source /opt/ros/$ROS_DISTRO/setup.bash"
echo "   ros2 launch moveit_resources_panda_moveit_config demo.launch.py"
echo
echo "2. In another terminal, run the MCP server:"
echo "   source /opt/ros/$ROS_DISTRO/setup.bash"
echo "   moveit-mcp-server"
echo
echo "3. Test with the example client:"
echo "   source /opt/ros/$ROS_DISTRO/setup.bash"
echo "   python examples/test_client.py"
echo
echo "See docs/QUICKSTART.md for more information."
echo ""
echo "Using ROS2 distro: $ROS_DISTRO"
echo "For best results, use ROS2 Jazzy (recommended) or Rolling."
