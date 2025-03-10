from pydantic import BaseModel, EmailStr
from typing import Optional
from bson import ObjectId
#This ensures that when users register, their email is valid, and they provide a password.
class User(BaseModel):
    id: Optional[str] = None  # MongoDB's unique identifier (ObjectId)
    email: EmailStr  # Ensures valid email format
    password: str  # This will be hashed before storing
