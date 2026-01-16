import sys
import os
sys.path.append(os.getcwd())

import app.ml.recommender_system as rs
print(f"Loaded recommender_system from: {rs.__file__}")

from app.ml.service import get_recommender
rec = get_recommender()
rec.load_and_preprocess()

print("Testing retrieval...")
dept = "Computer Science"
top = rec.get_top_50_by_dept(dept)
print(f"Found {len(top)} books for {dept}")
if not top.empty:
    print(top.head(2)[['Title']])
else:
    print("WARNING: Empty results!")
