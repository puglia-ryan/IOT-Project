# Room Recommendation & Sensor Data Dashboard

## Overview

This project consists of two web-based user interfaces (UIs) and an API that work together to provide real-time sensor data, room facilities information, and a room recommendation system. The system allows users to select rooms, view environmental conditions, check facility availability, and receive recommendations based on their preferences.

## Components

API (Flask-based backend) - Provides sensor data, room facilities, and calendar events.

UI 1: Room Recommendation System - Allows users to input preferences and receive recommended rooms.

UI 2: Sensor Data Dashboard - Displays real-time environmental sensor data, room facilities, and calendar events.

## Running the API

### Prerequisites

- Python 3.x

- Flask

- pymongo

- pandas

- flask_cors

### Start the API:

Run the following command to start the API: **"python room_rec_algo.py"**

The API will be available at http://localhost:5009.

### API Endpoints

- GET /calendar_events?start=YYYY-MM-DDTHH:MM:SS&end=YYYY-MM-DDTHH:MM:SS - Fetches calendar events for the given time range.

- GET /rooms_with_metrics - Retrieves room sensor metrics.

- GET /room_facilities?room=<room_name> - Gets facilities available in the specified room.

- POST /recommend - Accepts user preferences (temperature, time slot) and returns recommended rooms.

## UI 1: Room Recommendation System

### Features

- Users can input their preferred temperature and time slot.

- The system provides room recommendations based on available sensor data and facilities.

- Results are displayed dynamically in the rankings section.

### Running the UI

Open index.html in a web browser.

Adjust the temperature slider and time slot.

Click Submit to receive room recommendations.

## UI 2: Sensor Data Dashboard

### Features

- Users can select a room to view sensor data (temperature, CO2 levels, humidity, sound level).

- A facilities table displays room resources (computers, projectors, seating, robots).

- Graphs update dynamically when the user selects a room.

### Running the UI

Open index.html in a web browser.

Select a room from the dropdown menu.

View graphs and facilities related to the selected room.

