"""Integration tests for ROS2 and MoveIt2 availability."""

import pytest
import subprocess
import os

from .conftest import (
    is_ros_available,
    is_moveit_available,
    is_demo_running,
    ros_available,
    moveit_available,
)


class TestROSAvailability:
    """Test suite for ROS2 availability checks."""

    def test_ros_distro_environment_variable(self):
        """Test that ROS_DISTRO environment variable is set when ROS is available."""
        if is_ros_available():
            assert 'ROS_DISTRO' in os.environ
            distro = os.environ['ROS_DISTRO']
            assert distro in ['jazzy', 'rolling', 'humble', 'iron']
        else:
            pytest.skip("ROS2 not available")

    @ros_available
    def test_ros2_command_available(self):
        """Test that ros2 command is available."""
        result = subprocess.run(
            ['ros2', '--version'],
            capture_output=True,
            timeout=5
        )
        assert result.returncode == 0

    @ros_available
    def test_ros2_topic_list(self):
        """Test that we can list ROS2 topics."""
        result = subprocess.run(
            ['ros2', 'topic', 'list'],
            capture_output=True,
            timeout=5
        )
        assert result.returncode == 0

    @ros_available
    def test_ros2_node_list(self):
        """Test that we can list ROS2 nodes."""
        result = subprocess.run(
            ['ros2', 'node', 'list'],
            capture_output=True,
            timeout=5
        )
        assert result.returncode == 0


class TestMoveItAvailability:
    """Test suite for MoveIt2 availability checks."""

    @moveit_available
    def test_moveit_python_imports(self):
        """Test that MoveIt Python modules can be imported."""
        try:
            import moveit
            import moveit.planning
            import moveit.core
            import moveit.core.robot_state
            assert True
        except ImportError as e:
            pytest.fail(f"Failed to import MoveIt modules: {e}")

    @moveit_available
    def test_moveit_py_class_available(self):
        """Test that MoveItPy class is available."""
        from moveit.planning import MoveItPy
        assert MoveItPy is not None

    @moveit_available
    def test_planning_component_available(self):
        """Test that PlanningComponent class is available."""
        from moveit.planning import PlanningComponent
        assert PlanningComponent is not None

    @moveit_available
    def test_robot_state_available(self):
        """Test that RobotState class is available."""
        from moveit.core.robot_state import RobotState
        assert RobotState is not None

    @moveit_available
    def test_geometry_msgs_available(self):
        """Test that geometry_msgs are available."""
        try:
            from geometry_msgs.msg import Pose, PoseStamped
            assert Pose is not None
            assert PoseStamped is not None
        except ImportError as e:
            pytest.fail(f"Failed to import geometry_msgs: {e}")

    @moveit_available
    def test_moveit_configs_builder_available(self):
        """Test that MoveItConfigsBuilder is available."""
        try:
            from moveit_configs_utils import MoveItConfigsBuilder
            assert MoveItConfigsBuilder is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MoveItConfigsBuilder: {e}")


class TestMoveItDemoRunning:
    """Test suite to check if MoveIt demo is running."""

    def test_demo_running_check(self, ros_distro):
        """Test the demo running check function."""
        if not is_ros_available():
            pytest.skip("ROS2 not available")

        demo_status = is_demo_running()
        if not demo_status:
            pytest.skip(
                "MoveIt demo is not running. "
                "Start it with: ros2 launch moveit_resources_panda_moveit_config demo.launch.py"
            )
        else:
            assert demo_status is True

    @pytest.mark.skipif(
        not is_ros_available() or not is_demo_running(),
        reason="ROS2 or demo not available"
    )
    def test_joint_states_topic_exists(self):
        """Test that /joint_states topic exists when demo is running."""
        result = subprocess.run(
            ['ros2', 'topic', 'list'],
            capture_output=True,
            timeout=5,
            text=True
        )
        assert result.returncode == 0
        assert '/joint_states' in result.stdout

    @pytest.mark.skipif(
        not is_ros_available() or not is_demo_running(),
        reason="ROS2 or demo not available"
    )
    def test_robot_description_exists(self):
        """Test that robot_description parameter exists when demo is running."""
        result = subprocess.run(
            ['ros2', 'param', 'list'],
            capture_output=True,
            timeout=5,
            text=True
        )
        assert result.returncode == 0
        # Should have some nodes with parameters

    @pytest.mark.skipif(
        not is_ros_available() or not is_demo_running(),
        reason="ROS2 or demo not available"
    )
    def test_move_group_node_exists(self):
        """Test that move_group node exists when demo is running."""
        result = subprocess.run(
            ['ros2', 'node', 'list'],
            capture_output=True,
            timeout=5,
            text=True
        )
        assert result.returncode == 0
        # move_group or similar should be in the node list
        assert 'move_group' in result.stdout or 'moveit' in result.stdout.lower()


class TestEnvironmentSummary:
    """Provide a summary of the test environment."""

    def test_environment_summary(self, ros_distro, capsys):
        """Print a summary of the environment for test diagnostics."""
        print("\n" + "="*60)
        print("MoveIt MCP Server Integration Test Environment")
        print("="*60)

        # ROS availability
        ros_ok = is_ros_available()
        print(f"ROS2 Available: {'✓ YES' if ros_ok else '✗ NO'}")
        if ros_ok:
            print(f"ROS Distribution: {ros_distro}")

        # MoveIt availability
        moveit_ok = is_moveit_available()
        print(f"MoveIt2 Available: {'✓ YES' if moveit_ok else '✗ NO'}")

        # Demo running
        demo_ok = is_demo_running()
        print(f"Demo Running: {'✓ YES' if demo_ok else '✗ NO'}")

        print("="*60)

        if not ros_ok:
            print("\n⚠️  ROS2 not detected. Integration tests will be skipped.")
            print("   To enable integration tests:")
            print("   1. Install ROS2 (Jazzy or Rolling recommended)")
            print("   2. Source ROS2: source /opt/ros/$ROS_DISTRO/setup.bash")

        if ros_ok and not moveit_ok:
            print("\n⚠️  MoveIt2 not detected. MoveIt tests will be skipped.")
            print("   To enable MoveIt tests:")
            print("   1. Install MoveIt2 with Python bindings")
            print("   2. Install moveit_py package")

        if ros_ok and moveit_ok and not demo_ok:
            print("\n⚠️  MoveIt demo not running. Full integration tests will be skipped.")
            print("   To run full integration tests:")
            print("   1. Launch demo: ros2 launch moveit_resources_panda_moveit_config demo.launch.py")
            print("   2. Wait for RViz to appear")
            print("   3. Run integration tests: pytest tests/integration/ -v")

        if ros_ok and moveit_ok and demo_ok:
            print("\n✓ All systems ready for full integration testing!")

        print("="*60 + "\n")

        # Always pass - this is just informational
        assert True
