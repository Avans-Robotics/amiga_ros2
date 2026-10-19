# Simulation

Gazebo and RViz run on a laptop, using the same image plus [`docker/compose.sim.yaml`](../docker/compose.sim.yaml) (desktop GPU via `/dev/dri`, ROS domain 1 so it stays separate from the robot). The Orin is for the real robot only.

```bash
cd docker
docker compose -f compose.yaml -f compose.sim.yaml up -d --build
xhost +local:
docker exec -it amiga-ros bash
# inside the container
cd /ros2_ws && colcon build --packages-select amiga_arm_description --symlink-install && source install/setup.bash
ros2 launch amiga_arm_description display.launch.py    # RViz with joint sliders
ros2 launch amiga_arm_description gazebo.launch.py     # Gazebo with the Lite 6 trajectory controller
```

`src/` is mounted into the container, so edits on the host are picked up after a `colcon build` (no image rebuild). The Amiga model (amiga_description) comes with the image, at the tag pinned in the Dockerfile.

## Launch files

| Launch file | What it does |
|---|---|
| `display.launch.py` | RViz with joint sliders. `use_real_arm:=true` mirrors the real arm from `/ufactory/joint_states` instead |
| `gazebo.launch.py` | Gazebo with the Lite 6 trajectory controller (laptop) |
| `moveit_real.launch.py` | MoveIt + driver for the real arm, arm pose from the config (Orin) |

In Gazebo, xarm's `lite6_controllers.yaml` is loaded by its xacro; the controllers are `joint_state_broadcaster` and `lite6_traj_controller`.
