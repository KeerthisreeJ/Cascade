"""
jobs_api_service.py — Fetches real, worldwide live job listings from the Adzuna API.

Searches across multiple countries IN PARALLEL and aggregates results globally.

Register at: https://developer.adzuna.com/ (free)
Add to local.settings.json:
  "ADZUNA_APP_ID": "your_app_id",
  "ADZUNA_APP_KEY": "your_app_key",
  "ADZUNA_COUNTRY": "worldwide"   <-- or a specific code like 'in', 'us', 'gb'
"""

import os
import logging
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

ADZUNA_APP_ID  = os.getenv("ADZUNA_APP_ID")
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY")
ADZUNA_COUNTRY = os.getenv("ADZUNA_COUNTRY", "worldwide")

# Results to fetch per country when running worldwide mode
RESULTS_PER_COUNTRY = 5

# Results to fetch when querying a single country
RESULTS_SINGLE = 20

# All Adzuna-supported country codes (fully operational regions)
ALL_COUNTRIES = {
    "us": "🇺🇸 USA",
    "gb": "🇬🇧 UK",
    "in": "🇮🇳 India",
    "au": "🇦🇺 Australia",
    "ca": "🇨🇦 Canada",
    "de": "🇩🇪 Germany",
    "fr": "🇫🇷 France",
    "sg": "🇸🇬 Singapore",
    "za": "🇿🇦 South Africa",
    "nl": "🇳🇱 Netherlands",
    "nz": "🇳🇿 New Zealand",
    "br": "🇧🇷 Brazil",
    "pl": "🇵🇱 Poland",
    "ru": "🇷🇺 Russia",
    "at": "🇦🇹 Austria",
    "be": "🇧🇪 Belgium",
    "ch": "🇨🇭 Switzerland",
    "es": "🇪🇸 Spain",
    "it": "🇮🇹 Italy",
    "no": "🇳🇴 Norway",
    "se": "🇸🇪 Sweden",
}

SKILL_KEYWORDS = [
    "python", "java", "c++", "c#", "javascript", "typescript",
    "html", "css", "sql", "mongodb", "postgresql", "mysql", "nosql", "redis",
    "azure", "aws", "gcp", "docker", "kubernetes",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "react", "node.js", "django", "flask", "fastapi", "spring",
    "git", "linux", "agile", "scrum", "rest api", "graphql",
]


def _build_query(skills: list) -> str:
    """Build a focused search query from resume skills."""
    generic = {"html", "css", "git", "linux", "agile", "scrum"}
    specific = [s for s in skills if s.lower() not in generic]
    top = specific[:4] if specific else skills[:4]
    return " ".join(top) if top else "software developer"


def _extract_skills_from_text(text: str) -> list:
    """Extract known tech skills mentioned in a job description."""
    text_lower = text.lower()
    return [s for s in SKILL_KEYWORDS if s in text_lower]


def _fetch_country(country_code: str, country_label: str, query: str, n_results: int) -> list:
    """
    Fetch jobs from a single Adzuna country endpoint.
    Returns a list of normalised job dicts (or [] on any failure).
    """
    url = f"https://api.adzuna.com/v1/api/jobs/{country_code}/search/1"
    params = {
        "app_id":           ADZUNA_APP_ID,
        "app_key":          ADZUNA_APP_KEY,
        "results_per_page": n_results,
        "what":             query,
        "content-type":     "application/json",
        "sort_by":          "relevance",
    }

    try:
        resp = requests.get(url, params=params, timeout=8)
        resp.raise_for_status()
        results = resp.json().get("results", [])
    except Exception as e:
        logging.warning(f"Adzuna [{country_code}] failed: {e}")
        return []

    jobs = []
    for i, r in enumerate(results):
        description = r.get("description", "")
        required_skills = _extract_skills_from_text(description)

        title_lower = r.get("title", "").lower()
        if any(w in title_lower for w in ["senior", "lead", "principal", "staff", "head", "architect"]):
            exp_level = "Senior"
        elif any(w in title_lower for w in ["junior", "intern", "graduate", "fresher", "entry", "trainee"]):
            exp_level = "Junior"
        else:
            exp_level = "Mid-level"

        # Adzuna location field — append country flag label for clarity
        raw_location = r.get("location", {}).get("display_name", country_label)
        location = f"{raw_location}, {country_label}" if country_label not in raw_location else raw_location

        jobs.append({
            "job_id":           f"az_{country_code}_{r.get('id', i)}",
            "job_title":        r.get("title", "Software Role"),
            "company":          r.get("company", {}).get("display_name", "Company"),
            "location":         location,
            "experience_level": exp_level,
            "description":      description[:500],
            "required_skills":  ", ".join(required_skills) if required_skills else query,
            "redirect_url":     r.get("redirect_url", "#"),
            "salary_min":       r.get("salary_min"),
            "salary_max":       r.get("salary_max"),
            "country_code":     country_code,
        })

    logging.info(f"Adzuna [{country_code}]: {len(jobs)} jobs fetched.")
    return jobs


def fetch_live_jobs(skills: list) -> list:
    """
    Fetch real job listings from Adzuna.

    - If ADZUNA_COUNTRY = 'worldwide' (default): queries ALL countries in parallel.
    - If ADZUNA_COUNTRY = a specific code (e.g. 'us'): queries only that country.

    Returns a merged, globally-sourced list of job dicts.
    """
    if not ADZUNA_APP_ID or not ADZUNA_APP_KEY:
        logging.warning("Adzuna API keys not set — falling back to DB jobs.")
        return []

    query = _build_query(skills)

    if ADZUNA_COUNTRY.lower() == "worldwide":
        # ── Parallel multi-country fetch ─────────────────────────────
        logging.info(f"Worldwide Adzuna fetch | query: '{query}' | {len(ALL_COUNTRIES)} regions")

        all_jobs = []
        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {
                pool.submit(_fetch_country, code, label, query, RESULTS_PER_COUNTRY): code
                for code, label in ALL_COUNTRIES.items()
            }
            for future in as_completed(futures):
                all_jobs.extend(future.result())

        logging.info(f"Total worldwide jobs fetched: {len(all_jobs)}")
        return all_jobs

    else:
        # ── Single country fetch ──────────────────────────────────────
        label = ALL_COUNTRIES.get(ADZUNA_COUNTRY, ADZUNA_COUNTRY.upper())
        logging.info(f"Single-country Adzuna fetch | country: {ADZUNA_COUNTRY} | query: '{query}'")
        return _fetch_country(ADZUNA_COUNTRY, label, query, RESULTS_SINGLE)
