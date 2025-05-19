import cv2
import time
import os
from datetime import datetime
import sqlite3
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
import sys

# Setup for tap tracking
tap_times = []
photo_timeout_seconds = 3  # RFID response wait threshold in seconds

# Folder to save captured photos
SAVE_DIR = "/home/Desktop/Timekeeping/id_timeout_photos"
os.makedirs(SAVE_DIR, exist_ok=True)

# Path to your SQLite database
DB_PATH = "/home/Desktop/Timekeeping/your_database.db"

# Global reference to prevent garbage collection of timer callback
timer_reference = None

last_rfid_time = None
rfid_timeout_threshold = 3  # seconds (match photo_timeout_seconds)

# Function to handle tap registration
def register_tap(camera, label):
    global tap_times, timer_reference
    now = time.time()
    tap_times = [t for t in tap_times if now - t < 5]  # Keep only taps from the last 5 seconds
    tap_times.append(now)

    # If 3 taps in 5 seconds, trigger response wait
    if len(tap_times) >= 3:
        print("Detected 3 rapid taps. Waiting for RFID response...")
        # Wait before checking if RFID responded
        timer_reference = QTimer()
        timer_reference.setSingleShot(True)
        timer_reference.timeout.connect(lambda: check_rfid_timeout(camera, label))
        timer_reference.start(photo_timeout_seconds * 1000)

# Check if RFID responded within the timeout threshold
def rfid_responded_recently():
    global last_rfid_time
    if last_rfid_time is None:
        return False
    return (time.time() - last_rfid_time) <= rfid_timeout_threshold

# Check if RFID failed to respond, then capture photo
def check_rfid_timeout(camera, label):
    if not rfid_responded_recently():
        print("RFID did not respond. Capturing photo...")
        ret, frame = camera.read()
        if ret:
            capture_and_process_id(frame, label)

# Save and show captured photo
def capture_and_process_id(frame, label):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    filename = f"id_timeout_{timestamp.replace(':', '_').replace(' ', '_')}.jpg"
    photo_path = os.path.join(SAVE_DIR, filename)

    # Save image
    cv2.imwrite(photo_path, frame)
    print(f"[INFO] Photo saved to {photo_path}")

    # Display on QLabel
    if label:
        show_image_on_label(frame, label)

    # Save to DB
    save_photo_record(photo_path, timestamp)

# Display captured image in PyQt QLabel (180x180)
def show_image_on_label(frame, label):
    image = QImage(frame.data, frame.shape[1], frame.shape[0], frame.strides[0], QImage.Format_BGR888)
    pixmap = QPixmap.fromImage(image).scaled(180, 180)
    label.setPixmap(pixmap)

# Insert photo info into database
def save_photo_record(photo_path, timestamp):
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO def_ids (photo_path, capture_time) VALUES (?, ?)", (photo_path, timestamp))
        conn.commit()
        conn.close()
        print("[INFO] Photo record saved to database.")
    except Exception as e:
        print(f"[ERROR] Failed to save photo record: {e}")

def on_rfid_read(tag_id):
    global last_rfid_time
    print(f"[RFID] Tag read: {tag_id}")
    last_rfid_time = time.time()
    # Your existing logic to handle authorized/unauthorized access

if __name__ == "__main__":
    # Initialize camera
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("[ERROR] Cannot open camera.")
        exit()

    label = None  # Replace with actual QLabel if running inside PyQt app

    # Simulate 3 taps
    for i in range(3):
        print(f"Simulating tap {i+1}")
        register_tap(camera, label)
        time.sleep(1)  # Tap every second

    # Optionally simulate RFID read (comment this out to test timeout behavior)
    # time.sleep(2)
    # on_rfid_read("123456")

    # Keep script running to allow QTimer to fire
    print("[INFO] Waiting for RFID timeout check...")

    app = QApplication(sys.argv)
    QTimer.singleShot(5000, app.quit)  # Quit app after 5 seconds
    sys.exit(app.exec_())
