"""MoveIt on the real Lite 6, with the arm pose taken from config/arm_platform.yaml.

xarm's MoveIt model has no platform, so the arm is attached straight to "world"
at the combined pose world -> platform_link -> link_base.
Usage: ros2 launch amiga_description moveit_real.launch.py [robot_ip:=10.95.76.155]
"""
import math

import numpy as np
import yaml
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def rpy_to_matrix(r, p, y):
    # URDF convention: fixed axes X, Y, Z, i.e. R = Rz(y) Ry(p) Rx(r)
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([
        [cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
        [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
        [-sp, cp * sr, cp * cr],
    ])


def matrix_to_rpy(m):
    cos_p = math.hypot(m[0, 0], m[1, 0])
    p = math.atan2(-m[2, 0], cos_p)
    if cos_p > 1e-9:
        return math.atan2(m[2, 1], m[2, 2]), p, math.atan2(m[1, 0], m[0, 0])
    # gimbal lock (pitch = +-90 deg): roll and yaw share an axis, put it all in yaw
    return 0.0, p, math.atan2(-m[0, 1], m[1, 1])


def compose(xyz1, rpy1, xyz2, rpy2):
    """Pose 2 expressed in frame 1, returned in frame 1's parent."""
    r1 = rpy_to_matrix(*rpy1)
    xyz = np.array(xyz1) + r1 @ np.array(xyz2)
    return xyz.tolist(), matrix_to_rpy(r1 @ rpy_to_matrix(*rpy2))


def moveit_rpy(rpy):
    """xarm feeds attach_rpy to the URDF as roll-pitch-yaw, but to static_transform_publisher
    as yaw-pitch-roll. Both agree only when roll == yaw, so otherwise the yaw is dropped.
    """
    # ponytail: MoveIt's world is then turned by the dropped yaw (fine while it has no
    # platform or Amiga); fix: patch xarm's static TF or pass rpy without its launch.
    if math.isclose(rpy[0], rpy[2], abs_tol=1e-6):
        return rpy
    print('moveit_real: dropping yaw {:.4f} from the arm pose (xarm rpy order)'.format(rpy[2]))
    return rpy[0], rpy[1], rpy[0]


def launch_setup(context):
    with open(LaunchConfiguration('config').perform(context)) as f:
        cfg = yaml.safe_load(f)
    xyz, rpy = compose(cfg['platform']['xyz'], cfg['platform']['rpy'], cfg['arm']['xyz'], cfg['arm']['rpy'])
    rpy = moveit_rpy(rpy)
    # xarm's launch strips the outer character of these values, so wrap them in quotes
    fmt = lambda v: '"{}"'.format(' '.join('{:.6f}'.format(x) for x in v))
    return [IncludeLaunchDescription(
        PathJoinSubstitution([FindPackageShare('xarm_moveit_config'), 'launch', 'lite6_moveit_realmove.launch.py']),
        launch_arguments={
            'robot_ip': LaunchConfiguration('robot_ip'),
            'attach_xyz': fmt(xyz),
            'attach_rpy': fmt(rpy),
        }.items())]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_ip', default_value='10.95.76.155'),
        DeclareLaunchArgument('config', default_value=PathJoinSubstitution(
            [FindPackageShare('amiga_description'), 'config', 'arm_platform.yaml'])),
        OpaqueFunction(function=launch_setup),
    ])


if __name__ == '__main__':
    # Self-check of the pose maths: python3 moveit_real.launch.py
    for rpy in [(0, 1.5708, 0), (0.3, -0.7, 2.0), (0, 0, math.pi / 2)]:
        back = matrix_to_rpy(rpy_to_matrix(*rpy))
        assert np.allclose(rpy_to_matrix(*back), rpy_to_matrix(*rpy)), rpy
    xyz, rpy = compose([0, 0, 0.503], [0, 0, 0], [0.025, 0, -0.095], [0, 1.5708, 0])
    assert np.allclose(xyz, [0.025, 0, 0.408]), xyz
    assert np.allclose(rpy_to_matrix(*rpy), rpy_to_matrix(0, 1.5708, 0)), rpy
    xyz, _ = compose([1, 0, 0], [0, 0, math.pi / 2], [1, 0, 0], [0, 0, 0])
    assert np.allclose(xyz, [1, 1, 0]), xyz
    assert np.allclose(moveit_rpy((0, 0, 3.1416)), (0, 0, 0))
    assert np.allclose(moveit_rpy((math.pi, 1.5708, math.pi)), (math.pi, 1.5708, math.pi))
    print('ok')
