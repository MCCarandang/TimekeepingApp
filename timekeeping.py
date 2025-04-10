import time
from time import time
import RPi.GPIO as GPIO 
import mfrc522
import sqlite3
import mysql.connector
import os
import socket
import threading
import subprocess

import uuid
import sys

import tkinter as tk
from tkinter import messagebox

# GPIO.setwarnings(False)

# Initialize the RFID reader
reader = mfrc522.MFRC522()

# MySQL Database connection
def connect_db():
    return mysql.connector.connect(
        host="10.44.0.170",
        user="raspberrypi",
        password="12345",
        database="timekeeping_app.db"
    )

# Check if the RFID is registered
def check_rfid(rfid_id):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM emp_profiles WHERE rfid_id = %s", (rfid_id,))
    result = cursor.fetchone()
    conn.close()
    return result

# Log unauthorized attempt
def log_unauthorized_attempt(rfid_id, photo=None):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO unauth_logs (rfid_id, status, photo) VALUES (%s, %s, %s)",
                   (rfid_id, "unauthorized", photo))
    conn.commit()
    conn.close()
    
# Function to read RFID
def read_rfid():
    reader = SimpleMFRC522()
    try:
        print("Tap your ID")
        rfid_id, text = reader.read()
        print(f"RFID ID scanned: {rfid_id}")

        # Check if the scanned RFID ID exists in the database
        profile = check_rfid(rfid_id)
        if profile:
            messagebox.showinfo("Access Granted", f"Welcome {profile[1]} {profile[2]}!")    # First and Last name from profile
            # Log the attendance (You can modify this part to log time-in, time-out, etc.)
            # Log attendance code here...
        else:
            log_unauthorized_attempt(rfid_id)
            messagebox.showwarning("Access Denied", "Unauthorized user!")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        reader.cleanup()

# Frontend UI with Tkinter
def create_ui():
    root = tk.Tk()
    root.title("Timekeeping System")
    root.geometry("300x200")

    label = tk.Label(root, text="RFID Timekeeping System", font=("Arial", 14))
    label.pack(pady=20)

    scan_button = tk.Button(root, text="Scan RFID", command=read_rfid, font=("Arial", 12))
    scan_button.pack(pady=20)

    root.mainloop()

# Run the app
if __name__ == "__main__":
    create_ui()