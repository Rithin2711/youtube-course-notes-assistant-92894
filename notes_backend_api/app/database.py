# PUBLIC_INTERFACE
"""
Database configuration and session management for the YouTube Course Notes App.
Uses SQLAlchemy with SQLite for out-of-the-box functionality.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from decouple import config

# Database configuration - SQLite with environment override
DATABASE_URL = config(
    "DATABASE_URL",
    default="sqlite:///./youtube_notes.db"
)

# SQLite-specific engine configuration
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite specific
        echo=config("DB_ECHO", default=False, cast=bool)
    )
else:
    # Fallback for other databases
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
        pool_recycle=300,
        echo=config("DB_ECHO", default=False, cast=bool)
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()


def get_db():
    """
    Database dependency that provides a database session.
    
    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
