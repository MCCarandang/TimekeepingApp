import sqlite3
import cv2
import os
import time
import numpy as np
from picamera.array import PiRGBArray
from datetime import datetime
from picamera import PiCamera

# Initialize PiCamera
camera = PiCamera()
camera.resolution = (640, 480)
camera.vflip = True
camera.hflip = True
raw_capture = PiRGBArray(camera, size=(640, 480))
time.sleep(0.1)

# Directory to save captured photos
save_dir = "/home/raspberrypi/Desktop/Timekeeping/defective_ids"
os.makedirs(save_dir, exist_ok=True)

# Connect to SQLite database
conn = sqlite3.connect('/home/raspberrypi/Desktop/TimekeepingApp/timekeepingapp.db')
cursor = conn.cursor()

# Dummy RFID tag (replace with real tag in integration)
rfid_tag = "1234567890"

def capture_and_process_frame():
    camera.capture(raw_capture, format="bgr")
    frame = raw_capture.array

    # Convert to grayscale and detect ID region
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 180, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            x, y, w, h = cv2.boundingRect(contour)
            cropped_id = frame[y:y+h, x:x+w]
            return cropped_id  # Return the cropped ID region

    return None  # No valid ID detected

def save_id_image(cropped_id, rfid_tag):
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{rfid_tag}_{timestamp}.jpg"
    file_path = os.path.join(save_dir, filename)

    # Save image to file
    cv2.imwrite(file_path, cropped_id)

    # Save to DB
    try:
        with open(file_path, 'rb') as f:
            img_blob = f.read()

        cursor.execute("""
            INSERT INTO def_ids (rfid_tag, photo, reported_time)
            VALUES (?, ?, ?)
        """, (rfid_tag, img_blob, time.strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()
    except Exception as e:
        print(f"[ERROR] Failed to save to database: {e}")

    return file_path

def display_in_lower_left(captured_img):
    # Create a black canvas
    screen = np.zeros((480, 640, 3), dtype=np.uint8)

    # Resize the captured image to 180x180
    resized = cv2.resize(captured_img, (180, 180))

    # Place it on the lower-left corner
    screen[480-180:480, 0:180] = resized

    # Display it
    cv2.imshow("Captured ID in Lower Left", screen)
    cv2.waitKey(3000)  # Show for 3 seconds
    cv2.destroyAllWindows()

# Main loop
print("Press 't' in the terminal to simulate ID tap. Press Ctrl+C to stop.")
try:
    while True:
        user_input = input("Tap (t): ").strip().lower()
        if user_input == 't':
            raw_capture.truncate(0)
            cropped = capture_and_process_frame()

            if cropped is not None:
                save_id_image(cropped, rfid_tag)
                display_in_lower_left(cropped)
            else:
                print("[INFO] No ID detected.")
except KeyboardInterrupt:
    print("\n[INFO] Exiting...")

# Clean up
conn.close()
