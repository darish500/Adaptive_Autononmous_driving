import rclpy
from rclpy.node import Node

from project_orion_interfaces.msg import OrionState
from project_orion_interfaces.srv import RequestStateTransition

from project_orion.orion_state_machine import OrionStateMachine, STATE_NAMES

class StateManagerNode(Node):
    def __init__(self):
        super().__init__('state_manager_node')

        self.state_machine = OrionStateMachine()

        self.state_publisher = self.create_publisher(
            OrionState, 'orion/system_state', 10
        )

        self.transition_service = self.create_service(

        RequestStateTransition,
        'orion/request_state_transition',
        self.handle_transition_request,

        )

        self.get_logger().info(
            f"ORION State Mananger started. Initial state: "
            f"{STATE_NAMES[self.state_machine.current_state]}"

        )
        self.publish_current_state()

    def publish_current_state(self):
        msg = OrionState()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.state = self.state_machine.current_state
        msg.state_label = STATE_NAMES[self.state_machine.current_state]
        self.state_publisher.publish(msg)

    def handle_transition_request(self,request,response):
        accepted, reason = self.state_machine.transition(request.requested_state)

        response.accepted = accepted 
        response.reason = reason 
        response.current_state = self.state_machine.current_state

        if accepted:
            self.get_logger().info(reason)
            self.publish_current_state()

        else:
            self.get_logger().warn(reason)

        return response

def main (args = None):
    rclpy.init(args=args)
    node = StateManagerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()