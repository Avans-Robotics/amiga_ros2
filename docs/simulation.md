# Simulation

Drive the Amiga and move the Lite 6 in Gazebo on your own laptop. The simulated robot uses the same topics as the real one, so code you write against the simulation also runs on the robot.

## What you need

- A laptop with Ubuntu (24.04 tested) and [Docker](https://docs.docker.com/engine/install/ubuntu/).
- A GPU that drives your desktop (Intel or AMD with Mesa works). Without one, run Gazebo without its window, see [Without a GPU](#without-a-gpu).

## Starting

The first time, clone the repo and build the image (takes a while):

```bash
git clone https://github.com/Avans-Robotics/amiga_ros2.git
cd amiga_ros2/docker
docker compose -f compose.yaml -f compose.sim.yaml up -d --build
```

Then, every time:

```bash
cd amiga_ros2/docker
docker compose -f compose.yaml -f compose.sim.yaml up -d
xhost +local:
docker exec -it amiga-ros bash
# inside the container
colcon build --symlink-install --packages-select amiga_arm_description amiga_bringup
source install/setup.bash
ros2 launch amiga_arm_description gazebo.launch.py rviz:=true
```

Gazebo opens with the Amiga and the arm on an empty ground plane; RViz shows the robot and its frames. Open a second terminal in the container for the next steps (`docker exec -it amiga-ros bash`).

![Gazebo (left) and RViz (right) with the simulated Amiga and arm](images/simulation-gazebo-rviz.png)

The simulation runs in ROS domain 1, so it does not mix with a real robot on the same network (domain 0).

## Driving

Keyboard:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
```

Keep that terminal focused: `i` forward, `,` backward, `j` / `l` turn, `k` stop. `q` / `z` change the speed.

Gamepad (plugged into the laptop, see [Driving](driving.md) for the buttons): `ros2 launch amiga_bringup teleop.launch.py agent:=false`.

Your own code: publish `geometry_msgs/msg/Twist` on `/cmd_vel`, exactly as on the real robot:

```bash
ros2 topic pub -r 10 /cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.5}, angular: {z: 0.2}}"
```

The Amiga keeps the last command until a new one arrives: send a zero Twist to stop.

## Moving the arm

The arm runs the `lite6_traj_controller` (joint trajectory controller; `xarm6_traj_controller` with `robot:=xarm6`, see [Picking a carrot](#picking-a-carrot)). Example: move all six joints in 2 seconds:

```bash
ros2 action send_goal /lite6_traj_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory \
  "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.3, 0.2, 0.3, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}]}}"
```

## Picking a carrot

The simulation can load a [pixelfield](https://github.com/Avans-Robotics/AgriSim) Field: Gazebo crop beds whose carrots can be pulled out. pixelfield comes with the image. For picking, the arm is mounted sideways (`sideways:=true`, the `arm_sideways` or `xarm6_sideways` pose in [`arm_platform.yaml`](../src/amiga_arm_description/config/arm_platform.yaml)): the platform on the rear cross tube, the arm on the front face of its vertical plank, pointing forward, so it reaches the soil between the axles. It also gets its gripper (`gripper:=true`). The real robot's pose (`platform`, `arm`) is not affected.

Two arms can be simulated:

| `robot:=` | Arm | Gripper | Grip force per finger | Pulls a carrot out? |
|---|---|---|---|---|
| `lite6` (default, the real robot) | Lite 6, 0.6 kg payload | Gripper Lite, 22.4 to 40.2 mm | 5 N | No |
| `xarm6` (option) | xArm 6, 5 kg payload | xArm Gripper as parallel jaws, 0 to 86 mm | 30 N | Yes |

`pick_carrot.py` is an example without perception or MoveIt: it takes a carrot from the Field's ground truth (`manifest.json`), moves the gripper straight down onto its leaf bunch, closes it and lifts it by the carrot's root length.

```bash
# inside the container
colcon build --symlink-install --packages-select amiga_arm_description
source install/setup.bash
ROBOT=xarm6   # or lite6
pixelfield build /opt/pixelfield/examples/amiga_10x10.yaml -o ~/fields/amiga_10x10 \
  --crops $(ros2 pkg prefix --share amiga_arm_description)/fields/crops
SPAWN=$(ros2 run amiga_arm_description pick_carrot.py spawn ~/fields/amiga_10x10/manifest.json --robot $ROBOT)
ros2 launch amiga_arm_description gazebo.launch.py gz_args:="-r $HOME/fields/amiga_10x10/world.sdf" robot:=$ROBOT sideways:=true gripper:=true $SPAWN
```

The `spawn` step chooses the carrot and prints the spawn pose (`x:=... y:=... yaw:=...`) that puts the Amiga on the bed between the first two paths, wheels in the paths on both sides and heading along the bed, with that carrot under the arm. The Field needs paths between its beds (Path Gaps), as `amiga_10x10` has. `--crops` plants the carrots 10 cm apart in the row instead of pixelfield's 4 cm ([`fields/crops/carrot.yaml`](../src/amiga_arm_description/fields/crops/carrot.yaml)): at 4 cm the jaws close on the neighbours' leaves and pull those out instead. Real carrots grow 3 to 5 cm apart, so a real picker needs narrower jaws or another approach. In a second terminal (`pick` reads the robot from the running simulation):

```bash
ros2 run amiga_arm_description pick_carrot.py pick ~/fields/amiga_10x10/manifest.json
```

It prints where the gripper actually is after each step and ends with a `RESULT` line: pulled out, or not pulled out with how far the root came up (`peak d`; the carrot comes free once d reaches its root length). Lines starting with `trajectory: Aborted` are the arm controller missing its goal tolerance; the script carries on. Restart the launch before the next pick: the carrot stays picked. A pick takes about a minute; the simulation slows down while the gripper squeezes a carrot's leaves.

Gripper: `/gripper_controller/commands` (`std_msgs/msg/Float64MultiArray`), one force in N per finger: positive opens, negative squeezes, for example `[-30.0, -30.0]`. Each finger is capped at its gripper's force (5 N or 30 N). The fingers move independently in the simulation, so one can close further than the other; the real grippers' linkage keeps them symmetric.

What to expect, in `amiga_10x10` with the carrots 10 cm apart:

- **xArm 6**: carrot `r2c2-004` (24.7 N, root 16 cm), pulled out in three of three runs. The carrot is gripped 0.10 m ahead of `base_footprint` and 0.12 m beside the bed's centre line: on the centre line, the vertical path crosses a wrist singularity of the sideways xArm 6.
- **Lite 6**: carrot `r2c3-013` (25.9 N, root 14 cm), not pulled out: the root came up 5 mm and the grip slipped. The Lite 6's wrist joints are weak (1.36 Nm on joints 4 and 6, UFactory's motor values), so the leaves turn the gripper about 20 degrees off vertical on the way down. The real Gripper Lite is specified at 5 N and the real Lite 6 at 600 g payload, both below the 15 to 26 N a carrot needs.
- With pixelfield's own 4 cm spacing, the xArm 6 did not pull its carrot out in five runs: the jaws close on the neighbours' leaves too and pull those out instead.

## Topics

| Topic | Type | |
|---|---|---|
| `/cmd_vel` | `geometry_msgs/msg/Twist` | Drive command (in) |
| `/wheel/odometry` | `nav_msgs/msg/Odometry` | Wheel odometry, frame `odom` to `base_footprint` |
| `/joint_states` | `sensor_msgs/msg/JointState` | Wheel and arm joints |
| `/tf` | `tf2_msgs/msg/TFMessage` | Includes `odom` to `base_footprint` from the wheel odometry |
| `/lite6_traj_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | Arm motion (action); `/xarm6_traj_controller/...` with `robot:=xarm6` |
| `/gripper_controller/commands` | `std_msgs/msg/Float64MultiArray` | Gripper force per finger, with `gripper:=true` |

Running your own localization (an EKF) that publishes `odom` to `base_footprint`? Start with `publish_odom_tf:=false`.

## Good to know

- **Wheel odometry drifts when turning.** The Amiga is a skid steer: its wheels slide sideways when it turns. With the arm on the back, it turns around a point near the rear axle instead of its centre, while the wheel odometry assumes the centre. Driving straight is accurate. The real robot behaves the same way, which is why localization fuses the odometry with an IMU or GNSS.
- Wheel friction is a setting in the Amiga model ([amiga_description](https://github.com/Avans-Robotics/amiga_description), `amiga.gazebo.xacro`); it is not tuned against the real robot yet.
- Crops come from pixelfield (see [Picking a carrot](#picking-a-carrot)). There are no sensors or camera in the simulation yet.
- Keep the wheels off the crops (drive in the paths): the chassis and wheels touch Plants and slow the simulation down a lot. The arm platform and the arm links pass through Plants; only the gripper touches them.

## Without a GPU

Run Gazebo without its window and watch the robot in RViz instead:

```bash
ros2 launch amiga_arm_description gazebo.launch.py gz_args:='-s -r empty.sdf' rviz:=true
```

## Launch files

| Launch file | What it does |
|---|---|
| `gazebo.launch.py` | Gazebo: the Amiga on `/cmd_vel`, the arm with its trajectory controller (`lite6_traj_controller`, or `xarm6_traj_controller` with `robot:=xarm6`). Arguments `rviz`, `publish_odom_tf`, `gz_args`, `x`, `y`, `yaw`, `robot`, `sideways`, `gripper` |
| `display.launch.py` | RViz with joint sliders, the Amiga fixed in place. `use_real_arm:=true` mirrors the real arm from `/ufactory/joint_states` instead |
| `moveit_real.launch.py` | MoveIt + driver for the real arm (Orin only) |

## For developers

`src/` is mounted into the container, so edits on the host are picked up after a `colcon build` (no image rebuild). The Amiga model (amiga_description) comes with the image, at the tag pinned in the Dockerfile.

The robot model is `amiga_arm.urdf.xacro` with `fixed:=false gazebo:=true`; the Gazebo drive comes from amiga_description's `amiga.gazebo.xacro`. xarm's `lite6_controllers.yaml` (`xarm6_controllers.yaml` with `robot:=xarm6`) is loaded by its xacro; the arm controllers are `joint_state_broadcaster` and `lite6_traj_controller` (`xarm6_traj_controller`). With `gripper:=true` the controllers come from `config/sim_controllers.yaml` instead (xarm's arm controllers plus `gripper_controller`).
