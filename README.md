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

## Remote access

RDP to the Orin desktop (e.g. Remmina from a laptop on the robot network), SSH as `hcr@10.95.76.50`.

## Status

Verified on the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP.

## Open items

Before the arm unit ships to the customer:

- Network at the customer site. Without the GL.iNet the robot has no WiFi or internet: only a cable with manual IP settings works, and Tailscale cannot connect. Proposal: a second GL.iNet on the robot.
- Tailscale for remote access (depends on the network item).
- Full disk image backup of the Orin (the customer gets sudo).

ROS 2:

- URDF: Amiga + Lite 6 (90° mount) + OAK-D, RealSense and GPS optional and off by default, IMU always on. Arm and camera pose (xyz, rpy) configurable from one YAML per robot. Mounts still need measuring.
- Teleop: PS4/F710 gamepad + micro-ROS agent, taken over from the competition workspace.
- MoveIt: simulation first, then the real arm, only once the URDF is correct.

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
