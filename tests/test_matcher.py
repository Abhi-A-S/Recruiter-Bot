"""
Unit tests for the Recruiter-Bot matching algorithm.
"""
import pytest
from recruiter_bot.matcher import (
    compute_match,
    rank_candidates_for_job,
    rank_jobs_for_candidate,
)


@pytest.fixture
def sample_job():
    return {
        "id": 1,
        "title": "Backend Detective",
        "required_skills": ["deduction", "pattern-recognition", "forensics"],
        "min_experience_years": 3,
        "culture_keywords": ["analytical", "autonomous"],
        "tagline": "We have a bug. We have no leads. We have you.",
    }


@pytest.fixture
def sample_candidates():
    return [
        {
            "id": 1,
            "name": "Sherlock H.",
            "skills": ["deduction", "pattern-recognition", "forensics"],
            "experience_years": 8,
            "availability": "Immediate",
            "traits": ["analytical", "blunt"],
            "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
        },
        {
            "id": 2,
            "name": "Hermione G.",
            "skills": ["research", "time-management", "public-speaking"],
            "experience_years": 4,
            "availability": "2 weeks",
            "traits": ["detail-oriented", "overachiever"],
            "quirk": "Reads the entire documentation before writing a single line of code.",
        },
        {
            "id": 3,
            "name": "Tony S.",
            "skills": ["systems-design", "rapid-prototyping", "leadership"],
            "experience_years": 12,
            "availability": "Not looking",
            "traits": ["confident", "innovative"],
            "quirk": "Ships an MVP overnight, refuses to write tests.",
        },
    ]


def test_perfect_candidate_match(sample_job, sample_candidates):
    sherlock = sample_candidates[0]
    match = compute_match(sherlock, sample_job)

    # Sherlock has all 3 required skills
    assert match["skill_score"] >= 48.0
    assert len(match["matched_skills"]) == 3
    assert len(match["missing_skills"]) == 0

    # 8 yrs experience exceeds 3 yr min -> max exp score
    assert match["experience_score"] == 25.0

    # Immediate availability
    assert match["availability_score"] == 15.0

    # 'analytical' trait matches 'analytical' culture keyword
    assert "analytical" in match["matched_culture"]
    assert match["culture_score"] == 5.0

    # Total score should be ~93-95
    assert match["overall_score"] >= 90.0
    assert "Complete skill match" in match["reason"]
    assert "Solves problems by eliminating the impossible" in match["reason"]


def test_zero_skill_overlap(sample_job, sample_candidates):
    tony = sample_candidates[2]
    match = compute_match(tony, sample_job)

    # 0 required skills matched
    assert match["skill_score"] == 0.0
    assert len(match["matched_skills"]) == 0
    assert len(match["missing_skills"]) == 3
    # Tony is not looking
    assert match["availability_score"] == 4.0
    # Overall score should be low
    assert match["overall_score"] < 40.0


def test_experience_deficit(sample_job):
    junior_candidate = {
        "id": 99,
        "name": "Junior Detective",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "experience_years": 1,
        "availability": "Immediate",
        "traits": ["analytical"],
        "quirk": "Always takes notes.",
    }
    match = compute_match(junior_candidate, sample_job)
    # Deficit should reduce experience score below 10 pts
    assert match["experience_score"] < 10.0
    assert "Deficit: 1 yrs vs 3 yrs required" in match["reason"]


def test_rank_candidates_ordering(sample_job, sample_candidates):
    ranked = rank_candidates_for_job(sample_job, sample_candidates)
    assert len(ranked) == 3
    # Sherlock must rank #1
    assert ranked[0]["candidate"]["name"] == "Sherlock H."
    assert ranked[0]["match"]["overall_score"] > ranked[1]["match"]["overall_score"]


def test_rank_jobs_reverse(sample_candidates):
    sherlock = sample_candidates[0]
    jobs = [
        {
            "id": 1,
            "title": "Backend Detective",
            "required_skills": ["deduction", "pattern-recognition", "forensics"],
            "min_experience_years": 3,
            "culture_keywords": ["analytical", "autonomous"],
            "tagline": "We have a bug. We have no leads.",
        },
        {
            "id": 2,
            "title": "Sales Engineer",
            "required_skills": ["sales", "public-speaking", "negotiation"],
            "min_experience_years": 3,
            "culture_keywords": ["enthusiastic"],
            "tagline": "Sell the vision.",
        },
    ]
    ranked = rank_jobs_for_candidate(sherlock, jobs)
    assert len(ranked) == 2
    # Backend Detective must be #1 for Sherlock
    assert ranked[0]["job"]["title"] == "Backend Detective"
    assert ranked[0]["match"]["overall_score"] > ranked[1]["match"]["overall_score"]
