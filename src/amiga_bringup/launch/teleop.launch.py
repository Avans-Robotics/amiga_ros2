"""Drive the Amiga with a PS4 gamepad: joy -> teleop_twist_joy -> /cmd_vel -> micro-ROS -> Portenta."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    agent = LaunchConfiguration('agent')
    return LaunchDescription([
        DeclareLaunchArgument(
            'agent', default_value='true',
            description='Start the micro-ROS agent (false = /cmd_vel only, the Amiga does not move)'),
        Node(package='joy', executable='game_controller_node', name='joy_node'),
        Node(
            package='teleop_twist_joy', executable='teleop_node', name='teleop_twist_joy_node',
            parameters=[PathJoinSubstitution([FindPackageShare('amiga_bringup'), 'config', 'ps4.yaml'])]),
        Node(
            package='micro_ros_agent', executable='micro_ros_agent', name='micro_ros_agent',
            arguments=['serial', '--dev', '/dev/portenta'],
            condition=IfCondition(agent)),
    ])
