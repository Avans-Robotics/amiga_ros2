"""Spawn the arm platform in Gazebo (gz sim) with the Lite 6 trajectory controller."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('amiga_description')
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg, 'urdf', 'arm_platform_standalone.urdf.xacro']),
                 ' config:=', LaunchConfiguration('config'),
                 ' ros2_control_plugin:=gz_ros2_control/GazeboSimSystem']),
        value_type=str)
    sim_time = {'use_sim_time': True}

    spawn = Node(package='ros_gz_sim', executable='create',
                 arguments=['-topic', 'robot_description', '-name', 'arm_platform'])
    controllers = [
        Node(package='controller_manager', executable='spawner', arguments=[name], parameters=[sim_time])
        for name in ('joint_state_broadcaster', 'lite6_traj_controller')
    ]

    return LaunchDescription([
        DeclareLaunchArgument('config', default_value=PathJoinSubstitution([pkg, 'config', 'arm_platform.yaml'])),
        DeclareLaunchArgument('rviz', default_value='false'),
        IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
            launch_arguments={'gz_args': '-r empty.sdf'}.items()),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}, sim_time]),
        Node(package='ros_gz_bridge', executable='parameter_bridge',
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock']),
        spawn,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=controllers)),
        Node(package='rviz2', executable='rviz2', parameters=[sim_time],
             arguments=['-d', PathJoinSubstitution([pkg, 'rviz', 'display.rviz'])],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
