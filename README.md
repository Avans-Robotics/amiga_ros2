# amiga_ros2

ROS 2 Jazzy software for a farm-ng Amiga with an optional UFactory Lite 6 arm and an optional Luxonis OAK-D camera. Everything runs in a Docker container on the onboard NVIDIA Jetson Orin.

![The Amiga with the Lite 6 arm](docs/images/overview-arm-side.jpg)

The arm and the camera are optional: without them, everything except [Arm with MoveIt](docs/arm-moveit.md) and [Camera](docs/camera.md) still applies.

## Quick start

Safety first: someone at the Amiga e-stop (red button above the pendant) whenever the robot can move.

1. **Charge**: connect the quick charger to the orange connector and plug it into mains. See [Power and charging](docs/power.md).
2. **Power on**: press the e-stop, turn both battery keys to ON, tap START on the pendant, release the e-stop. The Orin, arm controller, switch and router start by themselves.
3. **Connect**: join the WiFi `Agrorobotics Fieldlab` and log in to the Orin: `ssh hcr@10.95.76.50`, or RDP to `10.95.76.50`. See [Network and remote access](docs/network.md).
4. **Drive**: set the pendant to AUTO ACTIVE, then start gamepad teleop in the container. See [Driving](docs/driving.md).
5. **Power off**: `sudo shutdown now` on the Orin, wait until it is off, then turn both keys to OFF.

## Documentation

| Topic | What is in it |
|---|---|
| [Hardware](docs/hardware.md) | Parts, photos, where everything sits, the arm platform |
| [Power and charging](docs/power.md) | Power on/off, e-stops, batteries, chargers |
| [Network and remote access](docs/network.md) | IP addresses, WiFi, SSH, RDP, Tailscale |
| [Driving](docs/driving.md) | Gamepad teleop and the pendant |
| [Arm with MoveIt](docs/arm-moveit.md) | Moving the Lite 6 from RViz |
| [Camera](docs/camera.md) | OAK-D images in ROS |
| [Docker](docs/docker.md) | The container: entering it, updating, rebuilding |
| [Installation](docs/install.md) | Setting up the Orin from scratch |
| [Troubleshooting](docs/troubleshooting.md) | Common problems and fixes |
| [Simulation](docs/simulation.md) | Drive the Amiga and move the arm in Gazebo on a laptop |

For developers:

| Topic | What is in it |
|---|---|
| [Status and open items](docs/status.md) | What is verified, what is still to do |
