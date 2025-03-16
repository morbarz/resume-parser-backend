import jwt
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()  # Load secrets from .env file

SECRET_KEY = os.getenv("SECRET_KEY", "a64cd9588a251044abddb227a2aac6d007566c825a6aba7676f111a00ee0c77a")  # Use a secure secret key
ALGORITHM = "HS256"  # Defines the hashing algorithm for JWT
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # Token expiration time

def decode_access_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None  # Token expired
    except jwt.InvalidTokenError:
        return None  # Invalid token
