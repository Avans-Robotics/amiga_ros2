## 2026-10-06 Repo bootstrap: docker files and docs
### Goal & outcome
Bring the Docker setup that runs on the Orin into the new amiga_ros2 repo and record the robot context (hardware, IPs, gotchas, open items) in README.md and CLAUDE.md. Done.
### Decisions & why
- Docker files copied from the Orin (`~/amiga_ros`, md5 verified identical) with comments translated to English only, so the repo matches what runs on the robot. Functional changes (DISPLAY=:1, dropping the AMIGA_REPO build arg) are a separate step.
- New repo instead of forking Amiga_ws: Amiga_ws has credentials in its history.
- All repo content in English.
### Lessons / gotchas
- Laptop reaches the Orin only when on the robot network; key-based SSH as hcr works, hcr is in the docker group.
- Arm unit (arm, Orin, camera, switch on a plank, not the drive base) ships to the customer Thursday 2026-10-08. Network, Tailscale and Orin backup must be solved before that or remote access is lost.
### State
Branch feat/docker-and-docs. Validated: code lines of docker files identical to Orin originals (diff with comments stripped), `docker compose config` passes, secret grep clean. Not rebuilt on the Orin (no build change). Uncommitted.
### Open items
Customer network decision (second GL.iNet), Tailscale, Orin disk image backup, URDF with configurable arm/camera poses, teleop + micro-ROS agent, MoveIt.

## 2026-10-06 Orin restore path: host setup docs
### Goal & outcome
Backup for the Orin before it ships Thursday. Instead of a disk image: documented the stock Seeed base image plus every change made on top in host/README.md. Done.
### Decisions & why
- Docs-based restore over a disk image: a full image (NVMe removal, NVIDIA backup tools or live dd) took too long for the deadline, the base is a stock Seeed image, and the host changes are few. Any restore needs physical access anyway. Full image stays optional.
- Kept the work on feat/docker-and-docs: same theme, one PR.
### Lessons / gotchas
- Seeed BSP r39.2.0 pins the NVIDIA stack in /etc/apt/preferences.d/99-seeed-freeze-jp.pref; upgrading nvidia-l4t-bootloader fails on reComputer boards.
- RDP is GNOME Remote Desktop in system mode (port 3389), not xrdp; user-mode grd is disabled. gdm has WaylandEnable=false from the image.
- Tailscale is installed but logged out.
- Shell history on the Orin contained the sudo password; user cleared it, chose not to change the password.
### State
Branch feat/docker-and-docs. Static IP, pin file, ports and installed packages checked against the live Orin over SSH. Restore procedure itself not executed (UNVERIFIED as a full run). RDP credential setup not readable without sudo, documented as a manual step. Uncommitted.
### Open items
Customer network decision, Tailscale login, GitHub access for the Orin if the repo is private (deploy key or token).

## 2026-10-06 Arm platform URDF in Gazebo and RViz
### Goal & outcome
URDF for what ships Thursday: two planks + Lite 6, viewable in Gazebo and RViz on the laptop. Done: package amiga_description with a YAML-driven xacro, display and gazebo launch files, laptop sim compose override.
### Decisions & why
- Arm pose and plank geometry in one YAML (config/arm_platform.yaml), read directly by xacro (xacro.load_yaml), so no launch plumbing per value.
- platform_link origin on the top front edge of the Amiga back rail: the point you measure from on the real robot, so the macro attaches to the Amiga base_link later unchanged.
- Arm added through xarm's own xarm_device macro (attach_to=platform_link) instead of copying xarm URDFs; gazebo ros2_control params come from xarm_controller automatically.
- Simulation on the laptop (NVIDIA GPU) instead of the Orin (no GPU runtime in its container). Sim uses ROS_DOMAIN_ID=1 to avoid clashing with the robot.
- Platform height 0.503 m taken from the colleague's Amiga URDF (box chassis). farm-ng publishes no URDF/CAD; community models (CMU, OSU) have no license and a different frame config, so the Amiga model will be corrected from our own measurements later.
- OAK-D left out: it is not on the platform.
### Lessons / gotchas
- Arm rpy (0, pi/2, 0) assumes the Lite 6 cable ports are on link_base -X. Zero pose in sim extends to +X as intended; still to compare against the real arm.
- Colleague's Amiga URDF puts the wheels below the floor (joint z = wheel_radius - 0.50) and has no rail profile.
- pkill -f with a pattern that also matches the calling bash -c string kills the caller.
- Laptop image build: ~6 GB, xarm_ros2 resolved to the same commit as the Orin (3dc2b5e), but it is not pinned.
### State
Branch feat/arm-description. Validated on the laptop: URDF parses (check_urdf), Gazebo spawns the model at real-time speed with joint_state_broadcaster and lite6_traj_controller active, a test trajectory SUCCEEDED, TF shows the end effector in front of the planks, RViz display launch runs without mesh errors. Not yet visually confirmed by the user; not tested on the Orin with the real arm. Uncommitted.
### Open items
Visual check of RViz/Gazebo by the user; compare arm orientation with the real arm; MoveIt realmove on the Orin; pin xarm_ros2 commit; correct the Amiga URDF from measurements.
