from launch import LaunchDescription 
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='project_orion',
            executable='state_manager_node',
            name='state_manager_node',
            output="screen"
        ),
        Node(
            package='project_orion',
            executable='state_monitor_node',
            name='state_monitor_node',
            output='screen'
        ),
    ])