# MoveIt2 MCP Server

Model Context Protocol (MCP) server for MoveIt2 motion planning, providing AI assistants with the ability to control and plan robot motions (demo using the Panda robot arm).

[![License: Apache]](https://opensource.org/license/apache-2-0)
[![ROS2](https://img.shields.io/badge/ROS2-Jazzy%20%7C%20Rolling-blue)](https://docs.ros.org/)
[![MoveIt2](https://img.shields.io/badge/MoveIt2-Latest-green)](https://moveit.picknik.ai/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED?logo=docker&logoColor=white)](docs/DOCKER.md)

## Features

- **Async Stateful Server**: Efficient non-blocking operations with persistent MoveIt2 state
- **Motion Planning**: Plan to Cartesian poses, joint states, and named configurations
- **Execution Control**: Execute planned trajectories with progress monitoring
- **Planning Scene Management**: Add/remove collision objects dynamically
- **State Queries**: Get current robot state, compute FK/IK, check collisions
- **Resource Providers**: Real-time robot state and planning scene information

## Quick Links

- 📚 [Quick Start Guide](docs/QUICKSTART.md) - Get up and running in minutes
- 🚀 [Launch Guide](docs/LAUNCH_GUIDE.md) - **Important:** Collision-free startup
- 🐳 [Docker Guide](docs/DOCKER.md) - Run in Docker container
- 🏗️ [Architecture Documentation](docs/ARCHITECTURE.md) - Understand the system design
- 🔧 [Tools Reference](docs/TOOLS_REFERENCE.md) - Complete API documentation
- 🤝 [Contributing Guide](CONTRIBUTING.md) - Help improve the project

## Architecture

```
AI Client (Claude) ↔ MCP Server ↔ moveit_py ↔ MoveIt2 Core ↔ ROS2
```

The server maintains a stateful connection to MoveIt2, with async operation tracking for long-running planning and execution tasks. See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## Prerequisites

- **ROS2**: Rolling (recommended)
- **MoveIt2**: Installed with Python bindings (`moveit_py`)
- **Panda MoveIt Config**: `moveit_resources_panda_moveit_config` or equivalent
- **Python**: 3.10 or higher

**Note:** Rolling is recommended and fully supported via Docker. For native installation, Jazzy or Rolling are preferred.

## Installation

### Option 1: Docker (Recommended for Quick Start) 🐳

```bash
# Clone repository
git clone <repository-url>
cd moveit2-mcp-server

# Build and run with docker-compose
docker-compose build
xhost +local:docker
docker-compose run --rm moveit-mcp
```

See [docs/DOCKER.md](docs/DOCKER.md) for complete Docker instructions.

### Option 2: Native Install

**Quick Install:**

```bash
# Clone repository
cd moveit2-mcp-server

# Run setup script
./scripts/setup_environment.sh
```

**Manual Install:**

1. **Install ROS2 and MoveIt2**

   Follow the [official MoveIt2 installation guide](https://moveit.picknik.ai/main/doc/tutorials/getting_started/getting_started.html).

2. **Install the MCP Server**

   ```bash
   pip install -e .
   ```

See [QUICKSTART.md](docs/QUICKSTART.md) for detailed instructions.

## Usage

### 1. Launch MoveIt Demo (Terminal 1)

```bash
source /opt/ros/jazzy/setup.bash
cd moveit2-mcp-server

# Use fixed launch file (starts robot collision-free)
ros2 launch launch/panda_demo_fixed.launch.py
```

> **Important:** The default Panda demo starts with self-collisions. Our fixed launch file properly initializes the robot in a collision-free state by passing `initial_positions.yaml` to the URDF xacro. See [FIX_APPLIED.md](docs/FIX_APPLIED.md) for technical details.

### 2. Run MCP Server (Terminal 2)

```bash
source /opt/ros/jazzy/setup.bash
moveit-mcp-server
```

### 3. Test with Example Client (Terminal 3)

```bash
python examples/test_client.py
```

### Using with Claude Desktop

Add to your Claude Desktop configuration:

```json
{
  "mcpServers": {
    "moveit2": {
      "command": "/bin/bash",
      "args": ["-c", "source /opt/ros/jazzy/setup.bash && moveit-mcp-server"],
      "env": {"ROS_DOMAIN_ID": "0"}
    }
  }
}
```

**Note:** Make sure MoveIt is running before starting Claude Desktop.

See [QUICKSTART.md](docs/QUICKSTART.md) for complete usage guide.

## Available Tools

The server provides 20+ MCP tools organized into categories:

- **Planning Tools** (4): Plan motions to poses, joint states, or named configurations
- **Execution Tools** (4): Execute trajectories with async monitoring and control
- **Planning Scene Tools** (6): Manage collision objects in the environment
- **Query Tools** (5): Get robot state, compute kinematics, list configurations
- **Utility Tools** (2): List groups and planners

See [TOOLS_REFERENCE.md](docs/TOOLS_REFERENCE.md) for complete API documentation.

## Resources

MCP resources provide real-time information:

- `moveit://planning_groups`: Available robot groups
- `moveit://joint_states/{group}`: Current joint positions
- `moveit://planning_scene`: Collision objects
- `moveit://active_operations`: Running async operations

Resources update dynamically and can be queried at any time.

## Example Usage with Claude

Once configured, you can interact with MoveIt2 through natural language:

**User:** "What planning groups are available?"
**Claude:** Uses `list_planning_groups` → Shows "panda_arm" and "panda_hand"

**User:** "Get the current joint state of the panda arm"
**Claude:** Uses `get_current_joint_state` → Returns all joint angles

**User:** "Add a table obstacle at (0.5, 0, 0) with size 0.8m x 1.2m x 0.05m"
**Claude:** Uses `add_collision_box` → Table appears in RViz

**User:** "Plan a motion to the ready position"
**Claude:** Uses `plan_to_named_state` + `get_plan_result` → Reports success/failure

**User:** "Can you reach position (0.3, 0, 0.6)?"
**Claude:** Uses `compute_ik` → Returns joint solution or "not reachable"

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Format code
black src/

# Lint code
ruff check src/

# Run example
python examples/test_client.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or PR on GitHub.
