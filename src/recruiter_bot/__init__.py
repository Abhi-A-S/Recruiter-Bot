"""
RecruiterFlow Recruiter-Bot Package.
"""
import uvicorn


def main() -> None:
    """CLI launcher for the FastAPI server."""
    uvicorn.run(
        "recruiter_bot.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


__all__ = ["main"]
