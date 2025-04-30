from picamera import PiCamera
import time

camera = PiCamera()
time.sleep(2)
camera.capture('/home/raspberrypi/Desktop/img1.jpg')
print("Done")