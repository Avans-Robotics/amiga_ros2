# Camera

The Luxonis OAK-D-W-PoE is mounted on the crossbar and connected to the PoE switch (IP `10.95.76.11`).

![OAK-D camera](images/camera-oakd.jpg)

## Starting

In the [container](docker.md#entering-the-container):

```bash
ros2 launch depthai_ros_driver camera.launch.py
```

Images are published under `/oak/...`. List them with `ros2 topic list | grep oak`.

## Viewing in RViz

Over RDP, in a second container terminal: `rviz2`. Then **Add**, tab **By topic**, pick the Image under `/oak/rgb/...`.

`Stereo alignment error ... trying to recover` in the log is a depth warning; the colour image is not affected.

## Details

The OAK-D is not in the robot model (URDF) yet, so its own launch file runs it, including its own TF frames. Once the camera is added to the URDF, do not start `camera.launch.py` anymore: it runs its own robot_state_publisher and duplicates the TF frames.
