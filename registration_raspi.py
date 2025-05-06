import time
import RPi.GPIO as GPIO
import mfrc522
import mysql.connector
import os
import sqlite3
from picamera import PiCamera

GPIO.setwarnings(False)

#Initialize the RFID reader
reader = mfrc522.MFRC522()

#initialize the camera
camera = PiCamera()


#Define the directory to store photos
photo_directory = "/home/pi/Desktop/timekeepingdeviceapp/registeredusers"

try:
    #create the photo directory if it doesn't exist
    if not os.path.exists(photo_directory):
        os.makedirs(photo_directory)
    
    while True:
        #Scan for RFID cards
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("Card detected")
            #Get the UID of the detected card
            (status, uid) = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                # Take the first 4 bytes of the UID and convert to 8-character hexadecimal
                id_serial = ''.join([format(i, '02X') for i in uid[:4]])
                id_serial = id_serial[:8]
                print(f"Card Serial ID (Hex): {id_serial}")

                #Database connection
                db_connection = sqlite3.connect('/home/pi/Desktop/timekeepingdeviceapp/localtimekeeping.db')
                db_cursor = db_connection.cursor()
                

                #check if the card serial already exists in the database
                db_cursor.execute("SELECT id_serial FROM main_employees_tbl WHERE id_serial = ?", (id_serial,))
                existing_record = db_cursor.fetchone()

                if existing_record:
                    print(f"Card Serial ID {id_serial} already exists in the database.")
                else:
                    #insert the ID serial into the database
                    db_cursor.execute("INSERT INTO main_employees_tbl (id_serial) VALUES (?)", (id_serial,))
                    db_connection.commit()

                    #Wait for 5 seconds before capturing an image
                    time.sleep(5)

                    #Capture a photo and save with the serial ID as the filename
                    photo_filename = f"{id_serial}.jpg"
                    full_photo_path = os.path.join(photo_directory, photo_filename)
                    camera.capture(full_photo_path)

                    #manual input for other user information
                    id_number = input("Enter ID number (10 characters max, or press Enter for a default value):")

                    #check if the entered ID number is longer than 10 characters
                    if len(id_number) > 10:
                        print("ID number must be 10 characters or less.")
                        #You can choose to exit or handle this case as needed
                        continue
                    #if the entered ID number is empty or shorter than 10 characters, pad it with spaces to a length of 10
                    id_number = id_number.ljust(10)
                    last_name = input("Enter last name:")
                    first_name = input("Enter first name:")
                    middle_name = input("Enter middle name:")
                    #insert user information and photo filename into the database
                    db_cursor.execute("UPDATE main_employees_tbl SET id_number = ?, last_name = ?, first_name = ?, middle_name = ?, picture_file_name = ? WHERE id_serial = ?", (id_number, last_name, first_name, middle_name, photo_filename, id_serial,))
                    db_connection.commit()

                    print("User information and photo saved successfully.")

                    #close the database connection
                    db_cursor.close()
                    db_connection.close()
                    
                    
except KeyboardInterrupt:
    print("KeyboardInterrupt: Exiting...")
    camera.close() #close the camera instance
    GPIO.cleanup() #clean up GPIO

                    


