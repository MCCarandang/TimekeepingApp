# scripts/utils.py

import cv2
import time
from pathlib import Path
import csv

def create_output_dir(path):
    """Create directory if it doesn't exist."""
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_timestamp():
    """Return current timestamp as int and formatted string."""
    ts = int(time.time())
    formatted = time.strftime("%Y-%m-%d_%H-%M-%S")
    return ts, formatted

def crop_image(img, box):
    """Crop image using YOLO xyxy box [x1, y1, x2, y2]."""
    x1, y1, x2, y2 = map(int, box)
    return img[y1:y2, x1:x2]

def draw_bbox(img, box, label="ID Card", color=(0, 255, 0), thickness=2):
    """Draw bounding box with label."""
    x1, y1, x2, y2 = map(int, box)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def save_metadata(csv_path, data):
    """Append metadata to CSV."""
    fieldnames = ["filename", "timestamp", "confidence", "x1", "y1", "x2", "y2"]
    file_exists = Path(csv_path).exists()
    
    with open(csv_path, "a", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)

