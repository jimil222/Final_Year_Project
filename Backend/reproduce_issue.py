import sys
import os

# Add Backend directory to sys.path so we can import app
sys.path.append(os.getcwd())

try:
    print("Attempting to import get_recommender from app.ml.service...")
    from app.ml.service import get_recommender
    
    print("Getting recommender instance...")
    rec = get_recommender()
    
    print("Successfully got recommender.")
    
    dept = "Computer Science"
    print(f"Fetching top 50 for {dept}...")
    top_books = rec.get_top_50_by_dept(dept)
    
    print(f"Found {len(top_books)} books.")
    if not top_books.empty:
        print(top_books.head())
    else:
        print("No books found.")
        
except Exception as e:
    print(f"CRITICAL ERROR: {e}")
    import traceback
    traceback.print_exc()
