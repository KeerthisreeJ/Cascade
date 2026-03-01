"""
career_optimization_service.py

Pipeline:
  1. Fetch resume skills from DB
  2. Fetch LIVE jobs from Adzuna API (keyed by resume skills)
  3. Fall back to DB job listings if Adzuna isn't configured
  4. Run Jaccard similarity between resume skills and each job's required skills
  5. Generate AI learning roadmap (Groq) for jobs with missing skills
  6. Return recommendations sorted by match score
"""

from services.resume_skill_service import fetch_resume_skills
from services.recommendation_service import calculate_similarity
from services.grok_service import generate_learning_roadmap
from services.jobs_api_service import fetch_live_jobs
from services.job_service import fetch_all_jobs  # DB fallback


def generate_recommendations(resume_id: int) -> list:

    resume_skills = fetch_resume_skills(resume_id)

    # ── 1. Try live jobs first ─────────────────────────────────────
    live_jobs = fetch_live_jobs(resume_skills)

    if live_jobs:
        job_pool = live_jobs
        source   = "adzuna"
    else:
        # ── 2. Fallback to DB (works without Adzuna keys) ──────────
        job_pool = fetch_all_jobs()
        source   = "db"

    # ── 3. Score and rank ──────────────────────────────────────────
    resume_skill_set = set(s.lower() for s in resume_skills)
    recommendations  = []

    for job in job_pool:
        job_skills_raw = job.get("required_skills", "")
        job_skill_list = [s.strip() for s in job_skills_raw.split(",") if s.strip()]

        similarity = calculate_similarity(resume_skills, job_skills_raw)

        missing_skills  = [s for s in job_skill_list if s.lower() not in resume_skill_set]
        acquired_skills = [s for s in job_skill_list if s.lower() in resume_skill_set]

        # AI roadmap only when there are meaningful gaps
        if missing_skills:
            roadmap = generate_learning_roadmap(
                job.get("job_title", "this role"), missing_skills
            )
        else:
            roadmap = None

        recommendations.append({
            "job_id":           job.get("job_id"),
            "job_title":        job.get("job_title", "Software Role"),
            "company":          job.get("company", ""),
            "location":         job.get("location", ""),
            "experience_level": job.get("experience_level", ""),
            "similarity_score": similarity,
            "acquired_skills":  acquired_skills,
            "missing_skills":   missing_skills,
            "roadmap":          roadmap,
            "redirect_url":     job.get("redirect_url", "#"),
            "salary_min":       job.get("salary_min"),
            "salary_max":       job.get("salary_max"),
            "source":           source,
        })

    recommendations.sort(key=lambda x: x["similarity_score"], reverse=True)

    return recommendations