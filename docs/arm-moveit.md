# Arm with MoveIt

Move the Lite 6 by dragging a goal in RViz; MoveIt plans and executes the path.

Safety first: someone at the arm with the arm e-stop (red button on the wooden arm box) in reach. MoveIt does **not** know about the arm box, the Amiga or anything else around the arm, so keep moves small and away from the platform.

## Starting

1. Power on the robot (see [Power and charging](power.md)) and log in to the Orin desktop over RDP (see [Network and remote access](network.md)). Open a terminal.
2. Enter the container with the RDP display:

   ```bash
   xhost +local:
   docker exec -it -e DISPLAY=:1 amiga-ros bash
   ```

   The prompt changes to `root@amiga:/ros2_ws#`. Run the next steps there, not on the host.
3. Start the driver and MoveIt:

   ```bash
   ros2 launch amiga_arm_description moveit_real.launch.py
   ```

   This enables the arm: the motors switch on and the arm is put in servo mode. RViz opens. Check that the arm in RViz matches the real arm.

   If the arm does not enable, enable it in UFactory Studio first (Studio, on the Orin desktop), then restart the launch. Enabling from the launch alone has not been tested on the robot yet.
4. In a second terminal (same `docker exec` as step 2), check the controller:

   ```bash
   ros2 control list_controllers    # lite6_traj_controller must be "active"
   ```

5. In RViz, MotionPlanning panel: set **Velocity Scaling** and **Acceleration Scaling** to 0.1. Drag the goal marker a few centimetres, press **Plan**, check the path, then **Execute**.

Stop with Ctrl+C in the launch terminal: the driver puts the arm back in position mode.

## UFactory Studio

Do not jog the arm with UFactory Studio while ROS is in control: Studio switches the arm out of servo mode, the driver then deactivates the trajectory controller and every goal is rejected. Restart the launch file to recover. Viewing in Studio is fine.

## After an error or the arm e-stop

- **Arm e-stop pressed**: release it, wait until the arm controller is back up, then restart `moveit_real.launch.py`.
- **Collision stop or other arm error**: restart `moveit_real.launch.py`; it clears errors when it starts. Or clear them in Studio.

The driver also offers services to do this by hand, without a restart, for example:

```bash
ros2 service list | grep ufactory    # clean_error, motion_enable, set_mode, set_state, ...
```

## Details: arm pose in MoveIt

xarm's MoveIt model has no Amiga or platform, so `moveit_real.launch.py` combines the Amiga `base_link` height (from amiga_description) with `platform` and `arm` from [`arm_platform.yaml`](../src/amiga_arm_description/config/arm_platform.yaml) into one pose of the arm base relative to the world, the floor under the centre of the Amiga (`-0.344 0 0.676`, yaw 0, for the current mount). Check the maths with `python3 src/amiga_arm_description/launch/moveit_real.launch.py`. To change the mount, see [Hardware](hardware.md#adjusting-the-mount).

Known xarm issue: its MoveIt launch passes the rpy to `static_transform_publisher` as roll-pitch-yaw, while that tool expects yaw-pitch-roll. Both only agree when roll equals yaw; otherwise the arm shows upside down in MoveIt. `moveit_real.launch.py` then drops the yaw (it logs `dropping yaw ...`) and turns the position with it: the arm stands right and MoveIt's world keeps its origin under the centre of the Amiga, but is turned by that yaw. The current mount does not hit this: platform and arm are both turned 180°, so the arm has yaw 0 relative to the Amiga. The launch prints the pose it passes on. Harmless while MoveIt knows nothing about the platform; `display.launch.py` always shows the full pose.

All launch files of `amiga_arm_description`: see [Simulation](simulation.md#launch-files).
