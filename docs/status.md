# Status and open items

## Verified

On the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP, MoveIt plans and executes on the real Lite 6, the Amiga drives with the F710.

On a laptop: the Amiga with the arm platform in Gazebo (headless: spawn and both controllers active). RViz view of the Amiga with the arm not checked yet.

Not verified yet:

- Enabling the arm from `moveit_real.launch.py` alone, without enabling it in UFactory Studio first.
- PS4 controller over Bluetooth (needs a USB Bluetooth dongle).

## Open items

Network and access:

- The GL.iNet router ships with the robot for now. Without an uplink it has no internet: Tailscale and `git pull` on the Orin do not work.
- Orin restore path: stock Seeed image + [Installation](install.md). A full disk image is optional.

ROS 2:

- URDF: OAK-D on the Amiga model (depthai_camera macro), pose configurable from the YAML.
- Measure the platform pose on the Amiga (`platform.xyz`, currently an estimate from the model dimensions) and check the Amiga with the arm in RViz.
- MoveIt: fix the xarm static TF rpy order properly instead of dropping the arm yaw.
- MoveIt: planks and the Amiga as collision objects (currently the arm only).
- Amiga model (amiga_description): `ros2_control` and Gazebo drive tags, when AgriSim (M5) needs them.
- Pin the xarm_ros2 commit in the Dockerfile (both images are on 3dc2b5e).

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
