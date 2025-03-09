# Why do we need FastAPI?
# FastAPI is used to build the API that allows users to upload resumes.
from datetime import timedelta
from http.client import HTTPException

from fastapi import FastAPI, UploadFile, File, Query, Depends
from auth import hash_password, verify_password, create_access_token, SECRET_KEY, ALGORITHM
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer
import jwt
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")
# Why do we create a function to verify JWT tokens?
# It ensures only authenticated users can access protected endpoints.
async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# Why do we need PyMuPDF (fitz)?
# PyMuPDF extracts text from PDFs, which allows us to read resumes.
import fitz

# Why do we need spaCy?
# spaCy is an NLP library used to process resume text.
import spacy

# Why do we need scikit-learn?
# Scikit-learn provides tools for text similarity (TF-IDF).
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


from database import resume_collection, user_collection  # Import MongoDB collection


# Why do we define a User schema?
# It validates incoming user data.
class User(BaseModel):
    email: str
    password: str



# Why do we need the app instance?
# This initializes the FastAPI app so we can define endpoints.
app = FastAPI()


# Why do we create a /register endpoint?
# This allows users to create an account.
@app.post("/register/")
async def register_user(user: User):
    existing_user = await user_collection.find_one({"email": user.email})

    # Why do we check for duplicate users?
    # This prevents users from registering with the same email twice.
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Why do we hash the password?
    # It ensures passwords are stored securely.
    hashed_password = hash_password(user.password)

    # Why do we insert user data?
    # It saves the new user into MongoDB.
    new_user = {"email": user.email, "password": hashed_password}
    await user_collection.insert_one(new_user)

    return {"message": "User registered successfully"}


# Why do we create a login schema?
# It validates login credentials.
class Login(BaseModel):
    email: str
    password: str


# Why do we create a /login endpoint?
# This allows users to log in and receive a JWT token.
@app.post("/login/")
async def login(user: Login):
    db_user = await user_collection.find_one({"email": user.email})

    # Why do we check if the user exists?
    # It ensures only registered users can log in.
    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Why do we verify the password?
    # It checks if the provided password matches the stored hash.
    if not verify_password(user.password, db_user["password"]):
        raise HTTPException(status_code=400, detail="Invalid email or password")

    # Why do we generate an access token?
    # This allows the user to authenticate requests.
    access_token = create_access_token({"sub": user.email}, timedelta(minutes=60))

    return {"access_token": access_token, "token_type": "bearer"}




# Why do we load an NLP model?
# The "en_core_web_sm" model helps analyze the text for named entities and word relationships.
nlp = spacy.load("en_core_web_sm")

# Why do we read the skills list from a file?
# This allows us to compare resume text against a known list of skills.
with open("skill_list.txt", "r", encoding="utf-8") as file:
    SKILL_SET = set([line.strip().lower() for line in file.readlines()])


# Why do we define an extract_skills function?
# This function processes resume text and extracts matching skills.
def extract_skills(text):
    # Why do we use spaCy's NLP model?
    # It tokenizes the text and identifies meaningful words.
    doc = nlp(text)

    # Why do we use a set?
    # Sets avoid duplicate skills in the extracted results.
    extracted_skills = set()

    # Why do we loop through each token?
    # We want to check if the token matches a known skill.
    for token in doc:
        word = token.text.lower()

        # Why do we check against SKILL_SET?
        # If the word is in our predefined list, we consider it a skill.
        if word in SKILL_SET:
            extracted_skills.add(word)

    # Why do we return a list?
    # Converting to a list makes it easier to return as JSON.
    return list(extracted_skills)


# Why do we define a function to extract resume data?
# It extracts name, email, phone, and skills from the text.
async def extract_resume_data(text):
    doc = nlp(text)

    # Why do we set default values?
    # To prevent errors if data is missing.
    name = None
    email = None
    phone = None
    skills = []

    # Why do we extract named entities?
    # spaCy detects names, emails, and phone numbers.
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text
        elif ent.label_ == "EMAIL":
            email = ent.text
        elif ent.label_ == "PHONE":
            phone = ent.text

    # Why do we load a predefined skills list?
    # This ensures that extracted skills are relevant.
    with open("skill_list.txt", "r", encoding="utf-8") as file:
        skill_set = set([line.strip().lower() for line in file.readlines()])

    # Why do we check each word in the text?
    # This ensures only valid skills are extracted.
    skills = [token.text for token in doc if token.text.lower() in skill_set]

    return {"name": name, "email": email, "phone": phone, "skills": skills}


# Why do we define an API endpoint?
# This allows users to upload resumes and store data in MongoDB.
@app.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...)):
    # Why do we check the file extension?
    # We only support PDFs for now.
    if file.filename.endswith(".pdf"):
        # Why do we use fitz.open()?
        # It extracts text from PDF files.
        doc = fitz.open(stream=file.file.read(), filetype="pdf")

        # Why do we join text from multiple pages?
        # Resumes are usually multi-page documents.
        text = "\n".join([page.get_text() for page in doc])
    else:
        # Why do we return an error?
        # If the file format is not supported, we notify the user.
        return {"error": "Unsupported file format"}

    # Why do we extract structured resume data?
    # This function call processes the text and extracts details.
    resume_data = await extract_resume_data(text)

    # Why do we store data in MongoDB?
    # This saves parsed resumes for later retrieval.
    new_resume = {
        "filename": file.filename,
        "name": resume_data["name"],
        "email": resume_data["email"],
        "phone": resume_data["phone"],
        "skills": resume_data["skills"],
        "experience": text[:500]  # Storing only the first 500 characters
    }
    await resume_collection.insert_one(new_resume)

    # Why do we return a success message?
    # To confirm the resume has been saved successfully.
    return {"message": "Resume saved!", "data": resume_data}


# Why do we have example job descriptions?
# These help compare resume text to actual job requirements.
job_desc = [
    "Looking for a Python Developer with Django, Flask, and AWS experience.",
    "Seeking a Data Scientist with expertise in NLP and Machine Learning."
]

# Why do we use TfidfVectorizer?
# TF-IDF converts text into a numerical representation for similarity comparison.
vectorizer = TfidfVectorizer()
tfidf_matrix = vectorizer.fit_transform(job_desc)

def match_skills(text):
    # Why do we transform the input text?
    # It converts the resume text into a vector for comparison.
    user_vector = vectorizer.transform([text])

    # Why do we use cosine similarity?
    # It measures how similar the resume is to job descriptions.
    similarity_scores = cosine_similarity(user_vector, tfidf_matrix)

    # Why do we return the similarity scores?
    # This helps determine how well the candidate fits available job roles.
    return similarity_scores
# Why do we define a function to fetch resumes?
# It retrieves all stored resumes from MongoDB.


# Why do we define a function to convert MongoDB ObjectId to string?
# MongoDB stores "_id" as ObjectId, which is not JSON serializable.
def convert_mongo_object_id(resume):
    resume["_id"] = str(resume["_id"])  # Convert ObjectId to string
    return resume








# Why do we add authentication to /get-resumes/?
# It ensures only authenticated users can retrieve resumes.
@app.get("/get-resumes/")
async def get_resumes(
    skill: str = Query(None, description="Filter by skill"),
    name: str = Query(None, description="Filter by name"),
    email: str = Query(None, description="Filter by email"),
    current_user: str = Depends(get_current_user)  # Require authentication
):
    # Why do we create a query filter?
    # It builds a search filter based on user input.
    query = {}

    if skill:
        query["skills"] = skill  # Match resumes containing this skill
    if name:
        query["name"] = {"$regex": name, "$options": "i"}  # Case-insensitive name search
    if email:
        query["email"] = email  # Exact email match

    # Why do we find matching resumes?
    # It searches for resumes based on filters.
    resumes = await resume_collection.find(query).to_list(length=100)

    # Why do we convert ObjectId to a string?
    # FastAPI cannot serialize ObjectId directly.
    return {"resumes": [convert_mongo_object_id(resume) for resume in resumes]}