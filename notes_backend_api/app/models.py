# PUBLIC_INTERFACE
"""
SQLAlchemy database models for the YouTube Course Notes App.
Defines User, Note, and SharedNote tables with relationships.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """
    User model for authentication and note ownership.
    
    Attributes:
        id: Primary key
        email: User email address (unique)
        username: User display name (unique)
        hashed_password: Bcrypt hashed password
        is_active: Account status
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        notes: Relationship to user's notes
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    shared_notes = relationship("SharedNote", back_populates="user", cascade="all, delete-orphan")


class Note(Base):
    """
    Note model for storing course notes with rich content and metadata.
    
    Attributes:
        id: Primary key
        title: Note title
        content: Rich text content (JSON format)
        youtube_url: Original YouTube video URL
        video_title: YouTube video title
        video_duration: Video duration in seconds
        transcript: Full video transcript
        summary: AI-generated summary
        timestamps: Timestamped notes (JSON format)
        owner_id: Foreign key to user
        is_public: Public sharing status
        created_at: Creation timestamp
        updated_at: Last update timestamp
        owner: Relationship to user
        shared_instances: Relationship to sharing records
    """
    __tablename__ = "notes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    content = Column(JSON, nullable=True)  # Rich text editor content
    youtube_url = Column(String, nullable=False)
    video_title = Column(String, nullable=True)
    video_duration = Column(Integer, nullable=True)  # Duration in seconds
    transcript = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    timestamps = Column(JSON, nullable=True)  # Timestamped notes
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", back_populates="notes")
    shared_instances = relationship("SharedNote", back_populates="note", cascade="all, delete-orphan")


class SharedNote(Base):
    """
    SharedNote model for tracking note sharing permissions.
    
    Attributes:
        id: Primary key
        note_id: Foreign key to note
        user_id: Foreign key to user (recipient)
        permission: Permission level (read, write)
        shared_at: Sharing timestamp
        note: Relationship to note
        user: Relationship to user
    """
    __tablename__ = "shared_notes"

    id = Column(Integer, primary_key=True, index=True)
    note_id = Column(Integer, ForeignKey("notes.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission = Column(String, default="read")  # read, write
    shared_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    note = relationship("Note", back_populates="shared_instances")
    user = relationship("User", back_populates="shared_notes")
