"""
Database connection management and hand-written DDL execution.
Strictly raw SQL - no ORM or query builder.
"""
import sqlite3
from pathlib import Path
from typing import Optional
from recruiter_bot.config import DATABASE_PATH

SCHEMA_PATH = Path(__file__).resolve().parent / "schema.sql"


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """
    Returns a configured SQLite connection with foreign keys enabled
    and row factory configured for dictionary-like column access.
    """
    path = db_path or DATABASE_PATH
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """
    Initializes the database schema using hand-written DDL from schema.sql.
    """
    conn = get_db_connection(db_path)
    try:
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(ddl)
        conn.commit()
    finally:
        conn.close()


def reset_db(db_path: Optional[Path] = None) -> None:
    """
    Resets the database by dropping existing tables and recreating schema.
    """
    conn = get_db_connection(db_path)
    try:
        drop_script = """
        PRAGMA foreign_keys = OFF;
        DROP TABLE IF EXISTS matches;
        DROP TABLE IF EXISTS job_culture_keywords;
        DROP TABLE IF EXISTS job_required_skills;
        DROP TABLE IF EXISTS jobs;
        DROP TABLE IF EXISTS candidate_traits;
        DROP TABLE IF EXISTS candidate_skills;
        DROP TABLE IF EXISTS candidates;
        PRAGMA foreign_keys = ON;
        """
        conn.executescript(drop_script)
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        conn.executescript(ddl)
        conn.commit()
    finally:
        conn.close()
