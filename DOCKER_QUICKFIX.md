# Docker Graphics Quick Fix

If you see this error when running RViz2 in Docker:

```
QStandardPaths: XDG_RUNTIME_DIR not set, defaulting to '/tmp/runtime-root'
MESA: error: Failed to query drm device.
glx: failed to create dri3 screen
failed to load driver: iris
```

## Quick Solutions

### 1. Enable X11 Access (Try this first!)

```bash
# On your host machine, run:
xhost +local:docker

# Then restart the container
docker-compose down
docker-compose up
```

### 2. Already Fixed in docker-compose.yml

The latest `docker-compose.yml` includes software rendering:

```yaml
environment:
  - LIBGL_ALWAYS_SOFTWARE=1
  - XDG_RUNTIME_DIR=/tmp/runtime-root
```

This forces software rendering which works without GPU passthrough.

### 3. Alternative: Run RViz on Host

If graphics still don't work, run RViz on your host machine instead:

**Terminal 1 (Container) - MoveIt without RViz:**
```bash
ros2 launch moveit_resources_panda_moveit_config demo.launch.py use_rviz:=false
```

**Terminal 2 (Host) - Run RViz:**
```bash
source /opt/ros/jazzy/setup.bash
rviz2
```

