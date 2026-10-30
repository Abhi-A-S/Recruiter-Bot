"""
Application Configuration.
"""
import os
from pathlib import Path

# Base directory of the repository
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Database configuration
DATABASE_PATH = Path(os.environ.get("RECRUITERBOT_DB_PATH", BASE_DIR / "recruiterbot.db"))
