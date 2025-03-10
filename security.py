from passlib.context import CryptContext

# Define password hashing algorithm
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
#Hashes a plaintext password.
def hash_password(password: str) -> str:
    return pwd_context.hash(password)
#Compares a plaintext password with a stored hashed password.
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
