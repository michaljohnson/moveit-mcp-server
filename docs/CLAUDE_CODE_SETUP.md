# Connecting MoveIt MCP Server to Claude Code

## Overview

Since the MCP server runs in a Docker container, we need to use **HTTP/SSE transport** instead of stdio. This allows Claude Code to connect to the server over the network.

## Setup Steps

### 1. Rebuild the Docker Container

```bash
docker-compose build
```

### 2. Start the Container and Robot Demo

**Terminal 1: Start container and robot demo**
```bash
docker-compose run --rm moveit-mcp
source ~/ws_moveit/install/setup.bash
ros2 launch /workspace/moveit2-mcp-server/launch/panda_demo_fixed.launch.py
```

Wait for RViz to appear and the robot to be visible.

### 3. Start the MCP Server with SSE Transport

**Terminal 2: In a new terminal, exec into the running container**
```bash
# Find the container ID
docker ps

# Exec into the container
docker exec -it <container_id> bash

# Start MCP server with SSE transport
moveit-mcp-server-wrapper --transport sse --port 8000
```

You should see:
```
INFO - Starting MCP server with SSE transport on 0.0.0.0:8000
INFO - MoveItWrapper initialized successfully
INFO - Uvicorn running on http://0.0.0.0:8000
```

### 4. Configure Claude Code

Add the following to your Claude Code MCP settings:

**Option A: Via Claude Code Settings UI**
1. Open Claude Code settings
2. Navigate to MCP Servers
3. Add a new server with:
   - **Name**: `moveit-mcp-server`
   - **Type**: `sse`
   - **URL**: `http://localhost:8000/sse`

**Option B: Via Configuration File**

Edit your MCP configuration file (usually `~/.config/claude/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "transport": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### 5. Verify Connection

In Claude Code, you should now be able to:
- See the MoveIt MCP server in the list of available servers
- Call tools like `get_planning_groups`, `plan_to_joint_state`, etc.
- Access resources for robot state and planning scene

## Command Line Options

The MCP server supports the following options:

```bash
moveit-mcp-server-wrapper --help

Options:
  --transport, -t {stdio,sse}  Transport type (default: stdio)
  --host HOST                  Host to bind to for SSE (default: 0.0.0.0)
  --port, -p PORT              Port for SSE transport (default: 8000)
  --config, -c CONFIG          Path to config file
  --log-level LEVEL            Log level (DEBUG, INFO, WARNING, ERROR)
```

### Examples:

**Run with stdio (for local, non-container use):**
```bash
moveit-mcp-server-wrapper
```

**Run with SSE on custom port:**
```bash
moveit-mcp-server-wrapper --transport sse --port 8080
```

**Run with debug logging:**
```bash
moveit-mcp-server-wrapper --transport sse --log-level DEBUG
```

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Container                      │
│                                                          │
│  ┌──────────────┐         ┌─────────────────────┐      │
│  │ Panda Demo   │         │   MCP Server        │      │
│  │              │         │                     │      │
│  │ - RViz       │◄───────►│ - MoveItPy         │      │
│  │ - move_group │ ROS 2   │ - HTTP/SSE Server  │      │
│  │ - controllers│ Topics  │   (port 8000)      │      │
│  └──────────────┘         └─────────────────────┘      │
│                                    │                    │
│                                    │ HTTP/SSE           │
└────────────────────────────────────┼────────────────────┘
                                     │
                                     │ http://localhost:8000/sse
                                     ↓
                           ┌──────────────────┐
                           │   Claude Code    │
                           │                  │
                           │  MCP Client      │
                           └──────────────────┘
```

## Troubleshooting

### "Connection refused" when connecting from Claude Code

1. Verify the server is running:
   ```bash
   curl http://localhost:8000/sse
   ```

2. Check if the port is exposed:
   ```bash
   docker ps  # Should show 0.0.0.0:8000->8000/tcp
   ```

3. Since we use `network_mode: host`, the port should be directly accessible

### "Unable to configure planning scene monitor"

The robot demo must be running before starting the MCP server. Make sure:
1. Terminal 1 has the demo running
2. RViz is visible
3. `/joint_states` topic is publishing:
   ```bash
   ros2 topic echo /joint_states --once
   ```

### Server starts but tools don't work

Check the server logs for errors. Common issues:
- MoveIt planning pipelines not loaded
- Robot URDF not found
- TF transforms not available

## Security Note

The MCP server currently binds to `0.0.0.0`, which means it's accessible from any network interface. For production use, consider:
- Binding to `127.0.0.1` only (localhost)
- Adding authentication
- Using a reverse proxy with SSL
- Restricting access with firewall rules
