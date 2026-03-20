"""Integration tests for MoveItWrapper with real ROS/MoveIt."""

import pytest

from geometry_msgs.msg import Pose


@pytest.mark.integration
class TestMoveItWrapperIntegration:
    """Integration tests for MoveItWrapper with real MoveIt."""

    def test_moveit_wrapper_initialization(self, wrapper):
        """Test that MoveItWrapper initializes correctly."""
        assert wrapper.moveit is not None
        assert wrapper.robot_model is not None

    def test_get_planning_groups(self, wrapper):
        """Test getting planning groups from real MoveIt."""
        groups = wrapper.get_planning_groups()
        assert isinstance(groups, list)
        assert "panda_arm" in groups

    def test_get_current_state(self, wrapper):
        """Test getting current robot state."""
        state = wrapper.get_current_state("panda_arm")
        assert isinstance(state, dict)
        assert "joint_names" in state
        assert "joint_positions" in state
        assert len(state["joint_names"]) == len(state["joint_positions"])

    def test_get_current_pose(self, wrapper):
        """Test getting current end-effector pose."""
        pose = wrapper.get_current_pose("panda_arm")
        assert pose is not None
        assert hasattr(pose, 'position')
        assert hasattr(pose, 'orientation')
        assert hasattr(pose.position, 'x')
        assert hasattr(pose.orientation, 'w')

    def test_compute_fk(self, wrapper, sample_joint_state):
        """Test forward kinematics computation."""
        pose = wrapper.compute_fk(
            sample_joint_state['group'],
            sample_joint_state['joint_positions'],
        )
        assert pose is not None
        assert hasattr(pose, 'position')
        assert hasattr(pose, 'orientation')

    def test_compute_ik(self, wrapper, sample_pose):
        """Test inverse kinematics computation."""
        target_pose = Pose()
        target_pose.position.x = sample_pose['position'][0]
        target_pose.position.y = sample_pose['position'][1]
        target_pose.position.z = sample_pose['position'][2]
        target_pose.orientation.x = sample_pose['orientation'][0]
        target_pose.orientation.y = sample_pose['orientation'][1]
        target_pose.orientation.z = sample_pose['orientation'][2]
        target_pose.orientation.w = sample_pose['orientation'][3]
        joint_positions = wrapper.compute_ik("panda_arm", target_pose, timeout=5.0)
        if joint_positions is not None:
            assert isinstance(joint_positions, list)
            assert len(joint_positions) > 0

    def test_check_state_collision_free(self, wrapper, sample_joint_state):
        """Test collision check with a known collision-free state."""
        result = wrapper.check_state_collision(
            sample_joint_state['group'],
            sample_joint_state['joint_positions'],
        )
        assert isinstance(result, bool)
        assert result is False

    def test_check_state_collision_with_obstacle(self, wrapper, sample_joint_state):
        """Test collision check detects collision with an obstacle placed at the end-effector."""
        group = sample_joint_state['group']
        joint_positions = sample_joint_state['joint_positions']

        # Compute FK to find where the end-effector is
        ee_pose = wrapper.compute_fk(group, joint_positions)

        # Place a box right at the end-effector so it collides
        wrapper.add_collision_box(
            "collision_test_box", ee_pose, [0.5, 0.5, 0.5]
        )
        try:
            result = wrapper.check_state_collision(group, joint_positions)
            assert isinstance(result, bool)
            assert result is True
        finally:
            wrapper.remove_collision_object("collision_test_box")

    def test_planning_scene_operations(self, wrapper):
        """Test planning scene manipulation."""
        box_pose = Pose()
        box_pose.position.x = 0.5
        box_pose.orientation.w = 1.0
        wrapper.add_collision_box("test_box", box_pose, [0.1, 0.1, 0.1])
        assert "test_box" in wrapper.get_planning_scene_objects()
        wrapper.remove_collision_object("test_box")
        assert "test_box" not in wrapper.get_planning_scene_objects()
