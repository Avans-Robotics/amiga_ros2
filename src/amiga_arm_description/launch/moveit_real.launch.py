"""MoveIt on the real Lite 6, with the arm pose taken from config/arm_platform.yaml.

xarm's MoveIt model has no Amiga or platform, so the arm is attached straight to "world"
at the combined pose world -> base_link -> platform_link -> link_base.
Usage: ros2 launch amiga_arm_description moveit_real.launch.py [robot_ip:=10.95.76.155]
"""
import math
import os

import numpy as np
import xacro
import yaml
from ament_index_python.packages import get_package_share_directory
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


def moveit_pose(xyz, rpy):
    """xarm feeds attach_rpy to the URDF as roll-pitch-yaw, but to static_transform_publisher
    as yaw-pitch-roll. Both agree only when roll == yaw, so otherwise the yaw is dropped.
    xyz is then turned along, so MoveIt's world keeps its origin and is only turned by the
    dropped yaw about the vertical.
    """
    # ponytail: MoveIt's world is then turned by the dropped yaw (fine while it has no
    # platform or Amiga); fix: patch xarm's static TF or pass rpy without its launch.
    if math.isclose(rpy[0], rpy[2], abs_tol=1e-3):  # 3.1416 in the yaml is not exactly pi
        return list(xyz), tuple(rpy)
    print('moveit_real: dropping yaw {:.4f} from the arm pose (xarm rpy order)'.format(rpy[2]))
    new_rpy = (rpy[0], rpy[1], rpy[0])
    turn = rpy_to_matrix(*new_rpy) @ rpy_to_matrix(*rpy).T
    return (turn @ np.array(xyz)).tolist(), new_rpy


def amiga_base_link_pose():
    """Pose of the Amiga base_link relative to the floor, from the amiga_description model."""
    path = os.path.join(get_package_share_directory('amiga_description'), 'urdf', 'amiga.urdf.xacro')
    for joint in xacro.process_file(path).getElementsByTagName('joint'):
        if joint.getAttribute('name') == 'base_footprint_joint':
            origin = joint.getElementsByTagName('origin')[0]
            return ([float(v) for v in origin.getAttribute('xyz').split()],
                    [float(v) for v in origin.getAttribute('rpy').split()])
    raise RuntimeError('base_footprint_joint not found in ' + path)


def launch_setup(context):
    with open(LaunchConfiguration('config').perform(context)) as f:
        cfg = yaml.safe_load(f)
    xyz, rpy = compose(*amiga_base_link_pose(), cfg['platform']['xyz'], cfg['platform']['rpy'])
    xyz, rpy = compose(xyz, rpy, cfg['arm']['xyz'], cfg['arm']['rpy'])
    xyz, rpy = moveit_pose(xyz, rpy)
    print('moveit_real: arm base at xyz {} rpy {}'.format(np.round(xyz, 4).tolist(), np.round(rpy, 4).tolist()))
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
            [FindPackageShare('amiga_arm_description'), 'config', 'arm_platform.yaml'])),
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
    assert np.allclose(moveit_pose([1, 2, 3], (math.pi, 1.5708, math.pi))[0], [1, 2, 3])
    # current mount: platform and arm both turned pi, so no yaw to drop
    xyz, rpy = compose([0, 0, 0.216], [0, 0, 0], [-0.414, 0, 0.435], [0, 0, math.pi])
    xyz, rpy = compose(xyz, rpy, [-0.07, 0, 0.025], [0, 0, math.pi])
    assert np.allclose(xyz, [-0.344, 0, 0.676]), xyz
    assert np.allclose(moveit_pose(xyz, rpy)[0], xyz)
    assert np.allclose(rpy_to_matrix(*moveit_pose(xyz, rpy)[1]), np.eye(3))
    # platform not turned: yaw pi dropped, xyz turned with it, so the world origin stays put
    xyz, rpy = compose([0, 0, 0.216], [0, 0, 0], [-0.374, 0, 0.435], [0, 0, 0])
    xyz, rpy = compose(xyz, rpy, [-0.07, 0, 0.025], [0, 0, math.pi])
    assert np.allclose(xyz, [-0.444, 0, 0.676]), xyz
    m_xyz, m_rpy = moveit_pose(xyz, rpy)
    assert np.allclose(m_rpy, (0, 0, 0)) and np.allclose(m_xyz, [0.444, 0, 0.676]), (m_xyz, m_rpy)
    # MoveIt's world, seen from the real floor frame: only turned, origin unchanged
    turn = rpy_to_matrix(*rpy) @ rpy_to_matrix(*m_rpy).T
    assert np.allclose(np.array(xyz) - turn @ np.array(m_xyz), 0)
    print('ok')
