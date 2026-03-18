"""Fixtures and utilities for integration tests."""

import os
import pytest
import subprocess
import time


def is_ros_available():
    """Check if ROS2 is available in the environment."""
    try:
        # Check if ROS_DISTRO is set
        ros_distro = os.environ.get('ROS_DISTRO')
        if not ros_distro:
            return False

        # Check if ros2 command is available
        result = subprocess.run(
            ['ros2', '--version'],
            capture_output=True,
            timeout=5
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
        # Check if /joint_states topic exists
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


# Pytest markers
ros_available = pytest.mark.skipif(
    not is_ros_available(),
    reason="ROS2 is not available in the environment"
)

moveit_available = pytest.mark.skipif(
    not is_moveit_available(),
    reason="MoveIt2 Python bindings are not available"
)

demo_running = pytest.mark.skipif(
    not is_demo_running(),
    reason="MoveIt demo is not running. Start it with: ros2 launch moveit_resources_panda_moveit_config demo.launch.py"
)

requires_ros = pytest.mark.integration


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
        'orientation': [0.0, 0.0, 0.0, 1.0]  # quaternion
    }


@pytest.fixture
def wait_for_initialization():
    """Fixture that provides a function to wait for system initialization."""
    def wait(seconds=2.0):
        """Wait for the system to initialize."""
        time.sleep(seconds)
    return wait
