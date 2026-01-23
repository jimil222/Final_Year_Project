from fastapi import APIRouter, HTTPException, Depends, status
from app.db import db
from app.security import verify_password, get_password_hash, create_access_token
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import timedelta
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    roll_no: str
    department: Optional[str] = None
    role: Literal["student", "admin"] = "student"

class UserLogin(BaseModel):
    email: EmailStr
    password: str
    role: Literal["student", "admin"] = "student"

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    email: str
    roll_no: str
    department: Optional[str] = None
    role: str

ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

@router.post("/register", response_model=Token)
async def register(user: UserRegister):
    hashed_password = get_password_hash(user.password)
    
    if user.role == "admin":
        # Check if any admin exists
        # Note: Ideally this would be a race-condition safe check, 
        # but for this simple app await count is reasonable.
        admin_count = await db.admin.count()
        if admin_count > 0:
            raise HTTPException(status_code=400, detail="Admin already exists")
            
        # Check unique email/roll_no logic for admin table specifically
        existing_admin = await db.admin.find_unique(where={"email": user.email})
        if existing_admin:
            raise HTTPException(status_code=400, detail="Email already registered")
            
        new_user = await db.admin.create(
            data={
                "name": user.name,
                "email": user.email,
                "roll_no": user.roll_no,
                "password": hashed_password
            }
        )
        department = None
        
    else:
        # Check if user already exists
        existing_user_email = await db.user.find_unique(where={"email": user.email})
        if existing_user_email:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        existing_user_roll = await db.user.find_unique(where={"roll_no": user.roll_no})
        if existing_user_roll:
            raise HTTPException(status_code=400, detail="Roll number already registered")
    
        new_user = await db.user.create(
            data={
                "name": user.name,
                "email": user.email,
                "roll_no": user.roll_no,
                "department": user.department,
                "password": hashed_password
            }
        )
        department = new_user.department

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.email, "user_id": str(new_user.user_id), "role": user.role},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": int(new_user.user_id),
        "name": new_user.name,
        "email": new_user.email,
        "roll_no": new_user.roll_no,
        "department": department,
        "role": user.role
    }

@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin):
    user = None
    if user_credentials.role == "admin":
        user = await db.admin.find_unique(where={"email": user_credentials.email})
    else:
        user = await db.user.find_unique(where={"email": user_credentials.email})
        
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(user_credentials.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email, "user_id": str(user.user_id), "role": user_credentials.role},
        expires_delta=access_token_expires
    )
    
    department = getattr(user, "department", None)

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": int(user.user_id),
        "name": user.name,
        "email": user.email,
        "roll_no": user.roll_no,
        "department": department,
        "role": user_credentials.role
    }
