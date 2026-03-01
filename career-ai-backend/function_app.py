import azure.functions as func
import json
import logging
import os

from services.document_service import analyze_resume
from services.blob_service import upload_resume
from services.sql_service import insert_resume, insert_resume_skills
from services.skill_service import extract_skills
from services.career_optimization_service import generate_recommendations
from services.resume_skill_service import fetch_resume_skills
from services.score_service import compute_resume_score


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────
CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
}


def json_response(data: dict, status_code: int = 200) -> func.HttpResponse:
    return func.HttpResponse(
        json.dumps(data),
        status_code=status_code,
        mimetype="application/json",
        headers=CORS_HEADERS,
    )

app = func.FunctionApp()

MAX_FILE_SIZE_MB = 5


@app.function_name(name="processResume")
@app.route(route="processResume", methods=["POST"])
def process_resume(req: func.HttpRequest) -> func.HttpResponse:

    logging.info("Resume upload request received.")

    try:
        # -----------------------------
        # 1️⃣ Get File From FormData
        # -----------------------------
        file = req.files.get("file")

        if not file:
            return func.HttpResponse(
                json.dumps({"error": "No file provided"}),
                status_code=400,
                mimetype="application/json"
            )

        file_bytes = file.stream.read()

        # -----------------------------
        # 2️⃣ File Size Validation
        # -----------------------------
        file_size_mb = len(file_bytes) / (1024 * 1024)

        if file_size_mb > MAX_FILE_SIZE_MB:
            return func.HttpResponse(
                json.dumps({"error": "File exceeds 5MB limit"}),
                status_code=400,
                mimetype="application/json"
            )

        logging.info(f"File received: {file.filename}")
        logging.info(f"File size: {file_size_mb:.2f} MB")

        # -----------------------------
        # 3️⃣ Azure Document Intelligence
        # -----------------------------
        result = analyze_resume(file_bytes)

        extracted_text = result.get("extracted_text", "")
        ai_feedback = result.get("ai_feedback", "")

        logging.info(f"Extracted text length: {len(extracted_text)}")

        if not extracted_text:
            return func.HttpResponse(
                json.dumps({"error": "Resume extraction failed"}),
                status_code=500,
                mimetype="application/json"
            )

        # -----------------------------
        # 4️⃣ Upload to Blob (Correct Extension)
        # -----------------------------
        blob_url = upload_resume(file_bytes, file.filename)

        # -----------------------------
        # 5️⃣ Resume Scoring (Real algorithm)
        # -----------------------------
        resume_score = compute_resume_score(extracted_text)

        # -----------------------------
        # 6️⃣ Insert Into SQL
        # -----------------------------
        resume_id = insert_resume(
            user_id=1,
            blob_url=blob_url,
            extracted_text=extracted_text,
            resume_score=resume_score
        )

        # -----------------------------
        # 7️⃣ Skill Extraction
        # -----------------------------
        skills = extract_skills(extracted_text)
        insert_resume_skills(resume_id, skills)

        # -----------------------------
        # 8️⃣ Return JSON Response
        # -----------------------------
        return json_response({
            "success": True,
            "resume_id": resume_id,
            "resume_score": resume_score,
            "skills": skills,
            "ai_feedback": ai_feedback,
        })

    except Exception as e:
        logging.exception("Process Resume Failed")
        return json_response({"success": False, "error": str(e)}, 500)


# ─────────────────────────────────────────────
# 2. Recommend Jobs
# ─────────────────────────────────────────────
@app.function_name(name="recommendJobs")
@app.route(route="recommendJobs", methods=["GET", "OPTIONS"])
def recommend_jobs(req: func.HttpRequest) -> func.HttpResponse:

    # Handle CORS preflight
    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("recommendJobs request received.")

    resume_id_raw = req.params.get("resume_id")
    if not resume_id_raw:
        return json_response({"error": "resume_id query parameter is required."}, 400)

    try:
        resume_id = int(resume_id_raw)
    except ValueError:
        return json_response({"error": "resume_id must be an integer."}, 400)

    try:
        recommendations = generate_recommendations(resume_id)
        return json_response({"success": True, "recommendations": recommendations})

    except Exception as e:
        logging.exception("recommendJobs failed")
        return json_response({"success": False, "error": str(e)}, 500)


# ─────────────────────────────────────────────
# 3. Get Resume Skills (for Skills dashboard)
# ─────────────────────────────────────────────
@app.function_name(name="getResumeSkills")
@app.route(route="getResumeSkills", methods=["GET", "OPTIONS"])
def get_resume_skills(req: func.HttpRequest) -> func.HttpResponse:

    if req.method == "OPTIONS":
        return func.HttpResponse(status_code=204, headers=CORS_HEADERS)

    logging.info("getResumeSkills request received.")

    resume_id_raw = req.params.get("resume_id")
    if not resume_id_raw:
        return json_response({"error": "resume_id query parameter is required."}, 400)

    try:
        resume_id = int(resume_id_raw)
    except ValueError:
        return json_response({"error": "resume_id must be an integer."}, 400)

    try:
        skills = fetch_resume_skills(resume_id)
        return json_response({"success": True, "skills": skills})

    except Exception as e:
        logging.exception("getResumeSkills failed")
        return json_response({"success": False, "error": str(e)}, 500)