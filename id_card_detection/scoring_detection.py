from picamera2 import Picamera2
import cv2
import numpy as np
import time
import os
from datetime import datetime

# === Settings ===
save_dir = "captured_ids"
log_file = os.path.join(save_dir, "capture_log.csv")
os.makedirs(save_dir, exist_ok=True)

last_saved_time = 0
save_interval = 5  # seconds
confidence_threshold = 70  # Only save if confidence >= this value

def save_id_card(image, x, y, w, h, score):
    """Save cropped image with timestamp and detection log."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"id_{timestamp}.jpg"
    filepath = os.path.join(save_dir, filename)

    # Crop and save
    card_crop = image[y:y + h, x:x + w]
    cv2.imwrite(filepath, card_crop)

    # Log entry
    log_entry = f"{timestamp},{filename},{x},{y},{w},{h},{score:.2f}\n"
    with open(log_file, "a") as f:
        f.write(log_entry)

    print(f"[INFO] Saved ID with confidence {score:.2f}%: {filename}")
    return filename

def calculate_confidence(aspect_ratio, w, h, area):
    """Heuristic-based confidence score for ID shape."""
    ideal_ar = 1.6
    ar_score = max(0, 100 - abs(aspect_ratio - ideal_ar) * 100)

    size_score = min(w * h / 20000, 100)  # Prefer larger sizes

    combined = (0.6 * ar_score + 0.4 * size_score)
    return min(combined, 100)

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
            area = w * h

            if 1.3 < aspect_ratio < 1.7 and w > 100 and h > 60:
                confidence = calculate_confidence(aspect_ratio, w, h, area)

                # Draw rectangle and confidence score
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                label = f"ID Card: {confidence:.1f}%"
                cv2.putText(frame, label, (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                # Save if confidence is high enough
                current_time = time.time()
                if confidence >= confidence_threshold and (current_time - last_saved_time > save_interval):
                    last_saved_time = current_time
                    save_id_card(frame, x, y, w, h, confidence)

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