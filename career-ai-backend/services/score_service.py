"""
score_service.py — Real resume scoring algorithm.

Score is computed from 4 weighted signals (0–100):
  1. Skills coverage    (40%) — how many known skills are present
  2. Content length     (20%) — sufficient detail (word count)
  3. Structure signals  (20%) — section keywords present (education, experience, projects, etc.)
  4. Contact signals    (20%) — contact details present (email, phone, LinkedIn)

No ML model needed — fast, deterministic, transparent.
"""

import re

KNOWN_SKILLS = [
    "python", "java", "c++", "c#", "javascript", "typescript", "html", "css",
    "sql", "mongodb", "postgresql", "mysql", "nosql", "redis",
    "azure", "aws", "gcp", "docker", "kubernetes",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch", "scikit-learn",
    "react", "node.js", "django", "flask", "fastapi", "spring",
    "git", "linux", "agile", "scrum", "rest api", "graphql",
]

SECTION_KEYWORDS = [
    "experience", "education", "skills", "projects", "certifications",
    "achievements", "summary", "objective", "internship", "publications",
]

CONTACT_PATTERNS = [
    r"[\w.+-]+@[\w-]+\.[a-z]{2,}",          # email
    r"\+?\d[\d\s\-().]{7,}\d",               # phone
    r"linkedin\.com/in/[\w-]+",              # linkedin
    r"github\.com/[\w-]+",                   # github
]


def compute_resume_score(text: str) -> int:
    """
    Returns an integer score in range [0, 100].
    """
    text_lower = text.lower()
    words = text_lower.split()
    word_count = len(words)

    # ── 1. Skills coverage (40 pts) ──────────────────────────────────
    matched_skills = sum(1 for s in KNOWN_SKILLS if s in text_lower)
    skills_score = min(matched_skills / max(len(KNOWN_SKILLS) * 0.4, 1), 1.0) * 40

    # ── 2. Content length (20 pts) ───────────────────────────────────
    # Full marks at ≥ 400 words; scales linearly below
    length_score = min(word_count / 400, 1.0) * 20

    # ── 3. Structure signals (20 pts) ────────────────────────────────
    matched_sections = sum(1 for kw in SECTION_KEYWORDS if kw in text_lower)
    structure_score = min(matched_sections / max(len(SECTION_KEYWORDS) * 0.5, 1), 1.0) * 20

    # ── 4. Contact signals (20 pts) ──────────────────────────────────
    matched_contacts = sum(1 for p in CONTACT_PATTERNS if re.search(p, text_lower))
    contact_score = min(matched_contacts / len(CONTACT_PATTERNS), 1.0) * 20

    total = int(round(skills_score + length_score + structure_score + contact_score))
    return max(5, min(total, 100))  # clamp to [5, 100]
