from fastapi import APIRouter, Depends
from app.dependencies import get_current_user

router = APIRouter(prefix="/student", tags=["Student"])


@router.get("/recommendations")
async def get_recommendations(current_user=Depends(get_current_user)):
    user_dept = current_user.department
    print(f"User Department: {user_dept}")

    if not user_dept:
        return {"books": []}

    try:
        from app.ml.service import get_recommender
        rec = get_recommender()

        # Department mapping
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

        target_dept = mapping.get(user_dept, user_dept)
        if "Computer" in user_dept or "Data" in user_dept:
            target_dept = "Computer Science"

        print(f"Mapping '{user_dept}' -> '{target_dept}'")

        top_books = rec.get_top_50_by_dept(target_dept)

        if top_books.empty:
            print(f"No books found for '{target_dept}', retrying with raw department")
            top_books = rec.get_top_50_by_dept(user_dept)

        print(f"Found {len(top_books)} potential recommendations")

        top_10 = top_books.head(10)

        books_list = []
        for idx, row in top_10.iterrows():
            books_list.append({
                "id": idx + 1000,
                "book_id": f"CSV-{idx}",
                "title": row["Title"],
                "author": row["Author"],
                "department": row["Department"],
                "status": "available",
                "rating": float(row.get("Rating", 4.0))
            })

        return {
            "books": books_list
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"books": [], "error": str(e)}


@router.get("/recommend-similar")
async def recommend_similar_books(title: str, current_user=Depends(get_current_user)):
    """
    Get recommendations similar to a specific book title.
    Strictly uses content-based similarity. Returns empty if not found.
    """
    print(f"Fetching similar books for title: '{title}'")
    
    if not title:
         return {"books": []}

    try:
        from app.ml.service import get_recommender
        rec = get_recommender()
        
        # This will internally train TF-IDF if needed
        similar_df = rec.recommend_books(title, top_n=4)
        
        books_list = []
        
        if not similar_df.empty:
            for idx, row in similar_df.iterrows():
                books_list.append({
                    "id": idx + 2000, # Mock ID
                    "book_id": f"REC-{idx}",
                    "title": row['Title'],
                    "author": row['Author'],
                    "department": row['Department'],
                    "status": "available", 
                    "rating": float(row.get('Rating', 4.0))
                })
        
        print(f"Found {len(books_list)} books (Content-Based).")
        return {"books": books_list}

    except Exception as e:
        print(f"Error in recommend-similar: {e}")
        return {"books": [], "error": str(e)}



@router.get("/me")
async def read_users_me(current_user=Depends(get_current_user)):
    return {
        "user_id": str(current_user.user_id),
        "name": current_user.name,
        "email": current_user.email,
        "roll_no": current_user.roll_no,
        "department": current_user.department,
        "created_at": current_user.created_at
    }
