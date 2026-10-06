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
