# Troubleshooting

## Power and pendant

| Symptom | Cause | Fix |
|---|---|---|
| Pendant shows CLEAR E-STOP, "No healthy motors" | An e-stop was pressed | Release the e-stop, tap CLEAR E-STOP |
| Robot does not power on | Keys not both ON, or empty batteries | Both keys to ON; charge (see [Power and charging](power.md)) |
| Other pendant errors | | Power cycle: Orin shutdown, both keys OFF, both keys ON |

## Container and login

| Symptom | Cause | Fix |
|---|---|---|
| `permission denied while trying to connect to the docker API` | The session started before `hcr` was added to the `docker` group | Run `newgrp docker` in that terminal, or reboot the Orin once |
| `ros2: command not found` | You are on the host, not in the container | `docker exec -it -e DISPLAY=:1 amiga-ros bash` first |
| `Could not find a package configuration file provided by "ament_cmake"` | Non-interactive `docker exec ... bash -c` does not load ROS | Use `docker exec -w /ros2_ws amiga-ros /ros_entrypoint.sh <command>` |
| RViz window stays empty or tiny | No X access or no GPU access | Run `xhost +local:` on the host first; on a laptop use `compose.sim.yaml` |

## Driving

| Symptom | Cause | Fix |
|---|---|---|
| No `/cmd_vel` while holding L1 / LB | Controller not connected, F710 switch on D, or the container started before `/dev` was mounted | `ls /dev/input/js*`; `ros2 topic echo /joy`; F710 switch to X; `docker compose up -d` after a compose change |
| `/cmd_vel` published, Amiga does not move | Pendant not in AUTO ACTIVE, Portenta not connected (no `/dev/portenta`, `lsusb` shows no `2341:025b`), or Amiga e-stop pressed | Pendant to AUTO ACTIVE; plug the Portenta USB cable into the Orin with the Amiga on, then restart the launch; clear the e-stop |

## Arm

| Symptom | Cause | Fix |
|---|---|---|
| `Goal was rejected by server` / `ABORTED` in RViz | `lite6_traj_controller` is inactive: the arm left servo mode (UFactory Studio jog, error, collision stop, arm e-stop) | Clear errors in Studio, stop jogging there, restart `moveit_real.launch.py` |
| `Failed to parse yaw argument` from `static_transform_publisher` | `attach_xyz`/`attach_rpy` passed to xarm's launch without inner quotes | Use `moveit_real.launch.py`, which quotes them; by hand: `attach_xyz:='"0.025 0 0.408"'` |
| Arm drifts or stops with false collisions | Mount angle in UFactory Studio does not match the real mount | Set it in Studio (0° upright), see [Hardware](hardware.md#adjusting-the-mount) |
