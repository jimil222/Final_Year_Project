from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.security import SECRET_KEY, ALGORITHM
from app.db import db
from typing import Optional

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        role: str = payload.get("role", "student")
        
        if email is None or user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = None
    if role == "admin":
        user = await db.admin.find_unique(where={"email": email})
        if user:
            # Dynamically attach role for downstream checks if needed, 
            # though type checking is better.
            # Prisma models might be immutable, so we rely on the object type or just return it.
            pass
    else:
        user = await db.user.find_unique(where={"email": email})
        
    if user is None:
        raise credentials_exception
        
    return user

def get_current_student(user = Depends(get_current_user)):
    # Check if user is a Student (has 'user_id' field)
    # Admin model has 'admin_id'
    if hasattr(user, 'admin_id'):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Student access required"
        )
    return user

def get_current_admin(user = Depends(get_current_user)):
    # Check if user is Admin (has 'admin_id' field)
    if hasattr(user, 'user_id'): 
        # It's a student
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Admin access required"
        )
    return user
