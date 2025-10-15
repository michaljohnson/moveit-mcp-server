# MoveIt2 MCP Server - Project Summary

## Overview

This project implements a **Model Context Protocol (MCP)** server for **MoveIt2**, enabling AI assistants like Claude to control and plan robot motions through natural language.

## Architecture Choice

**Strategy 1 - Direct moveit_py Integration with Async Stateful Server**

This implementation provides:
- **Stateful** - Single MoveItPy instance maintained throughout server lifetime
- **Async** - Non-blocking operations with operation tracking
- **Efficient** - Cached planning components, no repeated initialization
- **Scalable** - Support for concurrent operations with progress monitoring

## Project Structure

```
moveit2-mcp-server/
├── src/moveit_mcp/              # Main package
│   ├── server.py                # MCP server entry point
│   ├── moveit_wrapper.py        # Stateful MoveItPy wrapper
│   ├── async_ops.py             # Async operation manager
│   ├── tools/                   # MCP tool implementations
│   │   ├── planning.py          # Planning tools
│   │   ├── execution.py         # Execution tools
│   │   ├── scene.py             # Planning scene tools
│   │   └── queries.py           # State query tools
│   └── resources/               # MCP resource providers
│       └── providers.py         # Resource implementations
├── config/                      # Configuration files
│   └── panda_mcp_server.yaml    # Panda robot config
├── docs/                        # Documentation
│   ├── QUICKSTART.md           # Getting started guide
│   ├── ARCHITECTURE.md         # System design
│   └── TOOLS_REFERENCE.md      # API documentation
├── examples/                    # Example code
│   └── test_client.py          # Test MCP client
├── scripts/                     # Utility scripts
│   └── setup_environment.sh    # Setup script
├── pyproject.toml              # Package metadata
└── README.md                   # Main documentation
```

## Key Components

### 1. MoveItWrapper (moveit_wrapper.py)
- Wraps MoveItPy for stateful operations
- Caches planning components per group
- Provides simplified API for:
  - Motion planning (pose, joint state, named state)
  - Trajectory execution
  - Planning scene manipulation
  - Forward/inverse kinematics
  - Collision checking

### 2. AsyncOperationManager (async_ops.py)
- Manages long-running async operations
- Tracks operation state: PENDING → RUNNING → COMPLETED/FAILED
- Provides progress monitoring (0.0 - 1.0)
- Automatic cleanup of old operations
- Concurrent operation limits

### 3. MCP Server (server.py)
- Handles MCP protocol (stdio transport)
- Routes tool calls to handlers
- Manages server lifecycle
- Loads configuration

### 4. Tool Handlers (tools/)
20+ MCP tools across 4 categories:
- **Planning**: plan_to_pose, plan_to_joint_state, plan_to_named_state, get_plan_result
- **Execution**: execute_plan, get_execution_status, stop_execution, plan_and_execute
- **Scene**: add_collision_box, add_collision_sphere, remove_collision_object, clear_planning_scene, list_collision_objects, check_state_collision
- **Queries**: get_current_joint_state, get_current_pose, compute_fk, compute_ik, list_planning_groups

### 5. Resource Providers (resources/)
Dynamic MCP resources:
- `moveit://planning_groups` - Available groups
- `moveit://joint_states/{group}` - Current joint positions
- `moveit://planning_scene` - Collision objects
- `moveit://active_operations` - Running operations

## Technology Stack

- **ROS2**: Rolling (recommended and fully tested)
- **MoveIt2**: Motion planning framework
- **moveit_py**: Python bindings for MoveIt2
- **MCP SDK**: Model Context Protocol (Python)
- **asyncio**: Python async framework

## Features Implemented

✅ **Async Planning**: Non-blocking motion planning with operation tracking
✅ **Async Execution**: Monitor trajectory execution progress
✅ **Planning Scene**: Add/remove collision objects dynamically
✅ **Kinematics**: Forward and inverse kinematics computation
✅ **State Queries**: Get current robot state and poses
✅ **Multiple Planners**: Support for different planning algorithms
✅ **Named States**: Plan to predefined robot configurations
✅ **Collision Checking**: Validate joint states for collisions
✅ **Resource Providers**: Real-time state information
✅ **Configuration System**: YAML-based robot configuration
✅ **Error Handling**: Comprehensive error handling and logging
✅ **Documentation**: Complete docs with examples

## Usage Flow

1. **Launch MoveIt**: Start MoveIt demo with Panda robot
2. **Run Server**: Start MCP server (connects to MoveIt)
3. **AI Interaction**: Claude uses MCP tools to control robot
4. **Async Operations**: Long operations return operation ID for polling
5. **Real-time Updates**: Resources provide current state

## Example Interaction

```
User: "Plan a motion for the panda arm to position (0.3, 0, 0.6)"

Claude:
1. Calls plan_to_pose tool → Gets operation_id
2. Polls get_plan_result → Monitors progress
3. Reports success/failure to user

User: "Execute it"

Claude:
1. Calls execute_plan with operation_id
2. Monitors execution_status
3. Reports completion
```

## Configuration

The server is configured via `config/panda_mcp_server.yaml`:
- Robot description package
- Planning groups and planners
- Execution controllers
- Operation timeouts
- Logging settings

## Testing

- **Example Client**: `examples/test_client.py` demonstrates all features
- **Setup Script**: `scripts/setup_environment.sh` validates environment
- **Integration**: Works with ROS2 demo launch files

## Documentation

- **README.md**: Project overview and quick start
- **QUICKSTART.md**: Step-by-step getting started guide
- **docs/ARCHITECTURE.md**: Detailed system design
- **docs/CLAUDE_CODE_SETUP.md**: Claude Code integration guide
- **docs/DOCKER.md**: Docker setup guide
- **docs/TROUBLESHOOTING.md**: Common issues and solutions
- **CONTRIBUTING.md**: Contribution guidelines

## Future Enhancements

Potential additions:
- Cartesian path planning tool
- Multi-robot support
- Custom collision mesh support
- Planning constraints API
- Trajectory visualization
- Recording/playback
- Real hardware controllers
- More kinematics solvers

## Design Decisions

**Why Stateful?**
- MoveItPy initialization is expensive (~seconds)
- Planning components can be cached
- Shared planning scene monitor

**Why Async?**
- Planning can take several seconds
- Execution can take 10+ seconds
- AI needs non-blocking operations
- Support multiple concurrent operations

**Why moveit_py over Services?**
- Direct API calls (better performance)
- More comprehensive feature set
- Official Python bindings
- Better error handling

**Why Operation IDs?**
- Track multiple concurrent operations
- Async polling pattern
- Clean operation lifecycle
- Progress monitoring

## Dependencies

**Required:**
- ROS2 (Rolling recommended)
- MoveIt2 with moveit_py
- Python 3.10+
- MCP SDK (pip)
- PyYAML (pip)

**Optional:**
- moveit_resources_panda_moveit_config (for demos)
- pytest, black, ruff (for development)

## License

Apache 2 License - See LICENSE file


## Getting Started

```bash
# 1. Clone and build
git clone <repo-url>
cd moveit-mcp-server
docker-compose build

# 2. Start container and MoveIt
docker-compose run --rm moveit-mcp
ros2 launch moveit_resources_panda_moveit_config demo.launch.py

# 3. Run MCP server (in new terminal)
docker exec -it moveit-mcp-server bash
moveit-mcp-server-wrapper --transport sse --port 8000

# 4. Configure Claude Code or Claude Desktop
# See docs/CLAUDE_CODE_SETUP.md
```

See [QUICKSTART.md](QUICKSTART.md) for full instructions.
