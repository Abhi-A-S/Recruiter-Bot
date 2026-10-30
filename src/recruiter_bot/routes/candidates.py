"""
Candidate routes: CRUD and the reverse GET /candidates/{id}/matches matching endpoint.
"""
from typing import List, Optional
import sqlite3
from fastapi import APIRouter, Depends, HTTPException, Query
from recruiter_bot.db import get_db_connection
from recruiter_bot.repository import (
    get_all_candidates,
    get_candidate_by_id,
    insert_candidate,
    get_all_jobs,
    upsert_match,
)
from recruiter_bot.matcher import rank_jobs_for_candidate
from recruiter_bot.models import (
    CandidateResponse,
    CandidateCreate,
    CandidateMatchesResponse,
    JobMatchItem,
    JobResponse,
    MatchBreakdown,
)

router = APIRouter(prefix="/candidates", tags=["Candidates"])


def get_db():
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()


@router.get("", response_model=List[CandidateResponse])
def list_candidates(conn: sqlite3.Connection = Depends(get_db)):
    """List all candidate profiles stored in the database."""
    return get_all_candidates(conn)


@router.post("", response_model=CandidateResponse, status_code=201)
def create_candidate(payload: CandidateCreate, conn: sqlite3.Connection = Depends(get_db)):
    """Create a new candidate profile using raw SQL."""
    cand_id = insert_candidate(conn, payload.model_dump())
    cand = get_candidate_by_id(conn, cand_id)
    return cand


@router.get("/{id}", response_model=CandidateResponse)
def get_candidate(id: int, conn: sqlite3.Connection = Depends(get_db)):
    """Get a single candidate profile by ID."""
    cand = get_candidate_by_id(conn, id)
    if not cand:
        raise HTTPException(status_code=404, detail=f"Candidate with ID {id} not found")
    return cand


@router.get("/{id}/matches", response_model=CandidateMatchesResponse)
def get_candidate_matches(
    id: int,
    limit: int = Query(50, ge=1, le=100, description="Max matches to return"),
    min_score: float = Query(0.0, ge=0.0, le=100.0, description="Minimum overall score threshold"),
    persist: bool = Query(True, description="Whether to persist computed matches to matches table"),
    conn: sqlite3.Connection = Depends(get_db),
):
    """
    GET /candidates/{id}/matches — Core requirement (reverse direction):
    Returns ranked jobs for a candidate, with an overall score, detailed breakdown, and short reason.
    """
    candidate = get_candidate_by_id(conn, id)
    if not candidate:
        raise HTTPException(status_code=404, detail=f"Candidate with ID {id} not found")

    jobs = get_all_jobs(conn)
    ranked = rank_jobs_for_candidate(candidate, jobs, min_score=min_score, limit=limit)

    results = []
    for item in ranked:
        match_info = item["match"]
        job_data = item["job"]

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
            JobMatchItem(
                job=JobResponse(**job_data),
                score=match_info["overall_score"],
                reason=match_info["reason"],
                breakdown=breakdown,
            )
        )

    return CandidateMatchesResponse(
        candidate=CandidateResponse(**candidate),
        total_jobs_evaluated=len(jobs),
        matches=results,
    )
