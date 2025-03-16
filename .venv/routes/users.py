from fastapi import APIRouter, HTTPException, Depends
from models import UserRegister, Login
from database import user_collection
from security import hash_password, verify_password,create_access_token,get_current_user
#from auth import create_access_token
from datetime import timedelta

router = APIRouter()


@router.post("/register/")
async def register_user(user: UserRegister, current_user: dict = Depends(get_current_user)):
    """Only admins can register new users."""

    # 🔹 Step 1: Check if the current user is an admin
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Access denied: Only admins can register users")

    # 🔹 Step 2: Ensure the email is not already registered
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 🔹 Step 3: Hash the new user's password before storing
    hashed_password = hash_password(user.password)

    new_user = {
        "email": user.email,
        "password": hashed_password,
        "role": user.role.lower()  # Default to "user" unless specified otherwise
    }
    await user_collection.insert_one(new_user)

    return {"message": "User registered successfully", "role": new_user["role"]}


@router.post("/login/")
async def login(user: Login):
    db_user = await user_collection.find_one({"email": user.email})

    # 🔹 Debugging: Print user from database
    print("\n🔍 DEBUG: User from DB:", db_user)

    if not db_user:
        print("❌ User not found in database!")
        raise HTTPException(status_code=400, detail="User not found in database")

    # 🔹 Debugging: Print stored password vs. entered password
    print("🔍 DEBUG: Stored Hashed Password:", db_user["password"])
    print("🔍 DEBUG: Entered Plain Password:", user.password)

    # 🔹 Debugging: Check if password verification passes
    password_match = verify_password(user.password, db_user["password"])
    print("🔍 DEBUG: Password Match:", password_match)

    if not password_match:
        print("❌ Hash comparison failed!")
        raise HTTPException(status_code=400, detail="Invalid password")

    # 🔹 Generate JWT Token if successful
    access_token = create_access_token({"sub": user.email, "role": db_user["role"]}, timedelta(minutes=60))

    print("✅ Login Successful! Returning Token...")
    return {"access_token": access_token, "token_type": "bearer", "role": db_user["role"]}
