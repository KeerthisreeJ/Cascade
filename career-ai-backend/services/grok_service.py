import os
import requests

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_ENDPOINT = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"


def _call_groq(prompt: str, temperature: float = 0.7) -> str:
    """Shared Groq API caller."""
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    response = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
    result = response.json()

    if "choices" not in result:
        return f"Groq API error: {result}"

    return result["choices"][0]["message"]["content"]


def generate_learning_roadmap(job_title: str, missing_skills: list) -> str:
    """
    Generate a structured learning roadmap with specific Coursera/Udemy
    course recommendations for each missing skill.
    """
    skills_str = ", ".join(missing_skills)

    prompt = f"""
You are a senior career development coach and learning strategist.

A candidate wants to become a '{job_title}' but is missing these skills:
{skills_str}

Generate a structured learning roadmap in this EXACT format (use plain text, no markdown asterisks):

TOTAL DURATION: X weeks

PHASE 1 – [Skill/Topic Name] (Week 1–N)
Overview: One sentence on what they will achieve in this phase.
- Task 1
- Task 2
- Task 3

COURSERA COURSES:
- [Exact Course Name] by [University/Provider] — [Duration] — [URL or search term]
- [Exact Course Name] by [University/Provider] — [Duration] — [URL or search term]

UDEMY COURSES:
- [Exact Course Name] by [Instructor] — [Duration]
- [Exact Course Name] by [Instructor] — [Duration]

PHASE 2 – [Next Topic] (Week N–M)
Overview: One sentence.
- Task 1
- Task 2

COURSERA COURSES:
- [Course Name] — [Duration]

UDEMY COURSES:
- [Course Name] — [Duration]

CERTIFICATIONS TO EARN:
- [Certification Name] by [Provider] — Estimated prep time: X weeks
- [Certification Name] by [Provider] — Estimated prep time: X weeks

PORTFOLIO PROJECTS:
- [Project Name]: Brief description of what to build and what skill it demonstrates
- [Project Name]: Brief description

Important rules:
- Recommend REAL, well-known courses that actually exist on Coursera and Udemy
- For Coursera, prefer courses from Google, IBM, Meta, Stanford, DeepLearning.AI
- For Udemy, prefer courses by well-known instructors (Jose Portilla, Angela Yu, Andrei Neagoie, etc.)
- Be specific with course names — do NOT make up courses
- Keep total output under 500 words
"""
    return _call_groq(prompt)


def generate_resume_feedback(extracted_text: str) -> str:
    """
    Generate structured AI resume feedback as bullet points.
    Returns a pipe-delimited structured string that the frontend parses
    into a clean, sectioned bullet-point display.
    """
    truncated = extracted_text[:3000]

    prompt = f"""
You are an expert resume reviewer and ATS specialist.

Analyze this resume and provide feedback in this EXACT format.
Use only plain text. No markdown. No asterisks. No bold. Use the exact section labels shown.

---
{truncated}
---

STRENGTHS:
• [specific strength 1]
• [specific strength 2]
• [specific strength 3]

IMPROVEMENTS:
• [specific actionable improvement 1]
• [specific actionable improvement 2]
• [specific actionable improvement 3]

MISSING KEYWORDS:
• [important keyword 1]
• [important keyword 2]
• [important keyword 3]
• [important keyword 4]

ATS SCORE ESTIMATE: [X]/100

OVERALL VERDICT: [One sentence, direct and honest assessment]

Rules:
- Each bullet must be a complete, actionable sentence
- MISSING KEYWORDS must be specific technical or industry terms not found in this resume
- ATS SCORE should honestly reflect how likely an ATS system would parse this resume
- Be direct, honest, and constructive
- Total output must be under 220 words
"""
    return _call_groq(prompt, temperature=0.4)