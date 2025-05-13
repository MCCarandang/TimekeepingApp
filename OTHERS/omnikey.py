from smartcard.System import readers
from smartcard.util import toHexString
import time

def get_uid(connection):
    # APDU to get UID from MIFARE-type cards (works for some cards)
    GET_UID = [0xFF, 0xCA, 0x00, 0x00, 0x00]

    try:
        data, sw1, sw2 = connection.transmit(GET_UID)
        if sw1 == 0x90 and sw2 == 0x00:
            uid = toHexString(data)
            return uid
        else:
            print(f"Failed to retrieve UID. SW1: {sw1}, SW2: {sw2}")
            return None
    except Exception as e:
        print("Error transmitting APDU:", e)
        return None

try:
    # Get available PC/SC readers
    available_readers = readers()
    
    if not available_readers:
        print("No smart card readers found.")
        exit()

    reader = available_readers[0]
    print(f"Using reader: {reader}")

    connection = reader.createConnection()
    
    print("Place your RFID tag near the OMNIKEY reader...")

    while True:
        try:
            connection.connect()
            print("Card detected!")

            uid = get_uid(connection)
            if uid:
                print("RFID Tag UID:", uid)
            else:
                print("UID could not be retrieved. Printing ATR instead:")
                atr = connection.getATR()
                print("ATR:", toHexString(atr))
            break  # Exit after successful read
        except:
            time.sleep(1)  # No card, wait and try again

except KeyboardInterrupt:
    print("Program interrupted by user.")
