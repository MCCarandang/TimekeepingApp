import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import os
from PyQt5.QtGui import QPixmap
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QDateTime
import sys


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
        
        # Create layout and add Widgets
        label_layout = QVBoxLayout(self.label_group)
        label_layout.setContentsMargins(15, 15, 15, 15)
        label_layout.addWidget(self.date_time_label)
        label_layout.addWidget(self.transaction_code_label)
        label_layout.addWidget(self.access_granted_label)
        label_layout.addStretch(1)

        central_widget = QWidget()
        central_widget.setLayout(label_layout)
        self.setCentralWidget(central_widget)

        # Create a horizontal layout for user info such as Name, ID number, and photo
        user_info_layout = QVBoxLayout()

        # Create a vertical layout for the user's name and ID number
        name_id_layout = QVBoxLayout()

        # Create the labels for user info
        self.user_name_label = QLabel("")
        self.id_number_label = QLabel("")

        # Set fonts and styles for user info
        font = QFont("Helvetica", 25, QFont.Bold)
        self.user_name_label.setFont(font)
        self.id_number_label.setFont(font)
        self.user_name_label.setStyleSheet("color: gray;")
        self.id_number_label.setStyleSheet("color: yellow;")

        # Add user name and ID number labels to the name_id_layout
        name_id_layout.addWidget(self.user_name_label)
        name_id_layout.addWidget(self.id_number_label)

        # Set alignment of user's name and ID number labels to center
        self.user_name_label.setAlignment(Qt.AlignCenter)
        self.id_number_label.setAlignment(Qt.AlignCenter)

        # Create the user's photo label
        self.photo_label = QLabel()

        # Add the name_id_layout and photo_label to the user_info_layout
        user_info_layout.addLayout(name_id_layout)
        user_info_layout.addWidget(self.photo_label)

        # Set alignment of user photo label to leftside of ID number and username
        self.photo_label.setAlignment(Qt.AlignCenter)

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

                    cursor.execute("""
                        SELECT time_in FROM attd_logs
                        WHERE employee_id = ? AND status = 'IN' AND time_out IS NULL
                        ORDER BY transaction_time DESC LIMIT 1
                    """, (employee_id,))
                    last_in = cursor.fetchone()

                    if last_in:
                        last_in_time = time.strptime(last_in[0], "%Y-%m-%d %H:%M:%S")
                        now = time.localtime()
                        diff = time.mktime(now) - time.mktime(last_in_time)

                        if diff >= 180:
                            cursor.execute("""
                                UPDATE attd_logs
                                SET time_out = ?, status = 'OUT'
                                WHERE employee_id = ? AND status = 'IN' AND time_out IS NULL
                            """, (current_time, employee_id))
                            self.access_granted_label.setText("ACCESS GRANTED")
                            self.transaction_code_label.setText("OUT")
                        else:
                            self.access_granted_label.setText("ALREADY TIMED IN")
                            self.transaction_code_label.setText("IN")
                    else:
                        cursor.execute("""
                            INSERT INTO attd_logs (employee_id, time_in, status, transaction_time)
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
                    attempt_time = current_time
                    cursor.execute("""
                        INSERT INTO denied_usr (rfid_tag, transaction_code, attempt_time)
                        VALUES (?, NULL, ?)
                    """, (rfid_str, attempt_time))
                    self.access_granted_label.setText("ACCESS DENIED")
                    self.transaction_code_label.setText("IN")

                conn.commit()
                conn.close()

                QTimer.singleShot(3000, lambda: self.access_granted_label.setText("TAP YOUR RFID TAG"))
                QTimer.singleShot(3000, lambda: self.transaction_code_label.setText("IN"))

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