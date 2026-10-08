# Docker

All ROS software runs in the Docker container `amiga-ros` on the Orin. It starts automatically when the Orin boots, so after power on it is already running (unless it was removed with `docker compose down`: then run `docker compose up -d` once).

The image `amiga-ros:jazzy` (built from [`docker/`](../docker/)) contains ROS 2 Jazzy, MoveIt 2, xarm_ros2 (jazzy branch, built from source), depthai-ros, joy, teleop_twist_joy and the micro-ROS agent (built from source).

## Entering the container

From an RDP desktop terminal (needed for RViz and other GUI tools):

```bash
xhost +local:
docker exec -it -e DISPLAY=:1 amiga-ros bash
```

Over SSH (no GUI):

```bash
docker exec -it amiga-ros bash
```

The prompt changes to `root@amiga:/ros2_ws#`. Run all `ros2` commands there, not on the host. Open a second terminal the same way.

## Updating the software

The repo lives in `~/amiga_ros2` on the Orin; `src/` is mounted into the container. To update:

```bash
cd ~/amiga_ros2
git pull
docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh colcon build --symlink-install --packages-select amiga_description amiga_bringup
```

If `docker/` changed (Dockerfile or compose file), rebuild the image and recreate the container:

```bash
cd ~/amiga_ros2/docker
docker compose up -d --build    # takes long on the Orin
```

## Starting and stopping

```bash
cd ~/amiga_ros2/docker
docker compose up -d     # start (or recreate after a compose change)
docker compose down      # stop and remove the container
docker ps                # check that amiga-ros is running
```

## Details

- `network_mode: host`: ROS 2 (DDS), the OAK-D and the Lite 6 need the host network.
- `/dev` and `/run/udev` are mounted, with cgroup rules for input devices (major 13) and ttyACM (major 166), so a gamepad or the Portenta is seen also when plugged in after the container started.
- `ROS_DOMAIN_ID=0` on the robot. The [simulation](simulation.md) on a laptop uses domain 1, so it stays separate.
- A non-interactive `docker exec amiga-ros bash -c ...` does not load ROS. Use `docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh <command>`.
- Build with at most 2 parallel jobs (`--parallel-workers 2`) for large builds: the Orin NX runs out of memory otherwise.
