# Displays a Camera Preview
# Captures a photo when access denied taps for in and out
# Captured photo is saved both in the disk and database
# Done with 4 Features
# Changing From In and Out
# Access Granted
# Access Denied
# Repeated Transaction
# FINAL but speaker not yet working

import sys
import time
from time import sleep
import os
import sqlite3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from picamera import PiCamera
from PIL import Image
import io
import cv2
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSizePolicy, QSpacerItem
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap, QImage
from PyQt5.QtCore import Qt, QTimer, QDateTime

SPECIAL_RFID_TAGS = {"529365863836", "452840563394"}

def get_label_from_code(code):
    return "IN" if code == 'I' else "OUT"

class AccessGrantedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timekeeping")
        self.showFullScreen()
        
        self.can_accept_denied_scan = True
        
        self.last_id_detected_time = 0
        self.id_currently_visible = False
        self.photo_captured = False
        self.TIME_THRESHOLD = 3  # seconds

        self.cv_timer = QTimer(self)
        self.cv_timer.timeout.connect(self.check_for_id_without_rfid)
        self.cv_timer.start(500)


        # Set background color to navy
        self.setAutoFillBackground(True)
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor("navy"))
        self.setPalette(palette)
        
        # Create a QWidget as the container
        self.label_group = QWidget()

        # Create the labels
        self.date_time_label = QLabel()
        self.transaction_code_label = QLabel("IN")
        self.message_label = QLabel("TAP YOUR ID")
        self.user_name_label = QLabel("")
        self.id_number_label = QLabel("")
        self.department_label = QLabel("")
        self.timestamp_label = QLabel("")
        self.photo_label = QLabel()

        # Set fonts and styles
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
        self.user_name_label.setStyleSheet("color: white;")
        #self.user_name_label.setAlignment(Qt.AlignCenter)

        self.id_number_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.id_number_label.setStyleSheet("color: white;")
        #self.id_number_label.setAlignment(Qt.AlignCenter)
        
        self.department_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.department_label.setStyleSheet("color: white;")
        #self.department_label.setAlignment(Qt.AlignCenter)
        
        self.timestamp_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.timestamp_label.setStyleSheet("color: white;")
        #self.timestamp_label.setAlignment(Qt.AlignCenter)

        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMaximumHeight(150)
        
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(180, 180)
        self.camera_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedSize(60, 30)
        self.exit_button.setStyleSheet("background-color: #f0f0ff;")
        self.exit_button.clicked.connect(QApplication.quit)
        
        top_info_layout = QHBoxLayout()
        top_info_layout.setContentsMargins(10, 0, 10, 0)
        top_info_layout.addWidget(self.transaction_code_label, alignment=Qt.AlignLeft)
        top_info_layout.addStretch()
        top_info_layout.addWidget(self.date_time_label, alignment=Qt.AlignRight)

        # Create vertical layout for name and ID
        name_id_layout = QVBoxLayout()
        name_id_layout.addWidget(self.user_name_label)
        name_id_layout.addWidget(self.id_number_label)
        name_id_layout.addWidget(self.department_label)
        name_id_layout.addWidget(self.timestamp_label)
        name_id_layout.setAlignment(Qt.AlignLeft)
        
        # Create horizontal layout with photo on the left and name/ID on the right
        user_info_group = QHBoxLayout()
        user_info_group.addWidget(self.photo_label)
        user_info_group.addSpacerItem(QSpacerItem(40, 0, QSizePolicy.Fixed, QSizePolicy.Minimum))
        user_info_group.addLayout(name_id_layout)
        user_info_group.setSpacing(8)
        
        # Wrap in a widget
        user_info_widget = QWidget()
        user_info_widget.setLayout(user_info_group)
        
        # Horizontal layout: camera | user info | exit button
        camera_info_layout = QHBoxLayout()
        camera_info_layout.setContentsMargins(10, 0, 10, 0)
        camera_info_layout.addWidget(self.camera_label, alignment=Qt.AlignLeft | Qt.AlignBottom)
        camera_info_layout.setSpacing(10)
        camera_info_layout.addWidget(user_info_widget, alignment=Qt.AlignCenter)
        camera_info_layout.addStretch()
        camera_info_layout.addWidget(self.exit_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        
        # Final vertical layout for the label group
        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(0, 5, 0, 5)
        label_layout.setSpacing(0)
        label_layout.addLayout(top_info_layout)
        label_layout.addWidget(self.message_label)
        label_layout.addLayout(camera_info_layout)
        
        # Central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.label_group)
        main_layout.setContentsMargins(0, 5, 0, 5)
        
        self.setCentralWidget(central_widget)

        self.camera = PiCamera()
        self.camera.resolution = (180, 180)
        self.camera.rotation = 180
        self.setGeometry(0, 0, QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height())
        #self.camera.start_preview(fullscreen=False, window=(0, 900, 180, 180))

        # RFID Setup
        GPIO.setwarnings(False)
        self.reader = SimpleMFRC522()

        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()

        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.check_rfid)
        self.rfid_timer.start(500)
        
        # State
        self.current_state = "IN"

    def update_date_time(self):
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("MM-dd-yyyy")
        time_str = current_time.toString("HH:mm:ss")
        self.date_time_label.setText(f"{date_str}\n{time_str}")
        
    def reset_ui(self):
        self.message_label.setText("TAP YOUR ID")
        self.message_label.setFont(QFont("Helvetica", 45, QFont.Bold))
        self.message_label.setStyleSheet("color: white;")
        self.transaction_code_label.setText("IN")
        self.transaction_code_label.setStyleSheet("color: white;")
        self.user_name_label.setText("")
        self.id_number_label.setText("")
        self.department_label.setText("")
        self.timestamp_label.setText("")
        self.photo_label.clear()

    def show_user_info(self, name, id_number, department, timestamp, photo_pixmap):
        self.user_name_label.setText(name)
        self.id_number_label.setText(id_number)
        self.department_label.setText(department)
        self.timestamp_label.setText(timestamp)
        self.photo_label.setPixmap(photo_pixmap)
        
        # Show for 1 second
        self.user_info_timer  = QTimer()
        self.user_info_timer.setSingleShot(True)
        self.user_info_timer.timeout.connect(self.clear_user_info)
        self.user_info_timer.start(1000)	 # 1000 ms = 1 second
        
    def clear_user_info(self):
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.department_label.clear()
        self.timestamp_label.clear()
        self.photo_label.clear()
        
    def handle_rfid_scan(self,rfid_tag):
        if self.is_repeated_scan(rfid_tag):
            self.clear_user_info()
            self.transaction_code_label.setText("IN")
            self.message_label.setText("REPEATED ACTION")
        else:
            name, id_number, department, photo_pixmap = self.get_user_info(rfid_tag)
            #transaction_status = self.get_transaction_status(rfid_tag)
            self.transaction_code_label.setText("IN" or "OUT")
            self.message_label.setText("ACCESS GRANTED")
            self.show_user_info(name, id_number, department, photo_pixmap)
            
    def handle_special_tag(self):
        #Trigger IN/OUT label without accessing the database
        self.current_state = "OUT" if self.current_state == "IN" else "IN"
        self.transaction_code_label.setText(self.current_state)
        self.message_label.setText("TAP YOUR ID")
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.department_label.clear()
        self.timestamp_label.clear()
        self.photo_label.clear()

    def capture_denied_photo(self, transaction_code):
        try:
            # Ensure directory exists
            save_dir = "/home/raspberrypi/Desktop/Timekeeping/denied_photos"
            os.makedirs(save_dir, exist_ok=True)

            timestamp = time.strftime("%Y%m%d_%H%M%S")
            if transaction_code == 'I':
                filename = f"denied_IN_{timestamp}.jpg"
            else:
                filename = f"denied_OUT_{timestamp}.jpg"

            file_path = os.path.join(save_dir, filename)

            # Capture photo
            self.camera.capture(file_path)

            # Display the captured photo in the camera_label
            image = Image.open(file_path)
            image = image.resize((180, 180)).convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qimage)
            self.camera_label.setPixmap(pixmap)

            QTimer.singleShot(3000, self.clear_camera_label)
            
            return file_path

        except Exception as e:
            print(f"Failed to capture denied photo: {e}")

    def clear_camera_label(self):
        self.camera_label.clear()

    def detect_id(self, frame):
        """
        Detects a possible ID in the frame and returns True if found.
        """
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 180, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            area = cv2.contourArea(contour)
            x, y, w, h = cv2.boundingRect(contour)

            if area > 1000:
                return True
        return False

    def check_for_id_without_rfid(self):
        try:
            # Capture frame from PiCamera
            stream = io.BytesIO()
            self.camera.capture(stream, format='jpeg')
            data = np.frombuffer(stream.getvalue(), dtype=np.uint8)
            frame = cv2.imdecode(data, 1)

            id_found = self.detect_id(frame)
            current_time = time.time()

            # You can replace this with a shared variable later
            rfid_recently_scanned = False  # Placeholder. Real logic should update this.

            if id_found:
                if not self.id_currently_visible:
                    self.last_id_detected_time = current_time
                    self.photo_captured = False
                self.id_currently_visible = True

                if (current_time - self.last_id_detected_time > self.TIME_THRESHOLD 
                    and not rfid_recently_scanned and not self.photo_captured):
                    self.capture_denied_photo(self.current_state[0])  # 'I' or 'O'
                    print("[INFO] No RFID detected. Denied photo captured.")
                    self.photo_captured = True
            else:
                self.id_currently_visible = False
                self.photo_captured = False

        except Exception as e:
            print(f"[ERROR] ID check failed: {e}")
        
    def check_rfid(self):
        try:
            id, _ = self.reader.read_no_block()

            if id:
                rfid_str = str(id)
                
                # Handles the RFID Tag that triggers only the IN and OUT
                if rfid_str in SPECIAL_RFID_TAGS:
                    self.handle_special_tag()
                    # QTimer.singleShot(3000, self.reset_ui)
                    return
                
                conn = sqlite3.connect('/home/raspberrypi/Desktop/TimekeepingApp/timekeepingapp.db')
                cursor = conn.cursor()

                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                # Check if RFID is authorized
                cursor.execute("SELECT id_number FROM employees WHERE rfid_tag = ?", (rfid_str,))
                result = cursor.fetchone()

                if result:
                    employee_id = result[0]
                
                    # Get the last transaction (most recent log)
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
                            # Repeated scan within 5 seconds of a Time IN
                            self.clear_user_info()
                            self.message_label.setText("REPEATED ACTION")
                            self.message_label.setFont(QFont("Helvetica", 45, QFont.Bold))
                            self.message_label.setStyleSheet("color: yellow;")
                            self.transaction_code_label.setText("IN")
                            self.transaction_code_label.setStyleSheet("color: yellow;")
                
                            # Check if a repeated scan already exists for this base time in
                            cursor.execute("""
                                SELECT id, scan_count FROM repeated_scans
                                WHERE rfid_tag = ? AND base_timein = ? AND transaction_code = 'I'
                            """, (rfid_str, last_time))
                            existing = cursor.fetchone()
                
                            if existing:
                                scan_id, scan_count = existing
                                cursor.execute("""
                                    UPDATE repeated_scans
                                    SET scan_count = ?, scan_time = ?
                                    WHERE id = ?
                                """, (scan_count + 1, current_time, scan_id))
                            else:
                                cursor.execute("""
                                    INSERT INTO repeated_scans (rfid_tag, transaction_code, base_timein, scan_count, scan_time)
                                    VALUES (?, 'I', ?, 1, ?)
                                """, (rfid_str, last_time, current_time))
                
                            conn.commit()
                            conn.close()
                            QTimer.singleShot(3000, self.reset_ui)
                            return
                
                        # Continue with regular flow
                        transaction_type = 'O' if last_code == 'I' else 'I'
                    else:
                        transaction_type = 'I'  # First-ever log
                
                    # Log attendance
                    cursor.execute("""
                        INSERT INTO attd_logs (id_number, rfid_tag, transaction_code, transaction_time)
                        VALUES (?, ?, ?, ?)
                    """, (employee_id, rfid_str, transaction_type, current_time))
                
                    self.message_label.setText("ACCESS GRANTED")
                    self.message_label.setFont(QFont("Helvetica", 15, QFont.Bold))
                    self.message_label.setFixedHeight(50)
                    self.message_label.setStyleSheet("background-color: yellow; color: black;")
                    self.transaction_code_label.setText(get_label_from_code(transaction_type))
                    self.transaction_code_label.setStyleSheet("color: yellow;")
                
                    # Fetch and display user info
                    cursor.execute(""" 
                        SELECT first_name, middle_name, last_name, id_number, photo, department 
                        FROM employees WHERE id_number = ? 
                    """, (employee_id,))
                    emp_info = cursor.fetchone()
                
                    if emp_info:
                        full_name = f"{emp_info[0]} {emp_info[1]} {emp_info[2]}"
                        id_number = emp_info[3]
                        photo_path = emp_info[4]
                        department = emp_info[5]
                        current_time = time.strftime("%H:%M | %Y-%m-%d")
                
                        self.user_name_label.setText(full_name)
                        self.id_number_label.setText(f"ID: {id_number}")
                        self.department_label.setText(f"{department}")
                        self.timestamp_label.setText(f"{current_time}")
                
                        if photo_path:
                            pixmap = QPixmap()
                            pixmap.loadFromData(photo_path)
                            if not pixmap.isNull():
                                self.photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio))
                            else:
                                self.photo_label.setText("Photo failed to load")
                        else:
                            self.photo_label.setText("Photo not found")

                else:
                    if not self.can_accept_denied_scan:
                        return # Skip processing if cooldown is active
                    
                    # UNAUTHORIZED: No repeated scan logic
                    cursor.execute(""" 
                        SELECT transaction_code FROM denied_usr 
                        WHERE rfid_tag = ? ORDER BY attempt_time DESC LIMIT 1 
                    """, (rfid_str,))
                    last_denied = cursor.fetchone()

                    #if last_denied:
                    new_transaction_code = 'O' if last_denied and last_denied[0] == 'I' else 'I'
                    
                    # capture the denied photo and get its path
                    photo_path = self.capture_denied_photo(new_transaction_code)
                    
                    # Convert image to binary (BLOB)
                    with open(photo_path, 'rb') as file:
                        photo_blob = file.read()
                    
                    # Insert into denied_usr with photo_blob
                    cursor.execute(""" 
                        INSERT INTO denied_usr (rfid_tag, transaction_code, photo, attempt_time) 
                        VALUES (?, ?, ?, ?) 
                    """, (rfid_str, new_transaction_code, photo_blob, current_time))

                    self.message_label.setText("ACCESS DENIED")
                    self.message_label.setFont(QFont("Helvetica", 15, QFont.Bold))
                    self.message_label.setFixedHeight(50)
                    self.message_label.setStyleSheet("background-color: red; color: black;")
                    self.transaction_code_label.setText(get_label_from_code(new_transaction_code))
                    self.transaction_code_label.setStyleSheet("color: red;")
                    
                    # Prevent immediate next scan
                    self.can_accept_denied_scan = False
                    QTimer.singleShot(2000, lambda: setattr(self, 'can_accept_denied_scan', True))	# Wait 2 seconds before allowing next scan

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