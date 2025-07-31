# PUBLIC_INTERFACE
"""
Sharing router for note collaboration and sharing functionality.
Handles sharing notes with other users and managing permissions.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import User, Note, SharedNote
from app.schemas import ShareNoteRequest, SharedNote as SharedNoteSchema, Note as NoteSchema
from app.middleware.auth import get_current_user

router = APIRouter()


@router.post("/{note_id}", response_model=SharedNoteSchema, summary="Share Note")
async def share_note(
    note_id: int,
    share_request: ShareNoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Share a note with another user.
    
    Args:
        note_id: Note ID to share
        share_request: Sharing configuration
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        SharedNoteSchema: Created sharing record
        
    Raises:
        HTTPException: If note not found, access denied, or user not found
    """
    # Get note
    note = db.query(Note).filter(Note.id == note_id).first()
    
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    if note.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only note owner can share notes"
        )
    
    # Find user to share with
    target_user = db.query(User).filter(User.email == share_request.user_email).first()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if target_user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share note with yourself"
        )
    
    # Check if already shared
    existing_share = db.query(SharedNote).filter(
        SharedNote.note_id == note_id,
        SharedNote.user_id == target_user.id
    ).first()
    
    if existing_share:
        # Update existing share
        existing_share.permission = share_request.permission
        db.commit()
        db.refresh(existing_share)
        return SharedNoteSchema.from_orm(existing_share)
    
    # Create new share
    shared_note = SharedNote(
        note_id=note_id,
        user_id=target_user.id,
        permission=share_request.permission
    )
    
    db.add(shared_note)
    db.commit()
    db.refresh(shared_note)
    
    return SharedNoteSchema.from_orm(shared_note)


@router.get("/received", response_model=List[SharedNoteSchema], summary="Get Shared Notes")
async def get_shared_notes(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get notes shared with the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[SharedNoteSchema]: List of notes shared with user
    """
    shared_notes = db.query(SharedNote).filter(
        SharedNote.user_id == current_user.id
    ).all()
    
    return [SharedNoteSchema.from_orm(share) for share in shared_notes]


@router.get("/{note_id}/shares", response_model=List[SharedNoteSchema], summary="Get Note Shares")
async def get_note_shares(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of users a note is shared with.
    
    Args:
        note_id: Note ID
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[SharedNoteSchema]: List of sharing records for the note
        
    Raises:
        HTTPException: If note not found or access denied
    """
    # Get note
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
    
    shares = db.query(SharedNote).filter(SharedNote.note_id == note_id).all()
    
    return [SharedNoteSchema.from_orm(share) for share in shares]


@router.delete("/{note_id}/shares/{user_id}", summary="Revoke Note Share")
async def revoke_note_share(
    note_id: int,
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke note sharing access from a user.
    
    Args:
        note_id: Note ID
        user_id: User ID to revoke access from
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Revocation confirmation
        
    Raises:
        HTTPException: If note not found, access denied, or share not found
    """
    # Get note
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
    
    # Find and delete share
    share = db.query(SharedNote).filter(
        SharedNote.note_id == note_id,
        SharedNote.user_id == user_id
    ).first()
    
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found"
        )
    
    db.delete(share)
    db.commit()
    
    return {"message": "Note share revoked successfully"}


@router.put("/{note_id}/public", response_model=NoteSchema, summary="Toggle Public Sharing")
async def toggle_public_sharing(
    note_id: int,
    make_public: bool,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Toggle public sharing status of a note.
    
    Args:
        note_id: Note ID
        make_public: Whether to make note public
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
    
    note.is_public = make_public
    db.commit()
    db.refresh(note)
    
    return NoteSchema.from_orm(note)
