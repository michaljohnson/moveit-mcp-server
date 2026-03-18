"""Tests for async operation manager."""

import asyncio

import pytest

from moveit_mcp.async_ops import (
    AsyncOperationManager,
    OperationStatus,
    OperationType,
)


@pytest.fixture
def manager():
    return AsyncOperationManager(max_concurrent_operations=3, operation_timeout=5.0)


@pytest.mark.asyncio
async def test_submit_operation(manager):
    """Test submitting an async operation."""
    await manager.start()
    try:
        async def dummy_op():
            return "success"

        op_id = await manager.submit_operation(dummy_op, OperationType.PLANNING)
        assert op_id is not None
        assert isinstance(op_id, str)
        assert len(op_id) > 0
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_operation_completes(manager):
    """Test that operations complete and return results."""
    await manager.start()
    try:
        async def dummy_op():
            return {"trajectory": "mock_data"}

        op_id = await manager.submit_operation(dummy_op, OperationType.PLANNING)

        # Wait for completion
        result = await manager.wait_for_operation(op_id, timeout=5.0)
        assert result is not None
        assert result["status"] == "completed"
        assert result["progress"] == 1.0
        assert result["result"] == {"trajectory": "mock_data"}
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_operation_failure(manager):
    """Test that failed operations are tracked correctly."""
    await manager.start()
    try:
        async def failing_op():
            raise ValueError("Planning failed: no valid path")

        op_id = await manager.submit_operation(failing_op, OperationType.PLANNING)
        result = await manager.wait_for_operation(op_id, timeout=5.0)

        assert result is not None
        assert result["status"] == "failed"
        assert "Planning failed" in result["error"]
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_cancel_operation(manager):
    """Test cancelling a running operation."""
    await manager.start()
    try:
        async def slow_op():
            await asyncio.sleep(10)
            return "done"

        op_id = await manager.submit_operation(slow_op, OperationType.EXECUTION)
        await asyncio.sleep(0.1)  # Let it start

        success = await manager.cancel_operation(op_id)
        assert success is True

        await asyncio.sleep(0.1)
        status = await manager.get_operation_status(op_id)
        assert status["status"] in ["cancelled", "running"]
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_max_concurrent_operations(manager):
    """Test that max concurrent operations limit is enforced."""
    await manager.start()
    try:
        async def slow_op():
            await asyncio.sleep(10)

        # Submit max operations
        for _ in range(3):
            await manager.submit_operation(slow_op, OperationType.PLANNING)

        # The next one should raise
        with pytest.raises(RuntimeError, match="Maximum concurrent operations"):
            await manager.submit_operation(slow_op, OperationType.PLANNING)
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_list_operations(manager):
    """Test listing all operations."""
    await manager.start()
    try:
        async def dummy_op():
            return "ok"

        await manager.submit_operation(
            dummy_op, OperationType.PLANNING, metadata={"group": "panda_arm"}
        )
        await manager.submit_operation(
            dummy_op, OperationType.EXECUTION, metadata={"controllers": []}
        )

        await asyncio.sleep(0.2)
        ops = await manager.list_operations()
        assert len(ops) == 2
        types = {op["type"] for op in ops}
        assert "planning" in types
        assert "execution" in types
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_get_nonexistent_operation(manager):
    """Test querying a non-existent operation."""
    await manager.start()
    try:
        status = await manager.get_operation_status("nonexistent-id")
        assert status is None
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_operation_metadata(manager):
    """Test that operation metadata is preserved."""
    await manager.start()
    try:
        async def dummy_op():
            return "ok"

        metadata = {"group": "panda_arm", "target": "pose"}
        op_id = await manager.submit_operation(
            dummy_op, OperationType.PLANNING, metadata=metadata
        )

        await asyncio.sleep(0.1)
        status = await manager.get_operation_status(op_id)
        assert status["metadata"] == metadata
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_operation_progress(manager):
    """Test that operation progress is tracked."""
    await manager.start()
    try:
        async def test_fn():
            await asyncio.sleep(0.1)
            return "done"

        op_id = await manager.submit_operation(test_fn, OperationType.PLANNING)

        # Initially should be pending or running
        status = await manager.get_operation_status(op_id)
        assert status["progress"] >= 0.0

        # Wait for completion
        await manager.wait_for_operation(op_id, timeout=5.0)

        # Should be 100% complete
        status = await manager.get_operation_status(op_id)
        assert status["progress"] == 1.0
    finally:
        await manager.stop()


@pytest.mark.asyncio
async def test_generate_unique_ids(manager):
    """Test that generated operation IDs are unique."""
    ids = {manager.generate_operation_id() for _ in range(100)}
    assert len(ids) == 100
