import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

# Initialize the RFID reader
GPIO.setmode(GPIO.BCM)
reader = SimpleMFRC522()


try:
    print("Place your RFID tag near the reader...")
    
    # Read the RFID tag and capture the ID
    id, text = reader.read()
    
    # Print the RFID tag ID
    print("RFID Tag ID: ", id)	
    
except KeyboardInterrupt:
    print("Program interrupted by user.")
    
finally:
    GPIO.cleanup()
