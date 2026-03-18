"""Integration tests for MoveItWrapper with real ROS/MoveIt."""

import pytest
import asyncio

from .conftest import (
    ros_available,
    moveit_available,
    demo_running,
    is_ros_available,
    is_moveit_available,
    is_demo_running,
)


@pytest.mark.integration
@moveit_available
class TestMoveItWrapperIntegration:
    """Integration tests for MoveItWrapper with real MoveIt."""

    def test_moveit_wrapper_initialization(self, wait_for_initialization):
        """Test that MoveItWrapper can be initialized with real MoveIt."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {
                "name": "panda",
                "description_package": "moveit_resources_panda_moveit_config"
            },
            "mcp_server": {
                "node_name": "test_moveit_wrapper"
            }
        }

        wait_for_initialization(2.0)

        # Initialize wrapper
        wrapper = MoveItWrapper(config)

        # Verify initialization
        assert wrapper is not None
        assert wrapper.moveit is not None
        assert wrapper.robot_model is not None

        # Cleanup
        wrapper.shutdown()

    def test_get_planning_groups(self, wait_for_initialization):
        """Test getting planning groups from real MoveIt."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_groups"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Get planning groups
        groups = wrapper.get_planning_groups()

        # Verify we have expected groups
        assert isinstance(groups, list)
        assert len(groups) > 0
        assert "panda_arm" in groups

        wrapper.shutdown()

    def test_get_current_state(self, wait_for_initialization):
        """Test getting current robot state."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_state"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Get current state
        state = wrapper.get_current_state("panda_arm")

        # Verify state structure
        assert isinstance(state, dict)
        assert "joint_names" in state
        assert "joint_positions" in state
        assert len(state["joint_names"]) > 0
        assert len(state["joint_positions"]) > 0
        assert len(state["joint_names"]) == len(state["joint_positions"])

        wrapper.shutdown()

    def test_get_current_pose(self, wait_for_initialization):
        """Test getting current end-effector pose."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_pose"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Get current pose
        pose = wrapper.get_current_pose("panda_arm")

        # Verify pose structure
        assert pose is not None
        assert hasattr(pose, 'position')
        assert hasattr(pose, 'orientation')
        assert hasattr(pose.position, 'x')
        assert hasattr(pose.position, 'y')
        assert hasattr(pose.position, 'z')
        assert hasattr(pose.orientation, 'x')
        assert hasattr(pose.orientation, 'y')
        assert hasattr(pose.orientation, 'z')
        assert hasattr(pose.orientation, 'w')

        wrapper.shutdown()

    def test_compute_fk(self, wait_for_initialization, sample_joint_state):
        """Test forward kinematics computation."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_fk"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Compute FK
        pose = wrapper.compute_fk(
            sample_joint_state['group'],
            sample_joint_state['joint_positions']
        )

        # Verify result
        assert pose is not None
        assert hasattr(pose, 'position')
        assert hasattr(pose, 'orientation')

        wrapper.shutdown()

    def test_compute_ik(self, wait_for_initialization, sample_pose):
        """Test inverse kinematics computation."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from geometry_msgs.msg import Pose

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_ik"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Create pose
        target_pose = Pose()
        target_pose.position.x = sample_pose['position'][0]
        target_pose.position.y = sample_pose['position'][1]
        target_pose.position.z = sample_pose['position'][2]
        target_pose.orientation.x = sample_pose['orientation'][0]
        target_pose.orientation.y = sample_pose['orientation'][1]
        target_pose.orientation.z = sample_pose['orientation'][2]
        target_pose.orientation.w = sample_pose['orientation'][3]

        # Compute IK
        joint_positions = wrapper.compute_ik("panda_arm", target_pose, timeout=5.0)

        # Verify result (may be None if unreachable)
        if joint_positions is not None:
            assert isinstance(joint_positions, list)
            assert len(joint_positions) > 0

        wrapper.shutdown()

    def test_planning_scene_operations(self, wait_for_initialization):
        """Test planning scene manipulation."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from geometry_msgs.msg import Pose

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_scene"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Add a box
        box_pose = Pose()
        box_pose.position.x = 0.5
        box_pose.position.y = 0.0
        box_pose.position.z = 0.0
        box_pose.orientation.w = 1.0

        wrapper.add_collision_box("test_box", box_pose, [0.1, 0.1, 0.1])

        # List objects
        objects = wrapper.get_planning_scene_objects()
        assert "test_box" in objects

        # Remove box
        wrapper.remove_collision_object("test_box")

        # Verify removed
        objects = wrapper.get_planning_scene_objects()
        assert "test_box" not in objects

        wrapper.shutdown()
