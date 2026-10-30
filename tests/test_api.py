"""
API Integration tests for Recruiter-Bot endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import os

from recruiter_bot.main import app
from recruiter_bot.db import init_db, get_db_connection
from recruiter_bot.seed_data import seed_database
import recruiter_bot.config as config


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    test_db_path = tmp_path / "test_recruiterbot.db"
    monkeypatch.setattr(config, "DATABASE_PATH", test_db_path)
    init_db(test_db_path)
    seed_database(test_db_path, reset=True)
    yield


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["stats"]["candidate_count"] == 15
    assert data["stats"]["job_count"] == 6


def test_list_jobs(client):
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 6
    titles = [j["title"] for j in jobs]
    assert "Backend Detective" in titles
    assert "Sales Engineer" in titles


def test_get_job_matches(client):
    # Job 1 is Backend Detective
    response = client.get("/jobs/1/matches")
    assert response.status_code == 200
    data = response.json()
    assert data["job"]["title"] == "Backend Detective"
    assert data["total_candidates_evaluated"] == 15
    assert len(data["matches"]) > 0

    # Top match must be Sherlock Holmes
    top_match = data["matches"][0]
    assert top_match["candidate"]["name"] == "Sherlock H."
    assert top_match["score"] >= 90.0
    assert "deduction" in top_match["breakdown"]["matched_skills"]
    assert "reason" in top_match
    assert len(top_match["reason"]) > 10


def test_job_not_found(client):
    response = client.get("/jobs/99999/matches")
    assert response.status_code == 404


def test_list_candidates(client):
    response = client.get("/candidates")
    assert response.status_code == 200
    cands = response.json()
    assert len(cands) == 15
    names = [c["name"] for c in cands]
    assert "Sherlock H." in names
    assert "Dwight S." in names


def test_get_candidate_matches(client):
    # Candidate 1 is Sherlock H.
    response = client.get("/candidates/1/matches")
    assert response.status_code == 200
    data = response.json()
    assert data["candidate"]["name"] == "Sherlock H."
    assert data["total_jobs_evaluated"] == 6
    assert len(data["matches"]) > 0

    # Top job match for Sherlock should be Backend Detective
    top_match = data["matches"][0]
    assert top_match["job"]["title"] == "Backend Detective"
    assert top_match["score"] >= 90.0


def test_candidate_not_found(client):
    response = client.get("/candidates/99999/matches")
    assert response.status_code == 404


def test_create_candidate(client):
    payload = {
        "name": "Bruce Wayne",
        "skills": ["detective", "martial-arts", "wealth"],
        "experience_years": 10,
        "availability": "Immediate",
        "traits": ["brooding", "vigilant"],
        "quirk": "Only works nights.",
    }
    response = client.post("/candidates", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 15
    assert created["name"] == "Bruce Wayne"
    assert "wealth" in created["skills"]


def test_create_job(client):
    payload = {
        "title": "Gotham Vigilante",
        "min_experience_years": 5,
        "tagline": "Protect the city in the dark.",
        "required_skills": ["martial-arts", "detective"],
        "culture_keywords": ["vigilant"],
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 201
    created = response.json()
    assert created["id"] > 6
    assert created["title"] == "Gotham Vigilante"


def test_reseed_api(client):
    response = client.post("/api/seed")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["candidates_inserted"] == 15
    assert data["jobs_inserted"] == 6
