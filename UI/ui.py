class AccessGrantedWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Attendance System")
        self.setGeometry(100, 100, 1080, 768)
        self.setStyleSheet("background-color: #3057f2;")  # Blue background
        self.current_state = "IN"

        # Main layout setup
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout()
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.central_widget.setLayout(self.main_layout)

        # Top bar
        top_bar = QHBoxLayout()
        self.transaction_code_label = QLabel(self.current_state)
        self.transaction_code_label.setStyleSheet("color: #fefae0;")
        self.transaction_code_label.setFont(QFont("Arial", 64, QFont.Bold))
        top_bar.addWidget(self.transaction_code_label, alignment=Qt.AlignLeft | Qt.AlignTop)

        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("color: white;")
        self.datetime_label.setFont(QFont("Arial", 16))
        self.datetime_label.setAlignment(Qt.AlignRight | Qt.AlignTop)
        top_bar.addWidget(self.datetime_label, alignment=Qt.AlignRight)

        self.main_layout.addLayout(top_bar)

        # Banner
        self.message_label = QLabel("TAP YOUR RFID TAG")
        self.message_label.setStyleSheet("background-color: yellow; color: black;")
        self.message_label.setFont(QFont("Arial", 24))
        self.message_label.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.message_label)

        # Info section
        info_container = QHBoxLayout()
        info_container.setContentsMargins(0, 0, 0, 30)
        info_widget = QWidget()
        info_widget.setStyleSheet("background-color: #fff176;")
        info_layout = QHBoxLayout()
        info_widget.setLayout(info_layout)

        # Camera preview
        self.camera_label = QLabel()
        self.camera_label.setFixedSize(180, 180)
        self.camera_label.setStyleSheet("background-color: lightgray;")
        info_layout.addWidget(self.camera_label)

        # User info
        self.user_name_label = QLabel()
        self.id_number_label = QLabel()
        self.department_label = QLabel()
        self.timestamp_label = QLabel()

        for label in [self.user_name_label, self.id_number_label, self.department_label, self.timestamp_label]:
            label.setFont(QFont("Arial", 20))

        text_info = QVBoxLayout()
        text_info.addWidget(self.user_name_label)
        text_info.addWidget(self.id_number_label)
        text_info.addWidget(self.department_label)
        text_info.addWidget(self.timestamp_label)

        info_layout.addLayout(text_info)
        info_container.addWidget(info_widget)
        self.main_layout.addLayout(info_container)

        # Spacer
        self.main_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Expanding, QSizePolicy.Expanding))

        # Exit Button
        exit_btn = QPushButton("Exit")
        exit_btn.setFixedSize(100, 40)
        exit_btn.setStyleSheet("background-color: lightgray; font-size: 18px;")
        exit_btn.clicked.connect(self.close)
        self.main_layout.addWidget(exit_btn, alignment=Qt.AlignRight | Qt.AlignBottom)

        # Set up timers
        self.update_time()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)

        # Setup camera and RFID
        self.setup_camera()
        self.setup_rfid()

    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.datetime_label.setText(current_time.toString("MM-dd-yyyy\nhh:mm:ss"))
        self.timestamp_label.setText(current_time.toString("yyyy-MM-dd HH:mm:ss"))

    def setup_camera(self):
        self.camera = PiCamera()
        self.camera.resolution = (180, 180)
        self.camera.rotation = 180
        self.camera_preview_timer = QTimer()
        self.camera_preview_timer.timeout.connect(self.update_camera_preview)
        self.camera_preview_timer.start(300)

    def update_camera_preview(self):
        try:
            stream = io.BytesIO()
            self.camera.capture(stream, format='jpeg')
            stream.seek(0)
            image = Image.open(stream).resize((180, 180)).convert("RGB")
            data = image.tobytes("raw", "RGB")
            qimage = QImage(data, image.width, image.height, QImage.Format_RGB888)
            self.camera_label.setPixmap(QPixmap.fromImage(qimage))
        except Exception as e:
            print(f"Camera update error: {e}")

    def setup_rfid(self):
        GPIO.setwarnings(False)
        self.reader = SimpleMFRC522()
        self.rfid_timer = QTimer(self)
        self.rfid_timer.timeout.connect(self.check_rfid)
        self.rfid_timer.start(500)

    def check_rfid(self):
        # Keep your RFID logic here or call self.handle_rfid_scan(...)
        pass

    def closeEvent(self, event):
        self.camera.close()
        event.accept()
