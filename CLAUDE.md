# amiga_ros2

ROS 2 Jazzy workspace for a farm-ng Amiga with a UFactory Lite 6 arm and an OAK-D PoE camera. See README.md for hardware, IPs and open items.

- All files, comments, docs and commits in English.
- Target is a Jetson Orin NX (arm64) at `hcr@10.95.76.50`, running everything in the Docker container `amiga-ros` (see `docker/`). Key-based SSH works; `hcr` is in the docker group.
- Never commit secrets. The competition workspace (`../Amiga_ws`) contains credentials: copy individual files from it, never its git history.
- Pull external code (xarm_ros2, micro-ROS-Agent) via the Dockerfile or a `.repos` file with pinned versions, do not vendor it.

- Simulation runs on the laptop (`docker/compose.sim.yaml`, ROS domain 1); the Orin is for the real arm only.
- Arm platform geometry and arm pose: `src/amiga_description/config/arm_platform.yaml`, the single source of truth.

Known gotchas:

- micro-ROS agent has no apt package for Jazzy: build it from source (micro-ROS-Agent, jazzy branch).
- The xArm driver publishes joint states on `/ufactory/joint_states`: add it to the `source_list` of joint_state_publisher, otherwise the arm shows in its zero pose.
- Include the OAK-D in the URDF via the depthai_camera macro and do not start `camera.launch.py`: it runs its own robot_state_publisher and duplicates TF frames.
- Gamepad and Portenta (`/dev/portenta`) in Docker need `/dev` and `/run/udev` mounted plus `device_cgroup_rules` for majors 13 (input) and 166 (ttyACM).
- Build with `-j2` / 2 colcon workers: the Orin NX runs out of memory otherwise.
- In Gazebo, xarm's `lite6_controllers.yaml` is loaded automatically by its xacro (`load_gazebo_plugin`); controllers are `joint_state_broadcaster` and `lite6_traj_controller`.
- Non-interactive `docker exec amiga-ros bash -c ...` does not source ROS (no .bashrc). Use `docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh <cmd>`.
- xarm's MoveIt launch passes `attach_rpy` to `static_transform_publisher` as roll pitch yaw, but that tool expects yaw pitch roll. Harmless while roll == yaw (current mounts); otherwise the static TF disagrees with the URDF.
- `moveit_real.launch.py` composes platform and arm pose into one world -> link_base pose because xarm's MoveIt model has no platform. Self-check: `python3 moveit_real.launch.py`.
- Do not start the real-arm launch from automation: it switches the arm to servo mode. The user runs it with someone at the e-stop.
