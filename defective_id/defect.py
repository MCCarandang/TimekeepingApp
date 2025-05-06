import cv2
from picamera import PiCamera
import datetime
import sqlite3
import os
import sys 

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