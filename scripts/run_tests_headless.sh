#!/usr/bin/env bash
# Run integration tests inside the container in headless mode.
# Starts the panda MoveIt demo without a display, waits for it to be ready,
# then runs pytest. Execution tests (which move the robot) are excluded by default.
#
# Usage:
#   ./scripts/run_tests_headless.sh [pytest-args...]
#   ./scripts/run_tests_headless.sh --run-execution-tests   # WARNING: moves robot

set -eo pipefail

# --- Environment setup -------------------------------------------------------
source /opt/ros/${ROS_DISTRO}/setup.bash
if [ -f ~/ws_moveit/install/setup.bash ]; then
    source ~/ws_moveit/install/setup.bash
fi
source ${VIRTUAL_ENV}/bin/activate

# --- Launch MoveIt demo in headless mode -------------------------------------
echo "Starting MoveIt panda demo (headless)..."
xvfb-run -a ros2 launch moveit_resources_panda_moveit_config demo.launch.py &
DEMO_PID=$!

cleanup() {
    echo "Stopping MoveIt demo (PID $DEMO_PID)..."
    kill "$DEMO_PID" 2>/dev/null || true
    wait "$DEMO_PID" 2>/dev/null || true
}
trap cleanup EXIT

# --- Wait for demo to be ready -----------------------------------------------
echo "Waiting for MoveIt demo to be ready..."
TIMEOUT=60
for i in $(seq 1 $TIMEOUT); do
    if ros2 topic list 2>/dev/null | grep -q "/joint_states"; then
        echo "Demo ready (${i}s)"
        break
    fi
    if [ "$i" -eq "$TIMEOUT" ]; then
        echo "ERROR: MoveIt demo did not start within ${TIMEOUT}s"
        exit 1
    fi
    sleep 1
done

# --- Run tests ---------------------------------------------------------------
# Execution tests are excluded by default (they move the physical robot).
# Pass --run-execution-tests to enable them.
# ROS2 context teardown may crash the Python process after tests complete,
# so pytest writes its exit code to a file before shutdown (see conftest.py).
cd /workspace/moveit-mcp-server
rm -f /tmp/.pytest_exitcode
python -m pytest -m "not execution" "$@" || true
if [ -f /tmp/.pytest_exitcode ]; then
    exit "$(cat /tmp/.pytest_exitcode)"
fi
exit 1
