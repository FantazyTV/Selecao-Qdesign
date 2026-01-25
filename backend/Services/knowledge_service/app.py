"""FastAPI application setup for knowledge service"""

import sys
from pathlib import Path
import os

# Load .env file for environment variables (including GEMINI_API_KEY)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / ".env")

# Add the Services directory to Python path FIRST (before any imports)
services_dir = Path(__file__).parent.parent
sys.path.insert(0, str(services_dir))

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from knowledge_service.api import router
from knowledge_service.models import Base



# Database setup
DATABASE_URL = "sqlite:///./knowledge_service.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """Dependency for getting DB session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Create FastAPI app
app = FastAPI(
    title="Knowledge Service API",
    description="Service for managing knowledge bases for protein engineering projects",
    version="1.0.0"
)

# Store get_db in app state so routes can access it
app.get_db = get_db

# Include router
app.include_router(router)


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8001, reload=False)
