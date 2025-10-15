# Troubleshooting Guide

Common issues and solutions for the MoveIt2 MCP Server.

## Docker Issues

### RViz2 Graphics/Display Issues

**Symptoms:**
```
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
MESA: error: Failed to query drm device.
glx: failed to create dri3 screen
failed to load driver: iris
```

**Solutions:**

#### Solution 1: Enable X11 Forwarding (Most Common)

```bash
# On host machine, allow Docker to access X11
xhost +local:docker

# Then restart container
docker-compose down
docker-compose run --rm moveit-mcp
```

#### Solution 2: Set Display Environment Variable

Inside the container:
```bash
export DISPLAY=:0
export QT_X11_NO_MITSHM=1
```

Or add to your docker-compose.yml:
```yaml
environment:
  - DISPLAY=:0
  - QT_X11_NO_MITSHM=1
  - XDG_RUNTIME_DIR=/tmp/runtime-root
```

#### Solution 3: Use GPU Passthrough (For NVIDIA GPUs)

For NVIDIA GPUs, use the `nvidia-docker` runtime:

```yaml
# docker-compose.yml
services:
  moveit-mcp:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
```

Or with docker run:
```bash
docker run -it --rm \
  --gpus all \
  --network host \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  moveit-mcp-server:rolling
```

#### Solution 4: Use Software Rendering

If GPU passthrough doesn't work, force software rendering:

```bash
export LIBGL_ALWAYS_SOFTWARE=1
rviz2
```

Add to docker-compose.yml:
```yaml
environment:
  - LIBGL_ALWAYS_SOFTWARE=1
```

#### Solution 5: Run RViz on Host (Recommended for Difficult Cases)

Instead of running RViz in the container, run it on the host:

**Terminal 1 (Host):**
```bash
# Install RViz on host if not already
sudo apt install ros-jazzy-rviz2  # or your ROS distro

# Source ROS and run RViz
source /opt/ros/jazzy/setup.bash
rviz2
```

**Terminal 2 (Container):**
```bash
# Run MoveIt without RViz
ros2 launch moveit_resources_panda_moveit_config demo.launch.py \
  rviz:=false
```

**Terminal 3 (Host):**
```bash
# Load MoveIt RViz config
rviz2 -d /opt/ros/jazzy/share/moveit_resources_panda_moveit_config/launch/moveit.rviz
```

#### Solution 6: Check X11 Socket Permissions

```bash
# On host
ls -la /tmp/.X11-unix/
# Should show X0 socket

# Fix permissions if needed
sudo chmod 1777 /tmp/.X11-unix
```

### Docker Build Errors

#### "externally-managed-environment" Error

This is already fixed in the Dockerfile with `--break-system-packages`. If you still see it:

```bash
# The current Dockerfile already uses a venv approach with --system-site-packages
# Rebuild the container if needed
docker-compose build
```

#### Out of Disk Space

Docker images are large (~6-8 GB). Clean up old images:

```bash
# Remove unused images
docker system prune -a

# Check disk usage
docker system df
```

## ROS2 Issues

### MoveIt Not Starting

**Check if ROS nodes are running:**
```bash
ros2 node list
```

Should show:
```
/move_group
/robot_state_publisher
/rviz2
```

**If nodes are missing:**
```bash
# Check if MoveIt launch file exists
ls /opt/ros/${ROS_DISTRO}/share/moveit_resources_panda_moveit_config/launch/

# Try launching with verbose output
ros2 launch moveit_resources_panda_moveit_config demo.launch.py \
  --show-args
```

### ROS_DOMAIN_ID Mismatch

If nodes don't see each other:

```bash
# Check domain ID
echo $ROS_DOMAIN_ID

# Set to same value everywhere (host and container)
export ROS_DOMAIN_ID=0
```

### "Package not found" Errors

```bash
# Source ROS setup
source /opt/ros/${ROS_DISTRO}/setup.bash

# Verify package is installed
ros2 pkg list | grep moveit

# Install if missing (adjust for your ROS distro)
apt update
apt install ros-${ROS_DISTRO}-moveit-resources-panda-moveit-config
```

## MCP Server Issues

### Server Won't Start

**"MoveIt Python bindings not available":**
```bash
# Check if moveit_py is installed
python3 -c "from moveit.planning import MoveItPy; print('OK')"

# Install if missing (adjust for your ROS distro)
apt install ros-${ROS_DISTRO}-moveit-py
```

**"No module named 'mcp'":**
```bash
# Install MCP SDK
pip3 install --break-system-packages mcp>=0.9.0
```

**"moveit-mcp-server command not found":**
```bash
# Reinstall the package
cd /workspace/moveit-mcp-server
pip3 install -e .

# Check if installed
which moveit-mcp-server
```

### Server Can't Connect to MoveIt

**Error: "Planning group 'panda_arm' not found"**

This means the server can't communicate with MoveIt:

```bash
# 1. Verify MoveIt is running
ros2 node list | grep move_group

# 2. Check topics
ros2 topic list | grep planning

# 3. Restart both MoveIt and the server with same ROS_DOMAIN_ID
export ROS_DOMAIN_ID=0
```

### Planning Always Fails

```bash
# Check for collision objects blocking the path
ros2 topic echo /planning_scene_world

# Clear planning scene from server
# In Python or via Claude:
# "Clear all collision objects from the planning scene"

# Check joint limits
ros2 param get /move_group robot_description_planning
```

## Python Issues

### Import Errors

```bash
# Check Python path
python3 -c "import sys; print('\n'.join(sys.path))"

# Verify packages are installed
pip3 list | grep -E 'mcp|moveit|yaml'

# Reinstall if needed
pip3 install --break-system-packages -e .
```

### Permission Errors with pip

```bash
# In Docker, use --break-system-packages
pip3 install --break-system-packages <package>

# Or use the venv Dockerfile
docker build -f Dockerfile.venv -t moveit-mcp-server:jazzy .
```

## Performance Issues

### Slow Planning

```bash
# Increase planning timeout
moveit-mcp-server --config config/panda_mcp_server.yaml

# Edit config to increase timeout:
# planning:
#   default_timeout: 10.0  # Increase from 5.0
```

### High CPU Usage

```bash
# Check running processes
top

# Limit concurrent operations in config:
# mcp_server:
#   max_concurrent_operations: 5  # Reduce from 10
```

## Network Issues (Host ↔ Container)

### Can't Access ROS Topics from Host

```bash
# Use host networking mode (already default in docker-compose.yml)
docker run --network host ...

# Or set ROS_DOMAIN_ID explicitly
export ROS_DOMAIN_ID=0
```

### Firewall Blocking ROS2

```bash
# Ubuntu/Debian
sudo ufw allow from 224.0.0.0/4
sudo ufw allow from 239.255.0.0/16

# Or disable firewall temporarily for testing
sudo ufw disable
```

## Debugging Tips

### Enable Debug Logging

```bash
# For MCP server
moveit-mcp-server --log-level DEBUG

# For ROS2
export RCUTILS_CONSOLE_OUTPUT_FORMAT="[{severity}] [{name}]: {message}"
export RCUTILS_LOGGING_USE_STDOUT=1
export RCUTILS_LOGGING_BUFFERED_STREAM=1
ros2 launch ... --log-level debug
```

### Check All Services Running

```bash
# Full diagnostic
echo "=== ROS2 Nodes ==="
ros2 node list

echo "=== ROS2 Topics ==="
ros2 topic list

echo "=== MoveIt Services ==="
ros2 service list | grep -E 'plan|execute|scene'

echo "=== Python Packages ==="
pip3 list | grep -E 'mcp|moveit'

echo "=== Environment ==="
env | grep -E 'ROS|DISPLAY'
```

### Test MoveIt Independently

```bash
# Test MoveIt without MCP server
ros2 launch moveit_resources_panda_moveit_config demo.launch.py

# In RViz, try planning manually:
# 1. Drag the interactive marker
# 2. Click "Plan" in Motion Planning panel
# 3. Click "Execute" if planning succeeds
```

## Getting More Help

If you're still stuck:

1. **Check logs:** Look at the full error output
2. **Search issues:** Check [GitHub Issues](https://github.com/...)
3. **Enable debug logging:** Use `--log-level DEBUG`
4. **Test components separately:** Test MoveIt, then ROS2, then MCP server
5. **Try Docker:** Use Docker if native installation has issues
6. **Ask for help:** Open an issue with:
   - Error messages (full output)
   - ROS2 distro and version
   - Docker or native installation
   - Output of diagnostic commands above

## Quick Fixes Summary

```bash
# Most common fixes

# 1. Graphics issues
xhost +local:docker
export DISPLAY=:0

# 2. ROS communication
export ROS_DOMAIN_ID=0
source /opt/ros/${ROS_DISTRO}/setup.bash

# 3. MoveIt not found (adjust for your ROS distro)
apt install ros-${ROS_DISTRO}-moveit ros-${ROS_DISTRO}-moveit-py

# 4. MCP server installation (in container)
cd /workspace/moveit-mcp-server
pip3 install -e .

# 5. Clean restart
docker-compose down
docker-compose build
xhost +local:docker
docker-compose run --rm moveit-mcp
```
