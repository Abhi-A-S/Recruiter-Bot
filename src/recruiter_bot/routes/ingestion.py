"""
Ingestion & admin routes for seeding, bulk loading, and system statistics.
"""
from typing import List, Dict, Any
import sqlite3
from fastapi import APIRouter, Depends
from recruiter_bot.db import get_db_connection
from recruiter_bot.seed_data import seed_database
from recruiter_bot.repository import (
    insert_candidate,
    insert_job,
    get_stats,
)
from recruiter_bot.models import CandidateCreate, JobCreate

router = APIRouter(prefix="/api", tags=["Ingestion & Admin"])


def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.post("/seed")
def trigger_seed():
    """
    Reseeds the database with the canonical 15 fictional candidates and 6 jobs
    from the RecruiterFlow specification.
    """
    result = seed_database(reset=True)
    return result


@router.get("/stats")
def read_system_stats(conn: sqlite3.Connection = Depends(get_db)):
    """Returns total counts of candidates, jobs, and persisted matches."""
    return get_stats(conn)


@router.post("/ingest/candidates")
def bulk_ingest_candidates(
    candidates: List[CandidateCreate],
    conn: sqlite3.Connection = Depends(get_db),
):
    """Bulk ingest new candidates into the system."""
    inserted = []
    for cand in candidates:
        cid = insert_candidate(conn, cand.model_dump())
        inserted.append(cid)
    return {"status": "success", "count": len(inserted), "candidate_ids": inserted}


@router.post("/ingest/jobs")
def bulk_ingest_jobs(
    jobs: List[JobCreate],
    conn: sqlite3.Connection = Depends(get_db),
):
    """Bulk ingest new job openings into the system."""
    inserted = []
    for job in jobs:
        jid = insert_job(conn, job.model_dump())
        inserted.append(jid)
    return {"status": "success", "count": len(inserted), "job_ids": inserted}
