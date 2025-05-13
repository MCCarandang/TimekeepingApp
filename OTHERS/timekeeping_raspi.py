import time
from time import sleep
import RPi.GPIO as GPIO
import mfrc522
import sqlite3
import os
from picamera import PiCamera
import pygame
import socket
import threading
import subprocess
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
from PyQt5.QtCore import QTimer, QDateTime
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QMainWindow, QWidget
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton
import uuid
import sys

GPIO.setwarnings(False)

#Initialize GPIO for the buzzer
BUZZER_PIN = 16 #Adjust the pin number as needed
GPIO.setmode(GPIO.BCM)
GPIO.setup(BUZZER_PIN, GPIO.OUT)

#Create a PWM instance with a frequency of 440Hz (A4 note)
pwm = GPIO.PWM(BUZZER_PIN, 1000)

#Initialize the RFID reader
reader = mfrc522.MFRC522()

#Initialize the camera
camera = PiCamera()

#Initialize pygame for the camera preview
pygame.init()

#Set the display dimensions for the preview (adjust as needed)
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 480

#Adjusted camera preview dimensions for a smaller size
CAMERA_PREVIEW_WIDTH = 250  #Adjust as needed
CAMERA_PREVIEW_HEIGHT = 160    #Adjust as needed

#Set the camera preview resolution
camera.resolution = (CAMERA_PREVIEW_WIDTH, CAMERA_PREVIEW_HEIGHT)

#Initialize the camera preview at the lower left corner
camera.start_preview(fullscreen=False, window=(0, SCREEN_HEIGHT - CAMERA_PREVIEW_HEIGHT, CAMERA_PREVIEW_WIDTH, CAMERA_PREVIEW_HEIGHT))

#Wait for a moment to ensure the camera preview window is created
sleep(2)

#Get the process ID (PID) of the camera preview window
preview_pid = os.getpid

#Hide the GUI window of the camera preview
subprocess.run(["xdotool", "search", "--onlyvisible", "--pid", str(preview_pid), "windowunmap"])

#Define clocking state (0 for clocking in, 1 for clocking out)
clocking_state = 0

#Define the RFID tag UID for changing clocking state
clocking_state_serial = "696F66A2"

#Define the RFID tag UID for taking photo of user who needs help
help_user_serial = "95344CD3"

#Establish a database connection
db_connection = sqlite3.connect('/home/pi/Desktop/timekeepingdevice/localtimekeeping.db', check_same_thread=False)
db_cursor = db_connection.cursor()

#Define the directory to load and store photos
registered_users_photo_directory = "/home/pi/Desktop/timekeepingdevice/registeredusers" #loading existing photos of registered employees
denied_users_photo_directory = "/home/pi/Desktop/timekeepingdevice/accessdenied" #storing taken photos of denied users
unscanned_id_photo_directory = "/home/pi/Desktop/timekeepingdevice/defectiveids" #storing pictures of users with defective id


#Create a Pygame screen for the camera preview
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Camera Preview")

#function to check if an RFID card/tag is registered
def is_registered(id_serial):
    db_cursor.execute("SELECT id_number FROM employees_tbl WHERE id_serial = ?", (id_serial,))
    result = db_cursor.fetchone()
    return result is not None, result[0] if result else None

#function to get the employee number of the registered rfid card 
def get_id_number_from_database(id_serial):
    db_cursor.execute("SELECT id_number FROM employees_tbl WHERE id_serial = ?", (id_serial,))
    result = db_cursor.fetchone()
    return result[0] if result else None

#function to convert the photo to blob
def convertToBinaryData(filename):
    # Convert digital data to binary format
    with open(filename, 'rb') as file:
        blobData = file.read()
    return blobData

#function to log the attendance
def log_attendance(id_serial, transaction_code):
    global clocking_state
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    if id_serial == clocking_state_serial:
        #Clocking RFID tag detected, toggle clocking state
        clocking_state = 1 - clocking_state
        print(f"Clocking{'out' if clocking_state == 1 else 'in'}...")

        #Update the GUI with the current clocking state
        attendance_window.show_clocking_state('Time Out' if clocking_state == 1 else 'Time In')

        if id_serial in registered_users_clocked_in and clocking_state == 0:
            pwm.start(50)
            play_melody(['D4','D4','D4']) #play a repeated action melody
            pwm.stop()
            repeated_query = "INSERT INTO repeated_tbl (id_number, transaction_date, transaction_code, mac_add, ip_add, comp_name) VALUES(?, ?, ?, ?, ?, ?)"
            repeated_data = (id_number, timestamp, transaction_code, mac_address, ip_address, "ttech",)
            db_cursor.execute(repeated_query, repeated_data)
            db_connection.commit()
            
            #Display the "REPEATED ACTION" message if the user has already clocked out
            attendance_window.show_repeated_action_message()
        else:
            attendance_window.clear_repeated_action_message() #Clear the message
            
    elif id_serial == help_user_serial:
        print("User with defective ID photo taken.")
        pwm.start(50)
        play_melody(['E4', 'D4', 'G4'])
        pwm.stop()

        #Capture a photo of user with unscanned id
        photo_filename = f"{id_serial}_{timestamp}.jpg"
        full_photo_path = os.path.join(unscanned_id_photo_directory, photo_filename)
        camera.capture(full_photo_path)
        print(f"Photo captured: {full_photo_path}")
        pictureBlob = convertToBinaryData(full_photo_path)
            
        #insert log information in unscanned_tbl
        defective_id_query = "INSERT INTO defective_id_tbl (id_serial, transaction_date, transaction_code, picture_file_name, picture_file_path, picture) VALUES (?, ?, ?, ?, ?, ?)"
        data = (id_serial, timestamp, transaction_code, photo_filename, full_photo_path, pictureBlob)
        db_cursor.execute(defective_id_query, data)
        db_connection.commit()
        print("Unscanned id logged successfully.")
                       
        #Display the "ACCESS DENIED!" message
        attendance_window.show_unscanned_id_message() #Display "ACCESS DENIED" message
            

        #Clear only the user's photo, name, and ID number
        attendance_window.clear_user_photo()
        attendance_window.clear_user_name()
        attendance_window.clear_id_number()

        #Explicitly call show_clocking_state to make sure it's updated
        attendance_window.show_clocking_state('Time Out' if clocking_state == 1 else 'Time In')
    
    else:
        is_registered_user, id_number, user_name, photo_file_name = get_user_info(id_serial)
        if is_registered_user:
            if clocking_state == 0:
                if id_serial not in registered_users_clocked_in:
                    print(f"Registered user {id_number} detected. Clocking in!")
                    pwm.start(50)
                    play_melody(['E4', 'D4', 'G4'])
                    pwm.stop()

                    #insert attendance log into the "logbox_tbl"
                    attendance_query = "INSERT INTO logbox_tbl (id_number, transaction_date, transaction_code, mac_add, ip_add, comp_name) VALUES(?, ?, ?, ?, ?, ?)"
                    attendance_data = (id_number, timestamp, transaction_code, mac_address, ip_address, "ttech",)
                    db_cursor.execute(attendance_query, attendance_data)
                    db_connection.commit()
                    print("Attendance for clocking in logged successfully.")
                    registered_users_clocked_in.add(id_serial)
                                                             
                    #Display the ID number and user's name
                    attendance_window.show_id_number(id_number)
                    attendance_window.show_user_name(user_name)
                    
                    attendance_window.show_access_granted_message()

                    #Display the user's photo
                    if photo_file_name:
                        photo_path = os.path.join(registered_users_photo_directory, photo_file_name)
                        attendance_window.show_user_photo(photo_path)
                    else:
                        attendance_window.show_repeated_action_message() #Display "REPEATED ACTION" message
                else:
                    pwm.start(50)
                    play_melody(['D4','D4','D4']) #play a repeated action melody
                    pwm.stop()
                    
                    repeated_query = "INSERT INTO repeated_tbl (id_number, transaction_date, transaction_code, mac_add, ip_add, comp_name) VALUES(?, ?, ?, ?, ?, ?)"
                    repeated_data = (id_number, timestamp, transaction_code, mac_address, ip_address, "ttech",)
                    db_cursor.execute(repeated_query, repeated_data)
                    db_connection.commit()
                    
                    attendance_window.show_repeated_action_message() #Display "REPEATED ACTION" message
            elif clocking_state == 1:
                if id_serial not in registered_users_clocked_out:
                    print(f"Registered user {id_number} detected. Clocking out!")
                    pwm.start(50)
                    play_melody(['E4', 'D4', 'G4'])
                    pwm.stop()

                    #insert attendance log into the "logbox_tbl"
                    attendance_query = "INSERT INTO logbox_tbl (id_number, transaction_date, transaction_code, mac_add, ip_add, comp_name) VALUES(?, ?, ?, ?, ?, ?)"
                    attendance_data = (id_number, timestamp, transaction_code, mac_address, ip_address, "ttech",)
                    db_cursor.execute(attendance_query, attendance_data)
                    db_connection.commit()
                    print("Attendance for clocking in logged successfully.")
                    registered_users_clocked_out.add(id_serial)
                                                             
                    #Display the ID number and user's name
                    attendance_window.show_id_number(id_number)
                    attendance_window.show_user_name(user_name)
                    
                    attendance_window.show_access_granted_message()

                    #Display the user's photo
                    if photo_file_name:
                        photo_path = os.path.join(registered_users_photo_directory, photo_file_name)
                        attendance_window.show_user_photo(photo_path)
                    else:
                        attendance_window.show_repeated_action_message() #Display "REPEATED ACTION" message
                else:
                    pwm.start(50)
                    play_melody(['D4','D4','D4']) #play a repeated action melody
                    pwm.stop()
                    
                    repeated_query = "INSERT INTO repeated_tbl (id_number, transaction_date, transaction_code, mac_add, ip_add, comp_name) VALUES(?, ?, ?, ?, ?, ?)"
                    repeated_data = (id_number, timestamp, transaction_code, mac_address, ip_address, "ttech",)
                    db_cursor.execute(repeated_query, repeated_data)
                    db_connection.commit()
                    
                    attendance_window.show_repeated_action_message() #Display "REPEATED ACTION" message
        else:
            print("Unregistered user detected. Access Denied!")
            pwm.start(50)
            play_melody(['D4','D4','D4']) #play an access denied melody
            pwm.stop()

            #Capture a photo and log attendance for unregistered users
            photo_filename = f"{id_serial}_{timestamp}.jpg"
            full_photo_path = os.path.join(denied_users_photo_directory, photo_filename)
            camera.capture(full_photo_path)
            print(f"Photo captured: {full_photo_path}")
            pictureBlob = convertToBinaryData(full_photo_path)
            
            #insert access attempts log into the "denied_tbl" table
            denied_query = "INSERT INTO denied_tbl (id_serial, transaction_date, transaction_code, picture_file_name, picture_file_path, picture) VALUES (?, ?, ?, ?, ?, ?)"
            data = (id_serial, timestamp, transaction_code, photo_filename, full_photo_path, pictureBlob)
            db_cursor.execute(denied_query, data)
            db_connection.commit()
            print("Access attempt logged successfully.")
                       
            #Display the "ACCESS DENIED!" message
            attendance_window.show_access_denied_message() #Display "ACCESS DENIED" message
            #attendance_window.message_label.setText("ACCESS DENIED!")

            #Clear only the user's photo, name, and ID number
            attendance_window.clear_user_photo()
            attendance_window.clear_user_name()
            attendance_window.clear_id_number()

            #Explicitly call show_clocking_state to make sure it's updated
            attendance_window.show_clocking_state('Time Out' if clocking_state == 1 else 'Time In')
                        
def get_user_info(id_serial):
    db_cursor.execute("SELECT id_number, last_name, first_name, middle_name, picture_file_name FROM employees_tbl WHERE id_serial = ?", (id_serial,))
    result = db_cursor.fetchone()
    if result:
        id_number, last_name, first_name, middle_name, picture_file_name = result
        user_name = f"{last_name}, {first_name} {middle_name}"
        return True, id_number, user_name, picture_file_name
    else:
        return False, None, None, None


#Add a new function to fetch user's name from the database
def get_user_name(id_number):
    db_cursor.execute("SELECT last_name, first_name, middle_name FROM employees_tbl WHERE id_number = ?", (id_number,))       
    result = db_cursor.fetchone()
    if result:
        last_name, first_name, middle_name = result
        return last_name, first_name, middle_name
    else:          
        return "", "", ""
#Add a new function to display the user's name in the GUI
def show_user_name(name):
    attendance_window.show_user_name(user_name)

def clear_displayed_info():
    attendance_window.clear_user_photo()
    attendance_window.clear_user_name()
    attendance_window.clear_id_number()

def play_melody(melody):
    notes = {
        'C4': 261.63,
        'D4': 293.66,
        'E4': 329.63,
        'F4': 349.23,
        'G4': 392.00,
        'A4': 440.00,
        'B4': 493.88
    }
    for note in melody:
        frequency = notes[note]
        pwm.ChangeFrequency(frequency)
        time.sleep(0.1) #Play each note for 0.1 seconds

registered_users_clocked_in = set()
registered_users_clocked_out = set()

#Function to get the MAC address
def get_mac():
    #Get the MAC address of the device
    mac = hex(uuid.getnode())[2:]
    return ":".join([mac[i:i+2] for i in range(0, len(mac),2)])

#Get the MAC address of the device
mac_address = get_mac()

#Get the IP address of the machine
ip_address = socket.gethostbyname(socket.gethostname())

#Create a PyQt5 application
app = QApplication([])

class ColoredWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(self.backgroundRole(), QColor(224, 224, 224)) #Light blue color
        self.setPalette(palette)

#...(previous code remains the same)
class AttendanceWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #initialize clocking state to 'Time In'
        self.clocking_state = 'Time In'

        #set up the main window
        self.setWindowTitle("Attendance System")
        self.setGeometry(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT) #Set full-screen size

        #create a colored central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #Apply a style sheet to set the background color for both central widget and main window
        self.setStyleSheet("background-color: darkblue;")
        central_widget.setStyleSheet("background-color: darkblue;")

        #Create a layout for date and time labels
        date_time_layout = QVBoxLayout() #Use a QVBoxLayout to stack date and time vertically

        #Create the date label and add it to the layout
        self.date_label = QLabel()
        date_time_layout.addWidget(self.date_label)

        #Create the time label and add it to the layout
        self.time_label = QLabel()
        date_time_layout.addWidget(self.time_label)

        #Create the clocking state label and add it to the layout
        self.clocking_state_label = QLabel()
        date_time_layout.addWidget(self.clocking_state_label)

        #Create a horizontal layout for user info (Name, ID number, photo)
        user_info_layout = QHBoxLayout()

        #Create a vertical layout for the user's name and ID number
        name_id_layout = QVBoxLayout()

        #Create labels for user name and ID number
        self.user_name_label = QLabel()
        self.id_number_label = QLabel()

        #Set font size and color for user name and ID number
        font = QFont("Arial", 15) #Adjust font size here
        self.user_name_label.setFont(font)
        self.id_number_label.setFont(font)
        self.user_name_label.setStyleSheet("color:white;") #set text color for user name (optional)
        self.id_number_label.setStyleSheet("color:white;") #set text color for id number (optional)

        #Add user name and ID number labels to the name_id_layout
        name_id_layout.addWidget(self.user_name_label)
        name_id_layout.addWidget(self.id_number_label)

        #Set alignment of user name annd ID number labels to center
        self.user_name_label.setAlignment(Qt.AlignCenter)
        self.id_number_label.setAlignment(Qt.AlignCenter)

        #Create the user's photo label
        self.photo_label = QLabel()

        #Add the name_id_layout and photo_label to the user_info_layout
        user_info_layout.addLayout(name_id_layout)
        user_info_layout.addWidget(self.photo_label)

        #Set alignment of user photo label to center
        self.photo_label.setAlignment (Qt.AlignCenter)

        #Create a vertical layout for the clocking state label
        clocking_state_layout = QVBoxLayout()

        #Set the clocking state label's properties
        self.clocking_state_label.setAlignment(Qt.AlignLeft | Qt.AlignTop) #Align to the upper left corner
        self.clocking_state_label.setFont(QFont("Arial", 55)) #Set font and font size
        self.clocking_state_label.setStyleSheet("color: yellow;") #set the text color (optional)

        #add the clocking state label to the clocking state layout
        clocking_state_layout.addWidget(self.clocking_state_label)

        #create a vertical layout for the entire window
        layout = QVBoxLayout(central_widget)

        #add the date and time layout to the main layout
        layout.addLayout(date_time_layout)

        #add a separator(optional)
        layout.addStretch(1) #add a stretch to create some space

        #add user info layout and clocking state layout to the main layout
        layout.addLayout(user_info_layout)
        layout.addLayout(clocking_state_layout)

        #setup the exit button
        self.setup_exit_button()    #add this line to set up the exit button

        #initialize the ID number label text
        self.id_number_label_text = ""

        #initialize the date and time label text
        self.date_label_text = ""
        self.time_label_text = ""

        #create a timer to update the date and time labels
        self.date_time_timer = QTimer(self)
        self.date_time_timer.timeout.connect(self.update_date_time)
        self.date_time_timer.start(1000) #update every one second

        #create a timer to clear the ID number label
        self.id_number_timer =QTimer(self)
        self.id_number_timer.timeout.connect(self.clear_id_number)

        #create a timer to clear the user name label
        self.user_name_timer = QTimer(self)
        self.user_name_timer.timeout.connect(self.clear_user_name)

        #set a timer to clear clocking state label
        self.clocking_state_timer = QTimer(self)
        self.clocking_state_timer.timeout.connect(self.clear_clocking_state)


        #create a timer to clear the user photo label
        self.photo_timer = QTimer(self)
        self.photo_timer.timeout.connect(self.clear_user_photo)

        #Create the date and time labels and set their initial properties
        self.date_label.setAlignment(Qt.AlignRight | Qt.AlignTop) #Align to the upper left corner
        self.date_label.setFont(QFont("Arial", 15)) #Set font and font size
        self.date_label.setStyleSheet("color: white;") #set the text color (optional)

        #Create the date and time labels and set their initial properties
        self.time_label.setAlignment(Qt.AlignRight | Qt.AlignTop) #Align to the upper left corner
        self.time_label.setFont(QFont("Arial", 15)) #Set font and font size
        self.time_label.setStyleSheet("color: white;") #set the text color (optional)

        #initialize the date and time labels with their initial values
        self.update_date_time()
        self.show_clocking_state(self.clocking_state)

        #create a label to display messages
        self.message_label = QLabel()
        date_time_layout.addWidget(self.message_label) #add the label to the layout

        #create a timer to clear the displayed user info and photo
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.clear_displayed_info)

        #create a timer to clear the repeated action message after 3 seconds
        self.repeated_action_timer = QTimer(self)
        self.repeated_action_timer.timeout.connect(self.clear_repeated_action_message)
        
        #create a timer to clear the access denied message after 3 seconds
        self.access_denied_timer = QTimer(self)
        self.access_denied_timer.timeout.connect(self.clear_repeated_action_message)
        
        #create a timer to clear the access denied message after 3 seconds
        self.unscanned_id_timer = QTimer(self)
        self.unscanned_id_timer.timeout.connect(self.clear_unscanned_id_message)
        
        #create a timer to clear the access granted message after 3 seconds
        self.access_granted_timer = QTimer(self)
        self.access_granted_timer.timeout.connect(self.clear_repeated_action_message)

        #create a timer to clear the message after a short duration
        self.message_timer = QTimer(self)
        self.message_timer.timeout.connect(self.clear_message)

        #connect the F11 keypress event to toggle_fullscreen method
        self.toggle_fullscreen_flag = False #flag to track full-screen state
        self.fullscreen_timer = QTimer(self)
        self.fullscreen_timer.timeout.connect(self.toggle_fullscreen)
        self.fullscreen_timer.setSingleShot(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()

    def toggle_fullscreen(self):
        #toggle fullscreen mode
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def update_date_time(self):
        #get the current date and time
        current_datetime = QDateTime.currentDateTime()

        #format date and time as strings (adjust the format as needed)
        formatted_date = current_datetime.toString("yyyy-MM-dd")
        formatted_time = current_datetime.toString("hh:mm:ss")

        #update the date and time labels with the current date and time
        self.date_label.setText(formatted_date)
        self.time_label.setText(formatted_time)

    def show_user_info (self, name, id_number, photo_path):
        #show user name and ID number
        self.user_name_label.setText(name)
        self.id_number_label.setText(f"ID Number: {id_number}")

        #show user's photo
        if photo_path:
            original_pixmap = QPixmap(photo_path)
            resized_pixmap = original_pixmap.scaled(200, 200, Qt.KeepAspectRatio)
            self.photo_label.setPixmap(resized_pixmap)

        #schedule a timer to clear the user info and photo after 5 seconds
        self.display_timer.start(1000) #1000 milliseconds = 5 seconds

    def clear_user_info(self):
        #clear user info and photo
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.photo_label.clear()

    def show_user_photo(self, filename):
        if filename:
            photo_path = os.path.join(registered_users_photo_directory, filename)
            original_pixmap = QPixmap(photo_path)
            resized_pixmap = original_pixmap.scaled(200, 200, Qt.KeepAspectRatio)
            self.photo_label.setPixmap(resized_pixmap)

            #schedule a timer to clear the photo after 1 second
            self.display_timer.start(1000) #1000 milliseconds = 1 second

    def clear_user_photo(self):
        #schedule a timer to clear the photo after 1 second
        QTimer.singleShot(1000, self.remove_photo)
    
    def remove_photo(self):
        #clear the user's photo label
        self.photo_label.clear()

    def show_user_name (self, name):
        self.user_name_label_text = name
        self.user_name_label.setText(name)

        #schedule a timer to clear the user's name after 5 seconds
        self.display_timer.start(1000) #1000 milliseconds = 5 seconds
    
    def clear_user_name(self):
        self.user_name_label_text = ""
        self.user_name_label.clear()

    def show_id_number (self, id_number):
        self.id_number_label_text = id_number
        self.id_number_label.setText(f"ID Number: {id_number}")

        #schedule a timer to clear the user's name after 1 second
        self.display_timer.start(1000) #1000 milliseconds = 1 second
    
    def clear_id_number(self):
        self.id_number_label_text = ""
        self.id_number_label.clear()

    def show_clocking_state(self, state):
        self.clocking_state = state
        if state == 'Time In':
            self.clocking_state_label.setText('IN')
        elif state == 'Time Out':
            self.clocking_state_label.setText('OUT')

    def clear_clocking_state(self):
        self.clocking_state = 'Time In'
        self.clocking_state_label.setText("")
    
    #repeated action message functionality - START
    def show_repeated_action_message(self):
        #Hide user information labels
        self.user_name_label.hide()
        self.id_number_label.hide()
        self.photo_label.hide()

        #show the "REPEATED ACTION" message for a short duration
        message_duration = 3000 #3000 milliseconds = 3 seconds
        self.show_message("REPEATED ACTION", message_duration)

        #Style the message
        font = QFont ("Arial", 30, QFont.Bold) #adjust font size and weight
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter) #align to center
        self.message_label.setStyleSheet("color:red;") #set text color to red
    
    def clear_repeated_action_message(self):
        self.repeated_action_timer.stop()
        self.message_label.clear()

        #show user information labels
        self.user_name_label.show()
        self.id_number_label.show()
        self.photo_label.show()
    
    def clear_message_and_start_timer(self):
        #clear the message and start the timer
        self.clear_repeated_action_message()
        self.repeated_action_timer.start(1000) #1000 milliseconds = 1 second
    #repeated action message functionality - END
        
    #access denied message functionality - START
    def show_access_denied_message(self):
        #Hide user information labels
        self.user_name_label.hide()
        self.id_number_label.hide()
        self.photo_label.hide()

        #show the "REPEATED ACTION" message for a short duration
        message_duration = 3000 #3000 milliseconds = 3 seconds
        self.show_message("ACCESS DENIED", message_duration)

        #Style the message
        font = QFont ("Arial", 30, QFont.Bold) #adjust font size and weight
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter) #align to center
        self.message_label.setStyleSheet("color:red;") #set text color to red
    
    def clear_access_denied_message(self):
        self.access_denied_timer.stop()
        self.message_label.clear()

    def clear_denied_message_and_start_timer(self):
        #clear the message and start the timer
        self.clear_access_denied_message()
        self.access_denied_timer.start(1000) #1000 milliseconds = 1 second
    #access denied message functionality - END
        
    #unscanned id message functionality - START
    def show_unscanned_id_message(self):
        #Hide user information labels
        self.user_name_label.hide()
        self.id_number_label.hide()
        self.photo_label.hide()

        #show the "REPEATED ACTION" message for a short duration
        message_duration = 3000 #3000 milliseconds = 3 seconds
        self.show_message("Photo taken \n and recorded in the database.", message_duration)

        #Style the message
        font = QFont ("Arial", 30, QFont.Bold) #adjust font size and weight
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter) #align to center
        self.message_label.setStyleSheet("color:yellow;") #set text color to red
    
    def clear_unscanned_id_message(self):
        self.unscanned_id_timer.stop()
        self.message_label.clear()

    def clear_unscanned_message_and_start_timer(self):
        #clear the message and start the timer
        self.clear_unscanned_id_message()
        self.access_denied_timer.start(1000) #1000 milliseconds = 1 second
    #unscanned id message functionality - END
    
    #access granted message functionality - START
    def show_access_granted_message(self):
        #Hide user information labels
        self.user_name_label.hide()
        self.id_number_label.hide()
        self.photo_label.hide()

        #show the "REPEATED ACTION" message for a short duration
        message_duration = 3000 #3000 milliseconds = 3 seconds
        self.show_message("ACCESS GRANTED", message_duration)

        #Style the message
        font = QFont ("Arial", 30, QFont.Bold) #adjust font size and weight
        self.message_label.setFont(font)
        self.message_label.setAlignment(Qt.AlignCenter) #align to center
        self.message_label.setStyleSheet("color:green;") #set text color to green
    
    def clear_access_granted_message(self):
        self.access_granted_timer.stop()
        self.message_label.clear()

    def clear_access_granted_and_start_timer(self):
        #clear the message and start the timer
        self.clear_access_granted_message()
        self.access_granted_timer.start(1000) #1000 milliseconds = 1 second
    #access granted message functionality - END
    
    def show_message(self, message, duration = 1000):
        #show the message
        self.message_label.setText(message)

        #start the timer to clear the message after the specified duration
        self.message_timer.start(duration)

    def clear_message(self):
        self.message_timer.stop()
        self.message_label.clear()

    def clear_displayed_info(self):
        self.user_name_label.clear()
        self.id_number_label.clear()
        self.photo_label.clear()
        self.message_label.clear()
        self.display_timer.stop() #stop the display timer

    def setup_exit_button(self):
        exit_button = QPushButton("Exit")
        exit_button.setStyleSheet("background-color:red; color:white;")
        exit_button.setFont(QFont("Arial", 10))
        exit_button.clicked.connect(self.on_exit_button_clicked)

        #create a widget to hold the button and set the alignment
        button_widget = QWidget()
        button_layout = QVBoxLayout(button_widget)
        button_layout.addWidget(exit_button)
        button_layout.addWidget(exit_button, alignment = Qt.AlignBottom | Qt.AlignRight) #Align to bottom-right corner

        #add the button container to the central widget's layout
        central_layout = self.centralWidget().layout()
        central_layout.addWidget(button_widget)

    def on_exit_button_clicked(self):
        self.close() #close the window
        sys.exit(1)

#Create an instance of the GUI window
attendance_window = AttendanceWindow()
attendance_window.show()

#function to update the user ID label
def update_user_id_label(user_id):
    user_id_label.setText(f"User ID: {user_id}")

#function to handle RFID card scanning
def scan_rfid_card():
    while True:
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)
        if status == reader.MI_OK:
            print("Card detected")
            (status, uid) = reader.MFRC522_Anticoll()
            if status == reader.MI_OK:
                id_serial = ''.join([format(i, '02X') for i in uid[:4]])
                id_serial = id_serial[:8]
                print(f"Card Serial ID (Hex): {id_serial}")
                transaction_code = 'I'if clocking_state == 0 else 'O'

                #Get user information and photo
                is_registered_user, id_number, user_name, photo_file_name = get_user_info(id_serial)
                if is_registered_user:
                    photo_path = os.path.join(registered_users_photo_directory, photo_file_name)
                    attendance_window.show_user_info(user_name, id_number, photo_path)
                else:
                    attendance_window.show_repeated_action_message()
                
                #Clear the message and start the timer (allow swiping another card)
                attendance_window.clear_message_and_start_timer()

                log_attendance(id_serial, transaction_code)
                time.sleep(1)
                attendance_window.clear_user_info()
                attendance_window.clear_message()

#Create a thread for RFID card scanning
rfid_thread = threading.Thread(target=scan_rfid_card)
rfid_thread.daemon = True
rfid_thread.start()

#run the PyQt5 application
app.exec_()

try:
    #Create the photo directories if they don't exist
    if not os.path.exists(registered_users_photo_directory):
        os.makedirs(registered_users_photo_directory)
    if not os.path.exists(denied_users_photo_directory):
        os.makedirs(denied_users_photo_directory)
    while True:
        #scan for RFID cards
        (status, TagType) = reader.MFRC522_Request(reader.PICC_REQIDL)

        if status == reader.MI_OK:
            print("Card detected")
            #get the UID of the detected card
            (status, uid) = reader.MFRC522_Anticoll()

            if status == reader.MI_OK:
                #take the first 4 bytes of the UID and convert to an 8-character hexadecimal
                id_serial = ''.join([format(i, '02X') for i in uid[:4]])
                id_serial = id_serial[:8] #ensure it is 8 characters long
                print(f"Card Serial ID (Hex): {id_serial}")

                #Define transaction_code based on the clocking_state
                transaction_code = 'I' if clocking_state == 0 else 'O'

                #Log attendance data
                is_registered_user, id_number, user_name, photo_file_name = get_user_info(id_serial)
                if is_registered_user:
                    photo_path = os.path.join(registered_users_photo_directory, photo_file_name)
                    attendance_window.show_user_info(user_name, id_number, photo_path)
                else:
                    attendance_window.show_repeated_action_message()

                #Show the appropriate message for a short duration
                message_duration = 1000 #1 second 
                message = "Access Granted" if is_registered_user else "Access Denied"
                attendance_window.show_message(message, message_duration)
                log_attendance(id_serial, transaction_code)
                time.sleep(1)
                attendance_window.clear_user_info() #clear user info and photo
except KeyboardInterrupt:
    print("KeyboardInterrupt: Stopping camera preview.")
    camera.stop_preview() #stop the camera preview
    camera.close() #close the camera instance
    pwm.stop() #stop the PWM instance
    GPIO.cleanup() #clean up GPIO
    db_cursor.close()
    db_connection.close()

#inside the main part of the code:
if __name__ == "__main__":
    app = QApplication([])
    #create an attendance window
    attendance_window = AttendanceWindow()
    attendance_window.show()
    app.exec()


                

                


    


    

