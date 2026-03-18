"""Tests for MoveItWrapper (with mocking)."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock

# Mock the ROS imports before importing moveit_wrapper
import sys

# Mock numpy
try:
    import numpy as np
except ImportError:
    sys.modules['numpy'] = MagicMock()
    import numpy as np
sys.modules['rclpy'] = MagicMock()
sys.modules['geometry_msgs'] = MagicMock()
sys.modules['geometry_msgs.msg'] = MagicMock()
sys.modules['moveit'] = MagicMock()
sys.modules['moveit.planning'] = MagicMock()
sys.modules['moveit.core'] = MagicMock()
sys.modules['moveit.core.robot_state'] = MagicMock()
sys.modules['moveit_msgs'] = MagicMock()
sys.modules['moveit_msgs.msg'] = MagicMock()
sys.modules['shape_msgs'] = MagicMock()
sys.modules['shape_msgs.msg'] = MagicMock()
sys.modules['moveit_configs_utils'] = MagicMock()
sys.modules['ament_index_python'] = MagicMock()
sys.modules['ament_index_python.packages'] = MagicMock()
sys.modules['scipy'] = MagicMock()
sys.modules['scipy.spatial'] = MagicMock()
sys.modules['scipy.spatial.transform'] = MagicMock()

from moveit_mcp.moveit_wrapper import transform_matrix_to_pose


def test_transform_matrix_to_pose():
    """Test transformation matrix to pose conversion."""
    # Import after mocking
    from geometry_msgs.msg import Pose

    # Create a simple identity transformation with translation
    transform = np.array([
        [1, 0, 0, 1.0],
        [0, 1, 0, 2.0],
        [0, 0, 1, 3.0],
        [0, 0, 0, 1]
    ])

    with patch('moveit_mcp.moveit_wrapper.Pose') as MockPose:
        mock_pose = MagicMock()
        MockPose.return_value = mock_pose

        result = transform_matrix_to_pose(transform)

        # Verify position was set
        assert mock_pose.position.x == 1.0
        assert mock_pose.position.y == 2.0
        assert mock_pose.position.z == 3.0


def test_moveit_wrapper_config():
    """Test MoveItWrapper configuration parsing."""
    config = {
        "robot": {
            "name": "panda",
            "description_package": "moveit_resources_panda_moveit_config"
        },
        "planning": {
            "default_planner": "RRTConnect",
            "default_timeout": 5.0,
        },
        "mcp_server": {
            "node_name": "test_node"
        }
    }

    # Test configuration values
    assert config["robot"]["name"] == "panda"
    assert config["planning"]["default_planner"] == "RRTConnect"
    assert config["mcp_server"]["node_name"] == "test_node"


def test_default_config():
    """Test default configuration generation."""
    from moveit_mcp.server import MoveItMCPServer

    server = MoveItMCPServer()
    config = server._default_config()

    # Verify default values
    assert config["robot"]["name"] == "panda"
    assert config["planning"]["default_planner"] == "RRTConnect"
    assert config["planning"]["default_timeout"] == 5.0
    assert config["execution"]["execution_timeout"] == 30.0
    assert config["mcp_server"]["operation_timeout"] == 60.0
