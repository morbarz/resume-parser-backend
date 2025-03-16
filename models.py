from pydantic import BaseModel

class UserRegister(BaseModel):
    email: str
    password: str
    role: str = "user"  # Default role is 'user'

class Login(BaseModel):
    email: str
    password: str
