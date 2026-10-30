"""
Recruiter-Bot: FastAPI Backend Application.
"""
from contextlib import asynccontextmanager
from pathlib import Path
import sqlite3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from recruiter_bot.config import DATABASE_PATH
from recruiter_bot.db import init_db, get_db_connection
from recruiter_bot.seed_data import seed_database
from recruiter_bot.repository import get_stats
from recruiter_bot.routes.jobs import router as jobs_router
from recruiter_bot.routes.candidates import router as candidates_router
from recruiter_bot.routes.ingestion import router as ingestion_router

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup & shutdown lifecycle handler.
    Initializes database schema and auto-seeds if database is empty.
    """
    init_db()
    conn = get_db_connection()
    try:
        stats = get_stats(conn)
        if stats["candidate_count"] == 0 or stats["job_count"] == 0:
            seed_database(reset=False)
    finally:
        conn.close()
    yield


app = FastAPI(
    title="Recruiter-Bot API",
    description="Intelligent Candidate & Job Matching Engine with Multi-Factor Scoring, Explainable Rationale, and Hand-Written Raw SQL.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(ingestion_router)


# Mount static directory if it exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
async def serve_index():
    """Serves the interactive Recruiter-Bot visual explorer."""
    index_file = STATIC_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "Welcome to Recruiter-Bot API. Visit /docs for Swagger documentation."}


@app.get("/health", tags=["Health"])
def health_check():
    """Health check endpoint verifying application and database connectivity."""
    conn = get_db_connection()
    try:
        stats = get_stats(conn)
        return {
            "status": "healthy",
            "service": "recruiter-bot",
            "database": "sqlite",
            "stats": stats,
        }
    finally:
        conn.close()
