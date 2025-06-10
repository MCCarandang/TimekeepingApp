import sys
import time
import os
import sqlite3
from time import sleep
from PIL import Image
import io
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera2 import Picamera2
import pygame
import cv2
import numpy as np
from datetime import datetime
from ultralytics import YOLO
from pathlib import Path
import utils
from utils import create_output_dir, get_timestamp, crop_image, draw_bbox, save_metadata
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout,
    QWidget, QPushButton, QSizePolicy, QSpacerItem
)
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QDateTime

# ==== PATHS ====
DB_PATH = "/home/raspberrypi/Desktop/TimekeepingApp/timekeepingapp.db"
DENIED_PHOTO_DIR = "/home/raspberrypi/Desktop/Timekeeping/denied_photos"
MODEL_PATH = "/home/raspberrypi/Desktop/TimekeepingApp/best.pt"
CAPTURE_DIR = "/home/raspberrypi/Desktop/TimekeepingApp/outputs/captures"
CSV_PATH = "/home/raspberrypi/Desktop/TimekeepingApp/outputs/metadata.csv"

create_output_dir(CAPTURE_DIR)

# Constants
SPECIAL_RFID_TAGS = {"529365863836", "452840563394"}
REPEAT_SCAN_SECONDS = 5
BUZZER_PIN = 18

def get_label_from_code(code):
    return "IN" if code == 'I' else "OUT"

class AccessGrantedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timekeeping")
        self.showFullScreen()
        self.can_accept_denied_scan = True
        self.current_state = "IN"

        self.setup_palette()
        self.setup_ui()
        self.setup_camera()
        self.setup_rfid()
        self.setup_timers()

        self.model = YOLO(MODEL_PATH)
        self.db = sqlite3.connect(DB_PATH)
        self.cursor = self.db.cursor()
        self.rfid_feedback = None

        self.id_detection_timer = QTimer()
        self.id_detection_timer.timeout.connect(self.detect_id_card)
        self.id_detection_timer.start(500)

    def setup_palette(self):
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("navy"))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

    def setup_ui(self):
        self.label_group = QWidget()

        # Labels
        self.date_time_label = QLabel()
        self.transaction_code_label = QLabel("IN")
        self.message_label = QLabel("TAP YOUR ID")
        self.user_name_label = QLabel("")
        self.id_number_label = QLabel("")
        self.department_label = QLabel("")
        self.timestamp_label = QLabel("")
        self.photo_label = QLabel()
        self.camera_label = QLabel()
        self.exit_button = QPushButton("Exit")

        self.setup_label_styles()
        self.setup_layouts()

    def setup_label_styles(self):
        font_15 = QFont("Helvetica", 15)
        font_15_bold = QFont("Helvetica", 15, QFont.Bold)
        font_45_bold = QFont("Helvetica", 45, QFont.Bold)

        self.date_time_label.setFont(font_15)
        self.date_time_label.setStyleSheet("color: white;")
        self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

        self.transaction_code_label.setFont(font_45_bold)
        self.transaction_code_label.setStyleSheet("color: white;")
        self.transaction_code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.message_label.setFont(font_45_bold)
        self.message_label.setStyleSheet("color: white;")
        self.message_label.setAlignment(Qt.AlignCenter)

        for label in [self.user_name_label, self.id_number_label, self.department_label, self.timestamp_label]:
            label.setFont(font_15_bold)
            label.setStyleSheet("color: white;")

        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMaximumHeight(150)

        self.camera_label.setFixedSize(180, 180)
        self.camera_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.exit_button.setFixedSize(60, 30)
        self.exit_button.setStyleSheet("background-color: #f0f0ff;")
        self.exit_button.clicked.connect(QApplication.quit)

    def setup_layouts(self):
        top_info_layout = QHBoxLayout()
        top_info_layout.setContentsMargins(10, 0, 10, 0)
        top_info_layout.addWidget(self.transaction_code_label, alignment=Qt.AlignLeft)
        top_info_layout.addStretch()
        top_info_layout.addWidget(self.date_time_label, alignment=Qt.AlignRight)

        name_id_layout = QVBoxLayout()
        for label in [self.user_name_label, self.id_number_label, self.department_label, self.timestamp_label]:
            name_id_layout.addWidget(label)
        name_id_layout.setAlignment(Qt.AlignLeft)

        user_info_group = QHBoxLayout()
        user_info_group.addWidget(self.photo_label)
        user_info_group.addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        user_info_group.addLayout(name_id_layout)
        user_info_widget = QWidget()
        user_info_widget.setLayout(user_info_group)

        camera_info_layout = QHBoxLayout()
        camera_info_layout.setContentsMargins(10, 0, 10, 0)
        camera_info_layout.addWidget(self.camera_label, alignment=Qt.AlignLeft | Qt.AlignBottom)
        camera_info_layout.addWidget(user_info_widget, alignment=Qt.AlignCenter)
        camera_info_layout.addStretch()
        camera_info_layout.addWidget(self.exit_button, alignment=Qt.AlignRight | Qt.AlignBottom)

        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(0, 5, 0, 5)
        label_layout.addLayout(top_info_layout)
        label_layout.addWidget(self.message_label)
        label_layout.addLayout(camera_info_layout)

        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.label_group)
        main_layout.setContentsMargins(0, 5, 0, 5)
        self.setCentralWidget(central_widget)

    def setup_camera(self):
        try:
            self.picam2 = Picamera2()
            config = self.picam2.create_still_configuration(main={"size": (640, 480), "format": "RGB888"})
            self.picam2.configure(config)
            self.picam2.start()
            sleep(1)  # Allow camera to warm up

            # Start camera preview timer
            self.camera_preview_timer = QTimer()
            self.camera_preview_timer.timeout.connect(self.update_camera_preview)
            self.camera_preview_timer.start(100)

        except Exception as e:
            print(f"Failed to initialize PiCamera2: {e}")
            self.picam2 = None

    def update_camera_preview(self):
        if not self.picam2:
            return
    
        try:
            frame = self.picam2.capture_array()
            frame = cv2.flip(frame, -1)
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb_image, (180, 180))
            h, w, ch = resized.shape
            bytes_per_line = ch * w
            qt_image = QImage(resized.data, w, h, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qt_image))
        except Exception as e:
            print(f"Camera preview error: {e}")

    def update_time(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%Y-%m-%d %H:%M:%S"))

    def setup_rfid(self):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(BUZZER_PIN, GPIO.OUT)
        self.reader = SimpleMFRC522()
        
    def beep_success(self):
        pwm = GPIO.PWM(BUZZER_PIN, 1000)
        pwm.start(50)
        sleep(0.5)
        pwm.stop()
        
    def beep_failure(self):
        # Two quick beeps
        pwm = GPIO.PWM(BUZZER_PIN, 1000)
        for _ in range(2):
            pwm.start(50)
            sleep(0.2)
            pwm.stop()
            sleep(0.2)

    def setup_timers(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()

        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.process_rfid)
        self.rfid_timer.start(1000)

    def update_date_time(self):
        now = QDateTime.currentDateTime()
        self.date_time_label.setText(now.toString("MM-dd-yyyy\nHH:mm:ss"))

    def reset_ui(self):
        self.message_label.setText("TAP YOUR ID")
        self.message_label.setFont(QFont("Helvetica", 45, QFont.Bold))
        self.message_label.setStyleSheet("color: white")
        self.transaction_code_label.setStyleSheet("color: white;")
        self.transaction_code_label.setText(self.current_state)
        for label in [self.user_name_label, self.id_number_label, self.department_label, self.timestamp_label]:
            label.clear()
        self.photo_label.clear()

    def capture_denied_photo(self, transaction_code):
        if not self.picam2:
            print("Camera not initialized")
            return None
    
        os.makedirs(DENIED_PHOTO_DIR, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"denied_{get_label_from_code(transaction_code)}_{timestamp}.jpg"
        file_path = os.path.join(DENIED_PHOTO_DIR, filename)
        
        self.camera_preview_timer.stop()
        QTimer.singleShot(3000, self.resume_camera_preview)

        try:
            frame = self.picam2.capture_array()
            flipped_frame = cv2.rotate(frame, cv2.ROTATE_180)
            cv2.imwrite(file_path, flipped_frame)

            # Convert and display
            rgb_image = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB)
            resized = cv2.resize(rgb_image, (180, 180))
            height, width, channel = resized.shape
            bytes_per_line = 3 * width
            q_image = QImage(resized.data, width, height, bytes_per_line, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(q_image))

            QTimer.singleShot(3000, self.clear_camera_label)
            return file_path
        except Exception as e:
            print(f"Failed to capture or save denied photo: {e}")
            return None
        
    def resume_camera_preview(self):
        self.camera_label.show()
        self.camera_preview_timer.start(300)
        
    def hide_camera(self, duration_ms=3000):
        self.camera_preview_timer.stop()
        self.camera_label.hide()
        QTimer.singleShot(duration_ms, self.resume_camera_preview)
        
    def detect_id_card(self):
        frame = self.picam2.capture_array()
        frame = cv2.flip(frame, 0)
        if frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        results = self.model(frame, verbose=False)[0]
        frame_h, frame_w = frame.shape[:2]

        for det in results.boxes:
            class_id = int(det.cls[0].item())
            if class_id != 0:
                continue

            x1, y1, x2, y2 = map(int, det.xyxy[0].tolist())
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame_w - 1, x2)
            y2 = min(frame_h - 1, y2)

            if x2 > x1 and y2 > y1:
                self.id_detection_timer.stop()
                QTimer.singleShot(5000, lambda: self.handle_missing_rfid(frame, [x1, y1, x2, y2]))
                return
    
    def handle_missing_rfid(self, frame, box):
        if self.rfid_feedback:
            self.rfid_feedback = None  # Reset for next loop
            self.id_detection_timer.start(2000)
            return

        cropped = crop_image(frame, box)
        if cropped is not None and cropped.size > 0:
            # Generate filename & timestamp
            _, timestamp = get_timestamp()
            filename = f"{timestamp}.jpg"
            filepath = os.path.join(CAPTURE_DIR, filename)

            cv2.imwrite(filepath, cropped)

            save_metadata(CSV_PATH, {
                "filename": filename,
                "timestamp": timestamp,
                "x1": box[0], "y1": box[1], "x2": box[2], "y2": box[3]
            })

            success, buffer = cv2.imencode(".jpg", cropped)

            now = time.strftime("%Y-%m-%d %H:%M:%S")
            if success:
                image_blob = buffer.tobytes()
                self.cursor.execute("""INSERT INTO def_ids (photo, reported_time) VALUES (?, ?)""", (image_blob, now))
                self.db.commit()

                self.message_label.setText("DEFECTIVE ID")
                QTimer.singleShot(3000, self.reset_ui)

        self.rfid_feedback = None
        self.id_detection_timer.start()

    def clear_camera_label(self):
        self.camera_label.clear()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()

    def process_rfid(self):
        tag = self.read_tag()
        if not tag:
            return
        self.rfid_feedback = True   # Mark as a proper RFID scan

        if tag in SPECIAL_RFID_TAGS:
            self.handle_special_tag()
        elif self.is_authorized(tag):
            self.handle_authorized(tag)
        else:
            self.handle_unauthorized(tag)

    def read_tag(self):
        try:
            id, _ = self.reader.read_no_block()
            return str(id) if id else None
        except Exception as e:
            print(f"Error reading RFID: {e}")
            return None
        
    def handle_special_tag(self):
        self.current_state = "OUT" if self.current_state == "IN" else "IN"
        self.transaction_code_label.setText(self.current_state)
        self.message_label.setText("TAP YOUR ID")
        self.reset_ui()

    def is_authorized(self, tag):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id_number FROM employees WHERE rfid_tag = ?", (tag,))
            result = cursor.fetchone()
            self.employee_id = result[0] if result else None
            conn.close()
            return result is not None
        except Exception as e:
            print(f"Database error in is_authorized: {e}")
            return False

    def handle_authorized(self, tag):
        conn = None
        try:
            if self.is_repeated_scan(tag, self.employee_id):
                self.message_label.setText("REPEATED ACTION")
                self.message_label.setStyleSheet("color: yellow;")
                self.transaction_code_label.setText("IN")
                self.transaction_code_label.setStyleSheet("color: yellow;")
                QTimer.singleShot(3000, self.reset_ui)
                return

            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = time.strftime("%Y-%m-%d %H:%M:%S")

            # Determine transaction type
            cursor.execute("""
                SELECT transaction_code FROM attd_logs
                WHERE id_number = ?
                ORDER BY transaction_time DESC LIMIT 1
            """, (self.employee_id,))
            last = cursor.fetchone()
            tx_type = 'O' if last and last[0] == 'I' else 'I'

            cursor.execute("""
                INSERT INTO attd_logs (id_number, rfid_tag, transaction_code, transaction_time)
                VALUES (?, ?, ?, ?)
            """, (self.employee_id, tag, tx_type, now))

            cursor.execute("""
                SELECT first_name, middle_name, last_name, id_number, photo, department
                FROM employees WHERE id_number = ?
            """, (self.employee_id,))
            emp = cursor.fetchone()

            if emp:
                full_name = f"{emp[0]} {emp[1]} {emp[2]}"
                self.user_name_label.setText(full_name)
                self.id_number_label.setText(f"ID: {emp[3]}")
                self.department_label.setText(emp[5])
                self.timestamp_label.setText(time.strftime("%H:%M | %Y-%m-%d"))

                pixmap = QPixmap()
                pixmap.loadFromData(emp[4])
                if not pixmap.isNull():
                    self.photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
                else:
                    self.photo_label.setText("Photo failed to load")

            self.message_label.setText("ACCESS GRANTED")
            self.message_label.setFont(QFont("Helvetica", 15, QFont.Bold))
            self.message_label.setFixedHeight(50)
            self.message_label.setStyleSheet("background-color: yellow; color: black;")
            self.transaction_code_label.setText(get_label_from_code(tx_type))
            self.transaction_code_label.setStyleSheet("color: yellow;")
            self.hide_camera(3000)
            self.beep_success()
            conn.commit()
        except Exception as e:
            print(f"Error in handle_authorized: {e}")
        finally:
            if conn:
                conn.close()
            QTimer.singleShot(3000, self.reset_ui)

    def handle_unauthorized(self, tag):
        if not self.can_accept_denied_scan:
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            now = time.strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
                SELECT transaction_code FROM denied_usr
                WHERE rfid_tag = ? ORDER BY attempt_time DESC LIMIT 1
            """, (tag,))
            last = cursor.fetchone()
            tx_code = 'O' if last and last[0] == 'I' else 'I'

            photo_path = self.capture_denied_photo(tx_code)
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as file:
                  photo_blob = file.read()

            else:
                photo_blob = None

            cursor.execute("""
                INSERT INTO denied_usr (rfid_tag, transaction_code, photo, attempt_time)
                VALUES (?, ?, ?, ?)
            """, (tag, tx_code, photo_blob, now))

            conn.commit()

            self.message_label.setText("ACCESS DENIED")
            self.message_label.setFont(QFont("Helvetica", 15, QFont.Bold))
            self.message_label.setFixedHeight(50)
            self.message_label.setStyleSheet("background-color: red; color: black;")
            self.transaction_code_label.setText(get_label_from_code(tx_code))
            self.transaction_code_label.setStyleSheet("color: red;")
            self.beep_failure()
        except Exception as e:
            print(f"Error in handle_unauthorized: {e}")
        finally:
            conn.close()
            self.can_accept_denied_scan = False
            QTimer.singleShot(2000, lambda: setattr(self, 'can_accept_denied_scan', True))
            QTimer.singleShot(3000, self.reset_ui)
            
    def closeEvent(self, event):
        GPIO.cleanup()
        event.accept()

    def is_repeated_scan(self, tag, employee_id):
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT transaction_code, transaction_time FROM attd_logs
                WHERE id_number = ?
                ORDER BY transaction_time DESC LIMIT 1
            """, (employee_id,))
            last_transaction = cursor.fetchone()
            if last_transaction:
                last_code, last_time = last_transaction
                last_time_struct = time.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                now_struct = time.localtime()
                time_diff = time.mktime(now_struct) - time.mktime(last_time_struct)
                if last_code == 'I' and time_diff < REPEAT_SCAN_SECONDS:
                    self.reset_ui()
                    return True
            return False
        except Exception as e:
            print(f"Error checking repeated scan: {e}")
            return False
        finally:
            conn.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccessGrantedWindow()
    window.show()
    sys.exit(app.exec_())