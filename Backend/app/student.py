from fastapi import APIRouter, Depends
from app.dependencies import get_current_user
from app.db import db

router = APIRouter(prefix="/student", tags=["Student"])

@router.get("/recommendations")
async def get_recommendations(current_user = Depends(get_current_user)):
    user_dept = current_user.department
    print(f"User Department: {user_dept}")
    
    if not user_dept:
        return {"books": []}

    try:
        from app.ml.service import get_recommender
        rec = get_recommender()
        
        # Map Frontend Departments to Model Departments
        target_dept = user_dept
        
        # Explicit mapping based on Register.jsx and Recommender System keys
        mapping = {
            "AI & Data Science": "Computer Science",
            "Information Technology": "Computer Science", 
            "Computer Science": "Computer Science",
            "Mechanical Engineering": "Mechanical Engineering",
            "Civil Engineering": "Civil Engineering",
            "Electronics": "Electronics",
            "Electrical Engineering": "Electrical Engineering",
            "Mathematics": "Mathematics",
            "Physics": "Physics",
            "Chemistry": "Chemistry",
            "Other": "General"
        }
        
        if user_dept in mapping:
            target_dept = mapping[user_dept]
        elif "Computer" in user_dept or "Data" in user_dept:
            target_dept = "Computer Science"
            
        print(f"Mapping '{user_dept}' -> '{target_dept}'")
        
        top_books = rec.get_top_50_by_dept(target_dept)
        
        if top_books.empty:
             print(f"No books found for '{target_dept}'. Trying strict user dept '{user_dept}'")
             top_books = rec.get_top_50_by_dept(user_dept)
             
        print(f"Found {len(top_books)} potential recommendations")
        
        # Take top 10
        top_10 = top_books.head(10)
        
        # Convert to list of dicts
        books_list = []
        for idx, row in top_10.iterrows():
            books_list.append({
                "id": idx + 1000, # Mock ID since it's from CSV
                "book_id": f"CSV-{idx}",
                "title": row['Title'],
                "author": row['Author'],
                "department": row['Department'],
                "status": "available", # Assume available for recommendations
                "rating": row.get('Rating', 4.0)
            })
            
        return {
            "id": 1,
            "student_id": int(current_user.user_id),
            "books": books_list,
            "debug": {
                "user_dept": user_dept,
                "target_dept": target_dept,
                "books_found": len(top_books),
                "mapping_used": True if user_dept in mapping else False,
                "columns": rec.df.columns.tolist() if rec.df is not None else "None"
            }
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error getting recommendations: {e}")
        return {"books": [], "error": str(e)}

@router.get("/me")
async def read_users_me(current_user = Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "name": current_user.name,
        "email": current_user.email,
        "roll_no": current_user.roll_no,
        "department": current_user.department,
        "created_at": current_user.created_at
    }
