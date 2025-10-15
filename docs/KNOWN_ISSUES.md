# Known Issues

## Controller Spawner Failures (Jazzy)

### Issue

When launching the Panda demo, you may see errors like:

```
[spawner-7] [FATAL] [1760013483.592423086] [spawner_panda_arm_controller]: Failed loading controller panda_arm_controller
[ERROR] [spawner-7]: process has died [pid 71, exit code 1, cmd '/opt/ros/jazzy/lib/controller_manager/spawner panda_arm_controller -c /controller_manager --ros-args'].
```

### Status

**Known upstream issue with ROS2 Jazzy + MoveIt2**

- GitHub Issue: https://github.com/moveit/moveit2_tutorials/issues/998
- Related: https://github.com/moveit/moveit2_tutorials/issues/995 (Testing tutorials on Jazzy)

### Root Cause

This appears to be a timing/compatibility issue between:
- `ros2_control` controller_manager
- `moveit_resources_panda_moveit_config`
- ROS2 Jazzy

The spawner nodes cannot contact the `/controller_manager/list_controllers` service in time, or there are configuration mismatches between Jazzy's ros2_control and the MoveIt config files.

### Impact

**May be cosmetic** - Some users report that despite the error:
- ✅ The controllers actually load successfully
- ✅ MoveIt planning and execution still work
- ✅ The demo functions normally

However, in some cases it may cause:
- ❌ No joint state updates
- ❌ Planning fails
- ❌ Execution doesn't work

### Workarounds

#### 1. Use Rolling Instead (Recommended)

If you need fully stable operation, use ROS2 Rolling instead of Jazzy:

```dockerfile
FROM ghcr.io/sloretz/ros:rolling-desktop-full
ENV ROS_DISTRO=rolling
```

#### 2. Ignore the Errors (If Everything Works)

If MoveIt planning works despite the errors, you can safely ignore them. Test with:

```bash
# Check if controllers actually loaded
ros2 control list_controllers

# Check if joint states are publishing
ros2 topic hz /joint_states

# Try planning in RViz - if it works, you're fine
```

#### 3. Add Delays to Spawners

Some users report success by adding delays before spawning controllers:

```python
# In launch file
import time

# Before spawner nodes
time.sleep(2)  # Give controller_manager time to start
```

#### 4. Check Controller Configuration

Verify your `ros2_controllers.yaml` has proper Jazzy format:

```yaml
controller_manager:
  ros__parameters:
    panda_arm_controller:
      type: joint_trajectory_controller/JointTrajectoryController

panda_arm_controller:
  ros__parameters:
    allow_nonzero_velocity_at_trajectory_end: true
    # ... other params
```

### When Will This Be Fixed?

The MoveIt team is actively working on Jazzy support. Monitor:
- https://github.com/moveit/moveit2/issues (for releases)
- https://github.com/moveit/moveit2_tutorials/issues/995 (Jazzy testing)

Expected to be resolved in upcoming MoveIt2 releases for Jazzy.

### Our Position

**We do not attempt to fix this in our MCP server** because:

1. It's an upstream MoveIt/ros2_control issue
2. The fix needs to be in `moveit_resources` package
3. Changes would be overwritten on package updates
4. May resolve itself with system updates

Instead, we document it and recommend:
- Use Rolling for production
- Or accept the warnings if functionality works
- Or contribute fixes upstream to MoveIt

## Other Known Issues

### Graphics in Docker

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md#rviz2-graphicsdisplay-issues) for RViz display issues in Docker.

### Self-Collision at Startup

The standard MoveIt Panda demo launch file should work correctly. If you encounter self-collision issues at startup, check that you're using the latest version of `moveit_resources_panda_moveit_config`.

---

**Note:** This document tracks issues outside our control. For issues with the MCP server itself, see the [GitHub Issues](https://github.com/...).
