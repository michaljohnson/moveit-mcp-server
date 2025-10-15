# Quick Start: MCP Server with SSE/HTTP Transport

## For Claude Code Integration

### 1. Build and Start
```bash
# Build container
docker-compose build

# Start container
docker-compose run --rm moveit-mcp

# In container - Terminal 1: Start robot demo
ros2 launch moveit_resources_panda_moveit_config demo.launch.py
```

### 2. Start MCP Server (New Terminal)
```bash
# Exec into running container
docker exec -it moveit-mcp-server bash

# Start MCP server with HTTP/SSE
moveit-mcp-server-wrapper --transport sse --port 8000
```

### 3. Configure Claude Code

Add to MCP settings:
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

### 4. Test Connection

In Claude Code, try:
```
Use the moveit-mcp-server to get available planning groups
```

## Available Tools

- `get_planning_groups` - List available robot groups
- `get_current_state` - Get current joint positions
- `plan_to_joint_state` - Plan a motion to joint positions
- `plan_to_pose` - Plan a motion to Cartesian pose
- `execute_trajectory` - Execute a planned motion
- `add_collision_box` - Add obstacles to planning scene
- And more...

See full documentation in [docs/CLAUDE_CODE_SETUP.md](docs/CLAUDE_CODE_SETUP.md)
