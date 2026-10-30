"""
Job routes: CRUD and the primary GET /jobs/{id}/matches matching endpoint.
"""
from typing import List, Optional
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from recruiter_bot.db import get_db_connection
from recruiter_bot.repository import (
    get_all_jobs,
    get_job_by_id,
    insert_job,
    get_all_candidates,
    upsert_match,
)
from recruiter_bot.matcher import rank_candidates_for_job
from recruiter_bot.models import (
    JobResponse,
    JobCreate,
    JobMatchesResponse,
    CandidateMatchItem,
    CandidateResponse,
    MatchBreakdown,
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])


def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.get("", response_model=List[JobResponse])
def list_jobs(conn: sqlite3.Connection = Depends(get_db)):
    """List all job openings stored in the database."""
    return get_all_jobs(conn)


@router.post("", response_model=JobResponse, status_code=201)
def create_job(payload: JobCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new job opening using raw SQL."""
    job_id = insert_job(conn, payload.model_dump())
    job = get_job_by_id(conn, job_id)
    return job


@router.get("/{id}", response_model=JobResponse)
def get_job(id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Get a single job opening by its ID."""
    job = get_job_by_id(conn, id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {id} not found")
    return job


@router.get("/{id}/matches", response_model=JobMatchesResponse)
def get_job_matches(
    id: int,
    limit: int = Query(50, ge=1, le=100, description="Max matches to return"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum overall score threshold"),
    persist: bool = Query(True, description="Whether to persist computed matches to matches table"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    GET /jobs/{id}/matches — Core requirement:
    Returns ranked candidates for a job, with an overall score, detailed breakdown, and short reason.
    """
    job = get_job_by_id(conn, id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job with ID {id} not found")

    candidates = get_all_candidates(conn)
    ranked = rank_candidates_for_job(job, candidates, min_score=min_score, limit=limit)

    results = []
    for item in ranked:
        match_info = item["match"]
        cand_data = item["candidate"]

        # Persist to matches table if requested
        if persist:
            upsert_match(conn, match_info)

        breakdown = MatchBreakdown(
            skill_score=match_info["skill_score"],
            experience_score=match_info["experience_score"],
            availability_score=match_info["availability_score"],
            culture_score=match_info["culture_score"],
            matched_skills=match_info["matched_skills"],
            missing_skills=match_info["missing_skills"],
            matched_culture=match_info["matched_culture"],
        )

        results.append(
            CandidateMatchItem(
                candidate=CandidateResponse(**cand_data),
                score=match_info["overall_score"],
                reason=match_info["reason"],
                breakdown=breakdown,
            )
        )

    return JobMatchesResponse(
        job=JobResponse(**job),
        total_candidates_evaluated=len(candidates),
        matches=results,
    )
