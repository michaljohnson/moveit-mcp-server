# Integration Tests

This directory contains integration tests that verify the MoveIt MCP Server works correctly with real ROS2 and MoveIt2.

## Test Organization

- `test_ros_availability.py` - Check if ROS2 and MoveIt2 are installed and available
- `test_moveit_integration.py` - Test MoveItWrapper with real MoveIt
- `test_motion_execution.py` - Test motion planning and execution (moves robot!)
- `test_end_to_end.py` - Complete end-to-end workflow tests

## Running Integration Tests

### Prerequisites

1. **ROS2 installed** (Jazzy or Rolling recommended)
2. **MoveIt2 installed** with Python bindings (`moveit_py`)
3. **Demo running**: `ros2 launch moveit_resources_panda_moveit_config demo.launch.py`

### Quick Test (No ROS Required)

Check what would run without ROS:

```bash
pytest tests/integration/ -v --collect-only
```

### Basic Integration Tests

Run tests that don't move the robot:

```bash
# Source ROS first
source /opt/ros/$ROS_DISTRO/setup.bash

# Run integration tests (skips tests that move robot)
pytest tests/integration/ -v -m integration
```

### Full Integration Tests (WARNING: Moves Robot!)

Run all tests including execution tests:

```bash
# WARNING: This will move the robot arm!
pytest tests/integration/ -v -m integration --run-execution-tests
```

### Running Specific Test Categories

```bash
# Only ROS availability checks
pytest tests/integration/test_ros_availability.py -v

# Only MoveIt wrapper tests
pytest tests/integration/test_moveit_integration.py -v

# Only planning tests (no execution)
pytest tests/integration/test_motion_execution.py::TestMotionPlanningIntegration -v

# End-to-end workflow tests
pytest tests/integration/test_end_to_end.py -v
```

## Test Markers

- `@integration` - Requires ROS/MoveIt to be available
- `@slow` - Tests that take longer to run
- `@execution` - Tests that will move the robot (use caution!)

## Skipping Slow Tests

```bash
# Run fast tests only
pytest tests/integration/ -v -m "integration and not slow"
```

## Environment Summary

Get a summary of your test environment:

```bash
pytest tests/integration/test_ros_availability.py::TestEnvironmentSummary -v -s
```

This will show:
- ✓ ROS2 Available (or ✗)
- ✓ MoveIt2 Available (or ✗)
- ✓ Demo Running (or ✗)

## Expected Output

### When ROS is NOT available:
```
tests/integration/test_ros_availability.py::test_ros_distro_environment_variable SKIPPED
⚠️  ROS2 not detected. Integration tests will be skipped.
```

### When ROS is available but demo not running:
```
tests/integration/test_moveit_integration.py::test_moveit_wrapper_initialization SKIPPED
⚠️  MoveIt demo not running. Full integration tests will be skipped.
```

### When everything is ready:
```
✓ All systems ready for full integration testing!
tests/integration/test_moveit_integration.py::test_get_planning_groups PASSED
✓ Successfully retrieved planning groups
```

## Troubleshooting

### Tests are skipped

1. **Check ROS is sourced:**
   ```bash
   echo $ROS_DISTRO  # Should show: jazzy, rolling, etc.
   ```

2. **Check MoveIt demo is running:**
   ```bash
   ros2 topic list | grep joint_states
   ```

3. **Run environment summary:**
   ```bash
   pytest tests/integration/test_ros_availability.py::TestEnvironmentSummary::test_environment_summary -v -s
   ```

### Import errors

Make sure moveit_py is installed:
```bash
python3 -c "import moveit.planning; print('MoveIt available')"
```

### Tests timeout

The demo may take time to start. Wait for RViz to fully load before running tests.

## Safety Notes

⚠️ **EXECUTION TESTS**: Tests marked with `@execution` will command the robot to move. Only run these if:
- You have verified it's safe for the robot to move
- The workspace is clear of obstacles
- You're ready to emergency stop if needed
- You use the `--run-execution-tests` flag explicitly

By default, execution tests are SKIPPED for safety.
