import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Load secrets from .env file

SECRET_KEY = os.getenv("SECRET_KEY", "mysecretkey")  # Use a secure secret key
ALGORITHM = "HS256"  # Defines the hashing algorithm for JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token expiration time

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})  # Add expiration time to token
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
