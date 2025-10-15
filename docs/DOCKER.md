# Docker Setup Guide

Run the MoveIt2 MCP Server in a Docker container with all dependencies pre-installed.

## Quick Start

### 1. Build the Docker Image

Using docker-compose:

```bash
docker-compose build
```

### 2. Run the Container

**Option A: Using docker-compose (Recommended)**

```bash
# Allow X11 forwarding for GUI
xhost +local:docker

# Start container
docker-compose run --rm moveit-mcp
```

**Option B: Using docker run**

```bash
# Allow X11 forwarding for GUI
xhost +local:docker

# Run container
docker run -it --rm \
  --network host \
  -e DISPLAY=$DISPLAY \
  -e ROS_DOMAIN_ID=0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $HOME/.Xauthority:/root/.Xauthority:rw \
  moveit-mcp-server:jazzy
```

### 3. Inside the Container

Once inside the container, you can run MoveIt and the MCP server:

**Terminal 1: Launch MoveIt Demo**

```bash
source /opt/ros/jazzy/setup.bash
ros2 launch moveit_resources_panda_moveit_config demo.launch.py
```

**Terminal 2: Run MCP Server**
```bash
# Exec into running container
docker exec -it moveit-mcp-server bash

# Start MCP server with HTTP/SSE
moveit-mcp-server-wrapper --transport sse --port 8000
```

## Troubleshooting

### GUI Not Working

```bash
# Enable X11 forwarding
xhost +local:docker

# Check DISPLAY variable
echo $DISPLAY

# If needed, set DISPLAY in container
export DISPLAY=:0
```

### ROS2 Nodes Not Communicating

```bash
# Check ROS_DOMAIN_ID matches
echo $ROS_DOMAIN_ID

# List nodes
ros2 node list

# Check topics
ros2 topic list
```

### MCP Server Can't Connect

```bash
# Verify MoveIt is running
ros2 node list | grep move_group

# Check if server can be imported
python3 -c "from moveit_mcp.server import main; print('OK')"

# Run with debug logging
moveit-mcp-server --log-level DEBUG
```

### Container Permissions

If you encounter permission issues with X11:

```bash
# More permissive (less secure)
xhost +

# Or add specific host
xhost +local:$(hostname)
```

### Python Package Installation Errors

If you see "externally-managed-environment" errors during build, the Dockerfile already handles this with `--break-system-packages`. If you prefer using a virtual environment:

```bash
# Use alternative Dockerfile with venv
docker build -f Dockerfile.venv -t moveit-mcp-server:jazzy .
```

## Development Workflow

For active development, mount the source code:

```bash
docker run -it --rm \
  --network host \
  -e DISPLAY=$DISPLAY \
  -e ROS_DOMAIN_ID=0 \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v $HOME/.Xauthority:/root/.Xauthority:rw \
  -v $(pwd):/workspace/moveit2-mcp-server \
  moveit-mcp-server:jazzy
```

Changes to the source code will be immediately reflected in the container.

## Cleanup

```bash
# Stop and remove container
docker-compose down

# Remove image
docker rmi moveit-mcp-server:jazzy

# Remove X11 permissions
xhost -local:docker
```

## Image Size

The built image is approximately **6-8 GB** due to:
- ROS2 Jazzy Desktop Full
- MoveIt2 and dependencies
- Visualization tools

To reduce size, use `ros:jazzy-ros-core` as base and install only required packages.

## Alternative: Development Container

For VS Code users, consider using a devcontainer. Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "MoveIt2 MCP Server",
  "dockerFile": "../Dockerfile",
  "runArgs": [
    "--network=host",
    "-e", "DISPLAY=${localEnv:DISPLAY}"
  ],
  "mounts": [
    "source=/tmp/.X11-unix,target=/tmp/.X11-unix,type=bind"
  ],
  "postCreateCommand": "source /opt/ros/jazzy/setup.bash"
}
```

This provides an integrated development environment with full IDE support.
