# amiga_ros2

ROS 2 Jazzy workspace for the farm-ng Amiga: robot description, gamepad teleop, arm and camera integration, Docker deployment.

## Hardware

| Part | Details |
|------|---------|
| Compute | NVIDIA Jetson Orin NX, Ubuntu 24.04 / JetPack 7.2 |
| Arm | UFactory Lite 6, firmware 2.8.2, mounted at 90° (mount angle set in UFactory Studio) |
| Camera | Luxonis OAK-D, PoE |
| Network | PLANET IGS-604HPT-M12 industrial PoE switch, all devices connected to it |

## Network

All devices have a static IP and work without a router.

| IP | Device |
|----|--------|
| 10.95.76.11 | OAK-D camera |
| 10.95.76.50 | Orin (user `hcr`) |
| 10.95.76.155 | Lite 6 controller |
| 10.95.76.254 | GL.iNet router (lab only, does not ship with the robot) |

## Docker

`docker/` holds the image `amiga-ros:jazzy`: ROS 2 Jazzy, MoveIt 2, xarm_ros2 (jazzy branch, built from source) and depthai-ros. The container `amiga-ros` restarts automatically after a reboot of the Orin.

On the Orin, from `docker/`:

```bash
docker compose up -d --build        # first build takes long on the Orin
docker exec -it amiga-ros bash
```

For GUI tools (RViz) over RDP, pass the RDP display:

```bash
docker exec -it -e DISPLAY=:1 amiga-ros bash
```

## Simulation (laptop)

Gazebo and RViz run on a laptop, using the same image plus `docker/compose.sim.yaml` (desktop GPU via `/dev/dri`, ROS domain 1 so it stays separate from the robot).

```bash
cd docker
docker compose -f compose.yaml -f compose.sim.yaml up -d --build
xhost +local:
docker exec -it amiga-ros bash
# inside the container
cd /ros2_ws && colcon build --packages-select amiga_description --symlink-install && source install/setup.bash
ros2 launch amiga_description display.launch.py    # RViz with joint sliders
ros2 launch amiga_description gazebo.launch.py     # Gazebo with the Lite 6 trajectory controller
```

`src/` is mounted into the container, so edits on the host are picked up after a `colcon build` (no image rebuild).

## Arm platform description

`src/amiga_description` models the arm platform: two 575 x 190 x 25 mm planks at 90 degrees on the Amiga back rail, with the Lite 6 on the vertical plank pointing forward (+X).
All geometry and the arm pose live in `src/amiga_description/config/arm_platform.yaml`; change values there after measuring.
`platform_link` sits on the top front edge of the rail, so the same macro can later be attached to the Amiga's `base_link`.

On the robot, `display.launch.py use_real_arm:=true` mirrors the real arm from `/ufactory/joint_states`.

## Remote access

RDP to the Orin desktop (e.g. Remmina from a laptop on the robot network), SSH as `hcr@10.95.76.50`.

## Host setup

Rebuilding the Orin from the stock Seeed image: see [host/README.md](host/README.md).

## Status

Verified on the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP.

## Open items

Before the arm unit ships to the customer:

- Network at the customer site. Without the GL.iNet the robot has no WiFi or internet: only a cable with manual IP settings works, and Tailscale cannot connect. Proposal: a second GL.iNet on the robot.
- Tailscale for remote access (installed, not logged in; depends on the network item).
- Orin restore path: stock Seeed image + [host/README.md](host/README.md). A full disk image is optional.

ROS 2:

- URDF: Amiga + Lite 6 (90° mount) + OAK-D, RealSense and GPS optional and off by default, IMU always on. Arm and camera pose (xyz, rpy) configurable from one YAML per robot. Mounts still need measuring.
- Teleop: PS4/F710 gamepad + micro-ROS agent, taken over from the competition workspace.
- MoveIt: simulation first, then the real arm, only once the URDF is correct.

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
