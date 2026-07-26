import rclpy
from rclpy.node import Node
from project_orion_interfaces.msg import OrionState

class StateMonitorNode(Node):
    def __init__(self):
        super().__init__('state_monitor_node')

        self.subscription = self.create_subscription(

            OrionState,
            'orion/system_state',
            self.handle_state_update,
            10,
        )

        self.get_logger().info("ORION state Monitor Ststarted, waiting for state update")

    def handle_state_update(self, msg):
        self.get_logger().info(
            f"State update received: {msg.state_label} (code={msg.state})  " 
            f"at stamp = {msg.header.stamp.sec}.{msg.header.stamp.nanosec}"
        )

def main (args = None):
    rclpy.init(args=args)
    node = StateMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__== "__main__":
    main()

