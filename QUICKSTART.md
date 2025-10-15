# Quick Start Guide

## Prerequisites
The MCP server requires an active ROS 2 + MoveIt environment with the robot running. We provide a container for quick testing.

## Starting the System

### Step 1: Build the Docker Container
```bash
docker-compose build
```

### Step 2: Start the Container
```bash
docker-compose run --rm moveit2-mcp-server
```

### Step 3: Launch Robot Demo (Terminal 1)
Inside the container, start the Panda robot demo:

```bash
# Source the workspace
source ~/ws_moveit/install/setup.bash

# Launch the robot with MoveIt
ros2 launch moveit_resources_panda_moveit_config demo.launch.py
# OR use the fixed launch file:
ros2 launch /workspace/moveit2-mcp-server/launch/panda_demo_fixed.launch.py
```

Wait for RViz to appear and the robot to be visible.

### Step 4: Start MCP Server (Terminal 2)
Open a second terminal in the container and start the MCP server:

```bash
# In a new terminal
docker exec -it <container_id> bash

# Run the MCP server
moveit-mcp-server-wrapper
```

You should see:
```
INFO - Building MoveIt configuration for panda
INFO - Found moveit_py config: /workspace/moveit2-mcp-server/config/moveit_py.yaml
INFO - Initializing MoveItPy with node name: moveit_mcp_server
INFO - MoveItWrapper initialized successfully
INFO - MoveIt MCP Server started successfully
```

## Troubleshooting

### "MoveIt Python bindings not available"
Make sure you're using the wrapper script:
```bash
moveit-mcp-server-wrapper
```

### "Unable to configure planning scene monitor"
The robot demo must be running FIRST before starting the MCP server. The MCP server needs:
- `/joint_states` topic publishing robot state
- `/tf` and `/tf_static` topics for transforms
- `robot_description` parameter loaded

Start the demo in Terminal 1, wait for it to fully load, then start the MCP server in Terminal 2.

### Import errors for numpy/geometry_msgs
Rebuild the container - the Dockerfile was updated to use `--system-site-packages`:
```bash
docker-compose build
```

## Architecture

```
┌─────────────────┐         ┌──────────────────┐
│  Panda Demo     │         │   MCP Server     │
│  (Terminal 1)   │         │   (Terminal 2)   │
│                 │         │                  │
│ - robot_state   │◄───────►│ - MoveItPy node  │
│ - move_group    │  ROS 2  │ - Planning API   │
│ - controllers   │ Topics  │ - MCP interface  │
│ - rviz          │         │                  │
└─────────────────┘         └──────────────────┘
```

Both the demo and MCP server create separate ROS 2 nodes that communicate via topics and services.
