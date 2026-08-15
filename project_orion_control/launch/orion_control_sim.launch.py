import os
import subprocess
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable
from launch.actions import TimerAction
import xacro


def generate_launch_description():
    sim_pkg_share = get_package_share_directory('project_orion_simulation')
    control_pkg_share = get_package_share_directory('project_orion_control')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')

    xacro_file = os.path.join(sim_pkg_share, 'urdf', 'orion_vehicle.gazebo.xacro')
    robot_description_config = xacro.process_file(
        xacro_file, mappings={'use_mock': 'false'}
    )

    urdf_path = '/tmp/orion_robot_sim.urdf'
    with open(urdf_path, 'w') as f:
        f.write(robot_description_config.toprettyxml(indent='  '))

    sdf_path = '/tmp/orion_robot_sim.sdf'
    with open(sdf_path, 'w') as f:
        subprocess.run(
            ['gz', 'sdf', '-p', urdf_path],
            stdout=f,
            check=True,
        )

    robot_description = {'robot_description': robot_description_config.toxml()}

    world_file = os.path.join(sim_pkg_share, 'worlds', 'orion_world.world')
    bridge_config_file = os.path.join(sim_pkg_share, 'config', 'orion_gz_bridge.yaml')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': f'-r -v 4 {world_file}'}.items(),
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}],
    )

    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        name='orion_spawn_entity',
        output='screen',
        arguments=[
            '-file', sdf_path,
            '-name', 'orion_vehicle',
            '-z', '0.15',
        ],
    )

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='orion_gz_bridge',
        output='screen',
        parameters=[{'config_file': bridge_config_file, 'use_sim_time': True}],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='joint_state_broadcaster_spawner',
        output='screen',
        arguments=['joint_state_broadcaster'],
    )

    wheel_velocity_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='wheel_velocity_controller_spawner',
        output='screen',
        arguments=['wheel_velocity_controller'],
    )

    steering_position_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='steering_position_controller_spawner',
        output='screen',
        arguments=['steering_position_controller'],
    )

    set_gz_plugin_path = SetEnvironmentVariable(
        name='GZ_SIM_SYSTEM_PLUGIN_PATH',
        value='/opt/ros/jazzy/lib'
    )

    joint_state_broadcaster_spawner_delayed = TimerAction(
        period=10.0,
        actions=[joint_state_broadcaster_spawner],
    )

    wheel_velocity_controller_spawner_delayed = TimerAction(
        period=12.0,
        actions=[wheel_velocity_controller_spawner],
    )

    steering_position_controller_spawner_delayed = TimerAction(
        period=14.0,
        actions=[steering_position_controller_spawner],
    )

    return LaunchDescription([
        set_gz_plugin_path,
        gazebo,
        robot_state_publisher,
        spawn_entity,
        ros_gz_bridge,
        joint_state_broadcaster_spawner_delayed,
        wheel_velocity_controller_spawner_delayed,
        steering_position_controller_spawner_delayed,
    ])