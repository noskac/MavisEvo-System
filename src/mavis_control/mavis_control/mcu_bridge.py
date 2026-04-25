#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import serial
import serial.tools.list_ports
from pynput import keyboard

class McuBridgeNode(Node):
    def __init__(self):
        super().__init__('mcu_bridge_node')

        # --- KONFIGURASI SERIAL OTOMATIS ---
        self.baudrate = 115200
        self.serial_port = self.auto_detect_port()

        if self.serial_port:
            try:
                self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=0.05)
                self.get_logger().info(f"✅ Serial OTOMATIS Terhubung ke: {self.serial_port}")
            except Exception as e:
                self.get_logger().warning(f"⚠️ Gagal buka port {self.serial_port} (Mungkin sedang dipakai GUI?): {e}")
                self.ser = None
        else:
            self.get_logger().error("❌ Tidak ada MCU (ESP32/Teensy) yang terdeteksi di USB!")
            self.ser = None

        # Variabel State
        self.current_mode = 0  # 0: Disabled, 1: Manual, 2: Auto
        self.target_val = [0, 0, 0, 0] 
        self.current_val = [0, 0, 0, 0] 
        self.MAX_SPEED = 300 

        # --- SUBSCRIBER DARI AI (YOLO) ---
        # (SEKARANG POSISINYA BENAR, DI DALAM __init__)
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel_auto',
            self.yolo_callback,
            10)

        # --- TIMER PENGIRIMAN DATA (Pengganti rate.sleep di ROS 1) ---
        # 90 Hz = sekitar 0.011 detik
        self.timer = self.create_timer(0.011, self.send_loop)

        # --- KEYBOARD LISTENER (Jalan di background) ---
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        self.print_menu()

    def auto_detect_port(self):
        """Fungsi untuk melacak port ESP32 atau Teensy secara otomatis di Linux"""
        self.get_logger().info("Mencari MCU yang terhubung...")
        ports = serial.tools.list_ports.comports()

        for port in ports:
            # Di Linux, ESP32 biasanya ttyUSB, Teensy biasanya ttyACM
            if 'USB' in port.device or 'ACM' in port.device:
                self.get_logger().info(f"🔎 Kandidat hardware ditemukan: {port.device} ({port.description})")
                return port.device
                
        return None

    def print_menu(self):
        print("\n=======================================")
        print("🚀 SISTEM JEMBATAN KENDALI AKTIF!")
        print("Tekan '1' (Manual), '2' (Disable), atau '3' (Auto AI).")
        print("Kendali Manual: Maju/Mundur(W/S), Putar(A/D), Naik/Turun(H/B), Guling(Q/E)")
        print("=======================================\n")

    def yolo_callback(self, msg):
        # AI hanya boleh menyetir jika Mode 3 (Auto) aktif
        if self.current_mode == 2:
            self.target_val[0] = int(msg.linear.x)
            self.target_val[3] = int(msg.angular.z)

    def on_press(self, key):
        try:
            if key.char == '1':
                self.current_mode = 1
                print("\n>>> MODE: MANUAL (ACTIVE) <<<")
            elif key.char == '2':
                self.current_mode = 0
                print("\n>>> MODE: DISABLED (IDLE) <<<")
                self.target_val = [0, 0, 0, 0]
            elif key.char == '3':
                self.current_mode = 2
                print("\n>>> MODE: AUTO (AI VISION) <<<")
                self.target_val = [0, 0, 0, 0]

            # Kontrol Gerak Keyboard
            if self.current_mode == 1:
                if key.char == 'w': self.target_val[0] = self.MAX_SPEED
                elif key.char == 's': self.target_val[0] = -self.MAX_SPEED
                elif key.char == 'a': self.target_val[3] = -self.MAX_SPEED
                elif key.char == 'd': self.target_val[3] = self.MAX_SPEED
                elif key.char == 'h': self.target_val[2] = self.MAX_SPEED
                elif key.char == 'b': self.target_val[2] = -self.MAX_SPEED
                elif key.char == 'q': self.target_val[1] = self.MAX_SPEED
                elif key.char == 'e': self.target_val[1] = -self.MAX_SPEED
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if self.current_mode == 1:
                if key.char in ['w', 's']: self.target_val[0] = 0
                elif key.char in ['a', 'd']: self.target_val[3] = 0
                elif key.char in ['h', 'b']: self.target_val[2] = 0
                elif key.char in ['q', 'e']: self.target_val[1] = 0
        except AttributeError:
            pass

    def approach(self, current, target, step):
        if current < target:
            return min(current + step, target)
        elif current > target:
            return max(current - step, target)
        return current

    def send_loop(self):
        step_pwm = 2 
        
        # Ramping Logic
        for i in range(4):
            self.current_val[i] = self.approach(self.current_val[i], self.target_val[i], step_pwm)
            
        # Safety Stop
        if self.current_mode == 0:
            self.current_val = [0, 0, 0, 0]
            
        packet = f"{self.current_val[0]},{self.current_val[1]},{self.current_val[2]},{self.current_val[3]},{self.current_mode}\n"
        
        # Kirim ke Serial jika Hardware terhubung
        if self.ser and self.ser.is_open:
            try:
                self.ser.write(packet.encode())
            except Exception as e:
                self.get_logger().error(f"Gagal kirim data: {e}")

def main(args=None):
    rclpy.init(args=args)
    node = McuBridgeNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node.ser and node.ser.is_open:
            node.ser.close()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()