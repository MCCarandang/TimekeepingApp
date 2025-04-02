import requests
import time
import random

# URL of Django backend
url = 'http://<your-django-backend-url>/record_attendance/'  # Update this with your actual URL

def mock_rfid_reader():
    """Simulate reading an RFID tag."""
    # Generate a random RFID tag for demonstration purposes
    return random.randint(1000000000, 9999999999)

try:
    while True:
        print("Simulating RFID tag reading...")
        rfid_tag = mock_rfid_reader()
        print(f"RFID Tag: {rfid_tag}")

        # Send the RFID tag to the Django backend
        response = requests.post(url, data={'rfid_tag': rfid_tag})
        print(response.json())  # Print the response from the server

        time.sleep(1)  # Wait for a second before reading again
except KeyboardInterrupt:
    print("Program terminated.")