import os 

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription,DeclareLaunchArgument
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration

import xacro

def generate_launch_description():
    sim_pkg_share = get_package_share_directory('project_orion_simulation')
    ros_gz_sim_share = get_package_share_directory('ros_gz_sim')
    description_pkg_share = get_package_share_directory('project_orion_description')
    xacro_file = os.path.join(sim_pkg_share,'urdf' , 'orion_vehicle.gazebo.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_description= {'robot_description': robot_description_config.toxml()}
    world_file = os.path.join(sim_pkg_share, 'worlds', 'orion_world.world')
    bridge_config_file = os.path.join(sim_pkg_share, 'config' , 'orion_gz_bridge.yaml')
    rviz_config_file = os.path.join(description_pkg_share,'rviz' , 'orion_description.rviz')

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_share , 'launch' ,'gz_sim.launch.py')

        ),
        launch_arguments={
            'gz_args':world_file}.items(),
    )
    use_rviz_arg = DeclareLaunchArgument(
        'use_rviz',
        default_value='true',
        description='start Rviz2 alongside Gazebo. '
    )

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[robot_description,{'use_sim_time':True}],
    )
    spawn_entity= Node(
        package='ros_gz_sim',
        executable='create',
        name='orion_spawn_entity',
        output='screen',
        arguments=[
            '-topic','robot_description',
            '-name', 'orion_vehicle',
            '-z', '0.15',
        ],
    )

    ros_gz_bridge = Node(

        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='origin_gz_bridge',
        output='screen',
        parameters= [
            {
                'config_file': bridge_config_file,
                'use_sim_time': True,

            }
        ]
    )

    joint_state_publisher = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen',
        parameters=[{'use_sim_time': True}],
    )

    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        arguments=['-d',rviz_config_file],
        parameters=[{'use_sim_time':True}],
        condition=IfCondition(LaunchConfiguration('use_rviz')),
    )

    return LaunchDescription([
        gazebo,
        use_rviz_arg,
        robot_state_publisher,
        spawn_entity,
        joint_state_publisher,
        ros_gz_bridge,
        rviz,
    ])