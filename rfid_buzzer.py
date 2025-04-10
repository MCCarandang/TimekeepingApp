import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import time

# Set up GPIO for RFID reader and buzzer
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Set up the buzzer on GPIO pin 17
buzzer_pin = 17
GPIO.setup(buzzer_pin, GPIO.OUT)

# Initialize the RFID reader
reader = SimpleMFRC522()

def beep():
    GPIO.output(buzzer_pin, GPIO.HIGH)
    time.sleep(0.2)
    GPIO.output(buzzer_pin, GPIO.LOW)
    time.sleep(0.2) # Pause between beeps

try:
    print("Place your RFID tag near the reader...")
    
    # Read the RFID tag and capture the ID
    id, text = reader.read()
    
    # Print the RFID tag ID
    print("RFID Tag ID: ", id)
    
    beep()
    
except KeyboardInterrupt:
    print("Program interrupted by user.")
finally:
    GPIO.cleanup()