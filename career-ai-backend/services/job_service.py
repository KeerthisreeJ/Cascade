import os
import pyodbc


def get_connection():
    return pyodbc.connect(os.getenv("SQL_CONNECTION_STRING"))


def fetch_all_jobs():
    """Returns list of dicts with full job metadata."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            job_id,
            required_skills,
            ISNULL(job_title,    'Position ' + CAST(job_id AS NVARCHAR)) AS job_title,
            ISNULL(company,      'Company')                               AS company,
            ISNULL(experience_level, 'Mid-level')                        AS experience_level,
            ISNULL(location,     'Remote')                               AS location,
            ISNULL(description,  '')                                     AS description
        FROM JobListings
    """)

    columns = [col[0] for col in cursor.description]
    jobs = [dict(zip(columns, row)) for row in cursor.fetchall()]

    cursor.close()
    conn.close()

    return jobs
