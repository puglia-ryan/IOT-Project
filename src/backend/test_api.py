import requests
import json

############
# Ensure the API is running before running this script
############

# Base API URL
BASE_URL = "http://127.0.0.1:5009"

def run_test(name, method, url, expected_status, json_data=None, params=None):
    """Helper function to run a test and return result."""
    try:
        response = method(url, json=json_data, params=params)
        result = {
            "test": name,
            "status_code": response.status_code,
            "expected": expected_status,
            "passed": response.status_code == expected_status,
            "response": response.json()
        }
        return result
    except Exception as e:
        return {"test": name, "error": str(e), "passed": False}

def test_recommend():
    return run_test(
        "Test /recommend",
        requests.post,
        f"{BASE_URL}/recommend",
        200,
        json_data={"temperature": 22, "min_seating_capacity": 20}
    )

def test_recommend_missing_params():
    return run_test(
        "Test /recommend with missing parameters",
        requests.post,
        f"{BASE_URL}/recommend",
        400,
        json_data={}
    )

def test_get_rooms():
    return run_test(
        "Test /rooms",
        requests.get,
        f"{BASE_URL}/rooms",
        200
    )

def test_get_rooms_with_metrics():
    return run_test(
        "Test /rooms_with_metrics",
        requests.get,
        f"{BASE_URL}/rooms_with_metrics",
        200
    )

def test_get_calendar_events():
    return run_test(
        "Test /calendar_events",
        requests.get,
        f"{BASE_URL}/calendar_events",
        200,
        params={"start": "2024-11-18T08:00:00", "end": "2024-11-18T10:00:00"}
    )

def test_calendar_events_missing_params():
    return run_test(
        "Test /calendar_events with missing parameters",
        requests.get,
        f"{BASE_URL}/calendar_events",
        400
    )

if __name__ == "__main__":
    print("\n🚀 Starting API Tests...\n")
    
    # Run all tests
    tests = [
        test_recommend(),
        test_recommend_missing_params(),
        test_get_rooms(),
        test_get_rooms_with_metrics(),
        test_get_calendar_events(),
        test_calendar_events_missing_params()
    ]
    
    # Print summary
    print("\n✅ Test Results:")
    for test in tests:
        print(f"{test['test']}: {'✅ Passed' if test['passed'] else '❌ Failed'} (Expected {test['expected']}, Got {test.get('status_code', 'Error')})")
    
    print("\n✅ All tests completed!")
