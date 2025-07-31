# PUBLIC_INTERFACE
"""
Pydantic schemas for request/response validation in the YouTube Course Notes API.
Defines data models for authentication, notes, and sharing operations.
"""

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re


# Authentication Schemas
class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8, description="User password (minimum 8 characters)")

    @validator('password')
    def validate_password(cls, v):
        if not re.search(r"[A-Za-z]", v):
            raise ValueError('Password must contain at least one letter')
        if not re.search(r"\d", v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class User(UserBase):
    """Schema for user response"""
    id: int = Field(..., description="User ID")
    is_active: bool = Field(..., description="Account active status")
    created_at: datetime = Field(..., description="Account creation timestamp")

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for authentication token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    user: User = Field(..., description="User information")


# YouTube Processing Schemas
class YouTubeURLValidation(BaseModel):
    """Schema for YouTube URL validation request"""
    url: str = Field(..., description="YouTube video URL")

    @validator('url')
    def validate_youtube_url(cls, v):
        youtube_regex = re.compile(
            r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
            r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
        )
        if not youtube_regex.match(v):
            raise ValueError('Invalid YouTube URL format')
        return v


class YouTubeVideoInfo(BaseModel):
    """Schema for YouTube video information response"""
    url: str = Field(..., description="YouTube video URL")
    video_id: str = Field(..., description="YouTube video ID")
    title: str = Field(..., description="Video title")
    duration: int = Field(..., description="Video duration in seconds")
    description: Optional[str] = Field(None, description="Video description")
    thumbnail_url: Optional[str] = Field(None, description="Video thumbnail URL")


# Note Schemas
class NoteBase(BaseModel):
    """Base note schema with common fields"""
    title: str = Field(..., min_length=1, max_length=200, description="Note title")
    youtube_url: str = Field(..., description="YouTube video URL")
    is_public: bool = Field(default=False, description="Public sharing status")


class NoteCreate(NoteBase):
    """Schema for note creation"""
    generate_ai_summary: bool = Field(default=True, description="Generate AI summary")


class NoteUpdate(BaseModel):
    """Schema for note updates"""
    title: Optional[str] = Field(None, min_length=1, max_length=200, description="Note title")
    content: Optional[Dict[str, Any]] = Field(None, description="Rich text content")
    is_public: Optional[bool] = Field(None, description="Public sharing status")


class TimestampedNote(BaseModel):
    """Schema for timestamped note entries"""
    timestamp: int = Field(..., description="Timestamp in seconds")
    text: str = Field(..., description="Note text")
    video_url_with_timestamp: str = Field(..., description="YouTube URL with timestamp")


class Note(NoteBase):
    """Schema for note response"""
    id: int = Field(..., description="Note ID")
    content: Optional[Dict[str, Any]] = Field(None, description="Rich text content")
    video_title: Optional[str] = Field(None, description="YouTube video title")
    video_duration: Optional[int] = Field(None, description="Video duration in seconds")
    transcript: Optional[str] = Field(None, description="Video transcript")
    summary: Optional[str] = Field(None, description="AI-generated summary")
    timestamps: Optional[List[TimestampedNote]] = Field(None, description="Timestamped notes")
    owner_id: int = Field(..., description="Note owner ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        from_attributes = True


class NotesList(BaseModel):
    """Schema for notes list response"""
    notes: List[Note] = Field(..., description="List of notes")
    total: int = Field(..., description="Total number of notes")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")


# Sharing Schemas
class ShareNoteRequest(BaseModel):
    """Schema for note sharing request"""
    user_email: EmailStr = Field(..., description="Email of user to share with")
    permission: str = Field(default="read", description="Permission level (read/write)")

    @validator('permission')
    def validate_permission(cls, v):
        if v not in ['read', 'write']:
            raise ValueError('Permission must be either "read" or "write"')
        return v


class SharedNote(BaseModel):
    """Schema for shared note response"""
    id: int = Field(..., description="Shared note ID")
    note_id: int = Field(..., description="Note ID")
    user_id: int = Field(..., description="User ID")
    permission: str = Field(..., description="Permission level")
    shared_at: datetime = Field(..., description="Sharing timestamp")
    note: Note = Field(..., description="Note details")

    class Config:
        from_attributes = True


# Export Schemas
class ExportRequest(BaseModel):
    """Schema for note export request"""
    format: str = Field(..., description="Export format (pdf/docx/txt)")
    include_timestamps: bool = Field(default=True, description="Include timestamped links")

    @validator('format')
    def validate_format(cls, v):
        if v not in ['pdf', 'docx', 'txt']:
            raise ValueError('Format must be pdf, docx, or txt')
        return v


# AI Processing Schemas
class AIProcessingStatus(BaseModel):
    """Schema for AI processing status"""
    status: str = Field(..., description="Processing status (pending/processing/completed/failed)")
    message: Optional[str] = Field(None, description="Status message")
    progress: Optional[int] = Field(None, description="Progress percentage")


class TranscriptionResult(BaseModel):
    """Schema for transcription results"""
    transcript: str = Field(..., description="Full video transcript")
    summary: str = Field(..., description="AI-generated summary")
    timestamps: List[TimestampedNote] = Field(..., description="Timestamped notes")
