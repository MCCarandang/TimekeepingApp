import cv2
import time
import yaml
import logging
import argparse
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from picamera2 import Picamera2
from utils import create_output_dir, get_timestamp, crop_image, draw_bbox, save_metadata

# === Setup logging ===
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# === CLI Args ===
parser = argparse.ArgumentParser(description="ID Card Detection")
parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
args = parser.parse_args()

# === Load config ===
with open(args.config, "r") as f:
    config = yaml.safe_load(f)

MODEL_PATH = config["model_path"]
CAPTURE_DIR = config["capture_dir"]
CSV_PATH = config["csv_path"]
CONF_THRESH = config["confidence_threshold"]
RESOLUTION = tuple(config["resolution"])
LABEL = config["label"]
HEADLESS = config.get("headless", False)
FPS_LIMIT = config.get("fps_limit", 10)

# === Init ===
create_output_dir(CAPTURE_DIR)
model = YOLO(MODEL_PATH)

picam2 = Picamera2()
picam2.preview_configuration.main.size = RESOLUTION
picam2.preview_configuration.main.format = "RGB888"
picam2.configure("preview")
picam2.start()
time.sleep(0.5)

if not HEADLESS:
    cv2.namedWindow("ID Detection", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("ID Detection", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

try:
    while True:
        start_time = time.time()
        frame = picam2.capture_array()
        if frame is None:
            logging.error("Failed to capture image.")
            break

        frame = cv2.flip(frame, 0)
        if frame.shape[2] == 4:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

        try:
            results = model(frame, verbose=False)[0]
        except Exception as e:
            logging.exception("YOLO inference failed.")
            continue

        frame_h, frame_w = frame.shape[:2]

        for det in results.boxes:
            class_id = int(det.cls[0].item())
            conf = det.conf[0].item()

            if class_id != 0 or conf < CONF_THRESH:
                continue

            x1, y1, x2, y2 = map(int, det.xyxy[0].tolist())
            x1, y1 = max(0, x1), max(0, y1)
            x2, y2 = min(frame_w - 1, x2), min(frame_h - 1, y2)

            if x2 <= x1 or y2 <= y1:
                logging.warning(f"Invalid box: ({x1}, {y1}) to ({x2}, {y2})")
                continue

            box = [x1, y1, x2, y2]
            draw_bbox(frame, box, label=LABEL)

            cropped = crop_image(frame, box)
            if cropped is not None and cropped.size > 0:
                _, timestamp = get_timestamp()
                filename = f"{timestamp}.jpg"
                filepath = Path(CAPTURE_DIR) / filename
                try:
                    cv2.imwrite(str(filepath), cropped)
                    save_metadata(CSV_PATH, {
                        "filename": filename,
                        "timestamp": timestamp,
                        "x1": x1, "y1": y1, "x2": x2, "y2": y2
                    })
                    logging.info(f"Saved: {filename}")
                except Exception as e:
                    logging.exception("Failed to save image/metadata.")
            else:
                logging.warning("Empty cropped image, skipping.")

        if not HEADLESS:
            cv2.imshow("ID Detection", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        elapsed = time.time() - start_time
        sleep_time = max(0, (1 / FPS_LIMIT) - elapsed)
        time.sleep(sleep_time)

finally:
    logging.info("Shutting down gracefully...")
    picam2.stop()
    if not HEADLESS:
        cv2.destroyAllWindows()
