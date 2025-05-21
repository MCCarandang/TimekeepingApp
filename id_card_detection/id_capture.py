from picamera2 import Picamera2
import cv2
import numpy as np
import time
import os
from datetime import datetime

# === Directories and Log Setup ===
save_dir = "captured_ids"
log_file = os.path.join(save_dir, "capture_log.csv")
os.makedirs(save_dir, exist_ok=True)

# Initialize cooldown to prevent duplicate captures
last_saved_time = 0
save_interval = 5  # seconds between saves

def save_id_card(image, x, y, w, h):
    """Save the cropped ID card image and log the detection."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"id_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)

    # Crop and save the image
    card_crop = image[y:y + h, x:x + w]
    cv2.imwrite(filepath, card_crop)

    # Log entry
    log_entry = f"{timestamp},{filename},{x},{y},{w},{h}\n"
    with open(log_file, "a") as f:
        f.write(log_entry)

    print(f"[INFO] ID card saved: {filename}")
    return filename

def detect_id_card(frame):
    global last_saved_time

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            ar = max(aspect_ratio, 1 / aspect_ratio)

            if 1.3 < ar < 1.7 and w > 100 and h > 60:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(frame, "Possible ID Card", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # === Save functionality ===
                current_time = time.time()
                if current_time - last_saved_time > save_interval:
                    last_saved_time = current_time
                    save_id_card(frame, x, y, w, h)

    return frame

def main():
    picam2 = Picamera2()
    preview_config = picam2.create_preview_configuration(main={"size": (640, 480)})
    picam2.configure(preview_config)
    picam2.start()

    time.sleep(2)

    while True:
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 0)
        detected_frame = detect_id_card(frame)

        cv2.imshow("ID Card Detection", detected_frame)

        if cv2.waitKey(1) & 0xFF == 27:
            break

    picam2.stop()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
