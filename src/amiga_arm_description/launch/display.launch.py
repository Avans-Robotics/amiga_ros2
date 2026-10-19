"""Show the Amiga with the arm platform in RViz.

use_real_arm:=false  joint sliders (joint_state_publisher_gui)
use_real_arm:=true   mirror the real arm from /ufactory/joint_states (start the xArm driver separately)
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('amiga_arm_description')
    use_real_arm = LaunchConfiguration('use_real_arm')
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg, 'urdf', 'amiga_arm.urdf.xacro']),
                 ' config:=', LaunchConfiguration('config')]),
        value_type=str)

    return LaunchDescription([
        DeclareLaunchArgument('use_real_arm', default_value='false'),
        DeclareLaunchArgument('config', default_value=PathJoinSubstitution([pkg, 'config', 'arm_platform.yaml'])),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}]),
        Node(package='joint_state_publisher_gui', executable='joint_state_publisher_gui',
             condition=UnlessCondition(use_real_arm)),
        Node(package='joint_state_publisher', executable='joint_state_publisher',
             parameters=[{'source_list': ['/ufactory/joint_states']}],
             condition=IfCondition(use_real_arm)),
        Node(package='rviz2', executable='rviz2',
             arguments=['-d', PathJoinSubstitution([pkg, 'rviz', 'display.rviz'])]),
    ])
