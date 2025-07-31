import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base

DATABASE_URL = os.getenv("NOTES_DB_URL", "sqlite:///./notes.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))
Base = declarative_base()

# PUBLIC_INTERFACE
def get_db():
    """Dependency that provides a SQLAlchemy session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
