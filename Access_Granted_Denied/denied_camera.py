# Camera Preview Working
# Can capture photo when access denied taps for time in and time out
# Captured photo is not yet connected to the database

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
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QSizePolicy
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
        self.message_label = QLabel("TAP YOUR RFID TAG")
        self.user_name_label = QLabel("")
        self.id_number_label = QLabel("")
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
        self.user_name_label.setStyleSheet("color: gray;")
        self.user_name_label.setAlignment(Qt.AlignCenter)

        self.id_number_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.id_number_label.setStyleSheet("color: yellow;")
        self.id_number_label.setAlignment(Qt.AlignCenter)

        self.photo_label.setAlignment(Qt.AlignCenter)
        self.photo_label.setMaximumHeight(150)
        
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(180, 180)
        self.camera_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.exit_button = QPushButton("Exit")
        self.exit_button.setFixedSize(60, 30)
        self.exit_button.setStyleSheet("background-color: white;")
        self.exit_button.clicked.connect(QApplication.quit)

        # Group user info (VBox)
        user_info_group = QVBoxLayout()
        user_info_group.addWidget(self.user_name_label)
        user_info_group.addWidget(self.id_number_label)
        user_info_group.addWidget(self.photo_label)
        user_info_widget = QWidget()
        user_info_widget.setLayout(user_info_group)
        
        # Horizontal layout: camera | user info | exit button
        camera_info_layout = QHBoxLayout()
        camera_info_layout.addWidget(self.camera_label, alignment=Qt.AlignLeft)
        camera_info_layout.setSpacing(100)
        camera_info_layout.addWidget(user_info_widget, alignment=Qt.AlignCenter)
        camera_info_layout.addStretch()
        camera_info_layout.addWidget(self.exit_button, alignment=Qt.AlignRight | Qt.AlignBottom)
        
        # Final vertical layout for the label group
        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(0, 5, 0, 5)
        label_layout.setSpacing(10)
        label_layout.addWidget(self.date_time_label)
        label_layout.addWidget(self.transaction_code_label)
        label_layout.setSpacing()
        label_layout.addWidget(self.message_label)
        label_layout.addLayout(camera_info_layout)
        
        # Central widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.label_group)
        
        self.setCentralWidget(central_widget)

        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()

        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.check_rfid)
        self.rfid_timer.start(500)
        
        self.camera_preview_timer = QTimer()
        self.camera_preview_timer.timeout.connect(self.update_camera_preview)
        self.camera_preview_timer.start(300)

        # RFID Setup
        GPIO.setwarnings(False)
        self.reader = SimpleMFRC522()
        
        # State
        self.current_state = "IN"
        
        self.camera = PiCamera()
        self.camera.resolution = (180, 180)
        self.camera.rotation = 180
        self.setGeometry(0, 0, QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height())
        #self.camera.start_preview(fullscreen=False, window=(0, 900, 180, 180))

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
        
    def update_camera_preview(self):
        try:
            stream = io.BytesIO()
            self.camera.capture(stream, format='jpeg')
            stream.seek(0)
            image = Image.open(stream)
            
            # Resize to 180x180
            image = image.resize((180,180))
            
            #Convert to RGB and then to QImage
            image = image.convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)
            
            # Set preview
            pixmap = QPixmap.fromImage(qimage)
            self.camera_label.setPixmap(pixmap)
            
        except Exception as e:
            print(f"Camera update error: {e}")
        
    def closeEvent(self, event):
        self.camera.stop_preview()
        self.camera.close()
        event.accept()

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

            # Stop preview updates for 2 seconds
            self.camera_preview_timer.stop()
            QTimer.singleShot(2000, self.resume_camera_preview)

        except Exception as e:
            print(f"Failed to capture denied photo: {e}")

    def resume_camera_preview(self):
        self.camera_preview_timer.start(300)
        
    def check_rfid(self):
        try:
            id, _ = self.reader.read_no_block()

            if id:
                rfid_str = str(id)
                print(f"Scanned RFID: {rfid_str}")
                
                # Handles the RFID Tag that triggers only the IN and OUT
                if rfid_str in SPECIAL_RFID_TAGS:
                    self.handle_special_tag()
                    # QTimer.singleShot(3000, self.reset_ui)
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
                            pixmap.loadFromData(photo_path)
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

                    #if last_denied:
                    new_transaction_code = 'O' if last_denied and last_denied[0] == 'I' else 'I'
                        
                    cursor.execute(""" 
                        INSERT INTO denied_usr (rfid_tag, transaction_code, attempt_time) 
                        VALUES (?, ?, ?) 
                    """, (rfid_str, new_transaction_code, current_time))

                    self.message_label.setText("ACCESS DENIED")
                    self.transaction_code_label.setText(get_label_from_code(new_transaction_code))
                    self.capture_denied_photo(new_transaction_code)

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