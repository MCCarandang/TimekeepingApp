import os
import csv
from datetime import datetime
import cv2

def create_output_dir(path):
    os.makedirs(path, exist_ok=True)

def get_timestamp():
    now = datetime.now()
    return now, now.strftime("%Y%m%d_%H%M%S")

def crop_image(image, box):
    x1, y1, x2, y2 = box
    return image[y1:y2, x1:x2]

def draw_bbox(image, box, label=""):
    x1, y1, x2, y2 = box
    cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
    if label:
        cv2.putText(image, label, (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

def save_metadata(csv_path, data):
    file_exists = os.path.isfile(csv_path)
    with open(csv_path, "a", newline="") as csvfile:
        fieldnames = ["filename", "timestamp", "x1", "y1", "x2", "y2"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(data)
