import os 

from ament_index_python.packages import get_package_share_directory 
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro


def generate_launch_description():
    description_pkg_share = get_package_share_directory('project_orion_description')
    control_pkg_share = get_package_share_directory('project_orion_control')

    xacro_file = os.path.join(description_pkg_share , 'urdf' ,'orion_vehicle.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)
    robot_description = {'robot_description':robot_description_config.toxml()}

    controllers_yaml = os.path.join(control_pkg_share, 'config' , 'orion_controllers.yaml')

    robot_state_publisher = Node(
        package= 'robot_state_publisher',
        executable= 'robot_state_publisher',
        name= 'robot_state_publisher',
        output= 'screen',
        parameters= [robot_description]
    )

    controller_manager = Node(
        package= 'controller_manager',
        executable= 'ros2_control_node',
        name= 'controller_manager',
        output= 'screen',
        parameters= [robot_description, controllers_yaml]
    )


    joint_state_broadcaster_spawner = Node(
        package= 'controller_manager',
        executable= 'spawner',
        name= 'joint_state_broadcaster_spawner',
        output ='screen',
        arguments= ['joint_state_broadcaster']
    )


    wheel_velocity_controller_spawner=  Node(
        package= 'controller_manager',
        executable= 'spawner',
        name= 'wheel_velocity_controller_spawner',
        output= 'screen',
        arguments= ['wheel_velocity_controller'],
    )

    steering_position_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        name='steering_position_controller_spawner',
        output= 'screen',
        arguments= ['steering_position_controller'],
    )
    
    return LaunchDescription(
        [
            robot_state_publisher,
            controller_manager,
            joint_state_broadcaster_spawner,
            wheel_velocity_controller_spawner,
            steering_position_controller_spawner,
        ]
    )
