import sys
import os

# Add the current directory to path so we can import from app
sys.path.append(os.getcwd())

try:
    import pandas as pd
    print("Pandas is installed.")
except ImportError:
    print("ERROR: Pandas is NOT installed.")

try:
    from app.ml.service import get_recommender
    print("Imported get_recommender successfully.")
    
    rec = get_recommender()
    print("Recommender initialized.")
    
    if rec.df is None:
        print("ERROR: DataFrame is None after initialization.")
    else:
        print(f"DataFrame loaded with {len(rec.df)} rows.")
        print(f"Columns: {rec.df.columns.tolist()}")
        print(f"Sample Departments: {rec.df['Department'].unique().tolist()[:10]}")
    
    dept = "Computer Science"
    print(f"\nTesting get_top_50_by_dept('{dept}')...")
    top_books = rec.get_top_50_by_dept(dept)
    
    if top_books.empty:
        print(f"No books found for {dept}.")
    else:
        print(f"Found {len(top_books)} books for {dept}.")
        print(top_books.head(3)[['Title', 'Author', 'Department']])

except Exception as e:
    print(f"CRITICAL ERROR during execution: {e}")
    import traceback
    traceback.print_exc()
