import requests
import json
############
# Ensure the API is running before running this script
############

# Base API URL
BASE_URL = "http://127.0.0.1:5009"

def test_recommend():
    """Test the /recommend endpoint"""
    url = f"{BASE_URL}/recommend"
    data = {
        "temperature": 22,
        "min_seating_capacity": 20
    }

    print("\n🔍 Testing /recommend endpoint...")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

def test_recommend_missing_params():
    """Test /recommend with missing parameters"""
    url = f"{BASE_URL}/recommend"
    data = {}  # Missing temperature

    print("\n❌ Testing /recommend with missing parameters...")
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

def test_get_rooms():
    """Test the /rooms endpoint"""
    url = f"{BASE_URL}/rooms"

    print("\n🔍 Testing /rooms endpoint...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

def test_get_rooms_with_metrics():
    """Test the /rooms_with_metrics endpoint"""
    url = f"{BASE_URL}/rooms_with_metrics"

    print("\n🔍 Testing /rooms_with_metrics endpoint...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

def test_get_calendar_events():
    """Test the /calendar_events endpoint"""
    url = f"{BASE_URL}/calendar_events"
    params = {
        "start": "2024-11-18T08:00:00",
        "end": "2024-11-18T10:00:00"
    }

    print("\n🔍 Testing /calendar_events endpoint...")
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

def test_calendar_events_missing_params():
    """Test /calendar_events with missing parameters"""
    url = f"{BASE_URL}/calendar_events"

    print("\n❌ Testing /calendar_events with missing parameters...")
    response = requests.get(url)
    print(f"Status Code: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=4))

if __name__ == "__main__":
    print("\n🚀 Starting API Tests...\n")
    
    # Run all tests
    test_recommend()
    test_recommend_missing_params()
    test_get_rooms()
    test_get_rooms_with_metrics()
    test_get_calendar_events()
    test_calendar_events_missing_params()

    print("\n✅ All tests completed!")

