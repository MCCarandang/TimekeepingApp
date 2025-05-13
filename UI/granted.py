import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QPalette
from PyQt5.QtCore import Qt, QTimer, QDateTime


class AttendanceScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance System")
        self.setGeometry(100, 100, 1080, 768)
        self.setStyleSheet("background-color: #3057f2;")  # Blue background
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Top bar: Status and Date/Time
        top_bar = QHBoxLayout()
        status_label = QLabel("IN")
        status_label.setStyleSheet("color: #fefae0;")
        status_label.setFont(QFont("Arial", 64, QFont.Bold))
        top_bar.addWidget(status_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("color: white;")
        self.datetime_label.setFont(QFont("Arial", 16))
        self.datetime_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)
        top_bar.addWidget(self.datetime_label, alignment=Qt.AlignRight)

        main_layout.addLayout(top_bar)

        # Access status banner
        banner = QLabel("Access Granted")
        banner.setStyleSheet("background-color: yellow; color: black;")
        banner.setFont(QFont("Arial", 24))
        banner.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(banner)

        # Employee details section
        info_container = QHBoxLayout()
        info_container.setContentsMargins(50, 30, 50, 30)
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #fff176;")  # Light yellow
        info_layout = QHBoxLayout()
        info_widget.setLayout(info_layout)

        # Photo
        photo_label = QLabel()
        pixmap = QPixmap("/mnt/data/Desktop - 1.jpg").scaled(180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        photo_label.setPixmap(pixmap)
        photo_label.setFixedSize(180, 180)
        photo_label.setStyleSheet("background-color: lightgray;")
        info_layout.addWidget(photo_label)

        # Text Info
        text_info = QVBoxLayout()
        name = QLabel("MARIANE C. CARANDANG")
        emp_id = QLabel("EMP0001")
        dept = QLabel("IT DEPARTMENT")
        timestamp = QLabel(QDateTime.currentDateTime().toString("yyyy-MM-dd HH:mm:ss"))

        for label in [name, emp_id, dept, timestamp]:
            label.setFont(QFont("Arial", 20))
            text_info.addWidget(label)

        info_layout.addLayout(text_info)
        info_container.addWidget(info_widget)
        main_layout.addLayout(info_container)

        # Spacer
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Exit button
        exit_btn = QPushButton("Exit")
        exit_btn.setFixedSize(100, 40)
        exit_btn.setStyleSheet("background-color: lightgray; font-size: 18px;")
        exit_btn.clicked.connect(self.close)
        main_layout.addWidget(exit_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        self.setLayout(main_layout)

    def update_time(self):
        current_time = QDateTime.currentDateTime().toString("MM-dd-yyyy\nhh:mm:ss")
        self.datetime_label.setText(current_time)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AttendanceScreen()
    window.showFullScreen()
    sys.exit(app.exec_())
