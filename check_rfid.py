import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
import time
import os

GPIO.setwarnings(False)
reader = SimpleMFRC522()

DB_PATH = 'home/raspberrypi/Desktop/TimekeepingApp/timekeeping_app.db'

def check_rfid_in_db(rfid_id):
    conn = sqlite3.connect('/home/raspberrypi/Desktop/TimekeepingApp/timekeeping_app.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT first_name, last_name FROM emp_profiles WHERE rfid_id = ?", (rfid_id,))
    result = cursor.fetchone()
    
    conn.close()
    return result

try:
    print("Place your RFID tag near the scanner...")
    
    while True:
        id, text = reader.read()
        rfid_id = str(id).strip()
        print(f"RFID Tag Detected: {rfid_id}")
        
        employee = check_rfid_in_db(rfid_id)
        if employee:
            first_name, last_name = employee
            print(f"Access Granted: Welcome {first_name} {last_name}")
        else:
            print(f"Acces Denied | Unregistered RFID Tag")
            
        time.sleep(2)	# delay to avoid rapid re-scanning
        
except KeyboardInterrupt:
    print("Exiting program...")

finally:
    GPIO.cleanup()