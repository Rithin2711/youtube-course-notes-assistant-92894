from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from passlib.context import CryptContext
from datetime import datetime

Base = declarative_base()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PUBLIC_INTERFACE
class User(Base):
    """User account (for authentication)"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(128), nullable=False)

    notes = relationship("Note", back_populates="owner")

    # PUBLIC_INTERFACE
    def set_password(self, password: str):
        self.hashed_password = pwd_context.hash(password)

    # PUBLIC_INTERFACE
    def verify_password(self, password: str) -> bool:
        return pwd_context.verify(password, self.hashed_password)

# PUBLIC_INTERFACE
class Note(Base):
    """A note generated from YouTube/AI + edited by user"""
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=True)  # Rich text
    youtube_url = Column(String(512), nullable=True)
    timestamps = Column(Text, nullable=True)  # JSON or stringified timestamps for per-note
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="notes")
