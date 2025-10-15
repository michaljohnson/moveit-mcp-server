# MoveIt2 MCP Server Architecture

## Overview

The MoveIt2 MCP Server provides an async, stateful bridge between AI assistants (via Model Context Protocol) and MoveIt2 motion planning capabilities.

## Architecture Diagram

```
┌─────────────────┐
│   AI Client     │
│   (Claude)      │
└────────┬────────┘
         │ MCP Protocol (stdio)
         │
┌────────▼────────────────────────────────────────┐
│           MCP Server (server.py)                │
│  ┌──────────────────────────────────────────┐  │
│  │        Tool Handlers                      │  │
│  │  - Planning Tools                         │  │
│  │  - Execution Tools                        │  │
│  │  - Scene Tools                            │  │
│  │  - Query Tools                            │  │
│  └──────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────┐  │
│  │      Resource Providers                   │  │
│  │  - Robot State                            │  │
│  │  - Planning Scene                         │  │
│  │  - Active Operations                      │  │
│  └──────────────────────────────────────────┘  │
└────────┬────────────────────────────┬──────────┘
         │                             │
         │                             │
┌────────▼────────┐          ┌────────▼──────────┐
│ AsyncOpsManager │          │  MoveItWrapper    │
│  - Tracks ops   │          │  - Stateful       │
│  - Non-blocking │          │  - Cached comps   │
│  - Progress     │          │  - Planning       │
└─────────────────┘          └────────┬──────────┘
                                      │
                             ┌────────▼──────────┐
                             │    moveit_py      │
                             │  (Python API)     │
                             └────────┬──────────┘
                                      │
                             ┌────────▼──────────┐
                             │   MoveIt2 Core    │
                             │   (C++ Library)   │
                             └────────┬──────────┘
                                      │
                             ┌────────▼──────────┐
                             │      ROS2         │
                             └───────────────────┘
```

## Component Details

### 1. MCP Server (server.py)

**Responsibilities:**
- Handles MCP protocol communication (stdio transport)
- Routes tool calls to appropriate handlers
- Manages server lifecycle
- Loads configuration

**Key Features:**
- Async initialization
- Graceful shutdown
- Configuration file support
- Logging setup

### 2. MoveItWrapper (moveit_wrapper.py)

**Responsibilities:**
- Wraps MoveItPy for stateful operations
- Caches planning components per group
- Provides simplified API for planning/execution
- Manages planning scene

**State Management:**
- Single MoveItPy instance (expensive to create)
- Planning components cached by group name
- Shared planning scene monitor
- Robot model loaded once

**Key Methods:**
- `plan_to_pose()` - Cartesian goal planning
- `plan_to_joint_state()` - Joint space planning
- `execute_trajectory()` - Execute planned motion
- `add_collision_box/sphere()` - Scene manipulation
- `compute_ik/fk()` - Kinematics
- `check_collision()` - Collision checking

### 3. AsyncOperationManager (async_ops.py)

**Responsibilities:**
- Tracks long-running async operations
- Provides non-blocking planning/execution
- Manages operation lifecycle
- Cleanup of completed operations

**Operation States:**
- PENDING - Queued but not started
- RUNNING - Currently executing
- COMPLETED - Successfully finished
- FAILED - Error occurred
- CANCELLED - User cancelled

**Features:**
- Operation ID generation
- Progress tracking (0.0 - 1.0)
- Automatic cleanup after timeout
- Concurrent operation limits

### 4. Tool Handlers

**Planning Tools (tools/planning.py):**
- `plan_to_pose` - Plan to Cartesian target
- `plan_to_joint_state` - Plan to joint configuration
- `plan_to_named_state` - Plan to predefined pose
- `get_plan_result` - Check planning status

**Execution Tools (tools/execution.py):**
- `execute_plan` - Execute trajectory
- `get_execution_status` - Monitor execution
- `stop_execution` - Cancel execution
- `plan_and_execute` - Combined operation

**Scene Tools (tools/scene.py):**
- `add_collision_box` - Add box obstacle
- `add_collision_sphere` - Add sphere obstacle
- `remove_collision_object` - Remove obstacle
- `clear_planning_scene` - Remove all obstacles
- `list_collision_objects` - List obstacles
- `check_state_collision` - Collision check

**Query Tools (tools/queries.py):**
- `get_current_joint_state` - Current joints
- `get_current_pose` - End-effector pose
- `compute_fk` - Forward kinematics
- `compute_ik` - Inverse kinematics
- `list_planning_groups` - Available groups

### 5. Resource Providers (resources/providers.py)

**Static Resources:**
- `moveit://planning_groups` - Available groups

**Dynamic Resources:**
- `moveit://joint_states/{group}` - Current joint positions
- `moveit://planning_scene` - Collision objects
- `moveit://active_operations` - Running operations

## Data Flow

### Planning Request Flow

1. AI client calls `plan_to_pose` tool via MCP
2. MCP server routes to planning tool handler
3. Handler creates async operation via AsyncOperationManager
4. Operation executes MoveItWrapper.plan_to_pose()
5. MoveItWrapper calls moveit_py planning API
6. Planning result stored in operation
7. Client polls with `get_plan_result` using operation ID
8. Result returned with status and trajectory

### Execution Flow

1. Client calls `execute_plan` with operation ID
2. Handler retrieves trajectory from planning operation
3. New execution operation created
4. MoveItWrapper.execute_trajectory() called
5. moveit_py executes via ROS2 controller
6. Client monitors with `get_execution_status`

## Async Operation Pattern

```python
# Submit operation
operation_id = await op_manager.submit_operation(
    async_function,
    OperationType.PLANNING,
    metadata={"group": "panda_arm"}
)

# Poll for result
status = await op_manager.get_operation_status(operation_id)

# Or wait for completion
result = await op_manager.wait_for_operation(operation_id, timeout=10.0)
```

## Configuration System

Configuration loaded from:
1. Command-line argument `--config`
2. `./config/panda_mcp_server.yaml`
3. `~/.config/moveit_mcp/config.yaml`
4. Built-in defaults

Configuration sections:
- `robot` - Robot description
- `planning` - Planning parameters
- `execution` - Execution settings
- `mcp_server` - Server settings
- `logging` - Log configuration

## Error Handling Strategy

1. **Tool Level:**
   - Try/catch around tool implementation
   - Return error as TextContent
   - Log with traceback

2. **Operation Level:**
   - Async operations catch exceptions
   - Set operation status to FAILED
   - Store error message

3. **Server Level:**
   - Graceful shutdown on fatal errors
   - Cleanup resources properly
   - Log all errors to stderr

## Performance Considerations

**Optimizations:**
- Stateful MoveItPy instance (avoid repeated init)
- Cached planning components per group
- Async operations (non-blocking)
- Parallel operation support

**Limits:**
- Max concurrent operations (configurable)
- Operation timeout and cleanup
- Resource update rate limits

## Extension Points

**Adding New Tools:**
1. Create handler in appropriate tools file
2. Register with `@server.call_tool()`
3. Add schema to `list_tools()`

**Adding New Resources:**
1. Add URI to `list_resources()`
2. Implement reader in `read_resource()`

**Custom Planning Scene:**
- Extend MoveItWrapper methods
- Add custom collision object types

**Multi-Robot Support:**
- Extend config with robot list
- Create MoveItWrapper per robot
- Add robot parameter to tools

## Security Considerations

- Server runs locally (stdio transport)
- No network exposure by default
- ROS2 security depends on system config
- Execution requires proper controller setup

## Testing Strategy

**Unit Tests:**
- Mock MoveItPy for tool testing
- Test async operation manager
- Validate configuration loading

**Integration Tests:**
- Use demo.launch.py from MoveIt
- Test with fake controllers
- Verify full planning/execution cycle

**Example Client:**
- Demonstrates all tool usage
- Validates end-to-end flow
- Serves as documentation
