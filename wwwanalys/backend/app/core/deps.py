"""Dependencies for FastAPI endpoints."""
from typing import Generator
from sqlalchemy.orm import Session
from fastapi import Depends
from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()