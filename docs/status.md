# Status and open items

## Verified

On the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP, MoveIt plans and executes on the real Lite 6, the Amiga drives with the F710.

On a laptop: the Amiga with the arm platform in RViz; in Gazebo (headless) driving on `/cmd_vel` (straight 0.5 m/s matches the Gazebo pose; turning drifts as described in [Simulation](simulation.md#good-to-know)) and an arm trajectory goal.

Not verified yet:

- Enabling the arm from `moveit_real.launch.py` alone, without enabling it in UFactory Studio first.
- PS4 controller over Bluetooth (needs a USB Bluetooth dongle).

## Open items

Network and access:

- The GL.iNet router ships with the robot for now. Without an uplink it has no internet: Tailscale and `git pull` on the Orin do not work.
- Orin restore path: stock Seeed image + [Installation](install.md). A full disk image is optional.

ROS 2:

- OAK-D in the URDF (`camera:=true`): check it on the robot with its driver (see [Camera](camera.md)) and measure its pose (`camera.xyz`, currently an estimate).
- Measure the platform pose on the Amiga (`platform.xyz`, currently an estimate from the model dimensions) and check the Amiga with the arm in RViz.
- MoveIt: fix the xarm static TF rpy order properly instead of dropping the arm yaw.
- MoveIt: planks and the Amiga as collision objects (currently the arm only).
- Simulation: tune wheel friction against the real robot; add an IMU when someone needs it.
- Simulation pick: on its way to the carrot the gripper sweeps through the leaves of a plant 20 cm along the row (`r6c1-039` in `avans_kas`: up 5 mm at 23.5 N of its 24 N). Approach from higher if it ever pulls one out.

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
