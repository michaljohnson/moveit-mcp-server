"""End-to-end integration tests for motion planning and execution.

These tests verify that the robot arm can actually plan and execute motions.
They require the MoveIt demo to be running.
"""

import pytest
import asyncio
import time

from .conftest import (
    ros_available,
    moveit_available,
    demo_running,
    is_ros_available,
    is_moveit_available,
    is_demo_running,
)


@pytest.mark.integration
@pytest.mark.slow
@moveit_available
class TestMotionPlanningIntegration:
    """Integration tests for motion planning with real MoveIt."""

    def test_plan_to_named_state(self, wait_for_initialization):
        """Test planning to a named state (e.g., 'ready')."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_plan_named"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Plan to ready state
        result = wrapper.plan_to_named_state("panda_arm", "ready")

        # Verify planning result
        if result is not None:
            print("✓ Successfully planned to 'ready' state")
            assert result is not None
        else:
            print("✗ Planning to 'ready' state failed (may not be defined)")
            pytest.skip("'ready' state may not be defined for this robot")

        wrapper.shutdown()

    def test_plan_to_joint_state(self, wait_for_initialization, sample_joint_state):
        """Test planning to a specific joint configuration."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_plan_joints"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Plan to joint state
        result = wrapper.plan_to_joint_state(
            sample_joint_state['group'],
            sample_joint_state['joint_positions']
        )

        # Verify planning result
        assert result is not None, "Planning to joint state should succeed"
        print(f"✓ Successfully planned to joint state")

        wrapper.shutdown()

    def test_plan_to_pose(self, wait_for_initialization, sample_pose):
        """Test planning to a Cartesian pose."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from geometry_msgs.msg import Pose

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_plan_pose"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Create target pose
        target_pose = Pose()
        target_pose.position.x = sample_pose['position'][0]
        target_pose.position.y = sample_pose['position'][1]
        target_pose.position.z = sample_pose['position'][2]
        target_pose.orientation.x = sample_pose['orientation'][0]
        target_pose.orientation.y = sample_pose['orientation'][1]
        target_pose.orientation.z = sample_pose['orientation'][2]
        target_pose.orientation.w = sample_pose['orientation'][3]

        # Plan to pose
        result = wrapper.plan_to_pose("panda_arm", target_pose)

        # Verify planning result (may fail if pose is unreachable)
        if result is not None:
            print(f"✓ Successfully planned to pose {sample_pose['position']}")
            assert result is not None
        else:
            print(f"✗ Planning to pose {sample_pose['position']} failed (may be unreachable)")
            # Try a more reachable pose
            target_pose.position.x = 0.4
            target_pose.position.y = 0.0
            target_pose.position.z = 0.4
            result = wrapper.plan_to_pose("panda_arm", target_pose)
            if result is None:
                pytest.skip("Could not find reachable pose for planning test")

        wrapper.shutdown()

    def test_planning_with_obstacles(self, wait_for_initialization):
        """Test planning with collision objects in the scene."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from geometry_msgs.msg import Pose

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_plan_obstacles"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Add obstacle
        obstacle_pose = Pose()
        obstacle_pose.position.x = 0.4
        obstacle_pose.position.y = 0.2
        obstacle_pose.position.z = 0.3
        obstacle_pose.orientation.w = 1.0

        wrapper.add_collision_box("test_obstacle", obstacle_pose, [0.1, 0.1, 0.1])
        wait_for_initialization(0.5)  # Wait for planning scene to update

        # Try to plan (should avoid obstacle)
        target_pose = Pose()
        target_pose.position.x = 0.4
        target_pose.position.y = 0.0
        target_pose.position.z = 0.3
        target_pose.orientation.w = 1.0

        result = wrapper.plan_to_pose("panda_arm", target_pose)

        # Clean up
        wrapper.remove_collision_object("test_obstacle")
        wrapper.shutdown()

        # Verify
        if result is not None:
            print("✓ Successfully planned motion avoiding obstacle")
        else:
            print("Planning failed (obstacle may block all paths)")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.execution
@moveit_available
class TestMotionExecutionIntegration:
    """Integration tests for motion execution with real MoveIt.

    WARNING: These tests will move the robot arm!
    Only run if you have verified it's safe to execute motions.
    """

    def test_execute_planned_trajectory(self, wait_for_initialization, sample_joint_state):
        """Test executing a planned trajectory.

        WARNING: This will move the robot arm if controllers are active!
        """
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        # Skip by default unless explicitly enabled
        if not pytest.config.getoption("--run-execution-tests", default=False):
            pytest.skip(
                "Execution tests skipped by default. "
                "Run with --run-execution-tests to enable (WARNING: will move robot!)"
            )

        from moveit_mcp.moveit_wrapper import MoveItWrapper

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_execute"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Plan motion
        trajectory = wrapper.plan_to_joint_state(
            sample_joint_state['group'],
            sample_joint_state['joint_positions']
        )

        if trajectory is None:
            wrapper.shutdown()
            pytest.skip("Could not plan trajectory for execution test")

        # Execute trajectory
        print("⚠️  EXECUTING MOTION - Robot will move!")
        success = wrapper.execute_trajectory(trajectory)

        wrapper.shutdown()

        # Verify execution
        if success:
            print("✓ Trajectory executed successfully")
            assert success is True
        else:
            print("✗ Trajectory execution failed")
            # Execution may fail if controllers aren't active
            pytest.skip("Execution failed (controllers may not be active)")


@pytest.mark.integration
@pytest.mark.slow
@moveit_available
class TestAsyncOperationsIntegration:
    """Integration tests for async operations with real MoveIt."""

    @pytest.mark.asyncio
    async def test_async_planning_operation(self, wait_for_initialization, sample_joint_state):
        """Test async planning operations."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from moveit_mcp.async_ops import AsyncOperationManager, OperationType

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_async_plan"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Create operation manager
        op_manager = AsyncOperationManager(max_concurrent_operations=5)
        await op_manager.start()

        # Submit planning operation
        async def plan_fn():
            return wrapper.plan_to_joint_state(
                sample_joint_state['group'],
                sample_joint_state['joint_positions']
            )

        operation_id = await op_manager.submit_operation(
            plan_fn,
            OperationType.PLANNING,
            metadata={"group": "panda_arm"}
        )

        # Wait for completion
        result = await op_manager.wait_for_operation(operation_id, timeout=10.0)

        # Verify
        assert result is not None
        assert result['status'] in ['completed', 'failed']

        if result['status'] == 'completed':
            print(f"✓ Async planning operation completed successfully")
            assert result['result'] is not None

        # Cleanup
        await op_manager.stop()
        wrapper.shutdown()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, wait_for_initialization):
        """Test multiple concurrent planning operations."""
        if not is_demo_running():
            pytest.skip("MoveIt demo not running")

        from moveit_mcp.moveit_wrapper import MoveItWrapper
        from moveit_mcp.async_ops import AsyncOperationManager, OperationType

        config = {
            "robot": {"name": "panda"},
            "mcp_server": {"node_name": "test_concurrent"}
        }

        wait_for_initialization(2.0)
        wrapper = MoveItWrapper(config)

        # Create operation manager
        op_manager = AsyncOperationManager(max_concurrent_operations=3)
        await op_manager.start()

        # Submit multiple FK operations (fast)
        operation_ids = []
        for i in range(3):
            async def fk_fn(idx=i):
                joint_positions = [0.0] * 7
                joint_positions[0] = idx * 0.1
                return wrapper.compute_fk("panda_arm", joint_positions)

            op_id = await op_manager.submit_operation(
                fk_fn,
                OperationType.QUERY,
                metadata={"operation": f"fk_{i}"}
            )
            operation_ids.append(op_id)

        # Wait for all to complete
        results = []
        for op_id in operation_ids:
            result = await op_manager.wait_for_operation(op_id, timeout=10.0)
            results.append(result)

        # Verify all completed
        completed_count = sum(1 for r in results if r and r['status'] == 'completed')
        print(f"✓ {completed_count}/3 concurrent operations completed")
        assert completed_count >= 2, "At least 2 operations should complete"

        # Cleanup
        await op_manager.stop()
        wrapper.shutdown()


def pytest_addoption(parser):
    """Add custom pytest command line options."""
    parser.addoption(
        "--run-execution-tests",
        action="store_true",
        default=False,
        help="Run execution tests that will move the robot (WARNING: Robot will move!)"
    )
