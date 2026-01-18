import sys
import os
# Add parent directory to path to find Recommendation_Model
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from Recommendation_Model.recommender_system import LibraryRecommender

def debug():
    # Use absolute path
    data_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Recommendation_Model", "enhanced_library_data.csv"))
    print(f"Loading data from: {data_path}")
    rec = LibraryRecommender(data_path)
    rec.load_and_preprocess()
    
    # Test 1: Fallback Structure
    dept = "Computer Science"
    print(f"\n--- Testing Fallback Structure for {dept} ---")
    top = rec.get_top_50_by_dept(dept)
    print(f"Columns: {top.columns.tolist()}")
    if 'Department' in top.columns:
        print("✅ Department column exists.")
    else:
        print("❌ Department column MISSING!")

    # Test 2: Normalized Matching
    # Choose a title we know exists but change case/white space
    # "Data structures through C++" -> "data structures through c++"
    title_raw = "Data structures through C++"
    title_lower = title_raw.lower()
    
    print(f"\n--- Testing Normalized Match: '{title_lower}' ---")
    rec.prepare_recommendation_model() # Ensure model is prepped
    sim_books = rec.recommend_books(title_lower, top_n=3)
    
    if not sim_books.empty:
        print(f"✅ Match found! Top result: {sim_books.iloc[0]['Title']}")
    else:
        print("❌ No match found for lowercase title.")

if __name__ == "__main__":
    debug()
