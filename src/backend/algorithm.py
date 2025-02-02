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

# Helper function for time slot overlap (optimized)
def is_time_within_slot(timestamp, user_time_slot):
    user_start, user_end = map(lambda t: pd.Timestamp(t.strip()).time(), user_time_slot.split('-'))
    timestamp_time = timestamp.time()
    return user_start <= timestamp_time <= user_end

# Regulations/standards
standards = {
    "co2_level": 1000,
    "temperature_min": 19,
    "temperature_max": 28,
    "humidity_min": 30,
    "humidity_max": 70,
    "voc_level": 400,
    "PM10": 50,
    "PM2.5": 25,
    "sound_level": 45
}

# Function to get recommendations based on time slot, temperature, and noise preference
def get_room_recommendation(temp_preference, time_slot, noise_preference):
    if not validate_time_slot_format(time_slot):
        print("Error: The time slot format is invalid. Please use the format 'HH:MM-HH:MM'.")
        return pd.DataFrame(), "time_slot"

    filtered_sensor_data = sensor_df[
        sensor_df['timestamp'].apply(lambda ts: is_time_within_slot(ts, time_slot))
    ]

    if filtered_sensor_data.empty:
        print(f"No sensor data is available for the time slot '{time_slot}'.")
        return pd.DataFrame(), "time_slot"

    filtered_room_data = pd.merge(room_data, filtered_sensor_data, on="room_name", how="inner")

    if 'temperature' not in filtered_room_data.columns or 'sound_level' not in filtered_room_data.columns:
        print("Error: Temperature or sound level data is missing. Unable to process recommendations.")
        return pd.DataFrame(), None

    # Check if 'voc_level' is present
    if 'voc_level' not in filtered_room_data.columns:
        print("Warning: 'voc_level' data is missing. Skipping VOC level filter.")
        voc_level_filter = True  # Set as always True if missing
    else:
        voc_level_filter = filtered_room_data['voc_level'] <= standards['voc_level']

    # Apply temperature, noise preference, and regulations
    filtered_rooms = filtered_room_data[
        (filtered_room_data['temperature'] >= temp_preference - 1) &
        (filtered_room_data['temperature'] <= temp_preference + 1) &
        (filtered_room_data['co2_level'] <= standards['co2_level']) &
        (filtered_room_data['temperature'] >= standards['temperature_min']) &
        (filtered_room_data['temperature'] <= standards['temperature_max']) &
        (filtered_room_data['humidity'] >= standards['humidity_min']) &
        (filtered_room_data['humidity'] <= standards['humidity_max']) &
        (voc_level_filter) &  # Only include VOC filter if 'voc_level' exists
        (filtered_room_data['PM10'] <= standards['PM10']) &
        (filtered_room_data['PM2.5'] <= standards['PM2.5']) &
        (filtered_room_data['sound_level'] <= noise_preference)  # Apply noise preference
    ]

    if filtered_rooms.empty:
        print(f"No rooms match your preferences and meet the regulations.")
        return pd.DataFrame(), "preferences"

    filtered_rooms = filtered_rooms[filtered_rooms['start_time'] <= time_slot.split('-')[0]]
    filtered_rooms = filtered_rooms[filtered_rooms['final_end_time'] >= time_slot.split('-')[1]]

    if filtered_rooms.empty:
        print(f"No rooms are available for the selected time slot '{time_slot}' with your preferences.")
        return pd.DataFrame(), "preferences"

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

    grouped_rooms["rank"] = (
        grouped_rooms["facilities_score"] * 0.5 +
        grouped_rooms[["temperature", "co2_level", "humidity", "sound_level"]].mean(axis=1) * 0.5
    ).rank(ascending=False)

    grouped_rooms["facilities_list"] = grouped_rooms.apply(
        lambda row: {
            "videoprojector": row.get("videoprojector", 0),
            "seating_capacity": row.get("seating_capacity", 0),
            "computers": row.get("computers", 0),
            "robots_for_training": row.get("robots_for_training", 0)
        },
        axis=1
    )

    return grouped_rooms.sort_values(by="rank").head(10), None

# Fetch data from MongoDB
client = MongoClient("mongodb+srv://iotproject:iot123@sensordata.gc5h4.mongodb.net/?retryWrites=true&w=majority&appName=SensorData")

facilities_db = client["facilities_db"]
agenda_db = client["agenda_db"]
arduino_data_db = client["arduino_data_db"]

sensor_collection = arduino_data_db["sensor_readings"]
sensor_data = list(sensor_collection.find({}, {"_id": 0}))
sensor_df = pd.DataFrame(sensor_data)
sensor_df['timestamp'] = pd.to_datetime(sensor_df['timestamp'])

agenda_collection = agenda_db["agenda"]
agenda_data = list(agenda_collection.find({}, {"_id": 0}))
agenda_df = pd.DataFrame(agenda_data)
agenda_df[['start_time', 'end_time']] = agenda_df['time_slot'].str.split('-', expand=True)
agenda_df['start_time'] = agenda_df['start_time'].str.strip()
agenda_df['end_time'] = agenda_df['end_time'].str.strip()
agenda_df['start_time'] = pd.to_datetime(agenda_df['start_time'], format='%H:%M').dt.strftime('%H:%M')
agenda_df['end_time'] = pd.to_datetime(agenda_df['end_time'], format='%H:%M').dt.strftime('%H:%M')

def update_final_end_time(df):
    df['final_end_time'] = df['end_time']
    for room in df['room_name'].unique():
        room_indices = df[df['room_name'] == room].index
        for i in range(len(room_indices) - 1, 0, -1):
            curr_idx = room_indices[i]
            prev_idx = room_indices[i - 1]
            if df.loc[prev_idx, 'end_time'] == df.loc[curr_idx, 'start_time']:
                df.loc[prev_idx, 'final_end_time'] = df.loc[curr_idx, 'final_end_time']
    return df

agenda_df = update_final_end_time(agenda_df)

facilities_collection = facilities_db["facilities"]
facilities_data = list(facilities_collection.find({}, {"_id": 0}))
for facility in facilities_data:
    if "facilities" in facility:
        facilities_info = facility.pop("facilities")
        for key, value in facilities_info.items():
            facility[key] = 1 if value is True else 0 if value is False else value

facilities_df = pd.DataFrame(facilities_data)

room_data = pd.merge(agenda_df, facilities_df, on="room_name", how="left")
room_data['facilities_score'] = room_data[['videoprojector', 'seating_capacity', 'computers', 'robots_for_training']].sum(axis=1)

# Main loop for user input and recommendations
while True:
    temp_preference = input("Enter your preferred room temperature: ")
    noise_preference = input("Enter your preferred maximum noise level (dB): ")
    time_slot = input("Enter your preferred time slot (e.g., '08:00-10:00'): ")

    try:
        temp_preference = float(temp_preference)
        noise_preference = float(noise_preference)
    except ValueError:
        print("Error: The temperature and noise level must be valid numbers.")
        continue

    recommended_rooms, suggestion_type = get_room_recommendation(temp_preference, time_slot, noise_preference)

    if not recommended_rooms.empty:
        print(recommended_rooms[['room_name', 'temperature', 'co2_level', 'humidity', 'sound_level', 'facilities_list', 'rank']])
        break
    else:
        print("Please adjust your preferences based on the suggestions above.")

