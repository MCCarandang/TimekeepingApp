import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QDateTime
import sys

class access_granted(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timekeeping")
        self.showFullScreen()
        
        # Set background color to black
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(Qt.black))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        
        # Date & time label
        self.date_time_label = QLabel(self)
        self.date_time_label.setStyleSheet("color: yellow; font-size: 20px;")
        self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # Access message label
        self.access_granted_label = QLabel("TAP YOUR RFID TAG", self)
        self.access_granted_label.setStyleSheet("color: yellow; font-size: 40px;")
        self.access_granted_label.setAlignment(Qt.AlignCenter)
        
        # Layout setup
        central_widget = QWidget(self)
        grid_layout = QGridLayout()
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 2)
        grid_layout.setRowStretch(2, 1)

        grid_layout.addWidget(self.date_time_label, 0, 1, alignment=Qt.AlignRight | Qt.AlignTop)
        grid_layout.addWidget(self.access_granted_label, 1, 0, 1, 2, alignment=Qt.AlignCenter)
        
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)
        
        # Timers
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)
        self.update_date_time()
        
        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.check_rfid)
        self.rfid_timer.start(500)
        
        GPIO.setwarnings(False)
        self.reader = SimpleMFRC522()

    def update_date_time(self):
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("MM-dd-yyyy")
        time_str = current_time.toString("HH:mm:ss")
        self.date_time_label.setText(f"<div>{date_str}</div><div>{time_str}</div>")

    def check_rfid(self):
        try:
            id, text = self.reader.read_no_block()

            if id:
                rfid_str = str(id)
                conn = sqlite3.connect('/home/raspberrypi/Desktop/Timekeeping/timekeepingapp.db')
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM employees WHERE rfid_tag = ?", (rfid_str,))
                result = cursor.fetchone()

                if result:
                    self.access_granted_label.setText("ACCESS GRANTED")
                    # You can add attendance logging here if needed
                else:
                    # Log unauthorized access
                    attempt_time = time.strftime("%Y-%m-%d %H:%M:%S")

                    cursor.execute("""
                        INSERT INTO denied_usr (rfid_tag, attempt_time)
                        VALUES (?, ?)
                    """, (rfid_str, attempt_time))
                    conn.commit()

                    self.access_granted_label.setText("ACCESS DENIED")

                conn.close()

                QTimer.singleShot(3000, lambda: self.access_granted_label.setText("TAP YOUR RFID TAG"))

        except Exception as e:
            print(f"Error reading RFID: {e}")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = access_granted()
    window.show()
    sys.exit(app.exec_())
