# Recruiter-Bot 🤖

> **Backend Developer Assignment — RecruiterFlow Engineering**  
> An intelligent candidate and job matching backend service built with **FastAPI Standard**, **uv**, and **SQLite**. Includes a modern, interactive recruitment explorer dashboard and solution for Part 2 **SQL Detective Challenge**.

---

## Table of Contents

1. [Overview](#overview)
2. [Quickstart & Local Installation](#quickstart--local-installation)
3. [Running Tests](#running-tests)
4. [API Reference & curl Examples](#api-reference--curl-examples)
5. [Database Schema & Raw SQL Design](#database-schema--raw-sql-design)
6. [The Matching Algorithm: Decisions & Trade-Offs](#the-matching-algorithm-decisions--trade-offs)
7. [Part 2: The SQL Detective Challenge](#part-2-the-sql-detective-challenge)
8. [Note on AI Tools Usage](#note-on-ai-tools-usage)

---

## Overview

RecruiterFlow is prototyping **Recruiter-Bot** — a backend service that ingests candidate profiles and job openings, then ranks the best matches for each.

### Core Deliverables

- **Ingestion & Seeding**: Auto-initializes schema on startup; provides both CLI (`recruiterbot-seed`) and REST endpoint (`POST /api/seed`) for reloading canonical data.
- **Bidirectional Matching API**:
  - `GET /jobs/{id}/matches`: Ranked candidates for a job opening with score breakdown and short recruitment rationale.
  - `GET /candidates/{id}/matches`: Ranked jobs for a candidate (reverse direction).
- **Multi-Factor Matching Algorithm**: Evaluates skill overlap, experience fit, availability velocity, and culture keywords, producing deterministic scores and human-readable hiring rationales.
- **Part 2 SQL Detective**: `sql_detective.sql` answering 5 SQL challenge questions
- **Interactive Visual Explorer**: A dashboard at `http://localhost:8000/` for interactive testing and match inspection.

---

## Quickstart & Local Installation

### Prerequisites

- Python `>= 3.12.15`
- [uv](https://docs.astral.sh/uv/) package manager

### 1. Install Dependencies

```bash
# Clone the repository and navigate into it
git clone <repo-url>
cd recruiterflow-gemini

# Sync dependencies using uv
uv sync
```

### 2. Run Database Seeding (Optional)

The server auto-initializes the schema and seeds data on first run if the database is empty. You can also seed explicitly via:

```bash
uv run python -m recruiter_bot.seed_data
# or using the configured uv script:
uv run recruiterbot-seed
```

### 3. Start the Backend Server

```bash
uv run uvicorn recruiter_bot.main:app --host 0.0.0.0 --port 8000 --reload
# or using the CLI runner:
uv run recruiterbot
```

### 4. Explore

- **Interactive Visual Explorer**: Open [http://localhost:8000/](http://localhost:8000/) in your browser.
- **Interactive Swagger Docs**: Open [http://localhost:8000/docs](http://localhost:8000/docs).
- **OpenAPI JSON**: Available at [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json).

---

## Running Tests

A test suite covers both unit logic (matcher score calculations, edge cases, tie breaking) and integration flows (FastAPI routes, raw SQL repository, and Part 2 SQL detective queries):

```bash
# Run all tests with uv
uv run pytest -v
```

---

## API Reference & curl Examples

### 1. Match Candidates for a Job (Required Endpoint)

`GET /jobs/{id}/matches`

Returns candidates ranked by match score for a given job, including a breakdown and recruitment rationale.

```bash
# Get top matching candidates for Job 1 (Backend Detective)
curl -s "http://localhost:8000/jobs/1/matches?limit=3" | python -m json.tool
```

**Example JSON Response:**

```json
{
  "job": {
    "title": "Backend Detective",
    "min_experience_years": 3,
    "tagline": "We have a bug. We have no leads. We have you.",
    "required_skills": ["deduction", "pattern-recognition", "forensics"],
    "culture_keywords": ["analytical", "autonomous"],
    "id": 1,
    "created_at": "2026-10-29 07:03:19"
  },
  "total_candidates_evaluated": 15,
  "matches": [
    {
      "candidate": {
        "name": "Sherlock H.",
        "experience_years": 8,
        "availability": "Immediate",
        "quirk": "Solves problems by eliminating the impossible; occasionally insufferable in standups.",
        "skills": ["deduction", "pattern-recognition", "forensics"],
        "traits": ["analytical", "blunt"],
        "id": 1,
        "created_at": "2026-10-29 07:03:19"
      },
      "score": 95.0,
      "reason": "Complete skill match on deduction, pattern-recognition, forensics. Solid fit: 8 yrs satisfies 3 yrs min. Available immediately. Culture alignment on analytical. Quirk note: Solves problems by eliminating the impossible; occasionally insufferable in standups.",
      "breakdown": {
        "skill_score": 50.0,
        "experience_score": 25.0,
        "availability_score": 15.0,
        "culture_score": 5.0,
        "matched_skills": ["deduction", "pattern-recognition", "forensics"],
        "missing_skills": [],
        "matched_culture": ["analytical"]
      }
    }
  ]
}
```

---

### 2. Match Jobs for a Candidate (Required Reverse Endpoint)

`GET /candidates/{id}/matches`

Returns jobs ranked by fit for a given candidate.

```bash
# Get top matching job roles for Candidate 1 (Sherlock H.)
curl -s "http://localhost:8000/candidates/1/matches?limit=2" | python -m json.tool
```

---

### 3. List All Jobs & Candidates

```bash
# List all jobs
curl -s http://localhost:8000/jobs | python -m json.tool

# List all candidates
curl -s http://localhost:8000/candidates | python -m json.tool
```

---

### 4. Create New Candidate or Job

```bash
# Create a new candidate via raw SQL
curl -X POST http://localhost:8000/candidates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Bruce Wayne",
    "skills": ["detective", "martial-arts", "wealth"],
    "experience_years": 10,
    "availability": "Immediate",
    "traits": ["vigilant", "analytical"],
    "quirk": "Only attends standups after midnight."
  }'

# Create a new job opening via raw SQL
curl -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Security Lead",
    "min_experience_years": 5,
    "tagline": "Protect our infrastructure from rogue villains.",
    "required_skills": ["detective", "security"],
    "culture_keywords": ["vigilant"]
  }'
```

---

### 5. Reseed Database API

```bash
curl -X POST http://localhost:8000/api/seed
```

---

## The Matching Algorithm: Decisions & Trade-Offs

The matching algorithm is the core of Recruiter-Bot. In real-world recruiting, black-box scores fail because recruiters need to defend their shortlists to hiring managers. The scoring model was designed to be **transparent, deterministic, and explainable**.

### The 100-Point Scoring Model

| Dimension                        | Max Points | Weight | Rationale                                                                                                                  |
| -------------------------------- | :--------: | :----: | -------------------------------------------------------------------------------------------------------------------------- |
| **1. Skill Overlap**             |    50.0    |  50%   | Hard technical requirements are non-negotiable in engineering. A candidate missing all required skills should not advance. |
| **2. Experience Fit**            |    25.0    |  25%   | Balances baseline competence against minimum requirements while penalizing extreme deficits or severe overqualification.   |
| **3. Availability Fit**          |    15.0    |  15%   | Pipeline velocity matters. Active candidates convert rapidly; passive candidates require prolonged persuasion.             |
| **4. Culture & Trait Alignment** |    10.0    |  10%   | Soft-skills and team chemistry. Boosts candidates whose traits mirror the job's cultural keywords.                         |

#### 1. Skill Overlap Formulation (50 pts)

- Normalized string intersection: `matched = candidate_skills ∩ required_skills`.
- Coverage ratio: `len(matched) / len(required_skills) * 48.0`.
- **Breadth Bonus**: Candidates with complementary adjacent skills earn up to +2.0 bonus points (capped at 50.0). Candidates with 0 matched skills earn 0 pts.

#### 2. Experience Fit Formulation (25 pts)

- **Deficit Penalty (`exp < min_exp`)**: If a role requires 5 years and a candidate has 2, experience score scales down proportionally (`(exp / min_exp) * 14.0`), capping below 14 pts.
- **Sweet Spot (`min_exp <= exp <= min_exp + 6`)**: Meeting minimum experience awards a baseline of 20.0 pts, plus a seniority premium of +1.0 pt per year above minimum (up to 25.0 pts).
- **Overqualification Guard (`exp >= 15` and `exp >= min_exp + 10`)**: Extremely senior candidates (e.g., Rick Sanchez with 20 yrs for a 2-yr role) receive an adjusted 22.0 pts with an explanatory flag (`"watch for overqualification or role mismatch"`).

#### 3. Availability Velocity (15 pts)

- `"Immediate"`: **15.0 pts** (ready to interview and start immediately).
- `"2 weeks"`: **12.0 pts** (standard notice period; actionable pipeline).
- `"Not looking"`: **4.0 pts** (passive prospect; lower short-term hiring probability).

#### 4. Culture & Trait Fit (10 pts)

- Compares candidate `traits` with job `culture_keywords`.
- Exact matches (e.g. `analytical` for Sherlock on `analytical` Backend Detective role) award proportional points up to 10.0.

#### 5. Deterministic Tie-Breaking

Ties are resolved deterministically across 4 tiers:

1. `overall_score DESC`
2. `skill_score DESC`
3. `experience_score DESC`
4. Alphabetical candidate name / job title

#### 6. Explainable Rationale ("Short Reason")

Rather than returning an opaque numerical value, every match generates a synthesized summary covering:

- Exact skills matched and missing.
- Experience seniority vs requirement.
- Availability status.
- Culture keyword matches.
- Candidate personality quirks (e.g., _"Reads the entire documentation before writing a single line of code"_, or _"Ships an MVP overnight, refuses to write tests"_).

### Design Trade-Offs Considered

- **Rule-Based Scoring vs Vector Embeddings / LLM Scoring**:
  - _Trade-off_: Embeddings capture semantic synonyms (e.g., "detective" ≈ "investigator"), but they introduce non-determinism, latency, and "black-box" scoring that recruiters cannot debug or defend.
  - _Decision_: A rule-based scoring engine with normalized set operations and transparent point breakdowns gives predictable, instant, auditable results.
- **Dynamic vs Pre-computed Matches**:
  - _Trade-off_: Pre-computing all pairwise matches scales well for reads but becomes stale when candidates update profiles.
  - _Decision_: Matches are computed on-the-fly and atomically persisted to the `matches` table (`ON CONFLICT DO UPDATE`), providing immediate query responsiveness and audit history.

---

## Part 2: The SQL Detective Challenge

All SQL Detective Challenge answers are saved in `sql_detective.sql`

---

## Note on AI Tools Usage

In accordance with the assignment guidelines:

- **Scaffolding & Boilerplate**: AI assistance was utilized to parse the candidate and job seed tables from the assignment PDF into structured Python dictionaries and generate initial Pydantic models. Also a basic frontend dashboard scaffold was generated using AI to visualize matches in a user-friendly manner compared to raw JSON via commandline
- **Test Generation**: Automated test cases for the API routes and scoring edge cases were co-authored with AI to achieve rapid verification across positive, negative, and boundary scenarios.
