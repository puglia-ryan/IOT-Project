from pymongo import MongoClient
import pandas as pd


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

    # Merge sensor data with room data
    filtered_room_data = pd.merge(room_data, filtered_sensor_data, on="room_name", how="inner")

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

    # Include facilities in the output
    grouped_rooms["facilities_list"] = grouped_rooms.apply(
        lambda row: {
            "videoprojector": row.get("videoprojector", 0),
            "seating_capacity": row.get("seating_capacity", 0),
            "computers": row.get("computers", 0),
            "robots_for_training": row.get("robots_for_training", 0)
        },
        axis=1
    )

    # Return top 10 recommendations
    return grouped_rooms.sort_values(by="rank").head(10), None


# Step 1: Connect to MongoDB and Fetch Data
client = MongoClient("mongodb+srv://iotproject:iot123@sensordata.gc5h4.mongodb.net/?retryWrites=true&w=majority&appName=SensorData")

# Access databases
facilities_db = client["facilities_db"]
agenda_db = client["agenda_db"]
arduino_data_db = client["arduino_data_db"]

# Fetch sensor data for all rooms
sensor_collection = arduino_data_db["sensor_readings"]
sensor_data = list(sensor_collection.find({}, {"_id": 0}))
sensor_df = pd.DataFrame(sensor_data)
sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])

# Fetch agenda data
agenda_collection = agenda_db["agenda"]
agenda_data = list(agenda_collection.find({}, {"_id": 0}))
agenda_df = pd.DataFrame(agenda_data)

# Fetch facilities data and flatten it
facilities_collection = facilities_db["facilities"]
facilities_data = list(facilities_collection.find({}, {"_id": 0}))
for facility in facilities_data:
    if "facilities" in facility:
        facilities_info = facility.pop("facilities")
        # Flatten nested fields
        for key, value in facilities_info.items():
            facility[key] = 1 if value is True else 0 if value is False else value

facilities_df = pd.DataFrame(facilities_data)

# Merge agenda, facilities, and sensor data
room_data = pd.merge(agenda_df, facilities_df, on="room_name", how="left")
room_data['facilities_score'] = room_data[['videoprojector', 'seating_capacity', 'computers', 'robots_for_training']].sum(axis=1)

# Loop for user inputs and suggestions
while True:
    temp_preference = input("Enter your preferred room temperature: ")
    time_slot = input("Enter your preferred time slot (e.g., '08:00-10:00'): ")

    # Validate temperature input
    try:
        temp_preference = float(temp_preference)
    except ValueError:
        print("Error: The temperature must be a valid number.")
        continue

    # Get recommendations
    recommended_rooms, suggestion_type = get_room_recommendation(temp_preference, time_slot)

    if not recommended_rooms.empty:
        print(recommended_rooms[['room_name', 'temperature', 'co2_level', 'humidity', 'sound_level', 'facilities_list', 'rank']])
        break
    else:
        print("Please adjust your preferences based on the suggestions above.")
