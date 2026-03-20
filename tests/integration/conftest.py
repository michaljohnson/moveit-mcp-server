"""Fixtures and utilities for integration tests."""

import os
import subprocess
import time

import pytest


def pytest_sessionfinish(session, exitstatus):
    """Write pytest exit code to a file before ROS2 teardown can crash the process."""
    with open("/tmp/.pytest_exitcode", "w") as f:
        f.write(str(exitstatus))


def pytest_addoption(parser):
    """Add custom pytest command line options."""
    parser.addoption(
        "--run-execution-tests",
        action="store_true",
        default=False,
        help="Run execution tests that will move the robot (WARNING: Robot will move!)",
    )


def is_ros_available():
    """Check if ROS2 is available in the environment."""
    try:
        if not os.environ.get('ROS_DISTRO'):
            return False
        result = subprocess.run(
            ['ros2', 'topic', 'list'],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def is_moveit_available():
    """Check if MoveIt2 Python bindings are available."""
    try:
        import moveit
        import moveit.planning
        return True
    except ImportError:
        return False


def is_demo_running():
    """Check if MoveIt demo is running by checking for required topics."""
    try:
        result = subprocess.run(
            ['ros2', 'topic', 'list'],
            capture_output=True,
            timeout=5,
            text=True
        )
        if result.returncode != 0:
            return False
        topics = result.stdout
        return '/joint_states' in topics and '/robot_description' in topics
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


@pytest.fixture(scope="session", autouse=True)
def require_moveit_demo():
    """Fail the test session immediately if the MoveIt demo is not running."""
    if not is_ros_available():
        pytest.fail(
            "ROS2 is not available. Source the ROS setup:\n"
            "  source /opt/ros/$ROS_DISTRO/setup.bash"
        )
    if not is_moveit_available():
        pytest.fail(
            "MoveIt2 Python bindings are not available. "
            "Ensure moveit_py is installed and ROS environment is sourced."
        )
    if not is_demo_running():
        pytest.fail(
            "MoveIt demo is not running. Start it with:\n"
            "  ros2 launch moveit_resources_panda_moveit_config demo.launch.py"
        )


@pytest.fixture(scope="session")
def wrapper():
    """Shared MoveItWrapper instance for all tests.

    Creating multiple MoveItPy nodes in the same process causes crashes,
    so we reuse a single instance across the entire test session.
    """
    from moveit_mcp.moveit_wrapper import MoveItWrapper

    time.sleep(2.0)
    w = MoveItWrapper({
        "robot": {"name": "panda"},
        "mcp_server": {"node_name": "test_wrapper"},
    })
    yield w
    w.shutdown()


@pytest.fixture(scope="session")
def mcp_server(wrapper):
    """MCP server instance that reuses the shared wrapper."""
    import asyncio
    from moveit_mcp.server import MoveItMCPServer

    server = MoveItMCPServer()
    loop = asyncio.get_event_loop_policy().new_event_loop()
    loop.run_until_complete(server.start_with_wrapper(wrapper))
    yield server
    loop.run_until_complete(server.stop())
    loop.close()


@pytest.fixture
def ros_distro():
    """Get the ROS distribution name."""
    return os.environ.get('ROS_DISTRO', 'unknown')


@pytest.fixture
def sample_joint_state():
    """Return a sample joint state for the Panda arm."""
    return {
        'group': 'panda_arm',
        'joint_positions': [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
    }


@pytest.fixture
def sample_pose():
    """Return a sample Cartesian pose."""
    return {
        'position': [0.3, 0.0, 0.5],
        'orientation': [0.0, 0.0, 0.0, 1.0]
    }
