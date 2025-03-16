from fastapi import APIRouter, Depends, HTTPException
from serpapi import GoogleSearch
from security import get_current_user
from database import resume_collection, job_collection
from sentence_transformers import SentenceTransformer
import numpy as np

router = APIRouter()

SERPAPI_KEY = "a64cd9588a251044abddb227a2aac6d007566c825a6aba7676f111a00ee0c77a"

# Load Sentence Transformer model (BERT)
model = SentenceTransformer("all-MiniLM-L6-v2")


### ✅ Fetch Jobs from SerpAPI and Store in MongoDB ###
async def fetch_jobs_from_serpapi(query="Software Engineer", location="United States"):
    """Fetches job listings from Google Jobs via SerpAPI and ensures necessary fields exist."""
    search = GoogleSearch({"engine": "google_jobs", "q": query, "location": location, "api_key": SERPAPI_KEY})
    results = search.get_dict()

    jobs = results.get("jobs_results", [])
    job_listings = []

    for job in jobs:
        job_listings.append({
            "title": job.get("title", "Unknown Title"),
            "company": job.get("company_name", "Unknown Company"),
            "location": job.get("location", "Unknown Location"),
            "description": job.get("description", "No Description Available"),
            "link": job.get("job_id", "#")  # Ensure job has a link
        })

    return job_listings


@router.get("/fetch-jobs/")
async def fetch_and_store_jobs(current_user: dict = Depends(get_current_user)):
    """Admin-only endpoint to fetch jobs from SerpAPI and store them in MongoDB."""
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admins only")

    jobs = await fetch_jobs_from_serpapi()
    if not jobs:
        raise HTTPException(status_code=500, detail="Failed to fetch jobs from SerpAPI.")

    await job_collection.delete_many({})  # Clear old jobs
    await job_collection.insert_many(jobs)  # Insert new jobs

    return {"message": "Jobs updated successfully", "jobs_count": len(jobs)}


### ✅ Match Resume to Jobs Using BERT Embeddings ###
async def match_resume_to_jobs(resume_text):
    """Matches a resume to job descriptions using BERT embeddings."""

    # Fetch job postings
    jobs = await job_collection.find().to_list(100)
    if not jobs:
        raise HTTPException(status_code=404, detail="No jobs found. Run /fetch-jobs first.")

    job_texts = [job.get("description", "No Description Available") for job in jobs]
    resume_text = resume_text.strip()

    if not resume_text:
        raise HTTPException(status_code=400, detail="Resume text is empty, cannot match jobs.")

    try:
        # Encode resume and jobs using BERT embeddings
        resume_embedding = model.encode(resume_text, convert_to_tensor=True)
        job_embeddings = model.encode(job_texts, convert_to_tensor=True)

        # Compute Cosine Similarity
        scores = np.dot(job_embeddings, resume_embedding).tolist()

        # Rank jobs by similarity score
        ranked_jobs = sorted(zip(jobs, scores), key=lambda x: x[1], reverse=True)

        # Return top 5 matches
        return [
            {
                "title": job.get("title", "Unknown Title"),
                "company": job.get("company", "Unknown Company"),
                "score": round(score * 100, 2),
                "link": job.get("link", "#")
            }
            for job, score in ranked_jobs[:5]
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in job matching: {str(e)}")


### ✅ Job Recommendation Endpoint ###
@router.get("/recommend-jobs/")
async def recommend_jobs(current_user: dict = Depends(get_current_user)):
    """Finds the best job matches for a user based on their resume."""

    # Fetch user's resume from MongoDB
    resume = await resume_collection.find_one({"email": current_user["email"]})

    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found for this user.")

    # Prepare resume text (skills + experience)
    resume_text = " ".join(resume.get("skills", [])) + " " + " ".join(resume.get("experience", []))

    if not resume_text.strip():
        raise HTTPException(status_code=400, detail="User's resume is empty, cannot generate recommendations.")

    # Match resume with job listings
    matched_jobs = await match_resume_to_jobs(resume_text)

    return {"user_email": current_user["email"], "recommended_jobs": matched_jobs}
