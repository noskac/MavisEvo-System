#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from sensor_msgs.msg import CompressedImage
import cv2
import numpy as np
import time
from ultralytics import YOLO

class YoloVisionNode(Node):
    def __init__(self):
        super().__init__('yolo_vision_node')
        
        # Publisher ROS 2
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel_auto', 10)
        self.img_pub = self.create_publisher(CompressedImage, '/yolo_vision/compressed', 10)

        # Path ke model TensorRT yang baru saja kita buat
        engine_path = "/media/cakson/NVME Volume/Code/MAVIS/mavis_ws/models/orange_pole_best.engine"
        self.get_logger().info(f"Memuat model YOLO dari: {engine_path}")
        
        # Inisialisasi model (Langsung baca .engine via Ultralytics)
        try:
            self.model = YOLO(engine_path, task='detect')
            self.get_logger().info("Model berhasil dimuat! TensorRT Aktif.")
        except Exception as e:
            self.get_logger().error(f"Gagal memuat model: {e}")
            sys.exit()

        self.cap = cv2.VideoCapture(0) # Kamera default
        self.screen_width = 640 # Resolusi YOLO standar
        self.center_x = self.screen_width / 2.0

        # Timer untuk looping (menggantikan while loop di ROS 1)
        # 0.033 detik = sekitar 30 FPS target looping
        self.timer = self.create_timer(0.033, self.vision_loop)
        self.prev_time = time.time()

    def vision_loop(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        # Resize frame agar sesuai dengan rasio
        frame = cv2.resize(frame, (self.screen_width, int(self.screen_width * frame.shape[0] / frame.shape[1])))

        # --- PROSES INFERENSI YOLO ---
        # verbose=False agar terminal tidak terlalu penuh dengan teks log
        results = self.model(frame, verbose=False)
        
        msg = Twist()
        boxes = results[0].boxes

        if len(boxes) > 0:
            # Ambil deteksi tiang oranye pertama (confidence tertinggi)
            box = boxes[0].xyxy[0].cpu().numpy() # Format: [x_min, y_min, x_max, y_max]
            
            obj_x = (box[0] + box[2]) / 2.0
            error_x = obj_x - self.center_x
            
            # Logika pergerakan AI 
            msg.angular.z = float(error_x * 0.6)  
            msg.linear.x = 150.0 # Maju
            
            # Gambar kotak penanda untuk dikirim ke GUI
            cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 165, 255), 2)
            cv2.putText(frame, "TARGET DETECTED", (int(box[0]), int(box[1])-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 165, 255), 2)
        else:
            # Jika tiang hilang, putar perlahan mencari target
            msg.linear.x = 0.0
            msg.angular.z = 30.0             

        self.cmd_pub.publish(msg)

        # --- MENGHITUNG FPS & KIRIM VIDEO KE GUI ---
        current_time = time.time()
        fps = 1.0 / (current_time - self.prev_time)
        self.prev_time = current_time
        
        cv2.putText(frame, f"FPS: {fps:.1f} (TensorRT)", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        msg_img = CompressedImage()
        msg_img.header.stamp = self.get_clock().now().to_msg()
        msg_img.format = "jpeg"
        # Kompresi gambar menjadi format .jpg byte array
        _, buffer = cv2.imencode('.jpg', frame)
        msg_img.data = np.array(buffer).tobytes()
        
        self.img_pub.publish(msg_img)

def main(args=None):
    rclpy.init(args=args)
    node = YoloVisionNode()
    try:
        rclpy.spin(node) # Menjaga node tetap hidup
    except KeyboardInterrupt:
        pass
    finally:
        node.cap.release()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
