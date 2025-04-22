import sys
import time
import os
import sqlite3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QDateTime


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
        self.access_granted_label = QLabel("TAP YOUR RFID TAG")
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

        self.access_granted_label.setFont(QFont("Helvetica", 45, QFont.Bold))
        self.access_granted_label.setStyleSheet("color: white;")
        self.access_granted_label.setAlignment(Qt.AlignCenter)

        self.user_name_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.user_name_label.setStyleSheet("color: gray;")
        self.user_name_label.setAlignment(Qt.AlignCenter)

        self.id_number_label.setFont(QFont("Helvetica", 15, QFont.Bold))
        self.id_number_label.setStyleSheet("color: yellow;")
        self.id_number_label.setAlignment(Qt.AlignCenter)

        self.photo_label.setAlignment(Qt.AlignCenter)

        # Create layout and add Widgets
        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(15, 15, 15, 15)
        label_layout.addWidget(self.date_time_label)
        label_layout.addWidget(self.transaction_code_label)
        label_layout.addWidget(self.access_granted_label)

        # Create a vertical layout for the user's name and ID number
        name_id_layout = QVBoxLayout()
        # Add user name and ID number labels to the name_id_layout
        name_id_layout.addWidget(self.user_name_label)
        name_id_layout.addWidget(self.id_number_label)

        # Add the name_id_layout after the access_granted_label
        label_layout.addLayout(name_id_layout)

        # Create a horizontal layout for user info such as Name, ID number, and photo
        user_info_layout = QVBoxLayout()
        # Add the photo_label to the user_info_layout
        user_info_layout.addWidget(self.photo_label)

        # Create a widget for user info and add the user_info_layout
        self.user_info_widget = QWidget()
        self.user_info_widget.setLayout(user_info_layout)

        # Create a central widget to hold both the labels and user info widget
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
        main_layout.addWidget(self.label_group)
        main_layout.addWidget(self.user_info_widget)

        # Set the central widget
        self.setCentralWidget(central_widget)

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

    def update_date_time(self):
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("MM-dd-yyyy")
        time_str = current_time.toString("HH:mm:ss")
        self.date_time_label.setText(f"{date_str}\n{time_str}")
        
    def reset_ui(self):
        self.access_granted_label.setText("TAP YOUR RFID TAG")
        self.transaction_code_label.setText("IN")
        self.user_name_label.setText("")
        self.id_number_label.setText("")
        self.photo_label.clear()

    def check_rfid(self):
        try:
            id, _ = self.reader.read_no_block()
    
            if id:
                rfid_str = str(id)
                conn = sqlite3.connect('/home/raspberrypi/Desktop/Timekeeping/timekeepingapp.db')
                cursor = conn.cursor()
    
                cursor.execute("SELECT id FROM employees WHERE rfid_tag = ?", (rfid_str,))
                result = cursor.fetchone()
    
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    
                if result:
                    employee_id = result[0]
    
                    # Check if the user is already timed in without timeout
                    cursor.execute(""" 
                        SELECT time_in FROM attd_logs 
                        WHERE employee_id = ? AND transaction_code = 'IN' AND time_out IS NULL 
                        ORDER BY transaction_time DESC LIMIT 1 
                    """, (employee_id,))
                    last_in = cursor.fetchone()
    
                    if last_in:
                        # Check if 3 mins have passed
                        last_in_time = time.strptime(last_in[0], "%Y-%m-%d %H:%M:%S")
                        now = time.localtime()
                        diff = time.mktime(now) - time.mktime(last_in_time)
    
                        if diff >= 180:
                            cursor.execute(""" 
                                UPDATE attd_logs 
                                SET time_out = ?, status = 'OUT' 
                                WHERE employee_id = ? AND transaction_code = 'IN' AND time_out IS NULL 
                            """, (current_time, employee_id))
                            self.access_granted_label.setText("ACCESS GRANTED")
                            self.transaction_code_label.setText("OUT")
                        else:
                            self.access_granted_label.setText("ALREADY TIMED IN")
                            self.transaction_code_label.setText("IN")
                    else:
                        cursor.execute(""" 
                            INSERT INTO attd_logs (employee_id, time_in, transaction_code, transaction_time) 
                            VALUES (?, ?, 'IN', ?) 
                        """, (employee_id, current_time, current_time))
                        self.access_granted_label.setText("ACCESS GRANTED")
                        self.transaction_code_label.setText("IN")
    
                    # Fetch user info
                    cursor.execute(""" 
                        SELECT first_name, middle_name, last_name, rfid_tag, photo 
                        FROM employees WHERE id = ? 
                    """, (employee_id,))
                    emp_info = cursor.fetchone()
    
                    if emp_info:
                        full_name = f"{emp_info[0]} {emp_info[1]} {emp_info[2]}"
                        rfid_tag = emp_info[3]
                        photo_path = emp_info[4]
    
                        self.user_name_label.setText(full_name)
                        self.id_number_label.setText(f"ID: {rfid_tag}")
    
                        # Load and set user photo
                        if photo_path:
                            pixmap = QPixmap(photo_path)
                            if not pixmap.isNull():
                                self.photo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            else:
                                self.photo_label.setText("Photo not found")
    
                else:
                    # Denied Access - Check the last denied transaction for this RFID tag
                    cursor.execute(""" 
                        SELECT transaction_code FROM denied_usr 
                        WHERE rfid_tag = ? ORDER BY attempt_time DESC LIMIT 1 
                    """, (rfid_str,))
                    last_denied = cursor.fetchone()
    
                    if last_denied:
                        # Toggle between IN and OUT for denied access
                        new_transaction_code = 'OUT' if last_denied[0] == 'IN' else 'IN'
                        cursor.execute(""" 
                            UPDATE denied_usr 
                            SET transaction_code = ?, attempt_time = ? 
                            WHERE rfid_tag = ?
                        """, (new_transaction_code, current_time, rfid_str))
                    else:
                        # First denied attempt for this RFID tag
                        cursor.execute(""" 
                            INSERT INTO denied_usr (rfid_tag, transaction_code, attempt_time) 
                            VALUES (?, 'IN', ?) 
                        """, (rfid_str, current_time))
    
                    self.access_granted_label.setText("ACCESS DENIED")
                    self.transaction_code_label.setText("IN" if last_denied is None else new_transaction_code)
    
                conn.commit()
                conn.close()
    
                #QTimer.singleShot(3000, lambda: self.access_granted_label.setText("TAP YOUR RFID TAG"))
                #QTimer.singleShot(3000, lambda: self.transaction_code_label.setText("IN"))
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