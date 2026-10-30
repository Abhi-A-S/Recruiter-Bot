-- ============================================================================
-- RecruiterFlow Engineering - Part 1: Hand-Written Database Schema (DDL)
-- Raw SQL only - No ORM or query builder abstractions.
-- ============================================================================

CREATE TABLE IF NOT EXISTS candidates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    experience_years INTEGER NOT NULL,
    availability TEXT NOT NULL,
    quirk TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS candidate_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE (candidate_id, skill)
);

CREATE TABLE IF NOT EXISTS candidate_traits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id INTEGER NOT NULL,
    trait TEXT NOT NULL,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE (candidate_id, trait)
);

CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    min_experience_years INTEGER NOT NULL,
    tagline TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS job_required_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    skill TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE (job_id, skill)
);

CREATE TABLE IF NOT EXISTS job_culture_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    UNIQUE (job_id, keyword)
);

CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id INTEGER NOT NULL,
    candidate_id INTEGER NOT NULL,
    overall_score REAL NOT NULL,
    skill_score REAL NOT NULL,
    experience_score REAL NOT NULL,
    availability_score REAL NOT NULL,
    culture_score REAL NOT NULL,
    reason TEXT NOT NULL,
    matched_skills TEXT NOT NULL,
    missing_skills TEXT NOT NULL,
    matched_culture TEXT NOT NULL,
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
    FOREIGN KEY (candidate_id) REFERENCES candidates(id) ON DELETE CASCADE,
    UNIQUE (job_id, candidate_id)
);

CREATE INDEX IF NOT EXISTS idx_candidate_skills_cid ON candidate_skills(candidate_id);
CREATE INDEX IF NOT EXISTS idx_candidate_traits_cid ON candidate_traits(candidate_id);
CREATE INDEX IF NOT EXISTS idx_job_skills_jid ON job_required_skills(job_id);
CREATE INDEX IF NOT EXISTS idx_job_culture_jid ON job_culture_keywords(job_id);
CREATE INDEX IF NOT EXISTS idx_matches_job_score ON matches(job_id, overall_score DESC);
CREATE INDEX IF NOT EXISTS idx_matches_candidate_score ON matches(candidate_id, overall_score DESC);
