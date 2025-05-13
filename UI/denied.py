import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QSpacerItem
)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime, QTimer


class AccessDeniedScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Access Denied - IN")
        self.setGeometry(100, 100, 1080, 768)
        self.setStyleSheet("background-color: #3057f2;")  # Blue background
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 30, 0, 30)

        # Top bar: "IN" on the left and datetime on the right
        top_bar = QHBoxLayout()
        
        in_label = QLabel("IN")
        in_label.setStyleSheet("color: #ff6b6b;")  # Red-like color
        in_label.setFont(QFont("Arial", 64, QFont.Bold))
        top_bar.addWidget(in_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("color: white;")
        self.datetime_label.setFont(QFont("Arial", 18))
        self.datetime_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        top_bar.addWidget(self.datetime_label, alignment=Qt.AlignRight)
        main_layout.addLayout(top_bar)

        # Access Denied Banner
        banner = QLabel("Access Denied")
        banner.setStyleSheet("background-color: #ff6b6b; color: black;")
        banner.setFont(QFont("Arial", 32))
        banner.setAlignment(Qt.AlignCenter)
        banner.setFixedHeight(70)
        main_layout.addWidget(banner)

        # Spacer for central empty space
        main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Exit Button
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
    window = AccessDeniedScreen()
    window.showFullScreen()
    sys.exit(app.exec_())
