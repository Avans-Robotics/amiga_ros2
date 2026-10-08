# Status and open items

## Verified

On the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP, MoveIt plans and executes on the real Lite 6, the Amiga drives with the F710.

On a laptop: the arm platform in RViz and Gazebo.

Not verified yet:

- Enabling the arm from `moveit_real.launch.py` alone, without enabling it in UFactory Studio first.
- PS4 controller over Bluetooth (needs a USB Bluetooth dongle).

## Open items

Network and access:

- The GL.iNet router ships with the robot for now. Without an uplink it has no internet: Tailscale and `git pull` on the Orin do not work.
- Orin restore path: stock Seeed image + [Installation](install.md). A full disk image is optional.

ROS 2:

- URDF: Amiga + Lite 6 + OAK-D, RealSense and GPS optional and off by default, IMU always on. Arm and camera pose (xyz, rpy) configurable from one YAML per robot.
- MoveIt: fix the xarm static TF rpy order properly instead of dropping the arm yaw.
- MoveIt: planks and the Amiga as collision objects (currently the arm only).
- Amiga URDF: correct the chassis model from measurements of our Amiga (wheel joints sit below the floor, no rail profile), then mount the platform on it.
- Pin the xarm_ros2 commit in the Dockerfile (both images are on 3dc2b5e).

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
