# 🌊 MavisEvoV1 - AI-Powereds AUV System (ONGOING)

Sistem kendali cerdas dan *computer vision* untuk Remotely Operated Vehicle (ROV) bawah air. Arsitektur ini menggabungkan pendeteksian objek secara *real-time* menggunakan YOLOv11 dengan sistem komunikasi robotika standar industri (ROS 2).

## ✨ Fitur Utama
* **Computer Vision (AI):** Deteksi target otomatis (*Orange Pole*) menggunakan YOLOv11 Nano, diakselerasi dengan TensorRT (FP16) untuk FPS maksimal.
* **ROS 2 Backbone:** Menggunakan ROS 2 (Jazzy Jalisco) untuk pertukaran data yang *modular*, cepat, dan aman antar komponen (Backend AI, GUI, dan Mikrokontroler).
* **Mission Control GUI:** Antarmuka Tkinter *custom* untuk memantau status *thruster*, log serial, dan *live video feed* dari AI.
* **Universal Firmware:** *Codebase* mikrokontroler (C++) yang dioptimalkan via PlatformIO, mendukung pergantian mulus antara **ESP32** dan **Teensy 4.1**.

## 📂 Struktur Repositori
* `src/mavis_vision/`: Node ROS 2 untuk *inference* YOLO dan kamera.
* `src/mavis_control/`: Node ROS 2 untuk GUI Dashboard dan jembatan Serial (MCU Bridge).
* `models/`: Tempat menyimpan file *weight* `.pt` dan `.engine`.

## 🛠️ Tech Stack
* **OS:** Ubuntu 24.04 LTS
* **Middleware:** ROS 2 Jazzy Jalisco
* **AI & Vision:** PyTorch, Ultralytics (YOLO), TensorRT, OpenCV
* **Hardware:** NVIDIA RTX Series (Backend), ESP32 / Teensy 4.1 (Controller)

---
*Developed by Andaru Wicaksono.*
