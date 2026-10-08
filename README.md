# amiga_ros2

ROS 2 Jazzy workspace for the farm-ng Amiga: robot description, gamepad teleop, arm and camera integration, Docker deployment.

## Hardware

| Part | Details |
|------|---------|
| Compute | NVIDIA Jetson Orin NX, Ubuntu 24.04 / JetPack 7.2 |
| Arm | UFactory Lite 6, firmware 2.8.2, upright on the top plank (mount angle 0° in UFactory Studio) |
| Camera | Luxonis OAK-D-W-PoE |
| Network | PLANET IGS-604HPT-M12 industrial PoE switch, all devices connected to it |
| Gamepad | Logitech F710 (USB dongle, switch on X), or a PS4 controller over USB or Bluetooth (the Orin has no Bluetooth: needs a USB dongle) |
| Base | Amiga, driven by its Portenta H7 via micro-ROS over USB (`/dev/portenta`) |

## Network

All devices have a static IP and work without a router.

| IP | Device |
|----|--------|
| 10.95.76.11 | OAK-D camera |
| 10.95.76.50 | Orin (user `hcr`) |
| 10.95.76.155 | Lite 6 controller |
| 10.95.76.254 | GL.iNet router (lab only, does not ship with the robot) |

## Docker

`docker/` holds the image `amiga-ros:jazzy`: ROS 2 Jazzy, MoveIt 2, xarm_ros2 (jazzy branch, built from source), depthai-ros, joy, teleop_twist_joy and the micro-ROS agent (built from source). The container `amiga-ros` restarts automatically after a reboot of the Orin.

On the Orin, the repo lives in `~/amiga_ros2` (cloned with a read-only deploy key, see [host/README.md](host/README.md)). From `~/amiga_ros2/docker`:

```bash
docker compose up -d --build        # first build takes long on the Orin
docker exec -it amiga-ros bash
```

`src/` is mounted into the container. After a `git pull`, rebuild the repo packages:

```bash
docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh colcon build --packages-select amiga_description --symlink-install
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

`src/amiga_description` models the arm platform: two 575 x 190 x 25 mm planks at 90 degrees on the Amiga back rail, with the Lite 6 upright on the middle of the top plank, cable ports to the front.
`platform_link` sits on the top front edge of the rail, so the same macro can later be attached to the Amiga's `base_link`.

| Launch file | What it does |
|---|---|
| `display.launch.py` | RViz with joint sliders. `use_real_arm:=true` mirrors the real arm from `/ufactory/joint_states` instead |
| `gazebo.launch.py` | Gazebo with the Lite 6 trajectory controller (laptop) |
| `moveit_real.launch.py` | MoveIt + driver for the real arm, arm pose from the config (Orin) |

## Running the arm with MoveIt (Orin)

Safety first: someone at the arm with the emergency stop in reach. MoveIt does **not** know about the planks or anything else around the arm, so keep moves small and away from the platform.

1. Log in to the Orin desktop over RDP (Remmina, `10.95.76.50`) and open a terminal.
2. Enter the container with the RDP display:

   ```bash
   xhost +local:
   docker exec -it -e DISPLAY=:1 amiga-ros bash
   ```

   The prompt changes to `root@amiga:/ros2_ws#`. Run the next steps there, not on the host.
3. Start the driver and MoveIt:

   ```bash
   ros2 launch amiga_description moveit_real.launch.py
   ```

   RViz opens. Check that the arm in RViz matches the real arm.
4. In a second terminal (same `docker exec` as step 2), check the controller:

   ```bash
   ros2 control list_controllers    # lite6_traj_controller must be "active"
   ```

5. In RViz, MotionPlanning panel: set **Velocity Scaling** and **Acceleration Scaling** to 0.1. Drag the goal marker a few centimetres, press **Plan**, check the path, then **Execute**.

Do not jog the arm with UFactory Studio while ROS is in control: Studio switches the arm out of servo mode, the driver then deactivates the trajectory controller and every goal is rejected. Restart the launch file to recover. Viewing in Studio is fine.

## Driving with a gamepad (Orin)

Safety first: someone at the Amiga e-stop.

1. Connect the gamepad:
   - Logitech F710: plug the USB dongle into the Orin and set the switch on the back of the gamepad to **X**. In D mode the Orin kernel has no working driver for it.
   - PS4: USB cable, or Bluetooth with a USB dongle (pair once, see [host/README.md](host/README.md#6-ps4-controller-bluetooth); after that, press the PS button to reconnect).

   Check: `ls /dev/input/js*` shows a device.
2. In the container:

   ```bash
   ros2 launch amiga_bringup teleop.launch.py
   ```

| Control | Function |
|---|---|
| L1 / LB (hold) | Deadman: the Amiga only moves while it is held |
| Left stick up/down | Forward/backward, 0.5 m/s at full stick |
| Right stick left/right | Turn, 0.5 rad/s at full stick |
| R1 / RB (hold, instead of L1 / LB) | Turbo: 1.0 m/s |

Speeds and buttons are in [`src/amiga_bringup/config/ps4.yaml`](src/amiga_bringup/config/ps4.yaml). Indices follow joy's `game_controller_node` (SDL mapping), so they are the same for the PS4 (USB and Bluetooth) and the F710 in X mode.

The launch terminal does not print commands. Test without moving the Amiga: `ros2 launch amiga_bringup teleop.launch.py agent:=false`, then in a second terminal `ros2 topic echo /cmd_vel` while holding L1 / LB.

The Portenta must be connected over USB and the Amiga switched on: `ls -l /dev/portenta` shows `-> ttyACM0`.

## Camera (Orin)

The OAK-D is not in the URDF yet, so its own launch file runs without duplicate TF frames:

```bash
ros2 launch depthai_ros_driver camera.launch.py
```

In RViz: **Add**, tab **By topic**, pick the Image under `/oak/rgb/...`. `Stereo alignment error ... trying to recover` in the log is a depth warning; the colour image is not affected.

## Adjusting the mount

The mount is set by the user of the robot: measure it and enter it in [`src/amiga_description/config/arm_platform.yaml`](src/amiga_description/config/arm_platform.yaml). The values shipped are estimates. RViz, Gazebo and `moveit_real.launch.py` all read it, so there is one place to change. Units are metres and radians; frames are X forward, Y left, Z up.

| Key | Meaning |
|---|---|
| `platform.xyz`, `platform.rpy` | Pose of `platform_link` (top front edge of the rail) relative to the floor. Later, on the Amiga model: relative to the Amiga `base_link` |
| `platform.plank` | Plank size |
| `arm.xyz`, `arm.rpy` | Pose of the Lite 6 base (`link_base`) relative to `platform_link` |

Examples for `arm`:

| Mount | `xyz` | `rpy` |
|---|---|---|
| Upright on the middle of the top plank, cable ports to the front (current) | `[-0.07, 0.0, 0.025]` | `[0.0, 0.0, 3.1416]` |
| Upright on the middle of the top plank, cable ports to the back | `[-0.07, 0.0, 0.025]` | `[0.0, 0.0, 0.0]` |
| Sideways on the vertical plank, pointing forward, cable ports up | `[0.025, 0.0, -0.095]` | `[0.0, 1.5708, 0.0]` |

For the upright mount, yaw (third `rpy` value) turns the arm around its base axis.

After changing the file:

1. Rebuild (only needed once per new file; with `--symlink-install` edits are picked up directly) and check in RViz with `display.launch.py`.
2. **Also set the mount angle in UFactory Studio** to match (90° sideways, 0° upright). The arm uses it for gravity compensation and collision detection; a wrong value makes it drift or trigger false collision stops.

How MoveIt gets the pose: xarm's MoveIt model has no platform, so `moveit_real.launch.py` combines `platform` and `arm` into one pose of the arm base relative to the world (currently `-0.07 0 0.528`). Check the maths with `python3 src/amiga_description/launch/moveit_real.launch.py`.

Known xarm issue: its MoveIt launch passes the rpy to `static_transform_publisher` as roll-pitch-yaw, while that tool expects yaw-pitch-roll. Both only agree when roll equals yaw; otherwise the arm shows upside down in MoveIt. `moveit_real.launch.py` then drops the yaw (it logs `dropping yaw ...`): the arm stands right, but MoveIt's world is turned by that yaw relative to the Amiga. Harmless while MoveIt knows nothing about the platform; `display.launch.py` always shows the full pose.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `permission denied while trying to connect to the docker API` | The session started before `hcr` was added to the `docker` group | Run `newgrp docker` in that terminal, or reboot the Orin once |
| `ros2: command not found` | You are on the host, not in the container | `docker exec -it -e DISPLAY=:1 amiga-ros bash` first |
| `Goal was rejected by server` / `ABORTED` in RViz | `lite6_traj_controller` is inactive: the arm left servo mode (UFactory Studio jog, error, collision stop) | Clear errors in Studio, stop jogging there, restart `moveit_real.launch.py` |
| `Could not find a package configuration file provided by "ament_cmake"` | Non-interactive `docker exec ... bash -c` does not load ROS | Use `docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh <command>` |
| No `/cmd_vel` while holding L1 / LB | Controller not connected, F710 switch on D, or the container started before `/dev` was mounted | `ls /dev/input/js*`; `ros2 topic echo /joy`; F710 switch to X; `docker compose up -d` after a compose change |
| `/cmd_vel` published, Amiga does not move | Portenta not connected (no `/dev/portenta`, `lsusb` shows no `2341:025b`) or Amiga off | Plug the Portenta USB cable into the Orin with the Amiga on, then restart the launch |
| RViz window stays empty or tiny | No X access or no GPU access | Run `xhost +local:` on the host first; on the laptop use `compose.sim.yaml` |
| `Failed to parse yaw argument` from `static_transform_publisher` | `attach_xyz`/`attach_rpy` passed to xarm's launch without inner quotes | Use `moveit_real.launch.py`, which quotes them; by hand: `attach_xyz:='"0.025 0 0.408"'` |

## Remote access

RDP to the Orin desktop (e.g. Remmina from a laptop on the robot network), SSH as `hcr@10.95.76.50`.

## Host setup

Rebuilding the Orin from the stock Seeed image: see [host/README.md](host/README.md).

## Status

Verified on the robot: ROS 2 connects to the arm, the camera publishes, camera images show in RViz over RDP, MoveIt plans and executes on the real Lite 6, the Amiga drives with the F710. Verified on the laptop: the arm platform in RViz and Gazebo.

## Open items

Customer site:

- Network at the customer site. Without the GL.iNet the robot has no WiFi or internet: only a cable with manual IP settings works, and Tailscale cannot connect. Proposal: a second GL.iNet on the robot.
- Tailscale for remote access (installed and logged in to the avans.nl tailnet; needs internet, see the network item).
- Orin restore path: stock Seeed image + [host/README.md](host/README.md). A full disk image is optional.

ROS 2:

- URDF: Amiga + Lite 6 + OAK-D, RealSense and GPS optional and off by default, IMU always on. Arm and camera pose (xyz, rpy) configurable from one YAML per robot.
- MoveIt: fix the xarm static TF rpy order properly instead of dropping the arm yaw.
- Teleop: PS4 over Bluetooth needs a USB Bluetooth dongle (not tested).
- MoveIt: planks and the Amiga as collision objects (currently the arm only).
- Amiga URDF: correct the chassis model from measurements of our Amiga (wheel joints sit below the floor, no rail profile), then mount the platform on it.
- Pin the xarm_ros2 commit in the Dockerfile (both images are on 3dc2b5e).

Small:

- Set `DISPLAY=:1` in `compose.yaml`.
- Lower the OAK-D bandwidth if images stutter over PoE.
