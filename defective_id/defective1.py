import sqlite3
import cv2
import os
import time
import numpy as np
from picamera.array import PiRGBArray
from datetime import datetime
from picamera import PiCamera

camera = PiCamera()
camera.resolution = (180, 180)
camera.vflip = True
camera.hflip = True

# Ensure 'defective_ids' directory exists inside 'Timekeeping'
save_dir = "/home/raspberrypi/Desktop/Timekeeping/defective_ids"
os.makedirs(save_dir, exist_ok=True)

# Create a coonnection to the database
conn = sqlite3.connect('/home/raspberrypi/Desktop/TimekeepingApp/timekeepingapp.db')
cursor = conn.cursor()

def detect_id(frame):
    # Convert frame to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Apply threshold for ID detection
    _, thresh = cv2.threshold(gray, 0, 180, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours of ID
    contours,_ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Loop through contours for ID detection
    for contour in contours:
        area = cv2.contourArea(contour)
        x, y, w, h = cv2.boundingRect(contour)

        # Check if contour has sufficient size for ID
        if area > 1000:
            # Draw rectangle around contour
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 180, 0), 2)

            # Check if user tapped their ID on picamera
            if cv2.waitKey(1) & 0xFF == ord("t"):
                
                # Capture Id
                capture_id(frame, x, y, w, h)
                break

def capture_id(frame, x, y, w, h, rfid_tag):
    # Crop the detected ID region
    cropped_id = frame[y:y+h, x:x+w]

    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{rfid_tag}_{timestamp}.jpg"
    file_path = os.path.join(save_dir, filename)

    # Save the image to disk
    cv2.imwrite(file_path, cropped_id)

    current_time = time.strftime("%Y-%m-%d %H:%M:%S")

    # Convert image to binary (BLOB)
    with open(file_path, 'rb') as f:
        img_blob = f.read()

    # Save to SQLite database
    try:
        # Insert into database with current timestamp
        cursor.execute("""
            INSERT INTO def_ids (rfid_tag, photo, reported_time)
            VALUES (?, ?, ?)
        """, (rfid_tag, img_blob, current_time))

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[ERROR] Failed to save to database: {e}")

# Main Loop
while True:
    # Capture frame from picamera
    camera.capture('temp.jpg')
    frame = cv2.imread('temp.jpg')

    # Detect ID in frame
    detect_id(frame)

    # Display frame
    cv2.imshow("Frame", frame)

    # Move the window to the lower left side of the screen
    cv2.moveWindow("Frame", 0, 290)  # Adjust the y-coordinate ad needed

    # Check if user pressed 'q' to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
camera.close()
conn.close()