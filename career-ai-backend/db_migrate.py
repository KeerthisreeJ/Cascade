"""
db_migrate.py — Run once to:
  1. Add job_title, company, description, experience_level, location columns to JobListings
  2. Seed realistic job listings

Run from the backend venv:
    python db_migrate.py
"""
import os
import pyodbc

# Reads from environment variable set by 'func start', or falls back to hardcoded value
conn_str = os.getenv("SQL_CONNECTION_STRING") or (
    "Driver={ODBC Driver 18 for SQL Server};"
    "Server=tcp:career-ai-sqlserver01.database.windows.net,1433;"
    "Database=career-ai-db;"
    "Uid=azureadmin;Pwd=Test@123;"
    "Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

print("Connected to Azure SQL.")

# ─────────────────────────────────────────────
# 1. Alter JobListings — add new columns if they don't exist
# ─────────────────────────────────────────────
alter_stmts = [
    "IF COL_LENGTH('JobListings','job_title')    IS NULL ALTER TABLE JobListings ADD job_title        NVARCHAR(255)  NULL;",
    "IF COL_LENGTH('JobListings','company')       IS NULL ALTER TABLE JobListings ADD company          NVARCHAR(255)  NULL;",
    "IF COL_LENGTH('JobListings','description')   IS NULL ALTER TABLE JobListings ADD description      NVARCHAR(MAX)  NULL;",
    "IF COL_LENGTH('JobListings','experience_level') IS NULL ALTER TABLE JobListings ADD experience_level NVARCHAR(50) NULL;",
    "IF COL_LENGTH('JobListings','location')      IS NULL ALTER TABLE JobListings ADD location         NVARCHAR(100)  NULL;",
]

for stmt in alter_stmts:
    cursor.execute(stmt)
    print(f"  Ran: {stmt[:80]}...")

conn.commit()
print("JobListings columns added.")

# ─────────────────────────────────────────────
# 2. Upsert realistic job listings
# ─────────────────────────────────────────────
jobs = [
    (1, "Software Engineer",           "Microsoft",  "Python, SQL, Azure, Machine Learning",              "Mid-level", "Bangalore, India"),
    (2, "Data Engineer",               "Google",     "Python, SQL, MongoDB, Machine Learning",            "Mid-level", "Hyderabad, India"),
    (3, "Cloud Solutions Architect",   "Amazon AWS", "Azure, Python, SQL, JavaScript",                    "Senior",    "Remote"),
    (4, "Full Stack Developer",        "Infosys",    "JavaScript, HTML, CSS, Python, MongoDB",            "Junior",    "Chennai, India"),
    (5, "Machine Learning Engineer",   "TCS",        "Python, Machine Learning, SQL",                     "Mid-level", "Pune, India"),
    (6, "Backend Developer",           "Wipro",      "Java, Python, SQL, MongoDB",                       "Junior",    "Bangalore, India"),
    (7, "DevOps Engineer",             "HCL",        "Azure, Python, SQL, JavaScript",                   "Mid-level", "Noida, India"),
    (8, "AI Research Scientist",       "IBM",        "Python, Machine Learning, SQL, C++",               "Senior",    "Delhi, India"),
]

cursor.execute("SET IDENTITY_INSERT JobListings ON")

for job_id, title, company, skills, exp_level, location in jobs:
    cursor.execute("""
        MERGE JobListings AS target
        USING (SELECT ? AS job_id) AS source ON target.job_id = source.job_id
        WHEN MATCHED THEN
            UPDATE SET job_title = ?, company = ?, required_skills = ?, experience_level = ?, location = ?
        WHEN NOT MATCHED THEN
            INSERT (job_id, job_title, company, required_skills, experience_level, location)
            VALUES (?, ?, ?, ?, ?, ?);
    """, job_id, title, company, skills, exp_level, location,
         job_id, title, company, skills, exp_level, location)

cursor.execute("SET IDENTITY_INSERT JobListings OFF")

conn.commit()
print(f"Seeded {len(jobs)} job listings.")

cursor.close()
conn.close()
print("Done. Database migration complete.")
