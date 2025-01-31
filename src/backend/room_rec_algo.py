from pymongo import MongoClient
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.INFO)

# MongoDB Connection
try:
    client = MongoClient("mongodb+srv://iotproject:iot123@sensordata.gc5h4.mongodb.net/?retryWrites=true&w=majority&appName=SensorData")
    facilities_db = client["facilities_db"]
    agenda_db = client["agenda_db"]
    arduino_data_db = client["arduino_data_db"]
    #env_metrics_db = client["environmental_metrics_db"]
    #env_metrics_collection = env_metrics_db["room_metrics"]

except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")

# Fetch agenda data
try:
    agenda_collection = agenda_db["agenda"]
    agenda_data = list(agenda_collection.find({}, {"_id": 0}))
    agenda_df = pd.DataFrame(agenda_data)
except Exception as e:
    logging.error(f"Error fetching agenda data: {e}")
    agenda_df = pd.DataFrame()

# Fetch sensor data
try:
    sensor_collection = arduino_data_db["sensor_readings"]
    sensor_data = list(sensor_collection.find({}, {"_id": 0}))
    sensor_df = pd.DataFrame(sensor_data)
    sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])
except Exception as e:
    logging.error(f"Error fetching sensor data: {e}")
    sensor_df = pd.DataFrame()


# Fetch temperature readings
try:
    temp_collection = arduino_data_db["temperature_readings"]
    temp_data = list(temp_collection.find({}, {"_id": 0}))
    temp_df = pd.DataFrame(temp_data)
    temp_df['timestamp'] = pd.to_datetime(temp_df['timestamp'])
except Exception as e:
    logging.error(f"Error fetching temperature readings: {e}")
    temp_df = pd.DataFrame()

# Fetch facilities data
try:
    facilities_collection = facilities_db["facilities"]
    facilities_data = list(facilities_collection.find({}, {"_id": 0}))
    for facility in facilities_data:
        if "facilities" in facility:
            facilities_info = facility.pop("facilities")
            for key, value in facilities_info.items():
                facility[key] = int(value) if isinstance(value, bool) else value
    facilities_df = pd.DataFrame(facilities_data)
except Exception as e:
    logging.error(f"Error fetching facilities data: {e}")
    facilities_df = pd.DataFrame()


# Merge datasets
try:
    room_data = pd.merge(agenda_df, facilities_df, on="room_name", how="left")
    room_data['facilities_score'] = room_data[['videoprojector', 'seating_capacity']].sum(axis=1, min_count=1)
except Exception as e:
    logging.error(f"Error merging datasets: {e}")
    room_data = pd.DataFrame()

@app.route('/calendar_events', methods=['GET'])
def get_calendar_events():
    try:
        start_time_str = request.args.get("start")
        end_time_str = request.args.get("end")

        if not start_time_str or not end_time_str:
            return jsonify({"error": "Start and end times are required"}), 400

        # Convert ISO 8601 format (YYYY-MM-DDTHH:MM:SS) into HH:MM
        start_time = datetime.strptime(start_time_str, "%Y-%m-%dT%H:%M:%S").time()
        end_time = datetime.strptime(end_time_str, "%Y-%m-%dT%H:%M:%S").time()

        # Fetch all events from MongoDB
        events = list(agenda_collection.find({}, {"_id": 0}))

        # Filter events based on time slot
        filtered_events = []
        for event in events:
            time_slot = event.get("time_slot", "")
            if " - " in time_slot:
                slot_start, slot_end = map(lambda t: datetime.strptime(t.strip(), "%H:%M").time(), time_slot.split(" - "))

                # Check if event is within requested time range
                if slot_start >= start_time and slot_end <= end_time:
                    filtered_events.append(event)

        if not filtered_events:
            return jsonify({"message": "No events found in the specified period"}), 404

        return jsonify({"events": filtered_events}), 200

    except Exception as e:
        logging.error(f"Error fetching calendar events: {e}")
        return jsonify({"error": "Server error"}), 500

# Fetch rooms with environmental metrics
@app.route('/rooms_with_metrics', methods=['GET'])
def get_rooms_with_metrics():
    try:
        if facilities_df.empty:
            return jsonify({"error": "No facilities data available"}), 404
        if sensor_df.empty:
            return jsonify({"error": "No sensor data available"}), 404
        if temp_df.empty:
            return jsonify({"error": "No temperature data available"}), 404

        # Merge sensor readings with facilities
        rooms_with_env_data = pd.merge(sensor_df, facilities_df, on="room_name", how="left")

        # Merge temperature readings separately
        rooms_with_env_data = pd.merge(rooms_with_env_data, temp_df, on="timestamp", how="left")

        return jsonify({"rooms_with_metrics": rooms_with_env_data.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Error fetching rooms with metrics: {e}")
        return jsonify({"error": "Server error"}), 500

# API Route for all rooms (without recommendation filtering)
@app.route('/rooms', methods=['GET'])
def get_all_rooms():
    try:
        print("Room Data Columns:", room_data.columns)  # Debugging line

        if room_data.empty:
            return jsonify({"error": "No room data available"}), 404

        # Check if 'facilities' exists
        if "facilities" in room_data.columns:
            all_rooms = room_data[["room_name", "facilities_score", "time_slot", "facilities"]]
        else:
            all_rooms = room_data[["room_name", "facilities_score", "time_slot"]]  # Avoid KeyError

        return jsonify({"rooms": all_rooms.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Server error"}), 500


# Function to validate time slot format
def validate_time_slot_format(time_slot):
    try:
        start, end = time_slot.split('-')
        pd.Timestamp(start.strip())
        pd.Timestamp(end.strip())
        return True
    except Exception:
        return False

# Helper function for time slot overlap
def is_time_within_slot(timestamp, user_time_slot):
    try:
        # Extract time portion only for comparison
        timestamp_time = timestamp.time()
        user_start, user_end = map(lambda t: pd.Timestamp(t.strip()).time(), user_time_slot.split('-'))
        return user_start <= timestamp_time <= user_end
    except Exception as e:
        print(f"Error in time slot comparison: {e}")
        return False

# Regulations/standards
standards = {
    "co2_level": 1000,
    "temperature_min": 19,
    "temperature_max": 28,
    "humidity_min": 30,
    "humidity_max": 70,
    "voc_level": 400,  # WHO guideline (ppb)
    "PM10": 50,  # μg/m³
    "PM2.5": 25,  # μg/m³
    "sound_level": 45  # dB
}



def is_room_available(room_name, time_slot):
    """
    Check if a room is available based on the agenda.
    If the room appears in the agenda for the given time slot, it's considered booked.
    """
    booked_slots = agenda_df[agenda_df["room_name"] == room_name]["time_slot"].tolist()
    
    for booked_time in booked_slots:
        if is_time_within_slot(pd.Timestamp(time_slot.split('-')[0]), booked_time):
            return False  # Room is booked

    return True  # Room is available



# Function to get recommendations based on time slot and preferences
def get_room_recommendation(temp_preference, time_slot):
    # Check if the provided time slot is in the correct format
    if not validate_time_slot_format(time_slot):
        print("Error: The time slot format is invalid. Please use the format 'HH:MM-HH:MM'.")
        return pd.DataFrame(), "time_slot"

    # Filter sensor data for the given time slot
    filtered_sensor_data = sensor_df[
        sensor_df['timestamp'].apply(lambda ts: is_time_within_slot(ts, time_slot))
    ]

    if filtered_sensor_data.empty:
        print(f"No sensor data is available for the time slot '{time_slot}'.")
        return pd.DataFrame(), "time_slot"

 
    # Filter out rooms that are booked in the agenda for the given time slot
    available_rooms = room_data[room_data["room_name"].apply(lambda room: is_room_available(room, time_slot))]

    # Merge available rooms with sensor data
    filtered_room_data = pd.merge(available_rooms, filtered_sensor_data, on="room_name", how="inner")

    # Check if the temperature column exists
    if 'temperature' not in filtered_room_data.columns:
        print("Error: Temperature data is missing. Unable to process recommendations.")
        return pd.DataFrame(), None

    # Apply temperature preference and regulations
    filtered_rooms = filtered_room_data[
        (filtered_room_data['temperature'] >= temp_preference - 1) &
        (filtered_room_data['temperature'] <= temp_preference + 1) &
        (filtered_room_data['co2_level'] <= standards['co2_level']) &
        (filtered_room_data['temperature'] >= standards['temperature_min']) &
        (filtered_room_data['temperature'] <= standards['temperature_max']) &
        (filtered_room_data['humidity'] >= standards['humidity_min']) &
        (filtered_room_data['humidity'] <= standards['humidity_max']) &
        (filtered_room_data['voc_level'] <= standards['voc_level']) &
        (filtered_room_data['PM10'] <= standards['PM10']) &
        (filtered_room_data['PM2.5'] <= standards['PM2.5']) &
        (filtered_room_data['sound_level'] <= standards['sound_level'])
    ]

    if filtered_rooms.empty:
        print(f"No rooms match your preferences and meet the regulations for the time slot '{time_slot}'.")
        
        # Suggest alternative temperatures if temperature is the issue
        if (temp_preference < standards['temperature_min'] or 
            temp_preference > standards['temperature_max']):
            print(f"The preferred temperature {temp_preference}°C is outside the acceptable range.")
            available_temps = (
                room_data['temperature']
                .dropna()
                .unique() if 'temperature' in room_data.columns else []
            )
            if len(available_temps) > 0:
                print(f"Available temperatures within acceptable range: {sorted(available_temps)}")
        else:
            print(f"Available time slots for the selected temperature preference: {time_slot}.")
        
        return pd.DataFrame(), "preferences"

    # Group by room_name and summarize sensor values
    grouped_rooms = (
        filtered_rooms.groupby("room_name")
        .agg({
            "temperature": "median",  # Use median temperature for summarizing
            "co2_level": "median",
            "humidity": "median",
            "sound_level": "median",
            "facilities_score": "first",  # Keep facilities score as-is
            "videoprojector": "first",
            "seating_capacity": "first",
            "computers": "first",
            "robots_for_training": "first",
        })
        .reset_index()
    )

    # Calculate rank based on the summarized data
    grouped_rooms["rank"] = (
        grouped_rooms["facilities_score"] * 0.5 +
        grouped_rooms[["temperature", "co2_level", "humidity", "sound_level"]].mean(axis=1) * 0.5
    ).rank(ascending=False)

    # Prepare the facilities column as a string/dictionary, handling NaN values
    grouped_rooms["facilities"] = grouped_rooms.apply(
        lambda row: {
            "videoprojector": row.get("videoprojector", 0) if pd.notna(row.get("videoprojector")) else 0,
            "seating_capacity": row.get("seating_capacity", 0) if pd.notna(row.get("seating_capacity")) else 0,
            "computers": row.get("computers", 0) if pd.notna(row.get("computers")) else 0,
            "robots_for_training": row.get("robots_for_training", 0) if pd.notna(row.get("robots_for_training")) else 0
        },
        axis=1
    )

    # Select the required columns (rank, room_name, and facilities)
    final_recommendation = grouped_rooms[["rank", "room_name", "facilities"]]

    # Return top 10 recommendations
    return final_recommendation.sort_values(by="rank").head(10), None


def insert_environmental_data(room_name, temperature, co2_level, humidity, voc_level, pm10, pm2_5, sound_level):
    try:
        # Insert data into MongoDB collection
        env_data = {
            "room_name": room_name,
            "temperature_min": temperature.get("min"),
            "temperature_max": temperature.get("max"),
            "co2_level": co2_level,
            "humidity": humidity,
            "voc_level": voc_level,
            "PM10": pm10,
            "PM2.5": pm2_5,
            "sound_level": sound_level,
            "timestamp": pd.Timestamp.now()
        }
        env_metrics_collection.insert_one(env_data)
        logging.info(f"Environmental data inserted for room: {room_name}")
    except Exception as e:
        logging.error(f"Error inserting environmental data: {e}")

# API Route recommended Rooms after filter
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        logging.info(f"Received request with data: {data}")  # Log request data

        temp_preference = float(data.get("temperature", 0))
        time_slot = data.get("time_slot", "")

        if not temp_preference or not time_slot:
            return jsonify({"error": "Invalid input. Please provide temperature and time_slot."}), 400

        recommended_rooms, suggestion_type = get_room_recommendation(temp_preference, time_slot)

        if recommended_rooms.empty:
            logging.info(f"No matching rooms for input: {data}")  # Log no results
            return jsonify({"error": "No rooms match the preferences."}), 404

        logging.info(f"Returning rooms: {recommended_rooms.to_dict(orient='records')}")  # Log results
        return jsonify({"rooms": recommended_rooms.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Server error"}), 500


if __name__ == "__main__":
    app.run(port=5009, debug=True)


