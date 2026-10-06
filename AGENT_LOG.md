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
Customer network decision, Tailscale login, repo URL in host/README.md once the repo is on GitHub.
