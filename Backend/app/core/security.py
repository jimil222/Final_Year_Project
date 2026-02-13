from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))


# bcrypt has a 72-byte limit; passlib had compatibility issues with bcrypt 5.x
def verify_password(plain_password: str, hashed_password: str) -> bool:
  if not isinstance(hashed_password, bytes):
    hashed_password = hashed_password.encode("utf-8")
  return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)


def get_password_hash(password: str) -> str:
  # bcrypt truncates at 72 bytes
  pwd_bytes = password.encode("utf-8")[:72]
  return bcrypt.hashpw(pwd_bytes, bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
  to_encode = data.copy()
  if expires_delta:
    expire = datetime.utcnow() + expires_delta
  else:
    expire = datetime.utcnow() + timedelta(minutes=15)

  # Ensure all values are JSON serializable (convert BigInt/int to str if needed or just handle basic types)
  # user_id might be int, pydantic handles it, but jwt expects standard types.
  if "user_id" in to_encode:
    to_encode["user_id"] = str(to_encode["user_id"])

  to_encode.update({"exp": expire})
  encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  return encoded_jwt

