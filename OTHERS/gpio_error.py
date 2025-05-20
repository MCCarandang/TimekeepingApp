
>>> %Run timekeeping.py
Traceback (most recent call last):
  File "/home/raspberrypi/Desktop/TimekeepingApp/timekeeping.py", line 440, in <module>
    window = AccessGrantedWindow()
  File "/home/raspberrypi/Desktop/TimekeepingApp/timekeeping.py", line 155, in __init__
    self.reader = SimpleMFRC522()
  File "/usr/local/lib/python3.9/dist-packages/mfrc522/SimpleMFRC522.py", line 14, in __init__
    self.READER = MFRC522()
  File "/usr/local/lib/python3.9/dist-packages/mfrc522/MFRC522.py", line 151, in __init__
    GPIO.setup(pin_rst, GPIO.OUT)
RuntimeError: Not running on a RPi!