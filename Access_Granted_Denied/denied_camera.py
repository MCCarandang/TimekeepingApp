# Repeated Transaction Working Fine
# It shows user name, id number, photo

import sys
import time
from time import sleep
import os
import sqlite3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from picamera.array import PiRGBArray
import cv2
import numpy as np
import pygame
import subprocess
import io
from io import BytesIO
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QDateTime

SPECIAL_RFID_TAG = "529365863836"

def get_label_from_code(code):
    return "IN" if code == 'I' else "OUT"

def __init__(self):
    super().__init__()
    self.setWindowTitle("Timekeeping")

    # Set background color to navy
    self.setAutoFillBackground(True)
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("navy"))
    self.setPalette(palette)

    # Create central widget and grid layout
    central_widget = QWidget()
    grid_layout = QGridLayout(central_widget)
    grid_layout.setContentsMargins(20, 20, 20, 20)
    grid_layout.setSpacing(15)

    # Set row and column stretch factors to limit how much space they take
    grid_layout.setRowStretch(0, 0)  # Do not stretch row 0
    grid_layout.setRowStretch(1, 1)  # Allow row 1 to grow slightly
    grid_layout.setRowStretch(2, 1)
    grid_layout.setRowStretch(3, 1)
    grid_layout.setColumnStretch(0, 1)  # Allow column 0 to grow a bit
    grid_layout.setColumnStretch(1, 2)  # Allow column 1 to take more space
    grid_layout.setColumnStretch(2, 0)  # Do not stretch column 2

    # Set maximum width for labels and buttons to prevent stretching
    self.transaction_code_label.setFixedWidth(200)
    self.message_label.setFixedWidth(500)

    # Create the labels
    self.date_time_label = QLabel()
    self.transaction_code_label = QLabel("IN")
    self.message_label = QLabel("TAP YOUR RFID TAG")
    self.user_name_label = QLabel("")
    self.id_number_label = QLabel("")
    self.photo_label = QLabel()
    self.camera_label = QLabel()

    # Set properties
    self.date_time_label.setFont(QFont("Helvetica", 15))
    self.date_time_label.setStyleSheet("color: white;")
    self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)

    self.transaction_code_label.setFont(QFont("Helvetica", 45, QFont.Bold))
    self.transaction_code_label.setStyleSheet("color: white;")
    self.transaction_code_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

    self.message_label.setFont(QFont("Helvetica", 45, QFont.Bold))
    self.message_label.setStyleSheet("color: white;")
    self.message_label.setAlignment(Qt.AlignCenter)

    self.user_name_label.setFont(QFont("Helvetica", 15, QFont.Bold))
    self.user_name_label.setStyleSheet("color: gray;")
    self.user_name_label.setAlignment(Qt.AlignCenter)

    self.id_number_label.setFont(QFont("Helvetica", 15, QFont.Bold))
    self.id_number_label.setStyleSheet("color: yellow;")
    self.id_number_label.setAlignment(Qt.AlignCenter)

    self.photo_label.setAlignment(Qt.AlignCenter)
    self.photo_label.setMaximumHeight(150)

    self.camera_label.setFixedSize(180, 180)
    self.camera_label.setAlignment(Qt.AlignLeft | Qt.AlignBottom)

    # Add widgets to grid layout
    grid_layout.addWidget(self.date_time_label, 0, 2, alignment=Qt.AlignRight)
    grid_layout.addWidget(self.transaction_code_label, 1, 0)
    grid_layout.addWidget(self.message_label, 1, 1, 1, 2)
    grid_layout.addWidget(self.user_name_label, 2, 1, alignment=Qt.AlignCenter)
    grid_layout.addWidget(self.id_number_label, 3, 1, alignment=Qt.AlignCenter)
    grid_layout.addWidget(self.photo_label, 4, 1, alignment=Qt.AlignCenter)
    grid_layout.addWidget(self.camera_label, 4, 0, alignment=Qt.AlignLeft | Qt.AlignBottom)

    # Exit button
    self.exit_button = QPushButton()
    self.exit_button.setFixedSize(40, 10)
    self.exit_button.setStyleSheet("background-color: white;")
    self.exit_button.clicked.connect(QApplication.quit)

    # Add exit button to bottom-right
    grid_layout.addWidget(self.exit_button, 5, 2, alignment=Qt.AlignRight)

    # Set layout
    self.setCentralWidget(central_widget)
    self.setFixedSize(1024, 768)  # Limit the window size to fit Raspberry Pi's screen

    # Initialize camera
    self.camera = PiCamera(resolution=(320, 240), framerate=24)
    self.raw_capture = PiRGBArray(self.camera, size=(320, 240))

    self.camera_timer = QTimer(self)
    self.camera_timer.timeout.connect(self.update_camera_preview)
    self.camera_timer.start(30)

    # Timers
    self.timer = QTimer(self)
    self.timer.timeout.connect(self.update_date_time)
    self.timer.start(1000)
    self.update_date_time()

    self.rfid_timer = QTimer(self)
    self.rfid_timer.timeout.connect(self.check_rfid)
    self.rfid_timer.start(500)

    # RFID Setup
    GPIO.setwarnings(False)
    self.reader = SimpleMFRC522()

    # State
    self.current_state = "IN"

    def update_date_time(self):
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("MM-dd-yyyy")
        time_str = current_time.toString("HH:mm:ss")
        self.date_time_label.setText(f"{date_str}\n{time_str}")
        
    def reset_ui(self):
        self.message_label.setText("TAP YOUR RFID TAG")
        self.transaction_code_label.setText("IN")
        self.user_name_label.setText("")
        self.id_number_label.setText("")
        self.photo_label.clear()

    def show_user_info(self, name, id_number, photo_pixmap):
        self.user_name_label.setText(name)
        self.id_number_label.setText(id_number)
        self.photo_label.setPixmap(photo_pixmap)
        
        # Show for 1 second
        self.user_info_timer  = QTimer()
        self.user_info_timer.setSingleShot(True)
        self.user_info_timer.timeout.connect(self.clear_user_info)
        self.user_info_timer.start(1000)	 # 1000 ms = 1 second
        
    def clear_user_info(self):
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.photo_label.clear()

    def update_camera_preview(self):
        try:
            self.raw_capture.truncate(0)
            self.camera.capture(self.raw_capture, format="bgr", use_video_port=True)
            image = self.raw_capture.array
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            image = cv2.resize(image, (180, 180))
            height, width, channel = image.shape
            bytes_per_line = 3 * width
            qimg = QPixmap.fromImage(QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888))
            self.camera_label.setPixmap(qimg)
        except Exception as e:
            print(f"Camera preview error: {e}")
    
    def handle_rfid_scan(self,rfid_tag):
        if self.is_repeated_scan(rfid_tag):
            self.clear_user_info()
            self.transaction_code_label.setText("IN")
            self.message_label.setText("REPEATED ACTION")
        else:
            name, id_number, photo_pixmap = self.get_user_info(rfid_tag)
            transaction_status = self.get_transaction_status(rfid_tag)
            self.transaction_code_label.setText("IN" or "OUT")
            self.message_label.setText("ACCESS GRANTED")
            self.show_user_info(name, id_number, photo_pixmap)
            
    def handle_special_tag(self):
        #Trigger IN/OUT label without accessing the database
        self.current_state = "OUT" if self.current_state == "IN" else "IN"
        self.transaction_code_label.setText(self.current_state)
        self.message_label.setText("TAP YOUR RFID TAG")
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.photo_label.clear()

    def check_rfid(self):
        try:
            id, _ = self.reader.read_no_block()

            if id:
                rfid_str = str(id)
                
                # Handles the RFID Tag that triggers only the IN and OUT
                if rfid_str == SPECIAL_RFID_TAG:
                    self.handle_special_tag()
                    QTimer.singleShot(3000, self.reset_ui)
                    return
                
                conn = sqlite3.connect('/home/raspberrypi/Desktop/Timekeeping/timekeepingapp.db')
                cursor = conn.cursor()

                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                # Check if RFID is authorized
                cursor.execute("SELECT id FROM employees WHERE rfid_tag = ?", (rfid_str,))
                result = cursor.fetchone()

                if result:
                    employee_id = result[0]
                
                    # Determine last transaction
                    cursor.execute(""" 
                        SELECT transaction_code, transaction_time FROM attd_logs 
                        WHERE id_number = ?
                        ORDER BY transaction_time DESC LIMIT 1 
                    """, (employee_id,))
                    last_transaction = cursor.fetchone()
                
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                
                    if last_transaction:
                        last_code, last_time = last_transaction
                        last_time_struct = time.strptime(last_time, "%Y-%m-%d %H:%M:%S")
                        now_struct = time.localtime()
                        time_diff = time.mktime(now_struct) - time.mktime(last_time_struct)
                
                        if last_code == 'I' and time_diff < 5:
                            # Repeated scan after Time IN
                            self.clear_user_info()  # clear user info immediately
                            self.message_label.setText("REPEATED ACTION")
                            self.transaction_code_label.setText("IN")
                            
                            # Check if a repeated scan already exists for the same RFID and transaction code
                            cursor.execute("""
                                SELECT id, scan_count FROM repeated_scans
                                WHERE rfid_tag = ? AND transaction_code = 'I'
                                ORDER BY scan_time DESC LIMIT 1
                            """,(rfid_str,))
                            existing_scan = cursor.fetchone()
                            
                            if existing_scan:
                                # Update scan_count by incrementing it
                                scan_id, current_count = existing_scan
                                cursor.execute("""
                                    UPDATE repeated_scans
                                    SET scan_count = ?, scan_time = ?
                                    WHERE id = ?
                                """, (current_count + 1, current_time, scan_id))
                            else:
                                # Insert new record with scan_count = 1
                                cursor.execute("""
                                    INSERT INTO repeated_scans (rfid_tag, transaction_code, scan_time)
                                    VALUES (?, 'I', ?)
                                """, (rfid_str, current_time))
                
                            conn.commit()
                            conn.close()
                            QTimer.singleShot(3000, self.reset_ui)
                            return
                
                        transaction_type = 'O' if last_code == 'I' else 'I'
                    else:
                        transaction_type = 'I'  # First-ever log is always IN
                
                    # Log attendance
                    cursor.execute("""
                        INSERT INTO attd_logs (id_number, rfid_tag, transaction_code, transaction_time)
                        VALUES (?, ?, ?, ?)
                    """, (employee_id, rfid_str, transaction_type, current_time))
                
                    self.message_label.setText("ACCESS GRANTED")
                    self.transaction_code_label.setText(get_label_from_code(transaction_type))
                
                    # Fetch and display user info
                    cursor.execute(""" 
                        SELECT first_name, middle_name, last_name, id_number, photo 
                        FROM employees WHERE id = ? 
                    """, (employee_id,))
                    emp_info = cursor.fetchone()
                
                    if emp_info:
                        full_name = f"{emp_info[0]} {emp_info[1]} {emp_info[2]}"
                        id_number = emp_info[3]
                        photo_path = emp_info[4]
                
                        self.user_name_label.setText(full_name)
                        self.id_number_label.setText(f"ID: {id_number}")
                
                        if photo_path:
                            pixmap = QPixmap()
                            pixmap.load(photo_path)
                            if not pixmap.isNull():
                                self.photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
                            else:
                                self.photo_label.setText("Photo failed to load")
                        else:
                            self.photo_label.setText("Photo not found")

                else:
                    # UNAUTHORIZED: No repeated scan logic
                    cursor.execute(""" 
                        SELECT transaction_code FROM denied_usr 
                        WHERE rfid_tag = ? ORDER BY attempt_time DESC LIMIT 1 
                    """, (rfid_str,))
                    last_denied = cursor.fetchone()

                    new_transaction_code = 'O' if last_denied and last_denied[0] == 'I' else 'I'
                        
                    cursor.execute(""" 
                        INSERT INTO denied_usr (rfid_tag, transaction_code, attempt_time) 
                        VALUES (?, ?, ?) 
                    """, (rfid_str, new_transaction_code, current_time))

                    self.message_label.setText("ACCESS DENIED")
                    self.transaction_code_label.setText(get_label_from_code(new_transaction_code))

                conn.commit()
                conn.close()

                QTimer.singleShot(3000, self.reset_ui)

        except Exception as e:
            print(f"Error reading RFID: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AccessGrantedWindow()
    window.show()
    sys.exit(app.exec_())