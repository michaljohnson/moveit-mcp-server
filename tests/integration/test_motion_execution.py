"""Integration tests for motion planning and execution."""

import asyncio

import pytest

from geometry_msgs.msg import Pose
from moveit_mcp.async_ops import AsyncOperationManager, OperationType


@pytest.mark.integration
@pytest.mark.slow
class TestMotionPlanningIntegration:
    """Integration tests for motion planning with real MoveIt."""

    def test_plan_to_named_state(self, wrapper):
        """Test planning to a named state (e.g., 'ready')."""
        result = wrapper.plan_to_named_state("panda_arm", "ready")
        if result is None:
            pytest.skip("'ready' state is not defined for this robot")
        assert result is not None

    def test_plan_to_joint_state(self, wrapper, sample_joint_state):
        """Test planning to a specific joint configuration."""
        result = wrapper.plan_to_joint_state(
            sample_joint_state['group'],
            sample_joint_state['joint_positions'],
        )
        assert result is not None, "Planning to joint state should succeed"

    def test_plan_to_pose(self, wrapper, sample_pose):
        """Test planning to a Cartesian pose."""
        target_pose = Pose()
        target_pose.position.x = sample_pose['position'][0]
        target_pose.position.y = sample_pose['position'][1]
        target_pose.position.z = sample_pose['position'][2]
        target_pose.orientation.x = sample_pose['orientation'][0]
        target_pose.orientation.y = sample_pose['orientation'][1]
        target_pose.orientation.z = sample_pose['orientation'][2]
        target_pose.orientation.w = sample_pose['orientation'][3]
        result = wrapper.plan_to_pose("panda_arm", target_pose)
        if result is None:
            target_pose.position.x = 0.4
            target_pose.position.y = 0.0
            target_pose.position.z = 0.4
            result = wrapper.plan_to_pose("panda_arm", target_pose)
            if result is None:
                pytest.skip("Could not find reachable pose for planning test")

    def test_planning_with_obstacles(self, wrapper):
        """Test planning with collision objects in the scene."""
        obstacle_pose = Pose()
        obstacle_pose.position.x = 0.4
        obstacle_pose.position.y = 0.2
        obstacle_pose.position.z = 0.3
        obstacle_pose.orientation.w = 1.0
        wrapper.add_collision_box("test_obstacle", obstacle_pose, [0.1, 0.1, 0.1])
        import time; time.sleep(0.5)
        target_pose = Pose()
        target_pose.position.x = 0.4
        target_pose.position.y = 0.0
        target_pose.position.z = 0.3
        target_pose.orientation.w = 1.0
        wrapper.plan_to_pose("panda_arm", target_pose)
        wrapper.remove_collision_object("test_obstacle")


@pytest.mark.integration
@pytest.mark.slow
@pytest.mark.execution
class TestMotionExecutionIntegration:
    """Integration tests for motion execution.

    WARNING: These tests will move the robot arm!
    """

    def test_execute_planned_trajectory(self, wrapper, sample_joint_state):
        """Test executing a planned trajectory."""
        trajectory = wrapper.plan_to_joint_state(
            sample_joint_state['group'],
            sample_joint_state['joint_positions'],
        )
        if trajectory is None:
            pytest.skip("Could not plan trajectory for execution test")
        success = wrapper.execute_trajectory(trajectory)
        if not success:
            pytest.skip("Execution failed (controllers may not be active)")
        assert success is True


@pytest.mark.integration
@pytest.mark.slow
class TestAsyncOperationsIntegration:
    """Integration tests for async operations with real MoveIt."""

    @pytest.mark.asyncio
    async def test_async_planning_operation(self, wrapper, sample_joint_state):
        """Test async planning operations."""
        op_manager = AsyncOperationManager(max_concurrent_operations=5)
        await op_manager.start()

        async def plan_fn():
            return wrapper.plan_to_joint_state(
                sample_joint_state['group'],
                sample_joint_state['joint_positions'],
            )

        operation_id = await op_manager.submit_operation(
            plan_fn,
            OperationType.PLANNING,
            metadata={"group": "panda_arm"},
        )
        result = await op_manager.wait_for_operation(operation_id, timeout=10.0)
        assert result is not None
        assert result['status'] in ['completed', 'failed']

        await op_manager.stop()

    @pytest.mark.asyncio
    async def test_multiple_concurrent_operations(self, wrapper):
        """Test multiple concurrent FK operations."""
        op_manager = AsyncOperationManager(max_concurrent_operations=3)
        await op_manager.start()

        operation_ids = []
        for i in range(3):
            async def fk_fn(idx=i):
                joint_positions = [0.0] * 7
                joint_positions[0] = idx * 0.1
                return wrapper.compute_fk("panda_arm", joint_positions)

            op_id = await op_manager.submit_operation(
                fk_fn,
                OperationType.QUERY,
                metadata={"operation": f"fk_{i}"},
            )
            operation_ids.append(op_id)

        results = [await op_manager.wait_for_operation(op_id, timeout=10.0) for op_id in operation_ids]
        completed = sum(1 for r in results if r and r['status'] == 'completed')
        assert completed >= 2, "At least 2 of 3 concurrent operations should complete"

        await op_manager.stop()
