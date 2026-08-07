import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32
import time

class TestNode(Node):
    def __init__(self):
        super().__init__("test_node")
        self.battery_charge_ratio = 0.75

        self.last_time = time.time()
        ros_subscriber = self.create_subscription(Float32, "/battery/charge_ratio", self.callback, 10)

    def callback(self, msg):
        if msg.data != self.battery_charge_ratio:

            # percentage difference from the previous message to the current message
            percentage = (msg.data - self.battery_charge_ratio) / msg.data * 100 if msg.data != 0 else 0
            self.battery_charge_ratio = msg.data
            # adding a timer from the time of the previous message to the time of the current message
            now = time.time()
            duration = now - self.last_time
            self.last_time = now
            print(f"Received message: {self.battery_charge_ratio * 100:2f}% (Duration: {duration:.2f}s) (Percentage Change: {percentage:.2f}%) (Time: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))} )")

def main(args=None):
    rclpy.init(args=args)
    node = TestNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":    main()