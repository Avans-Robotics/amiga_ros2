# Network and remote access

All Ethernet devices connect to the PoE switch on the robot and have a static IP. The GL.iNet router on the robot provides WiFi; it currently ships with the robot.

![PoE switch](images/network-poe-switch.jpg)

## IP addresses

| IP | Device |
|----|--------|
| 10.95.76.11 | OAK-D camera |
| 10.95.76.50 | Orin (user `hcr`) |
| 10.95.76.155 | Lite 6 controller |
| 10.95.76.254 | GL.iNet router (gateway and DNS for the Orin) |

## Connecting a laptop

- **WiFi**: join `Agrorobotics Fieldlab`. Ask the robot owner for the password.
- **Cable**: plug into a free port on the switch and set a manual IP on your laptop, for example `10.95.76.100`, netmask `255.255.255.0`.

## Logging in to the Orin

- **SSH**: `ssh hcr@10.95.76.50`. Ask the robot owner for the password, or add your SSH key.
- **RDP** (desktop, needed for RViz): connect to `10.95.76.50` with an RDP client, for example Remmina on Linux or Remote Desktop Connection on Windows.
- **Tailscale**: installed on the Orin and logged in to the avans.nl tailnet. Only works when the router has internet access.

Without internet on the router (no uplink), the robot network works locally, but Tailscale and `git pull` on the Orin do not.

Setting the Orin's static IP and enabling RDP: see [Installation](install.md).
