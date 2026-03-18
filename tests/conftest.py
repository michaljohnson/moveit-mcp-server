"""Shared test fixtures and mocks for moveit_mcp tests."""

import asyncio
import sys
from unittest.mock import MagicMock, AsyncMock, patch

import pytest

# --- Mock ROS2/MoveIt dependencies before any imports ---
# These must be set before any moveit_mcp module is imported.

def create_mock_pose():
    """Create a mock Pose object with position and orientation."""
    pose = MagicMock()
    pose.position.x = 0.307
    pose.position.y = 0.0
    pose.position.z = 0.590
    pose.orientation.x = 0.0
    pose.orientation.y = 1.0
    pose.orientation.z = 0.0
    pose.orientation.w = 0.0
    return pose


# Create mock numpy with a usable ndarray for type annotations
mock_numpy = MagicMock()
mock_numpy.ndarray = type("ndarray", (), {})
sys.modules["numpy"] = mock_numpy

# Mock geometry_msgs
mock_geometry_msgs = MagicMock()
mock_geometry_msgs.msg.Pose = MagicMock(side_effect=create_mock_pose)
mock_geometry_msgs.msg.PoseStamped = MagicMock
sys.modules["geometry_msgs"] = mock_geometry_msgs
sys.modules["geometry_msgs.msg"] = mock_geometry_msgs.msg

# Mock other ROS2 modules
for mod in [
    "rclpy",
    "moveit",
    "moveit.planning",
    "moveit.core",
    "moveit.core.robot_state",
    "moveit_msgs",
    "moveit_msgs.msg",
    "shape_msgs",
    "shape_msgs.msg",
    "moveit_configs_utils",
    "ament_index_python",
    "ament_index_python.packages",
    "scipy",
    "scipy.spatial",
    "scipy.spatial.transform",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()


@pytest.fixture
def mock_moveit_wrapper():
    """Create a mock MoveItWrapper."""
    wrapper = MagicMock()
    wrapper.get_planning_groups.return_value = ["panda_arm", "panda_hand"]
    wrapper.get_current_state.return_value = {
        "joint_names": [
            "panda_joint1", "panda_joint2", "panda_joint3", "panda_joint4",
            "panda_joint5", "panda_joint6", "panda_joint7",
        ],
        "joint_positions": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
    }
    wrapper.get_current_pose.return_value = create_mock_pose()
    wrapper.compute_fk.return_value = create_mock_pose()
    wrapper.compute_ik.return_value = [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
    wrapper.check_collision.return_value = False
    wrapper.get_planning_scene_objects.return_value = []
    wrapper.plan_to_pose.return_value = MagicMock()  # trajectory
    wrapper.plan_to_joint_state.return_value = MagicMock()
    wrapper.plan_to_named_state.return_value = MagicMock()
    wrapper.execute_trajectory.return_value = True
    return wrapper


@pytest.fixture
def op_manager():
    """Create an AsyncOperationManager instance."""
    from moveit_mcp.async_ops import AsyncOperationManager
    return AsyncOperationManager(max_concurrent_operations=5, operation_timeout=10.0)


@pytest.fixture
def mock_server_instance(mock_moveit_wrapper):
    """Create a mock server instance that reports as initialized."""
    server = MagicMock()
    server.is_initialized.return_value = True
    server.moveit = mock_moveit_wrapper
    return server
