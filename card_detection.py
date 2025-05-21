# Can detect id card and draws rectangle around the detected object

from picamera2 import Picamera2
import cv2
import numpy as np
import time

def detect_id_card(frame):
   # if frame is None or len(frame.shape) != 3 or frame.shape[2] != 3:
   #     return frame

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(blur, 50, 150)

    contours, _ = cv2.findContours(edged, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    frame_h, frame_w = frame.shape[:2]

    for cnt in contours:
        approx = cv2.approxPolyDP(cnt, 0.02 * cv2.arcLength(cnt, True), True)

        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            if 1.3 < aspect_ratio < 1.7 and w > 100 and h > 60:

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                # cv2.drawContours(frame, [approx], -1, (0, 255, 0), 2)
                cv2.putText(frame, "Possible ID Card", (x, y - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

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
        
        # show the detected frame
      #  try:
      #      safe_frame =cv2.resize(detected_frame, (640, 480))
      #      cv2.imshow("ID Card Detection", safe_frame)
      #  except Exception as e:
      #      print("Display error:", e)
            
      #  if cv2.waitKey(1) & 0xFF == 27:
      #      break
        
    picam2.stop()
    cv2.destroyAllWindows()
    
if __name__ == "__main__":
    main()