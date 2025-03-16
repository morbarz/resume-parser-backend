from fastapi import FastAPI
from routes import users, resumes, jobs

app = FastAPI()

# Register API routes
app.include_router(users.router)
app.include_router(resumes.router)
app.include_router(jobs.router)
