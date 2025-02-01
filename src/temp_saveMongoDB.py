import serial
import pymongo
from datetime import datetime
import time

# Set up the serial connection
ser = serial.Serial('COM4', 9600)  # Windows: 'COM3', Linux/Mac: '/dev/ttyUSB0'

# Set up MongoDB connection
client = pymongo.MongoClient("mongodb+srv://antoniacuba:LCKP6H9sghTmyzn6@sensordata.gc5h4.mongodb.net/arduino_data_db") 
db = client['arduino_data_db']  # Database name
collection = db['temperature_readings']  # Collection name

while True:
    # Read data from the serial port
    data = ser.readline().decode('utf-8').strip()

    # Check if the data contains temperature info (depending on Arduino format)
    if data.startswith("Temperature:"):
        temperature = float(data.split(":")[1].strip())

        # Create a record to insert into MongoDB
        record = {
            "temperature": temperature,
            "timestamp": datetime.now()
        }

        # Insert the record into MongoDB
        collection.insert_one(record)

        print(f"Temperature: {temperature} °C, Data inserted to MongoDB")