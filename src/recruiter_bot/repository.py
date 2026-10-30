"""
Repository module containing hand-written raw SQL queries for Candidates, Jobs, and Matches.
No ORM, query builder, or SQL generation abstractions are used.
"""
import sqlite3
import json
from typing import List, Optional, Dict, Any


def get_all_candidates(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Fetches all candidates with their associated skills and traits using raw SQL."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, experience_years, availability, quirk, created_at
        FROM candidates
        ORDER BY id ASC;
        """
    )
    candidate_rows = cursor.fetchall()
    candidates = []

    for row in candidate_rows:
        cand_id = row["id"]
        # Fetch skills
        cursor.execute(
            "SELECT skill FROM candidate_skills WHERE candidate_id = ? ORDER BY id ASC;",
            (cand_id,),
        )
        skills = [s["skill"] for s in cursor.fetchall()]

        # Fetch traits
        cursor.execute(
            "SELECT trait FROM candidate_traits WHERE candidate_id = ? ORDER BY id ASC;",
            (cand_id,),
        )
        traits = [t["trait"] for t in cursor.fetchall()]

        candidates.append(
            {
                "id": cand_id,
                "name": row["name"],
                "experience_years": row["experience_years"],
                "availability": row["availability"],
                "quirk": row["quirk"],
                "created_at": str(row["created_at"]),
                "skills": skills,
                "traits": traits,
            }
        )
    return candidates


def get_candidate_by_id(conn: sqlite3.Connection, candidate_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single candidate by ID with associated skills and traits."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, name, experience_years, availability, quirk, created_at
        FROM candidates
        WHERE id = ?;
        """,
        (candidate_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    cursor.execute(
        "SELECT skill FROM candidate_skills WHERE candidate_id = ? ORDER BY id ASC;",
        (candidate_id,),
    )
    skills = [s["skill"] for s in cursor.fetchall()]

    cursor.execute(
        "SELECT trait FROM candidate_traits WHERE candidate_id = ? ORDER BY id ASC;",
        (candidate_id,),
    )
    traits = [t["trait"] for t in cursor.fetchall()]

    return {
        "id": row["id"],
        "name": row["name"],
        "experience_years": row["experience_years"],
        "availability": row["availability"],
        "quirk": row["quirk"],
        "created_at": str(row["created_at"]),
        "skills": skills,
        "traits": traits,
    }


def insert_candidate(conn: sqlite3.Connection, candidate_data: Dict[str, Any]) -> int:
    """Inserts a new candidate and their skills/traits via raw SQL."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO candidates (name, experience_years, availability, quirk)
        VALUES (?, ?, ?, ?);
        """,
        (
            candidate_data["name"],
            candidate_data["experience_years"],
            candidate_data["availability"],
            candidate_data["quirk"],
        ),
    )
    candidate_id = cursor.lastrowid

    for skill in candidate_data.get("skills", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO candidate_skills (candidate_id, skill)
            VALUES (?, ?);
            """,
            (candidate_id, skill.strip()),
        )

    for trait in candidate_data.get("traits", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO candidate_traits (candidate_id, trait)
            VALUES (?, ?);
            """,
            (candidate_id, trait.strip()),
        )

    conn.commit()
    return candidate_id


def get_all_jobs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """Fetches all jobs with their required skills and culture keywords using raw SQL."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, title, min_experience_years, tagline, created_at
        FROM jobs
        ORDER BY id ASC;
        """
    )
    job_rows = cursor.fetchall()
    jobs = []

    for row in job_rows:
        job_id = row["id"]
        # Fetch required skills
        cursor.execute(
            "SELECT skill FROM job_required_skills WHERE job_id = ? ORDER BY id ASC;",
            (job_id,),
        )
        skills = [s["skill"] for s in cursor.fetchall()]

        # Fetch culture keywords
        cursor.execute(
            "SELECT keyword FROM job_culture_keywords WHERE job_id = ? ORDER BY id ASC;",
            (job_id,),
        )
        keywords = [k["keyword"] for k in cursor.fetchall()]

        jobs.append(
            {
                "id": job_id,
                "title": row["title"],
                "min_experience_years": row["min_experience_years"],
                "tagline": row["tagline"],
                "created_at": str(row["created_at"]),
                "required_skills": skills,
                "culture_keywords": keywords,
            }
        )
    return jobs


def get_job_by_id(conn: sqlite3.Connection, job_id: int) -> Optional[Dict[str, Any]]:
    """Fetches a single job by ID with required skills and culture keywords."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id, title, min_experience_years, tagline, created_at
        FROM jobs
        WHERE id = ?;
        """,
        (job_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None

    cursor.execute(
        "SELECT skill FROM job_required_skills WHERE job_id = ? ORDER BY id ASC;",
        (job_id,),
    )
    skills = [s["skill"] for s in cursor.fetchall()]

    cursor.execute(
        "SELECT keyword FROM job_culture_keywords WHERE job_id = ? ORDER BY id ASC;",
        (job_id,),
    )
    keywords = [k["keyword"] for k in cursor.fetchall()]

    return {
        "id": row["id"],
        "title": row["title"],
        "min_experience_years": row["min_experience_years"],
        "tagline": row["tagline"],
        "created_at": str(row["created_at"]),
        "required_skills": skills,
        "culture_keywords": keywords,
    }


def insert_job(conn: sqlite3.Connection, job_data: Dict[str, Any]) -> int:
    """Inserts a new job and its required skills/keywords via raw SQL."""
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO jobs (title, min_experience_years, tagline)
        VALUES (?, ?, ?);
        """,
        (
            job_data["title"],
            job_data["min_experience_years"],
            job_data["tagline"],
        ),
    )
    job_id = cursor.lastrowid

    for skill in job_data.get("required_skills", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO job_required_skills (job_id, skill)
            VALUES (?, ?);
            """,
            (job_id, skill.strip()),
        )

    for keyword in job_data.get("culture_keywords", []):
        cursor.execute(
            """
            INSERT OR IGNORE INTO job_culture_keywords (job_id, keyword)
            VALUES (?, ?);
            """,
            (job_id, keyword.strip()),
        )

    conn.commit()
    return job_id


def upsert_match(conn: sqlite3.Connection, match_record: Dict[str, Any]) -> None:
    """
    Saves or updates a computed match record in the database using raw SQL ON CONFLICT DO UPDATE.
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO matches (
            job_id, candidate_id, overall_score, skill_score, experience_score,
            availability_score, culture_score, reason, matched_skills, missing_skills,
            matched_culture, computed_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(job_id, candidate_id) DO UPDATE SET
            overall_score = excluded.overall_score,
            skill_score = excluded.skill_score,
            experience_score = excluded.experience_score,
            availability_score = excluded.availability_score,
            culture_score = excluded.culture_score,
            reason = excluded.reason,
            matched_skills = excluded.matched_skills,
            missing_skills = excluded.missing_skills,
            matched_culture = excluded.matched_culture,
            computed_at = CURRENT_TIMESTAMP;
        """,
        (
            match_record["job_id"],
            match_record["candidate_id"],
            match_record["overall_score"],
            match_record["skill_score"],
            match_record["experience_score"],
            match_record["availability_score"],
            match_record["culture_score"],
            match_record["reason"],
            json.dumps(match_record.get("matched_skills", [])),
            json.dumps(match_record.get("missing_skills", [])),
            json.dumps(match_record.get("matched_culture", [])),
        ),
    )
    conn.commit()


def get_stats(conn: sqlite3.Connection) -> Dict[str, int]:
    """Returns total counts for candidates, jobs, and matches."""
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            (SELECT COUNT(*) FROM candidates) AS candidate_count,
            (SELECT COUNT(*) FROM jobs) AS job_count,
            (SELECT COUNT(*) FROM matches) AS match_count;
        """
    )
    row = cursor.fetchone()
    return {
        "candidate_count": row["candidate_count"],
        "job_count": row["job_count"],
        "match_count": row["match_count"],
    }
