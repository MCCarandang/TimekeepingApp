import cv2
import numpy as np
import time
from ultralytics import YOLO
from pathlib import Path
from picamera2 import Picamera2
import utils
from utils import create_output_dir, get_timestamp, crop_image, draw_bbox, save_metadata

# === Paths ===
MODEL_PATH = "/home/raspberrypi/Desktop/TimekeepingApp/best.pt"
CAPTURE_DIR = "/home/raspberrypi/Desktop/TimekeepingApp/outputs/captures"
CSV_PATH = "/home/raspberrypi/Desktop/TimekeepingApp/outputs/metadata.csv"

# === Initialize ===
create_output_dir = (CAPTURE_DIR)
model = YOLO(MODEL_PATH)

LABEL = "ID Card"
RESOLUTION = (320, 240)

# === Start Picamera2 ===
picam2 = Picamera2()
picam2.preview_configuration.main.size = RESOLUTION
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(0.5)

# Create resizable window with safe size
cv2.namedWindow("ID Detection", cv2.WINDOW_NORMAL)
cv2.setWindowProperty("ID Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
cv2.resizeWindow("ID Detection", RESOLUTION[0], RESOLUTION[1])

while True:
    frame = picam2.capture_array()
    if frame is None:
        print("[ERROR] Failed to capture image from camera.")
        break

    frame = cv2.flip(frame, 0)
    if frame.shape[2] == 4:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BRG)
    
    results = model(frame, verbose=False)[0]
    frame_h, frame_w = frame.shape[:2]
    
    for det in results.boxes:
        class_id = int(det.cls[0].item())
        if class_id != 0:
            continue
            
        x1, y1, x2, y2 = map(int, det.xyxy[0].tolist())

        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(frame_w - 1, x2)
        y2 = min(frame_h - 1, y2)

        if x2 > x1 and y2 > y1:
            box = [x1, y1, x2, y2]
            draw_bbox(frame, box, label=LABEL)
            cropped = crop_image(frame, box)

            if cropped is not None and cropped.size > 0:
                _, timestamp = get_timestamp()
                filename = f"{timestamp}.jpg"
                filepath = Path(CAPTURE_DIR) / filename
                cv2.imwrite(str(filepath), cropped)

                # Save metadata
                save_metadata(CSV_PATH, {
                    "filename": filename,
                    "timestamp": timestamp,
                    "x1": x1, "y1": y1, "x2": x2, "y2": y2
                })
            else:
                print("[WARNING] Cropped image is empty or invalid, skipping save.")
        else:
            print(f"[WARNING] Invalid bounding box: x1={x1}, y1={y1}, x2={x2}, y2={y2}. Skipping crop.")

    
    cv2.imshow("ID Detection", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cv2.destroyAllWindows()