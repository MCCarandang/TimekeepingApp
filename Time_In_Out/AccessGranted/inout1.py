# This code implements Time in and Time Out for Access Granted
# This code is working properly

import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt, QTimer, QDateTime
import sys

class access_granted(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Timekeeping")
        self.showFullScreen()	# Launch in full screen
        
        # Set background color to black
        palette = QPalette()
        palette.setColor(QPalette.Window, QColor(Qt.black))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
        
        # Create a label for date and time
        self.date_time_label = QLabel(self)
        self.date_time_label.setStyleSheet("color: yellow; font-size: 20px;")
        self.date_time_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        
        # Label for Access Granted
        self.access_granted_label = QLabel("TAP YOUR RFID TAG", self)
        self.access_granted_label.setStyleSheet("color: yellow; font-size: 40px;")
        self.access_granted_label.setAlignment(Qt.AlignCenter)
        
        # Create a central widget and layout
        central_widget = QWidget(self)
        grid_layout = QGridLayout()
        
        # Adjust Spacing
        grid_layout.setContentsMargins(20, 20, 20, 20)
        grid_layout.setRowStretch(0, 1)
        grid_layout.setRowStretch(1, 2)
        grid_layout.setRowStretch(2, 1)
        # Add the date and time label to the top-right (row 0, column 1)
        grid_layout.addWidget(self.date_time_label, 0, 1, alignment=Qt.AlignRight | Qt.AlignTop)
        
        grid_layout.addWidget(self.access_granted_label, 1, 0, 1, 2, alignment=Qt.AlignCenter)
        
        central_widget.setLayout(grid_layout)
        self.setCentralWidget(central_widget)
        
        # Set up a timer to update the date and time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_date_time)
        self.timer.start(1000)	# Update every second
        self.update_date_time()
        
        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.check_rfid)
        self.rfid_timer.start(500)	# Check for RFID every 0.5 seconds
        
        # RFID reader
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
                conn = sqlite3.connect('/home/raspberrypi/Desktop/TimekeepingApp/timekeeping_app.db')
                cursor = conn.cursor()
            
                # Check if the scanned RFID is in the emp_profiles table
                cursor.execute("SELECT * FROM emp_profiles WHERE rfid_id = ?", (rfid_str,))
                result = cursor.fetchone()

                if result:
                    emp_id = result[0]
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

                    # Check the last IN record (with no time_out yet)
                    cursor.execute("""
                        SELECT time_in FROM attd_logs
                        WHERE emp_id = ? AND status = 'IN' AND time_out IS NULL
                        ORDER BY created_at DESC LIMIT 1
                    """, (emp_id,))
                    last_in = cursor.fetchone()

                    if last_in:
                        # Check if 3 minutes have passed since time_in
                        last_in_time = time.strptime(last_in[0], "%Y-%m-%d %H:%M:%S")
                        now = time.localtime()
                        diff = time.mktime(now) - time.mktime(last_in_time)

                        if diff >= 180:  # 3 minutes = 180 seconds
                            # Allow TIME OUT
                            cursor.execute("""
                                UPDATE attd_logs
                                SET time_out = ?, status = 'OUT'
                                WHERE emp_id = ? AND status = 'IN' AND time_out IS NULL
                            """, (current_time, emp_id))
                            self.access_granted_label.setText("TIME OUT")
                        else:
                            # Too early to TIME OUT
                            self.access_granted_label.setText("ALREADY TIMED IN")
                    else:
                        # No active IN, so allow TIME IN
                        cursor.execute("""
                            INSERT INTO attd_logs (emp_id, time_in, status, created_at)
                            VALUES (?, ?, 'IN', ?)
                        """, (emp_id, current_time, current_time))
                        self.access_granted_label.setText("TIME IN")
            
                else:
                    # Access Denied: Log to unauth_logs
                    attempt_time = time.strftime("%Y-%m-%d %H:%M:%S")
                    status = "Access Denied"
                    attempt_details = "RFID not found in emp_profiles"
                    photo = "none"

                    cursor.execute("""
                        INSERT INTO unauth_logs (rfid_id, attempt_time, status, attempt_details, photo)
                        VALUES (?, ?, ?, ?, ?)
                    """, (rfid_str, attempt_time, status, attempt_details, photo))
                    self.access_granted_label.setText("ACCESS DENIED")

                conn.commit()
                conn.close()
        
            # Reset label after 3 seconds
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
