from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional

from app.core.security import SECRET_KEY, ALGORITHM
from app.core.db import db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)):
  credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
  )
  try:
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    email: Optional[str] = payload.get("sub")
    user_id: Optional[str] = payload.get("user_id")
    role: str = payload.get("role", "student")

    if email is None or user_id is None:
      raise credentials_exception
  except JWTError:
    raise credentials_exception

  user = None
  if role == "admin":
    user = await db.admin.find_unique(where={"email": email})
  else:
    user = await db.user.find_unique(where={"email": email})

  if user is None:
    raise credentials_exception

  return user


def get_current_student(user=Depends(get_current_user)):
  """Ensure the current principal is a student (has `user_id`, not `admin_id`)."""
  if hasattr(user, "admin_id"):
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Student access required",
    )
  return user


def get_current_admin(user=Depends(get_current_user)):
  """Ensure the current principal is an admin (has `admin_id`, not `user_id`)."""
  if hasattr(user, "user_id"):
    raise HTTPException(
      status_code=status.HTTP_403_FORBIDDEN,
      detail="Admin access required",
    )
  return user

