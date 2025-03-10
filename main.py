from datetime import timedelta
from fastapi import FastAPI, UploadFile, File, Query, Depends, HTTPException
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
import fitz  # PyMuPDF for PDF text extraction
import spacy
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from auth import create_access_token, SECRET_KEY, ALGORITHM
from security import hash_password, verify_password
from database import resume_collection, user_collection  # MongoDB collections
import re
# Initialize FastAPI app
app = FastAPI()

# Load NLP model
nlp = spacy.load("en_core_web_sm")

# Read skills list from file
try:
    with open("skill_list.txt", "r", encoding="utf-8") as file:
        SKILL_SET = set([line.strip().lower() for line in file.readlines() if line.strip()])
    print("Loaded Skills:", len(SKILL_SET))  # Debugging output
except Exception as e:
    print("Error loading skill_list.txt:", e)
    SKILL_SET = set()

# Authentication scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")

# Define User model
class User(BaseModel):
    email: str
    password: str

# Function to verify JWT token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# User registration endpoint
@app.post("/register/")
async def register_user(user: User):
    existing_user = await user_collection.find_one({"email": user.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = hash_password(user.password)
    new_user = {"email": user.email, "password": hashed_password}
    await user_collection.insert_one(new_user)
    return {"message": "User registered successfully"}

# User login endpoint
class Login(BaseModel):
    email: str
    password: str

@app.post("/login/")
async def login(user: Login):
    db_user = await user_collection.find_one({"email": user.email})
    if not db_user or not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")
    access_token = create_access_token({"sub": user.email}, timedelta(minutes=60))
    return {"access_token": access_token, "token_type": "bearer"}

# Function to extract skills from text
def extract_skills(text):
    doc = nlp(text)
    extracted_skills = set()

    # Check each token and phrase against the skill set
    for token in doc:
        word = token.text.lower().strip()
        if word in SKILL_SET:
            extracted_skills.add(word)

    # Also check for multi-word skills (e.g., "Machine Learning", "Deep Learning")
    extracted_phrases = set()
    for chunk in doc.noun_chunks:  # Extract multi-word noun phrases
        phrase = chunk.text.lower().strip()
        if phrase in SKILL_SET:
            extracted_phrases.add(phrase)

    extracted_skills.update(extracted_phrases)  # Merge single-word and multi-word skills

    print("Extracted Skills:", extracted_skills)  # Debugging output
    return list(extracted_skills)

# Function to extract resume details
async def extract_resume_data(text):
    doc = nlp(text)

    name, email, phone = None, None, None

    # Extract Name (PERSON), but filter out programming languages & incorrect entities
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            if ent.text.lower() not in {"c++", "javascript", "python", "java", "nodejs", "html", "css", "sql"}:  # Exclude programming languages
                name = ent.text
                break  # Stop after the first valid name

    # Extract email using regex as a backup
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    email = email_match.group() if email_match else None

    # Extract phone number using regex
    phone_match = re.search(r"\+?\d[\d -]{8,14}\d", text)
    phone = phone_match.group() if phone_match else None

    # Extract skills
    skills = extract_skills(text)

    print("Extracted Name:", name)
    print("Extracted Email:", email)
    print("Extracted Phone:", phone)
    print("Extracted Skills:", skills)

    return {"name": name, "email": email, "phone": phone, "skills": skills}

# Resume upload endpoint
@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        return {"error": "Unsupported file format"}
    doc = fitz.open(stream=file.file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])
    resume_data = await extract_resume_data(text)
    new_resume = {
        "filename": file.filename,
        "name": resume_data["name"],
        "email": resume_data["email"],
        "phone": resume_data["phone"],
        "skills": resume_data["skills"],
        "experience": text[:500]
    }
    await resume_collection.insert_one(new_resume)
    return {"message": "Resume saved!", "data": resume_data}

# Resume retrieval endpoint
@app.get("/get-resumes/")
async def get_resumes(
    skill: str = Query(None, description="Filter by skill"),
    name: str = Query(None, description="Filter by name"),
    email: str = Query(None, description="Filter by email"),
    current_user: str = Depends(get_current_user)
):
    query = {}
    if skill:
        query["skills"] = skill
    if name:
        query["name"] = {"$regex": name, "$options": "i"}
    if email:
        query["email"] = email
    resumes = await resume_collection.find(query).to_list(length=100)
    return {"resumes": resumes}
