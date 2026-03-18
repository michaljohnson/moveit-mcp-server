# Connecting MoveIt MCP Server to Claude Code

## Overview

Since the MCP server runs in a Docker container, we need to use an HTTP-based transport instead of stdio. This allows Claude Code to connect to the server over the network.

Two HTTP transports are available:
- **`http`** — Streamable HTTP (MCP spec 2025-03-26, **recommended**)
- **`sse`** — Legacy HTTP/SSE (older MCP clients)

## Setup Steps

### 1. Rebuild the Docker Container

```bash
docker-compose build
```

### 2. Start the Container and Robot Demo

**Terminal 1: Start container and robot demo**
```bash
docker-compose run --rm moveit-mcp
ros2 launch moveit_resources_panda_moveit_config demo.launch.py
```

Wait for RViz to appear and the robot to be visible.

### 3. Start the MCP Server

**Terminal 2: Exec into the running container**
```bash
docker exec -it moveit-mcp-server bash

# Streamable HTTP transport (recommended)
moveit-mcp-server-wrapper --transport http --port 8001

# Or legacy SSE transport
moveit-mcp-server-wrapper --transport sse --port 8000
```

You should see:
```
INFO - Starting MCP server with Streamable HTTP transport on 0.0.0.0:8001
INFO - MoveItWrapper initialized successfully
INFO - Uvicorn running on http://0.0.0.0:8001
```

### 4. Configure Claude Code

**Option A: Via Claude Code Settings UI**
1. Open Claude Code settings
2. Navigate to MCP Servers
3. Add a new server with:
   - **Name**: `moveit-mcp-server`
   - **Type**: `http`
   - **URL**: `http://localhost:8001/mcp`

**Option B: Via Configuration File**

Edit your MCP configuration file (usually `~/.config/claude/mcp_settings.json` or similar):

```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "type": "http",
      "url": "http://localhost:8001/mcp"
    }
  }
}
```

For legacy SSE clients:
```json
{
  "mcpServers": {
    "moveit-mcp-server": {
      "type": "sse",
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
  --transport, -t {stdio,sse,http}  Transport type (default: stdio)
  --host HOST                       Host to bind to for HTTP/SSE (default: 0.0.0.0)
  --port, -p PORT                   Port for HTTP/SSE transport (default: 8000)
  --config, -c CONFIG               Path to config file
  --log-level LEVEL                 Log level (DEBUG, INFO, WARNING, ERROR)
```

### Examples:

**Run with stdio (for local, non-container use):**
```bash
moveit-mcp-server-wrapper
```

**Run with Streamable HTTP (recommended for remote/container use):**
```bash
moveit-mcp-server-wrapper --transport http --port 8001
```

**Run with legacy SSE:**
```bash
moveit-mcp-server-wrapper --transport sse --port 8000
```

**Run with debug logging:**
```bash
moveit-mcp-server-wrapper --transport http --log-level DEBUG
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
│  │ - move_group │ ROS 2   │ - HTTP Server      │      │
│  │ - controllers│ Topics  │   (port 8001)      │      │
│  └──────────────┘         └─────────────────────┘      │
│                                    │                    │
│                                    │ Streamable HTTP    │
└────────────────────────────────────┼────────────────────┘
                                     │
                                     │ http://localhost:8001/mcp
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
   curl http://localhost:8001/
   ```

2. Check if the port is exposed:
   ```bash
   docker ps  # Should show 0.0.0.0:8001->8001/tcp
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
