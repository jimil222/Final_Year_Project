import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def create_admin():
    print("Creating Admin User...")
    name = input("Name: ")
    email = input("Email: ")
    password = input("Password: ")
    roll_no = input("Roll No (Admin ID): ")
    
    payload = {
        "name": name,
        "email": email,
        "password": password,
        "roll_no": roll_no,
        "role": "admin"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=payload)
        if response.status_code == 200:
            print("Admin created successfully!")
            print(json.dumps(response.json(), indent=2))
        else:
            print(f"Failed: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()
