# Why do we use Motor?
# Motor is the official async driver for MongoDB in Python.
from motor.motor_asyncio import AsyncIOMotorClient
import os

from dotenv import load_dotenv

# Why do we use dotenv?
# It loads secret keys and environment variables securely.
load_dotenv()

# Why do we use an environment variable for MongoDB URI?
# It keeps database credentials secure.
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")

# Why do we create a client?
# This connects FastAPI to MongoDB.
client = AsyncIOMotorClient(MONGO_URI)

# Why do we select a database?
# "resume_parser" will store all resume data.
db = client.resume_parser

# Why do we define a collection?
# "resumes" will store all parsed resumes.
resume_collection = db.resumes
user_collection = db.users
job_collection = db.jobs