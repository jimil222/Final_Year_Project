from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.db import db, connect_db, disconnect_db
from app.auth import router as auth_router
from app.dependencies import get_current_user
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    roll_no: str
    name: str
    email: str
    department: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await disconnect_db()

app = FastAPI(lifespan=lifespan)

# CORS Configuration
origins = [
    "http://localhost:5173", # Vite default
    "http://localhost:3000", # React default
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

@app.get("/")
async def root():
    return {"message": "Hello World"}

from app.student import router as student_router

# ... (rest of imports)

app.include_router(auth_router)
app.include_router(student_router)

# Remove the inline /student/me as it's now in student.py
# @app.get("/student/me") ...

# Keeping the original /users endpoint for compatibility/testing if needed, 
# though usually registration should go through /auth/register
@app.post("/users")
async def create_user(user: UserCreate):
    try:
        # Note: This endpoint does NOT hash passwords, so it shouldn't be used for auth users anymore
        # But if you need to maintain it, you'd need to provide a default or dummy password
        # Since 'password' is now required in DB, this will fail unless we update logic or schema default.
        # For now, we'll leave it but it might return 500.
        # Ideally, we should remove it or update it.
        # Let's update it to at least work with the new schema by providing a dummy password if used.
        from app.security import get_password_hash
        
        # Check existing
        existing = await db.user.find_first(where={"OR": [{"email": user.email}, {"roll_no": user.roll_no}]})
        if existing:
             raise HTTPException(status_code=400, detail="User already exists")

        new_user = await db.user.create(
            data={
                "roll_no": user.roll_no,
                "name": user.name,
                "email": user.email,
                "department": user.department,
                "password": get_password_hash("defaultpassword123") # Fallback
            }
        )
        return {
            "user_id": str(new_user.user_id),
            "roll_no": new_user.roll_no,
            "name": new_user.name,
            "email": new_user.email,
            "department": new_user.department
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
