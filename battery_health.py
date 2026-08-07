#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float32, Int16
from create_msgs.msg import ChargingState, Mode

class RoombaFaultMonitor(Node):
    def __init__(self):
        super().__init__('roomba_fault_monitor')

        # Internal State Tracking
        self.current_mode = -1
        self.voltage = 0.0
        self.current_amps = 0.0

        # Subscriptions to all create_robot battery and mode channels
        self.create_subscription(ChargingState, '/battery/charging_state', self.charging_state_callback, 10)
        self.create_subscription(Mode, '/mode', self.mode_callback, 10)
        self.create_subscription(Float32, '/battery/voltage', self.voltage_callback, 10)
        self.create_subscription(Float32, '/battery/current', self.current_callback, 10)
        self.create_subscription(Int16, '/battery/temperature', self.temperature_callback, 10)
        self.create_subscription(Float32, '/battery/charge_ratio', self.ratio_callback, 10)

        self.get_logger().info("🚀 Roomba Battery Fault Analyzer Engine Started.")

    def mode_callback(self, msg: Mode):
        self.current_mode = msg.mode

    def voltage_callback(self, msg: Float32):
        self.voltage = msg.data
        # Critical Fault: Cell Collapse Detection
        if self.voltage < 10.0 and self.voltage > 0.1:
            self.get_logger().error(
                f"🚨 CRITICAL FAULT: Battery Cell Collapse Detected! Voltage dropped to {self.voltage:.2f}V. "
                "Pack cannot sustain mainboard logic off-dock."
            )
        elif self.voltage == 0.0:
            self.get_logger().error(
                "🚨 HARDWARE FAULT: Battery reporting exactly 0.0V. "
                "Check for blown internal F1 motherboard fuse or unseated battery tabs."
            )

    def current_callback(self, msg: Float32):
        self.current_amps = msg.data

    def temperature_callback(self, msg: Int16):
        temp_celsius = msg.data
        # Thermal Limits monitoring
        if temp_celsius > 45:
            self.get_logger().error(f"🔥 THERMAL OVERHEAT: Battery temperature is critically high ({temp_celsius}°C)!")
        elif temp_celsius < 0:
            self.get_logger().error(f"❄️ THERMAL UNDERCOOL: Battery is below freezing limits ({temp_celsius}°C)!")
        elif temp_celsius > 38:
            self.get_logger().warning(f"⚠️ THERMAL WARNING: Battery temperature elevated ({temp_celsius}°C). Near throttle limit.")

    def ratio_callback(self, msg: Float32):
        ratio = msg.data * 100.0
        if ratio < 20.0 and self.current_amps <= 0:
            self.get_logger().warning(f"🔋 LOW BATTERY: Roomba is at {ratio:.1f}%. Seek Home Base immediately.")

    def charging_state_callback(self, msg: ChargingState):
        state = msg.state

        # Evaluation Matrix based on Roomba OI State Machine
        if state == ChargingState.CHARGE_FAULT:
            self.get_logger().error("🚨 HARDWARE CRASH: Charging circuit reported CHARGE_FAULT (State 5). Current cut for safety!")
            
        elif state == ChargingState.CHARGE_WAITING:
            self.get_logger().warning(
                f"🛑 CHARGING LOCKOUT: State is CHARGE_WAITING (State 4). Voltage: {self.voltage:.2f}V. "
                "Base power is cut. Verify your robot isn't simultaneously connected to a side barrel jack "
                "and a floor dock, or wait for surface charge to bleed."
            )
            
        elif state == ChargingState.CHARGE_RECONDITION:
            self.get_logger().warning("ℹ️ RECOVERY MODE: Battery is deeply depleted. Running low-current CHARGE_RECONDITION loop.")

        elif state == ChargingState.CHARGE_NONE:
            # Check for Mode Lock conflict paradox
            if self.current_amps < 0 and (self.current_mode == 2 or self.current_mode == 3) and self.voltage > 14.0:
                # The robot is drawing power but sitting on the dock without charging because it's in Safe/Full mode
                # We deduce this if current is negative despite being close to nominal docking positions
                pass

def main(args=None):
    rclpy.init(args=args)
    node = RoombaFaultMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()