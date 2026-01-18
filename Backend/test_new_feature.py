import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_recommend_similar():
    print("Testing GET /student/recommend-similar...")
    
    # 1. Login to get token (using existing test user credentials or creating one)
    # reusing logic from test_api_simple.py roughly
    user_data = {
        "email": "test_api_1468@example.com", # From previous logs
        "password": "password123" # Assuming default password logic or we register new
    }
    
    # Register new just in case
    import random
    rand_id = random.randint(10000, 99999)
    email = f"user_{rand_id}@test.com"
    r = requests.post(f"{BASE_URL}/auth/register", json={
        "name": "Test User",
        "email": email,
        "password": "password123",
        "roll_no": f"R-{rand_id}",
        "department": "Computer Science"
    })
    token = r.json().get("access_token")
    
    if not token:
        print("Failed to get token.")
        return

    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Test Recommendation (Normal)
    title_valid = "Data structures through C++" # This is now in dummyBooks.js
    print(f"\nRequesting similar to (Valid): '{title_valid}'")
    r = requests.get(f"{BASE_URL}/student/recommend-similar", params={"title": title_valid}, headers=headers)
    if r.status_code == 200:
        data = r.json()
        print(f"Valid Book Result Count: {len(data.get('books', []))}")
        if len(data.get('books', [])) > 0:
             print(f"First Recommendation: {data.get('books')[0]['title']}")
    
    # Test another one
    title_valid_2 = "Machine design data book"
    print(f"\nRequesting similar to (Valid - Mech): '{title_valid_2}'")
    r = requests.get(f"{BASE_URL}/student/recommend-similar", params={"title": title_valid_2}, headers=headers)
    if r.status_code == 200:
         print(f"Valid Book Result Count: {len(r.json().get('books', []))}")
    
    # 3. Test Recommendation (Strict Content-Based - No Fallback)
    title_invalid = "Introduction to Algorithms" # Not in CSV
    print(f"\nRequesting similar to (Missing): '{title_invalid}'")
    
    r = requests.get(f"{BASE_URL}/student/recommend-similar", params={"title": title_invalid}, headers=headers)
    
    if r.status_code == 200:
        data = r.json()
        books = data.get("books", [])
        print(f"Result Count: {len(books)}")
        if len(books) == 0:
            print("✅ Verification Passed: Correctly returned 0 books for missing title (No Fallback).")
        else:
             print("❌ Verification Failed: Returned books! Fallback might still be active.")
             print(f"First result: {books[0].get('title')} ({books[0].get('department')})")
    else:
        print(f"❌ Failed: {r.status_code}")
        print(r.text)

if __name__ == "__main__":
    test_recommend_similar()
