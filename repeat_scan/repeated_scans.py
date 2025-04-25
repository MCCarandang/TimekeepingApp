# Access Granted and Denied with Time IN and OUT 
# Added Repeated Scan feature for Access Granted

# Shows the photo of user pero hindi nakagitna yung user name and id number
# Nagkaroon ulit ng repeated action pag nag time out which is dapat wala na

import sys
import time
import os
import sqlite3
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QHBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QColor, QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, QDateTime, QByteArray, QBuffer

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

        self.photo_label.setAlignment(Qt.AlignLeft)

        # Create layout and add Widgets
        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(15, 15, 15, 15)
        label_layout.addWidget(self.date_time_label)
        label_layout.addWidget(self.transaction_code_label)
        label_layout.addWidget(self.message_label)
        
        # Second column (User name and ID number)
        name_id_layout = QVBoxLayout()
        name_id_layout.addWidget(self.user_name_label)
        name_id_layout.addWidget(self.id_number_label)
        name_id_layout.setAlignment(Qt.AlignCenter)

        # First column (Photo)
        photo_layout = QVBoxLayout()
        photo_layout.addStretch(1)
        photo_layout.addWidget(self.photo_label, alignment=Qt.AlignLeft | Qt.AlignBottom)

        # Combine both into a horizontal layout (two columns)
        user_info_layout = QHBoxLayout()
        user_info_layout.addLayout(photo_layout)
        user_info_layout.addStretch(1)
        user_info_layout.addLayout(name_id_layout)
        user_info_layout.addStretch(1)

        # Create a widget for user info and add the layout
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
        self.message_label.setText("TAP YOUR RFID TAG")
        self.transaction_code_label.setText("IN")
        self.user_name_label.setText("")
        self.id_number_label.setText("")
        self.photo_label.clear()

    def check_rfid(self):
        try:
            id, _ = self.reader.read_no_block()
            transaction_code = 'O'
            transaction_code = 'I'

            if id:
                rfid_str = str(id)
                conn = sqlite3.connect('/home/raspberrypi/Desktop/Timekeeping/timekeepingapp.db')
                cursor = conn.cursor()

                current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                # Check if RFID is authorized
                cursor.execute("SELECT id FROM employees WHERE rfid_tag = ?", (rfid_str,))
                result = cursor.fetchone()

                if result:
                    employee_id = result[0]

                    # Check for repeated scan within 3 seconds
                    cursor.execute("""
                        SELECT transaction_time FROM attd_logs
                        WHERE id_number = ?
                        ORDER BY transaction_time DESC LIMIT 1
                    """, (employee_id,))
                    last_log = cursor.fetchone()
                    
                    if last_log:
                        last_log_time = time.strptime(last_log[0], "%Y-%m-%d %H:%M:%S")
                        now = time.localtime()
                        diff = time.mktime(now) - time.mktime(last_log_time)
                        
                        if diff < 5:
                            self.message_label.setText("REPEATED SCAN")
                            self.transaction_code_label.setText("IN")
                            QTimer.singleShot(3000, self.reset_ui)
                            conn.close()
                            return
                            
                    else:
                        cursor.execute("""
                            INSERT INTO repeated_scans (rfid_tag, transaction_code, scan_time)
                            VALUES (?, 'I', ?)
                        """, (rfid_str, current_time))

                    # Now determine if it's a time in or time out
                    cursor.execute(""" 
                        SELECT transaction_code FROM attd_logs 
                        WHERE id_number = ?
                        ORDER BY transaction_time DESC LIMIT 1 
                    """, (employee_id,))
                    last_transaction = cursor.fetchone()

                    if last_transaction and last_transaction[0] == 'I':
                        # IF LAST IS TIME-IN, THIS IS TIME-OUT
                        cursor.execute(""" 
                            INSERT INTO attd_logs (id_number, rfid_tag, transaction_code, transaction_time)
                            VALUES (?, ?, 'O', ?) 
                        """, (employee_id, rfid_str, current_time))
                        self.message_label.setText("ACCESS GRANTED")
                        self.transaction_code_label.setText(get_label_from_code('O'))
                    else:
                        # IF LAST IS TIME-OUT, THIS IS TIME-IN
                        cursor.execute("""
                            INSERT INTO attd_logs (id_number, rfid_tag, transaction_code, transaction_time)
                            VALUES (?, ?, 'I', ?)
                        """, (employee_id, rfid_str, current_time))
                        self.message_label.setText("ACCESS GRANTED")
                        self.transaction_code_label.setText(get_label_from_code('I'))

                    # Display user info
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
                                # If the pixmap is valid, display it
                                self.photo_label.setPixmap(pixmap.scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                            else:
                                # If the image failed to load
                                self.photo_label.setText("Photo failed to load")
                        else:
                            # If there is no photo data in the database
                            self.photo_label.setText("Photo not found")

                else:
                    # UNAUTHORIZED: No repeated scan logic
                    cursor.execute(""" 
                        SELECT transaction_code FROM denied_usr 
                        WHERE rfid_tag = ? ORDER BY attempt_time DESC LIMIT 1 
                    """, (rfid_str,))
                    last_denied = cursor.fetchone()

                    if last_denied:
                        new_transaction_code = 'O' if last_denied[0] == 'I' else 'I'
                        cursor.execute(""" 
                            UPDATE denied_usr 
                            SET transaction_code = ?, attempt_time = ? 
                            WHERE rfid_tag = ?
                        """, (new_transaction_code, current_time, rfid_str))
                    else:
                        new_transaction_code = 'I'
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