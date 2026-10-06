# Orin host setup

How to rebuild the Orin from scratch. Restore = flash the stock Seeed image, then follow the steps below.

## Base image

| | |
|---|---|
| Board | Seeed reComputer Robotics J401 (`recomputer-orin-robotics-j401-gmsl`) |
| Module | Jetson Orin NX (3767-0000) |
| BSP | Seeed r39.2.0: L4T 39.2.0, JetPack 7.2-b187, Ubuntu 24.04 |
| Boot storage | NVMe (`nvme0n1`) |

Flash with Seeed's guide: <https://wiki.seeedstudio.com/recomputer_robotics_j401_getting_started/> (force recovery mode, USB-C to an Ubuntu host PC). Seeed also documents a full backup/restore: <https://wiki.seeedstudio.com/create_backup_and_restore_on_recomputer/>.

**Do not upgrade the NVIDIA stack.** The image pins it in `/etc/apt/preferences.d/99-seeed-freeze-jp.pref`; upgrading `nvidia-l4t-bootloader` fails on reComputer boards. Leave that file in place.

The image ships with `WaylandEnable=false` in `/etc/gdm3/custom.conf` (X11 desktop) and the NVIDIA container toolkit installed.

## Setup steps

User `hcr`, run on the Orin.

### 1. Static IP

The robot network is on `enP8p1s0` ("Wired connection 2"). See the main README for all IPs.

```bash
sudo nmcli con mod "Wired connection 2" \
  ipv4.method manual \
  ipv4.addresses 10.95.76.50/24 \
  ipv4.gateway 10.95.76.254 \
  ipv4.dns 10.95.76.254
sudo nmcli con up "Wired connection 2"
```

Gateway and DNS point at the lab GL.iNet router; adjust once the customer network is decided.

### 2. Docker

Install Docker CE and the compose plugin from Docker's apt repository: <https://docs.docker.com/engine/install/ubuntu/>. Then:

```bash
sudo usermod -aG docker hcr    # log out and back in
```

### 3. Remote access

- SSH: enabled in the image.
- RDP: GNOME Remote Desktop in system mode (remote login), port 3389. Enable it and set the RDP credentials in Settings > System > Remote Desktop > Remote Login.
- Tailscale:

  ```bash
  curl -fsSL https://tailscale.com/install.sh | sh
  sudo tailscale up
  ```

### 4. ROS container

```bash
git clone https://github.com/Avans-Robotics/amiga_ros2.git ~/amiga_ros2
cd ~/amiga_ros2/docker
docker compose up -d --build    # long first build on the Orin
```

The container restarts on boot. For GUI tools (RViz) from an RDP session:

```bash
xhost +local:
docker exec -it -e DISPLAY=:1 amiga-ros bash
```

### 5. Portenta (Amiga base)

udev rule for a stable `/dev/portenta`, used by the micro-ROS agent:

```bash
sudo cp ~/amiga_ros2/host/99-portenta.rules /etc/udev/rules.d/
sudo udevadm control --reload && sudo udevadm trigger
ls -l /dev/portenta    # -> ttyACM0
```

### 6. PS4 controller (Bluetooth)

The Orin has no Bluetooth on board: plug in a USB Bluetooth dongle (the kernel has `btusb`). The kernel has no `hid_sony` driver; the generic HID driver is enough for sticks and buttons (no rumble, no light bar).

Pair once:

```bash
bluetoothctl
  power on
  agent on
  default-agent
  scan on
  # hold Share + PS until the light bar flashes fast, wait for "Wireless Controller" and its MAC
  pair <MAC>
  trust <MAC>      # reconnects on a PS button press from now on
  connect <MAC>
  scan off
  quit
ls /dev/input/js*  # the controller shows up here
```

The container sees the controller through the `/dev` mount; no restart needed after connecting.

## Lab-only tools

Installed on the current Orin for bench testing, not needed to run the robot:

- Google Chrome (arm64 `.deb` from google.com)
- UFactory Studio (Linux AppImage from ufactory.cc), used to set the 90° arm mount
- Luxonis `oak-viewer` (`.deb` from luxonis.com)
