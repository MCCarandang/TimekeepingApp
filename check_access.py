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
        
        # Initialize the date and time display
        self.update_date_time()
        
    def update_date_time(self):
        current_time = QDateTime.currentDateTime()
        date_str = current_time.toString("MM-dd-yyyy")
        time_str = current_time.toString("HH:mm:ss")
        self.date_time_label.setText(f"<div>{date_str}</div><div>{time_str}</div>")

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = access_granted()
    window.show()
    sys.exit(app.exec_())