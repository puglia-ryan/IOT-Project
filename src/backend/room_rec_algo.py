from pymongo import MongoClient
import pandas as pd
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from datetime import datetime
import numpy as np

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

logging.basicConfig(level=logging.INFO)

# MongoDB Connection
try:
    client = MongoClient(
        "mongodb+srv://iotproject:iot123@sensordata.gc5h4.mongodb.net/?retryWrites=true&w=majority&appName=SensorData"
    )
    facilities_db = client["facilities_db"]
    agenda_db = client["agenda_db"]
    arduino_data_db = client["arduino_data_db"]
    # env_metrics_db = client["environmental_metrics_db"]
    # env_metrics_collection = env_metrics_db["room_metrics"]

except Exception as e:
    logging.error(f"Error connecting to MongoDB: {e}")

# Fetch agenda data
try:
    agenda_collection = agenda_db["agenda"]
    agenda_data = list(agenda_collection.find({}, {"_id": 0}))
    agenda_df = pd.DataFrame(agenda_data)
    agenda_df[['start_time', 'end_time']] = agenda_df['time_slot'].str.split('-', expand=True)
    agenda_df['start_time'] = agenda_df['start_time'].str.strip()
    agenda_df['end_time'] = agenda_df['end_time'].str.strip()
    agenda_df['start_time'] = pd.to_datetime(agenda_df['start_time'], format='%H:%M').dt.strftime('%H:%M')
    agenda_df['end_time'] = pd.to_datetime(agenda_df['end_time'], format='%H:%M').dt.strftime('%H:%M')

except Exception as e:
    logging.error(f"Error fetching agenda data: {e}")
    agenda_df = pd.DataFrame()

# Fetch sensor data
try:
    sensor_collection = arduino_data_db["sensor_readings"]
    sensor_data = list(sensor_collection.find({}, {"_id": 0}))
    sensor_df = pd.DataFrame(sensor_data)
    if "timestamp" in sensor_df.columns:
        sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"])
except Exception as e:
    logging.error(f"Error fetching sensor data: {e}")
    sensor_df = pd.DataFrame()

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
    room_data["facilities_score"] = room_data[
        ["videoprojector", "seating_capacity"]
    ].sum(axis=1, min_count=1)
except Exception as e:
    logging.error(f"Error merging datasets: {e}")
    room_data = pd.DataFrame()

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
    "sound_level": 45,  # dB
}


@app.route("/calendar_events", methods=["GET"])
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
                slot_start, slot_end = map(
                    lambda t: datetime.strptime(t.strip(), "%H:%M").time(),
                    time_slot.split(" - "),
                )

                # Check if event is within requested time range
                if slot_start >= start_time and slot_end <= end_time:
                    filtered_events.append(event)

        if not filtered_events:
            return jsonify({"message": "No events found in the specified period"}), 404

        return jsonify({"events": filtered_events}), 200

    except Exception as e:
        logging.error(f"Error fetching calendar events: {e}")
        return jsonify({"error": "Server error"}), 500


@app.route("/rooms_with_metrics", methods=["GET"])
def get_rooms_with_metrics():
    try:
        if facilities_df.empty:
            return jsonify({"error": "No facilities data available"}), 404
        if sensor_df.empty:
            return jsonify({"error": "No sensor data available"}), 404

        # Ensure timestamps are in datetime format
        sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"], errors="coerce")


        # Merge sensor readings with facilities
        rooms_with_env_data = pd.merge(
            sensor_df, facilities_df, on="room_name", how="left"
        )

        rooms_with_env_data.fillna(
            {
                "PM10": 0.0,
                "PM2.5": 0.0,
                "co2_level": 0.0,
                "computers": 0,
                "humidity": 0.0,
                "robots_for_training": 0,
                "room_name": "Room_1",
                "seating_capacity": 0,
                "sound_level": 0,
                "temperature": 0,
                "videoprojector": 1,
                "voc_level": 0.0,
            },
            inplace=True,
        )

        # Ensure no NaN values in the final JSON response
        rooms_with_env_data = rooms_with_env_data.replace({np.nan: None})
        rooms_with_env_data = rooms_with_env_data.astype(object).where(pd.notna(rooms_with_env_data), None)
        return (
            jsonify(
                {"rooms_with_metrics": rooms_with_env_data.to_dict(orient="records")}
            ),
            200,
        )

    except Exception as e:
        logging.error(f"Error fetching rooms with metrics: {e}")
        return jsonify({"error": "Server error", "details": str(e)}), 500


=======

# API Route: Get Time-Series Sensor Data
@app.route("/sensor_history", methods=["GET"])
def get_sensor_history():
    try:
        sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"], errors="coerce")
        room_name = request.args.get("room")
        limit = int(request.args.get("limit", 10))

        if room_name:
            filtered_data = sensor_df[sensor_df["room_name"] == room_name]
        else:
            filtered_data = sensor_df

        filtered_data = filtered_data.head(limit)
        return jsonify({"sensor_history": filtered_data.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Error fetching sensor history: {e}")
        return jsonify({"error": "Server error"}), 500


# API Route: Detect Disconnected Sensors
@app.route("/sensor_status", methods=["GET"])
def get_sensor_status():
    try:
        sensor_df["timestamp"] = pd.to_datetime(sensor_df["timestamp"], errors="coerce")
        sensor_df.sort_values("timestamp", inplace=True)

        # Identify gaps in sensor data
        sensor_df["time_diff"] = sensor_df.groupby("room_name")["timestamp"].diff()
        disconnected_sensors = sensor_df[
            sensor_df["time_diff"].dt.total_seconds() > 300
        ]  # More than 5 min gap

        return (
            jsonify(
                {"disconnected_sensors": disconnected_sensors.to_dict(orient="records")}
            ),
            200,
        )
    except Exception as e:
        logging.error(f"Error detecting sensor disconnections: {e}")
        return jsonify({"error": "Server error"}), 500

@app.route("/room_facilities", methods=["GET"])
def get_room_facilities():
    try:
        room_name = request.args.get("room")
        if not room_name:
            return jsonify({"error": "Room name is required"}), 400

        # Get facilities for the requested room
        facilities = facilities_df[facilities_df["room_name"] == room_name]

        if facilities.empty:
            return jsonify({"room_facilities": []}), 200  # Return empty list instead of error

        # Ensure NaN values are replaced with valid JSON-friendly types
        facilities = facilities.fillna({
            "computers": 0,
            "robots_for_training": 0,
            "videoprojector": 0,
            "seating_capacity": 0,
        }).replace({np.nan: None})

        # Convert all numeric values to native Python types
        facilities = facilities.astype(object).where(pd.notna(facilities), None)

        return jsonify({"room_facilities": facilities.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Error fetching room facilities: {e}")
        return jsonify({"error": "Server error"}), 500

# API Route for all rooms (without recommendation filtering)
@app.route("/rooms", methods=["GET"])
def get_all_rooms():
    try:
        print("Room Data Columns:", room_data.columns)  # Debugging line

        if room_data.empty:
            return jsonify({"error": "No room data available"}), 404

        # Check if 'facilities' exists
        if "facilities" in room_data.columns:
            all_rooms = room_data[
                ["room_name", "facilities_score", "time_slot", "facilities"]
            ]
        else:
            all_rooms = room_data[
                ["room_name", "facilities_score", "time_slot"]
            ]  # Avoid KeyError

        return jsonify({"rooms": all_rooms.to_dict(orient="records")}), 200
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        return jsonify({"error": "Server error"}), 500



#####UI1 RECOMENDATION
def update_final_end_time(df):
    time_rooms_df = df[['room_name', 'start_time', 'end_time']].drop_duplicates()
    time_rooms_df['final_end_time'] = time_rooms_df['end_time']
    for room in df['room_name'].unique():
        room_indices = time_rooms_df[time_rooms_df['room_name'] == room].index
        for i in range(len(room_indices) - 1, 0, -1):
            curr_idx = room_indices[i]
            prev_idx = room_indices[i - 1]
            if time_rooms_df.loc[prev_idx, 'end_time'] == time_rooms_df.loc[curr_idx, 'start_time']:
                time_rooms_df.loc[prev_idx, 'final_end_time'] = time_rooms_df.loc[curr_idx, 'final_end_time']
    time_rooms_df = time_rooms_df.sort_values(by=['room_name', 'start_time'])
    time_rooms_df = time_rooms_df.drop_duplicates(subset=['room_name', 'final_end_time'], keep='first')
    #print(time_rooms_df)
    return time_rooms_df
agenda_df = update_final_end_time(agenda_df)


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
def get_room_recommendation(temp_preference, noise_preference, time_slot, w1=0.5, w2=0.5):
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

    # Merge sensor data with room data
    filtered_room_data = pd.merge(room_data, filtered_sensor_data, on="room_name", how="inner")

    # Add initial final_end_time from end_time
    filtered_room_data['final_end_time'] = filtered_room_data['end_time']

    # Check if the temperature column exists
    if 'temperature' not in filtered_room_data.columns:
        print("Error: Temperature data is missing. Unable to process recommendations.")
        return pd.DataFrame(), None

    # apply noise filter first
    filtered_by_noise = filtered_room_data[filtered_room_data['sound_level'] <= noise_preference]

    if filtered_by_noise.empty:
        print(f"No rooms match your noise preference.")
        return pd.DataFrame(), "preferences"

    # Apply other filters (temperature, co2_level, etc.)
    filtered_rooms = filtered_by_noise[
        (filtered_by_noise['temperature'] >= temp_preference - 2) &
        (filtered_by_noise['temperature'] <= temp_preference + 2) &
        (filtered_by_noise['co2_level'] <= standards['co2_level']) &
        (filtered_by_noise['temperature'] >= standards['temperature_min']) &
        (filtered_by_noise['temperature'] <= standards['temperature_max']) &
        (filtered_by_noise['humidity'] >= standards['humidity_min']) &
        (filtered_by_noise['humidity'] <= standards['humidity_max']) &
        (filtered_by_noise['voc_level'] <= standards['voc_level']) &
        (filtered_by_noise['PM10'] <= standards['PM10']) &
        (filtered_by_noise['PM2.5'] <= standards['PM2.5'])
    ]

    filtered_rooms = filtered_rooms[filtered_rooms['start_time'] <= time_slot.split('-')[0]]
    filtered_rooms = filtered_rooms[filtered_rooms['final_end_time'] >= time_slot.split('-')[1]]

    if filtered_rooms.empty:
        print(f"No rooms are available for the selected time slot '{time_slot}' with your preferences.")
        return pd.DataFrame(), "preferences"

    # Group by room_name and summarize sensor values
    grouped_rooms = (
        filtered_rooms.groupby("room_name")
        .agg({
            "temperature": "median",  
            "co2_level": "median",
            "humidity": "median",
            "sound_level": "median",
            "facilities_score": "first", 
            "videoprojector": "first",
            "seating_capacity": "first",
            "computers": "first",
            "robots_for_training": "first",
        })
        .reset_index()
    )

    # Calculate rank based on the summarized data using w1 (temperature importance) and w2 (sound importance)
    grouped_rooms["rank"] = (
        grouped_rooms["facilities_score"] * 0.4 +
        grouped_rooms["sound_level"] * w2 +  # Adjust sound weight using w2
        grouped_rooms[["temperature", "co2_level", "humidity"]].mean(axis=1) * w1  # Adjust temperature weight using w1
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


@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        logging.info(f"Received request with data: {data}")  # Log request data

        temp_preference = float(data.get("temperature", 0))
        noise_preference = float(data.get("noiseLevel", 100))
        time_slot = data.get("time_slot", "")
        temperature_importance = float(data.get("temperature_importance", 0.5))  # Get the temperature importance
        noise_importance = float(data.get("noise_importance", 0.5))  # Get the noise importance

        if not temp_preference or not time_slot:
            return jsonify({"error": "Invalid input. Please provide temperature, noise level, and time_slot."}), 400

        # Pass the importance values to the recommendation function
        recommended_rooms, suggestion_type = get_room_recommendation(
            temp_preference, noise_preference, time_slot, w1=temperature_importance, w2=noise_importance
        )

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
