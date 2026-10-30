"""
Pydantic Schemas for API requests, responses, and match representations.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# --- Candidate Schemas ---
class CandidateBase(BaseModel):
    name: str = Field(..., description="Candidate full name")
    experience_years: int = Field(..., ge=0, description="Years of professional experience")
    availability: str = Field(..., description="'Immediate', '2 weeks', or 'Not looking'")
    quirk: str = Field(..., description="Notable personality quirk or behavior")
    skills: List[str] = Field(default_factory=list, description="List of candidate skills")
    traits: List[str] = Field(default_factory=list, description="List of personality/work traits")


class CandidateCreate(CandidateBase):
    pass


class CandidateResponse(CandidateBase):
    id: int
    created_at: Optional[str] = None


# --- Job Schemas ---
class JobBase(BaseModel):
    title: str = Field(..., description="Job opening title")
    min_experience_years: int = Field(..., ge=0, description="Minimum required experience in years")
    tagline: str = Field(..., description="Short catchy job tagline or pitch")
    required_skills: List[str] = Field(default_factory=list, description="Skills required for the role")
    culture_keywords: List[str] = Field(default_factory=list, description="Culture and team fit keywords")


class JobCreate(JobBase):
    pass


class JobResponse(JobBase):
    id: int
    created_at: Optional[str] = None


# --- Match Breakdown & Response Schemas ---
class MatchBreakdown(BaseModel):
    skill_score: float = Field(..., description="Skill overlap score (max 50 pts)")
    experience_score: float = Field(..., description="Experience fit score (max 25 pts)")
    availability_score: float = Field(..., description="Availability fit score (max 15 pts)")
    culture_score: float = Field(..., description="Culture/trait alignment score (max 10 pts)")
    matched_skills: List[str] = Field(default_factory=list, description="Skills present in both job and candidate")
    missing_skills: List[str] = Field(default_factory=list, description="Job required skills missing in candidate")
    matched_culture: List[str] = Field(default_factory=list, description="Overlapping traits and culture keywords")


class CandidateMatchItem(BaseModel):
    candidate: CandidateResponse
    score: float = Field(..., description="Overall match score (0-100)")
    reason: str = Field(..., description="Human-readable recruitment justification")
    breakdown: MatchBreakdown


class JobMatchesResponse(BaseModel):
    job: JobResponse
    total_candidates_evaluated: int
    matches: List[CandidateMatchItem]


class JobMatchItem(BaseModel):
    job: JobResponse
    score: float = Field(..., description="Overall match score (0-100)")
    reason: str = Field(..., description="Human-readable recruitment justification")
    breakdown: MatchBreakdown


class CandidateMatchesResponse(BaseModel):
    candidate: CandidateResponse
    total_jobs_evaluated: int
    matches: List[JobMatchItem]
