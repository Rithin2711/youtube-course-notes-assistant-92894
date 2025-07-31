# PUBLIC_INTERFACE
"""
Notes router for CRUD operations on course notes.
Handles note creation, retrieval, updating, and deletion with AI integration.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.models import User, Note
from app.schemas import NoteCreate, NoteUpdate, Note as NoteSchema, NotesList
from app.middleware.auth import get_current_user
from app.services.ai_service import AIService
from app.routers.youtube import get_video_transcript, extract_video_id

router = APIRouter()
ai_service = AIService()


@router.post("/", response_model=NoteSchema, summary="Create New Note")
async def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new note from YouTube video.
    
    Processes YouTube URL, extracts transcript, and generates AI summary if requested.
    
    Args:
        note_data: Note creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteSchema: Created note with AI-generated content
        
    Raises:
        HTTPException: If YouTube URL is invalid or processing fails
    """
    try:
        # Extract video ID and get transcript
        video_id = extract_video_id(note_data.youtube_url)
        
        # Create initial note
        db_note = Note(
            title=note_data.title,
            youtube_url=note_data.youtube_url,
            owner_id=current_user.id,
            is_public=note_data.is_public
        )
        
        db.add(db_note)
        db.commit()
        db.refresh(db_note)
        
        # Generate AI content if requested
        if note_data.generate_ai_summary:
            try:
                transcript_result = await get_video_transcript(video_id, current_user)
                
                # Update note with AI-generated content
                db_note.transcript = transcript_result.transcript
                db_note.summary = transcript_result.summary
                db_note.timestamps = [ts.dict() for ts in transcript_result.timestamps]
                
                # Get video info
                from pytube import YouTube
                yt = YouTube(note_data.youtube_url)
                db_note.video_title = yt.title
                db_note.video_duration = yt.length
                
                db.commit()
                db.refresh(db_note)
                
            except Exception as e:
                # Note created but AI processing failed
                print(f"AI processing failed: {e}")
        
        return NoteSchema.from_orm(db_note)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get("/", response_model=NotesList, summary="Get User Notes")
async def get_user_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in title and content")
):
    """
    Get paginated list of user's notes.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        page: Page number for pagination
        size: Number of notes per page
        search: Optional search term
        
    Returns:
        NotesList: Paginated list of notes
    """
    query = db.query(Note).filter(Note.owner_id == current_user.id)
    
    # Apply search filter if provided
    if search:
        query = query.filter(
            Note.title.ilike(f"%{search}%") |
            Note.summary.ilike(f"%{search}%")
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    notes = query.offset((page - 1) * size).limit(size).all()
    
    return NotesList(
        notes=[NoteSchema.from_orm(note) for note in notes],
        total=total,
        page=page,
        size=size
    )


@router.get("/{note_id}", response_model=NoteSchema, summary="Get Note by ID")
async def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific note by ID.
    
    Args:
        note_id: Note ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteSchema: Note details
        
    Raises:
        HTTPException: If note not found or access denied
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Check if user has access (owner or note is public)
    if note.owner_id != current_user.id and not note.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return NoteSchema.from_orm(note)


@router.put("/{note_id}", response_model=NoteSchema, summary="Update Note")
async def update_note(
    note_id: int,
    note_update: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing note.
    
    Args:
        note_id: Note ID
        note_update: Note update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        NoteSchema: Updated note
        
    Raises:
        HTTPException: If note not found or access denied
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Update note fields
    update_data = note_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(note, field, value)
    
    db.commit()
    db.refresh(note)
    
    return NoteSchema.from_orm(note)


@router.delete("/{note_id}", summary="Delete Note")
async def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a note.
    
    Args:
        note_id: Note ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Deletion confirmation
        
    Raises:
        HTTPException: If note not found or access denied
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    db.delete(note)
    db.commit()
    
    return {"message": "Note deleted successfully"}


@router.get("/public/list", response_model=NotesList, summary="Get Public Notes")
async def get_public_notes(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size")
):
    """
    Get paginated list of public notes.
    
    Args:
        db: Database session
        page: Page number for pagination
        size: Number of notes per page
        
    Returns:
        NotesList: Paginated list of public notes
    """
    query = db.query(Note).filter(Note.is_public == True)
    total = query.count()
    notes = query.offset((page - 1) * size).limit(size).all()
    
    return NotesList(
        notes=[NoteSchema.from_orm(note) for note in notes],
        total=total,
        page=page,
        size=size
    )
