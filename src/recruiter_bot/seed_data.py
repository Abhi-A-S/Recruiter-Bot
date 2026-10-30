"""
Seed dataset definitions and raw SQL ingestion logic for Candidates and Jobs.
All queries are hand-written raw SQL.
"""
import sqlite3
from typing import Optional
from pathlib import Path
from recruiter_bot.db import get_db_connection, reset_db

SEED_CANDIDATES = [
    {
        "name": "Sherlock H.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "experience_years": 8,
        "availability": "Immediate",
        "traits": ["analytical", "blunt"],
        "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
    },
    {
        "name": "Hermione G.",
        "skills": ["research", "time-management", "public-speaking"],
        "experience_years": 4,
        "availability": "2 weeks",
        "traits": ["detail-oriented", "overachiever"],
        "quirk": "Reads the entire documentation before writing a single line of code.",
    },
    {
        "name": "Tony S.",
        "skills": ["systems-design", "rapid-prototyping", "leadership"],
        "experience_years": 12,
        "availability": "Not looking",
        "traits": ["confident", "innovative"],
        "quirk": "Ships an MVP overnight, refuses to write tests.",
    },
    {
        "name": "Leslie K.",
        "skills": ["project-management", "stakeholder-management", "public-speaking"],
        "experience_years": 6,
        "availability": "Immediate",
        "traits": ["tenacious", "organized"],
        "quirk": "Has a binder for everything, including the binder.",
    },
    {
        "name": "Ron S.",
        "skills": ["woodworking", "minimalism", "negotiation"],
        "experience_years": 15,
        "availability": "Not looking",
        "traits": ["stubborn", "principled"],
        "quirk": "Refuses to use more than one monitor.",
    },
    {
        "name": "Rick S.",
        "skills": ["systems-design", "rapid-prototyping", "chemistry"],
        "experience_years": 20,
        "availability": "Immediate",
        "traits": ["genius", "reckless"],
        "quirk": "Solution works, mechanism deeply concerning.",
    },
    {
        "name": "Elle W.",
        "skills": ["persuasion", "research", "public-speaking"],
        "experience_years": 3,
        "availability": "Immediate",
        "traits": ["optimistic", "sharp"],
        "quirk": "Underestimated in every standup, correct in every retro.",
    },
    {
        "name": "MacGyver",
        "skills": ["rapid-prototyping", "resourcefulness", "chemistry", "systems-design"],
        "experience_years": 10,
        "availability": "2 weeks",
        "traits": ["calm", "improviser"],
        "quirk": "Fixes production outages with duct tape and a paperclip metaphor.",
    },
    {
        "name": "Sheldon C.",
        "skills": ["theoretical-analysis", "pattern-recognition", "research"],
        "experience_years": 9,
        "availability": "Immediate",
        "traits": ["rigid", "brilliant"],
        "quirk": "Correct 95% of the time, insufferable 100% of the time.",
    },
    {
        "name": "Katniss E.",
        "skills": ["precision", "strategy", "crisis-management"],
        "experience_years": 5,
        "availability": "Immediate",
        "traits": ["resilient", "decisive"],
        "quirk": "Excellent under pressure, terrible with public speaking.",
    },
    {
        "name": "Michael S.",
        "skills": ["sales", "public-speaking", "team-building"],
        "experience_years": 11,
        "availability": "Not looking",
        "traits": ["enthusiastic", "chaotic"],
        "quirk": "World's best boss, according to a mug he bought himself.",
    },
    {
        "name": "Olivia P.",
        "skills": ["crisis-management", "negotiation", "strategy", "leadership"],
        "experience_years": 13,
        "availability": "2 weeks",
        "traits": ["decisive", "intense"],
        "quirk": "Handles it. Whatever it is.",
    },
    {
        "name": "Ted L.",
        "skills": ["team-building", "optimism", "mentorship", "public-speaking"],
        "experience_years": 7,
        "availability": "Immediate",
        "traits": ["empathetic", "persistent"],
        "quirk": "Turns every technical setback into a folksy metaphor.",
    },
    {
        "name": "Miranda P.",
        "skills": ["leadership", "negotiation", "stakeholder-management", "precision"],
        "experience_years": 18,
        "availability": "Not looking",
        "traits": ["demanding", "decisive"],
        "quirk": "Reviews every PR personally. Says nothing. Everyone panics.",
    },
    {
        "name": "Dwight S.",
        "skills": ["sales", "negotiation", "security", "loyalty"],
        "experience_years": 9,
        "availability": "Immediate",
        "traits": ["intense", "loyal"],
        "quirk": "Assistant to the regional backend engineer.",
    },
]

SEED_JOBS = [
    {
        "title": "Backend Detective",
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "min_experience_years": 3,
        "culture_keywords": ["analytical", "autonomous"],
        "tagline": "We have a bug. We have no leads. We have you.",
    },
    {
        "title": "Rapid Prototyping Engineer",
        "required_skills": ["rapid-prototyping", "systems-design"],
        "min_experience_years": 2,
        "culture_keywords": ["innovative", "fast-paced"],
        "tagline": "Ship first, document never (kidding — please document).",
    },
    {
        "title": "Developer Relations Lead",
        "required_skills": ["public-speaking", "research"],
        "min_experience_years": 2,
        "culture_keywords": ["energetic", "curious"],
        "tagline": "Explain complex things to confused humans, cheerfully.",
    },
    {
        "title": "Engineering Manager, Chaos Team",
        "required_skills": ["team-building", "stakeholder-management", "leadership"],
        "min_experience_years": 5,
        "culture_keywords": ["empathetic", "organized"],
        "tagline": "Herd cats. The cats are senior engineers.",
    },
    {
        "title": "Incident Commander",
        "required_skills": ["crisis-management", "strategy", "negotiation"],
        "min_experience_years": 4,
        "culture_keywords": ["decisive", "calm-under-pressure"],
        "tagline": "3am page. You're the one who picks up.",
    },
    {
        "title": "Sales Engineer",
        "required_skills": ["sales", "public-speaking", "negotiation"],
        "min_experience_years": 3,
        "culture_keywords": ["enthusiastic", "persistent"],
        "tagline": "Sell the vision, then go build it.",
    },
]


def seed_database(db_path: Optional[Path] = None, reset: bool = True) -> dict:
    """
    Seeds candidates and jobs into the SQLite database using raw SQL.
    Returns counts of inserted records.
    """
    if reset:
        reset_db(db_path)

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # Insert candidates
        inserted_candidates = 0
        for cand in SEED_CANDIDATES:
            cursor.execute(
                """
                INSERT INTO candidates (name, experience_years, availability, quirk)
                VALUES (?, ?, ?, ?);
                """,
                (cand["name"], cand["experience_years"], cand["availability"], cand["quirk"]),
            )
            candidate_id = cursor.lastrowid

            for skill in cand["skills"]:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO candidate_skills (candidate_id, skill)
                    VALUES (?, ?);
                    """,
                    (candidate_id, skill.strip()),
                )

            for trait in cand["traits"]:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO candidate_traits (candidate_id, trait)
                    VALUES (?, ?);
                    """,
                    (candidate_id, trait.strip()),
                )
            inserted_candidates += 1

        # Insert jobs
        inserted_jobs = 0
        for job in SEED_JOBS:
            cursor.execute(
                """
                INSERT INTO jobs (title, min_experience_years, tagline)
                VALUES (?, ?, ?);
                """,
                (job["title"], job["min_experience_years"], job["tagline"]),
            )
            job_id = cursor.lastrowid

            for skill in job["required_skills"]:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO job_required_skills (job_id, skill)
                    VALUES (?, ?);
                    """,
                    (job_id, skill.strip()),
                )

            for keyword in job["culture_keywords"]:
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO job_culture_keywords (job_id, keyword)
                    VALUES (?, ?);
                    """,
                    (job_id, keyword.strip()),
                )
            inserted_jobs += 1

        conn.commit()
        return {
            "status": "success",
            "candidates_inserted": inserted_candidates,
            "jobs_inserted": inserted_jobs,
        }
    finally:
        conn.close()


def seed_cli() -> None:
    """CLI wrapper for database seeding."""
    result = seed_database()
    print(f"Seed complete: {result}")


if __name__ == "__main__":
    seed_cli()
