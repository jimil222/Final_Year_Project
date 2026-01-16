import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def run_test():
    print(f"Testing API at {BASE_URL}")
    
    # 1. Register a fresh user to ensure clean state
    # Using a random email to avoid collision
    import random
    rand_id = random.randint(1000, 9999)
    email = f"test_api_{rand_id}@example.com"
    password = "password123"
    
    reg_payload = {
        "name": "API Tester",
        "email": email,
        "password": password,
        "roll_no": f"TEST-{rand_id}",
        "department": "Computer Science"
    }
    
    print(f"\n1. Registering user: {email} (Dept: Computer Science)...")
    try:
        r = requests.post(f"{BASE_URL}/auth/register", json=reg_payload)
        if r.status_code != 200:
            print(f"Registration Failed: {r.text}")
            # Try login if already exists (unlikely with rand_id but safety)
            return
        
        data = r.json()
        token = data.get("access_token")
        dept = data.get("department")
        print("Registration Successful.")
        print(f"Token received. Department in response: '{dept}'")
        
        if not token:
            print("CRITICAL: No access token returned!")
            return

    except Exception as e:
        print(f"Error during registration: {e}")
        return

    # 2. Get Recommendations
    print("\n2. Fetching Recommendations...")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        r = requests.get(f"{BASE_URL}/student/recommendations", headers=headers)
        if r.status_code == 200:
            rec_data = r.json()
            print("Response Response:")
            # Pretty print strictly
            print(json.dumps(rec_data, indent=2))
            
            books = rec_data.get("books", [])
            print(f"\nTotal Books Recieved: {len(books)}")
            if len(books) > 0:
                print("SUCCESS: API is returning books.")
                print(f"First book: {books[0].get('title')} ({books[0].get('department')})")
            else:
                print("FAILURE: API returned 0 books.")
        else:
            print(f"Failed to fetch recommendations. Status: {r.status_code}")
            print(r.text)

    except Exception as e:
        print(f"Error fetching recommendations: {e}")

if __name__ == "__main__":
    run_test()
