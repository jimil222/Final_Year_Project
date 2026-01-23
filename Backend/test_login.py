import requests
import json

# Test admin login
url = "http://127.0.0.1:8000/auth/login"
payload = {
    "email": "admin@library.edu",
    "password": "password123",
    "role": "admin"
}

print("Testing admin login...")
print(f"URL: {url}")
print(f"Payload: {json.dumps(payload, indent=2)}")
print()

try:
    response = requests.post(url, json=payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
    print(f"Response text: {response.text if 'response' in locals() else 'No response'}")
