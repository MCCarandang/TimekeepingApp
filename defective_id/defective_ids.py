import cv2
import time
import os
from datetime import datetime
from mfrc522 import SimpleMFRC522
import RPi.GPIO as GPIO

# Setup
reader = SimpleMFRC522()
camera = cv2.VideoCapture(0)
DETECTION_TIMEOUT = 5  # seconds
SAVE_PATH = "/home/pi/defective_ids"
os.makedirs(SAVE_PATH, exist_ok=True)

def detect_id_card(frame):
    """Use OpenCV to detect possible ID card based on contour size."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 5000 < area < 30000:  # Adjust depending on actual card size
            return True
    return False

def capture_photo_and_log(frame):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    img_path = os.path.join(SAVE_PATH, f'defective_id_{timestamp}.jpg')
    log_path = os.path.join(SAVE_PATH, 'defective_log.txt')

    cv2.imwrite(img_path, frame)
    with open(log_path, 'a') as f:
        f.write(f'{timestamp} - Defective ID detected. Photo saved at: {img_path}\n')
    print(f'[!] Defective ID logged and photo saved: {img_path}')

def wait_for_rfid(timeout):
    """Try to read RFID UID within the timeout. Return UID or None."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            id, _ = reader.read_no_block()
            if id:
                return id
        except Exception as e:
            pass
        time.sleep(0.1)
    return None

try:
    print("[INFO] Starting defective ID detection system...")
    while True:
        ret, frame = camera.read()
        if not ret:
            continue

        id_visible = detect_id_card(frame)

        if id_visible:
            print("[INFO] ID card detected visually. Checking RFID...")
            uid = wait_for_rfid(DETECTION_TIMEOUT)
            if uid:
                print(f"[OK] RFID read successfully: UID={uid}")
            else:
                print("[WARNING] No RFID detected. Marking as defective...")
                capture_photo_and_log(frame)
                time.sleep(2)  # Pause to prevent duplicate logging
        else:
            print("[INFO] No ID visible.")
        
        time.sleep(0.5)  # Adjust for responsiveness

except KeyboardInterrupt:
    print("[INFO] Stopping system...")

finally:
    GPIO.cleanup()
    camera.release()
    cv2.destroyAllWindows()