from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Query
from database import resume_collection
from security import get_current_user
import fitz
import uuid

router = APIRouter()

@router.post("/upload-resume/")
async def upload_resume(file: UploadFile = File(...), current_user: dict = Depends(get_current_user)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Unsupported file format")

    doc = fitz.open(stream=file.file.read(), filetype="pdf")
    text = "\n".join([page.get_text() for page in doc])

    resume_id = str(uuid.uuid4())

    new_resume = {
        "_id": resume_id,
        "email": current_user["email"],
        "filename": file.filename,
        "content": text
    }

    await resume_collection.insert_one(new_resume)
    return {"message": "Resume saved!", "resume_id": resume_id}
