import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QVBoxLayout
from PyQt5.QtGui import QPalette, QColor, QFont
from PyQt5.QtCore import Qt, QTimer, QDateTime
import sys

app = QApplication([])

class ColoredWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(244, 244, 244)) #Dark blue color
        self.setPalette(palette)

class AttendanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Timekeeping")
        self.showFullScreen()	# Launch in full screen

        # Create a colored central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #Apply a style sheet to set the background color for both central widget and main window
        self.setStyleSheet("background-color: navy;")
        central_widget.setStyleSheet("background-color: navy;")

        # Create a layout for date and time labels
        date_time_layout = QVBoxLayout()

        # Create the date label and add time lables
        self.date_label = QLabel()
        date_time_layout.addWidget(self.date_label)
        
        self.time_label = QLabel()
        date_time_layout.addWidget(self.time_label)

        # Create a horizontal layout for user info such as name, id number(rfid_tag), and photo
        user_info_layout = QVBoxLayout()

        named_id_layout = QVBoxLayout()

        self.user_name_label = QLabel("")

        self.id_number_label = QLabel("")

        

        



    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.showNormal()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    attendance_window = AttendanceWindow()
    attendance_window.show()
    sys.exit(app.exec_())