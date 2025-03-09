from passlib.context import CryptContext
from datetime import datetime, timedelta
import jwt
import os
from dotenv import load_dotenv

# Why do we use dotenv?
# It loads secret keys and environment variables securely.
load_dotenv()

# Why do we define a secret key?
# This is used to sign and verify JWT tokens.
SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Why do we use Passlib?
# It securely hashes and verifies passwords.
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Why do we hash passwords?
# This ensures stored passwords are secure and not stored in plain text.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# Why do we verify passwords?
# This checks if the provided password matches the stored hash.
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


# Why do we generate JWT tokens?
# Tokens authenticate users and allow them to access protected routes.
def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()

    # Why do we set an expiration time?
    # Tokens should expire after a set period for security.
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    # Why do we encode a JWT?
    # It creates a secure, signed token that users must provide for authentication.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
