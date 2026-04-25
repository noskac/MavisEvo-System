#!/bin/bash

# Root folder
PROJECT_NAME="MavisEvo-ROV"

# Buat struktur folder
mkdir -p $PROJECT_NAME/firmware
mkdir -p $PROJECT_NAME/models
mkdir -p $PROJECT_NAME/src/mavis_vision/scripts
mkdir -p $PROJECT_NAME/src/mavis_control/scripts

# Buat file firmware
touch $PROJECT_NAME/firmware/main.cpp

# Buat file models (placeholder)
touch $PROJECT_NAME/models/yolov8n_custom.pt
touch $PROJECT_NAME/models/yolov8n_custom.engine

# Buat file mavis_vision
touch $PROJECT_NAME/src/mavis_vision/scripts/yolo_vision_node.py
touch $PROJECT_NAME/src/mavis_vision/scripts/yoloDet.py
touch $PROJECT_NAME/src/mavis_vision/CMakeLists.txt

# Buat file mavis_control
touch $PROJECT_NAME/src/mavis_control/scripts/teensy_bridge.py
touch $PROJECT_NAME/src/mavis_control/scripts/mission_control.py
touch $PROJECT_NAME/src/mavis_control/CMakeLists.txt

# File root
touch $PROJECT_NAME/README.md
touch $PROJECT_NAME/requirements.txt

echo "Struktur project $PROJECT_NAME berhasil dibuat!"
