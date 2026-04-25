#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import CompressedImage
import tkinter as tk
from tkinter import ttk, scrolledtext
import serial
import serial.tools.list_ports
import threading
import time
import re
import cv2
import numpy as np
from PIL import Image, ImageTk

# --- NODE ROS 2 (Berjalan di Background) ---
class VisionSubscriber(Node):
    def __init__(self, gui_app):
        super().__init__('gui_dashboard_node')
        self.gui_app = gui_app
        self.subscription = self.create_subscription(
            CompressedImage,
            '/yolo_vision/compressed',
            self.image_callback,
            10)

    def image_callback(self, msg):
        # Hanya tampilkan jika mode AUTO
        if "AUTO" not in self.gui_app.lbl_mode.cget("text"):
            return

        try:
            np_arr = np.frombuffer(msg.data, np.uint8)
            cv_img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
            cv_img = cv2.resize(cv_img, (480, 270)) 
            cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
            
            pil_img = Image.fromarray(cv_img)
            tk_img = ImageTk.PhotoImage(image=pil_img)

            # Update GUI secara aman dari thread ROS
            self.gui_app.root.after(0, self.gui_app.update_video_screen, tk_img)
        except Exception as e:
            self.get_logger().error(f"Error decoding image: {e}")

# --- APLIKASI GUI TKINTER ---
class ROVMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MavisEvo - Mission Control")
        self.root.geometry("650x850") 
        
        self.serial_port = None
        self.is_connected = False
        self.read_thread = None

        self.setup_ui()
        self.refresh_ports()

    def setup_ui(self):
        # Frame Koneksi
        conn_frame = ttk.LabelFrame(self.root, text="Koneksi Serial Teensy", padding=(10, 5))
        conn_frame.pack(fill=tk.X, padx=10, pady=5)
        self.port_combo = ttk.Combobox(conn_frame, state="readonly", width=25)
        self.port_combo.pack(side=tk.LEFT, padx=5)
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).pack(side=tk.LEFT, padx=5)
        self.btn_connect = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.btn_connect.pack(side=tk.LEFT, padx=5)
        self.lbl_status = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.lbl_status.pack(side=tk.LEFT, padx=10)

        # Frame Status System
        sys_frame = ttk.LabelFrame(self.root, text="System Status", padding=(10, 5))
        sys_frame.pack(fill=tk.X, padx=10, pady=5)
        self.lbl_mode = ttk.Label(sys_frame, text="Mode: UNKNOWN", font=("Arial", 12, "bold"))
        self.lbl_mode.pack(anchor=tk.W)

        # Frame Video Live Feed
        video_frame = ttk.LabelFrame(self.root, text="Live Vision (AI YOLOv11)", padding=(5, 5))
        video_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.lbl_video = ttk.Label(video_frame, text="[ Kamera Standby - Beralih ke Mode AUTO untuk Menampilkan ]", font=("Arial", 10, "italic"))
        self.lbl_video.pack(pady=10)

        # Frame PWM Thrusters
        pwm_frame = ttk.LabelFrame(self.root, text="Thruster Output (1100 - 1900)", padding=(10, 10))
        pwm_frame.pack(fill=tk.X, padx=10, pady=5)

        self.thrusters = {}
        thruster_names = [
            ("DKIRI", "Depan Kiri"), ("DKANAN", "Depan Kanan"),
            ("BKIRI", "Belakang Kiri"), ("BKANAN", "Belakang Kanan"),
            ("TBKIRI", "Tengah Kiri"), ("TBKANAN", "Tengah Kanan")
        ]
        for i, (key, desc) in enumerate(thruster_names):
            ttk.Label(pwm_frame, text=f"{desc} ({key}):", width=25).grid(row=i, column=0, sticky=tk.W, pady=2)
            pb = ttk.Progressbar(pwm_frame, orient=tk.HORIZONTAL, length=200, mode='determinate', maximum=800)
            pb.grid(row=i, column=1, pady=2, padx=5)
            val_lbl = ttk.Label(pwm_frame, text="1500", width=5, font=("Arial", 10, "bold"))
            val_lbl.grid(row=i, column=2, pady=2)
            self.thrusters[key] = {'pb': pb, 'val': val_lbl}

        # Frame Raw Console
        console_frame = ttk.LabelFrame(self.root, text="Raw Serial Data", padding=(10, 5))
        console_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.console_text = scrolledtext.ScrolledText(console_frame, height=8, state=tk.DISABLED, bg="black", fg="lime")
        self.console_text.pack(fill=tk.BOTH, expand=True)

    def update_video_screen(self, tk_img):
        self.lbl_video.config(image=tk_img, text="")
        self.lbl_video.image = tk_img 

    def refresh_ports(self):
        ports = serial.tools.list_ports.comports()
        port_list = [port.device for port in ports]
        self.port_combo['values'] = port_list
        if port_list: self.port_combo.current(0)
        else: self.port_combo.set("No ports detected")

    def toggle_connection(self):
        if self.is_connected: self.disconnect_serial()
        else: self.connect_serial()

    def connect_serial(self):
        selected_port = self.port_combo.get()
        if not selected_port or selected_port == "No ports detected": return
        try:
            self.serial_port = serial.Serial(selected_port, 115200, timeout=1)
            self.is_connected = True
            self.btn_connect.config(text="Disconnect")
            self.lbl_status.config(text=f"Connected", foreground="green")
            self.port_combo.config(state=tk.DISABLED)
            self.read_thread = threading.Thread(target=self.read_from_serial, daemon=True)
            self.read_thread.start()
        except Exception as e:
            self.log_console(f"Connection error: {e}\n")

    def disconnect_serial(self):
        self.is_connected = False
        if self.serial_port and self.serial_port.is_open: self.serial_port.close()
        self.btn_connect.config(text="Connect")
        self.lbl_status.config(text="Disconnected", foreground="red")
        self.port_combo.config(state="readonly")
        for key in self.thrusters: self.update_pwm_ui(key, 1500)
        self.lbl_mode.config(text="Mode: UNKNOWN")
        self.lbl_video.config(image='', text="[ Kamera Standby - Beralih ke Mode AUTO untuk Menampilkan ]")

    def log_console(self, text):
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, text)
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)

    def read_from_serial(self):
        while self.is_connected and self.serial_port.is_open:
            try:
                if self.serial_port.in_waiting > 0:
                    line = self.serial_port.readline().decode('utf-8', errors='ignore').strip()
                    if line:
                        self.root.after(0, self.log_console, line + "\n")
                        self.root.after(0, self.parse_serial_data, line)
            except Exception:
                self.root.after(0, self.disconnect_serial)
                break
            time.sleep(0.01)

    def parse_serial_data(self, line):
        if "Mode:" in line:
            parts = line.split("Mode:")
            if len(parts) > 1:
                mode_str = parts[1].strip().split(" ")[0] 
                self.lbl_mode.config(text=f"Mode: {mode_str}")
                if mode_str != "AUTO":
                    self.lbl_video.config(image='', text="[ Kamera Standby - Beralih ke Mode AUTO untuk Menampilkan ]")

        if "DK:" in line and "TBKn:" in line:
            nums = re.findall(r'\d+', line)
            if len(nums) >= 6:
                try:
                    self.update_pwm_ui("DKIRI", int(nums[0]))
                    self.update_pwm_ui("DKANAN", int(nums[1]))
                    self.update_pwm_ui("BKIRI", int(nums[2]))
                    self.update_pwm_ui("BKANAN", int(nums[3]))
                    self.update_pwm_ui("TBKIRI", int(nums[4]))
                    self.update_pwm_ui("TBKANAN", int(nums[5]))
                except ValueError: pass

    def update_pwm_ui(self, thruster_key, value):
        if thruster_key in self.thrusters:
            clamped_val = max(1100, min(1900, value))
            self.thrusters[thruster_key]['pb']['value'] = clamped_val - 1100
            self.thrusters[thruster_key]['val'].config(text=str(value))

# --- FUNGSI UTAMA (Menjalankan Tkinter & ROS 2 bersamaan) ---
def main(args=None):
    rclpy.init(args=args)
    root = tk.Tk()
    app = ROVMonitorApp(root)
    
    ros_node = VisionSubscriber(app)
    
    # Jalankan ROS Spin di thread terpisah agar GUI tidak hang
    ros_thread = threading.Thread(target=rclpy.spin, args=(ros_node,), daemon=True)
    ros_thread.start()

    # Fungsi saat window ditutup
    def on_closing():
        app.disconnect_serial()
        ros_node.destroy_node()
        rclpy.shutdown()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Jalankan loop Tkinter
    root.mainloop()

if __name__ == "__main__":
    main()