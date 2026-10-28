"""Spawn the Amiga with the arm platform in Gazebo (gz sim): drive it with /cmd_vel, move the arm
with its trajectory controller (lite6_traj_controller, or xarm6_traj_controller with robot:=xarm6).

publish_odom_tf:=false  do not publish odom -> base_footprint (when an EKF publishes it instead)
rviz:=true              also start RViz (fixed frame odom)
gz_args:='-s -r empty.sdf'  Gazebo without its window (server only)
x:=, y:=, yaw:=         spawn pose in the world (pixelfield: wheels in the Path Gaps or on the Border, not on Plants)
robot:=xarm6            an xArm 6 instead of the Lite 6 (simulation option)
sideways:=true          arm mounted sideways (arm_sideways, xarm6_sideways in the config), reaches the soil
gripper:=true           adds the arm's gripper and its gripper_controller
"""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, RegisterEventHandler
from launch.conditions import IfCondition
from launch.event_handlers import OnProcessExit
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    pkg = FindPackageShare('amiga_arm_description')
    robot_description = ParameterValue(
        Command(['xacro ', PathJoinSubstitution([pkg, 'urdf', 'amiga_arm.urdf.xacro']),
                 ' config:=', LaunchConfiguration('config'),
                 ' fixed:=false gazebo:=true',
                 ' robot:=', LaunchConfiguration('robot'),
                 ' sideways:=', LaunchConfiguration('sideways'),
                 ' gripper:=', LaunchConfiguration('gripper'),
                 ' ros2_control_plugin:=gz_ros2_control/GazeboSimSystem']),
        value_type=str)
    sim_time = {'use_sim_time': True}

    spawn = Node(package='ros_gz_sim', executable='create',
                 arguments=['-topic', 'robot_description', '-name', 'amiga_arm', '-z', '0.05',
                            '-x', LaunchConfiguration('x'), '-y', LaunchConfiguration('y'),
                            '-Y', LaunchConfiguration('yaw')])
    # A pixelfield world can run slowly while it loads: the default 5 s switch timeout then fails.
    timeout = ['--switch-timeout', '30']
    controllers = [
        Node(package='controller_manager', executable='spawner', arguments=[name] + timeout,
             parameters=[sim_time])
        for name in ('joint_state_broadcaster', [LaunchConfiguration('robot'), '_traj_controller'])
    ] + [Node(package='controller_manager', executable='spawner',
              arguments=['gripper_controller'] + timeout,
              parameters=[sim_time], condition=IfCondition(LaunchConfiguration('gripper')))]

    return LaunchDescription([
        DeclareLaunchArgument('config', default_value=PathJoinSubstitution([pkg, 'config', 'arm_platform.yaml'])),
        DeclareLaunchArgument('publish_odom_tf', default_value='true'),
        DeclareLaunchArgument('rviz', default_value='false'),
        DeclareLaunchArgument('gz_args', default_value='-r empty.sdf'),
        DeclareLaunchArgument('x', default_value='0.0'),
        DeclareLaunchArgument('y', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        DeclareLaunchArgument('robot', default_value='lite6', choices=['lite6', 'xarm6']),
        DeclareLaunchArgument('sideways', default_value='false'),
        DeclareLaunchArgument('gripper', default_value='false'),
        IncludeLaunchDescription(
            PathJoinSubstitution([FindPackageShare('ros_gz_sim'), 'launch', 'gz_sim.launch.py']),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args')}.items()),
        Node(package='robot_state_publisher', executable='robot_state_publisher',
             parameters=[{'robot_description': robot_description}, sim_time]),
        # Topics of amiga_description's Gazebo drive, see its README
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='amiga_bridge',
             parameters=[sim_time],
             arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
                        '/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                        '/wheel/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                        '/wheel_joint_states@sensor_msgs/msg/JointState[gz.msgs.Model'],
             remappings=[('/wheel_joint_states', '/joint_states')]),
        Node(package='ros_gz_bridge', executable='parameter_bridge', name='amiga_tf_bridge',
             parameters=[sim_time],
             arguments=['/tf@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V'],
             condition=IfCondition(LaunchConfiguration('publish_odom_tf'))),
        spawn,
        RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=controllers)),
        Node(package='rviz2', executable='rviz2', parameters=[sim_time],
             arguments=['-d', PathJoinSubstitution([pkg, 'rviz', 'display.rviz']), '-f', 'odom'],
             condition=IfCondition(LaunchConfiguration('rviz'))),
    ])
