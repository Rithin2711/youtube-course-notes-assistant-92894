import os
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from typing import List, Optional, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import uvicorn

from db import Base, engine, get_db
from models import User, Note
from schemas import (UserCreate, UserLogin, UserOut, Token, NoteCreate, NoteEdit, NoteOut,
                     NoteExportFormat, NoteShareMode)
from auth import authenticate_user, create_access_token, get_current_user
from utils import (
    is_valid_youtube_url, 
    extract_youtube_video_id, 
    openai_transcribe_and_summarize,
    generate_pdf_from_note, 
    generate_txt_from_note
)

# --- FastAPI App configuration ---
app = FastAPI(
    title="NoteGPT: YouTube Course Notes Generator API",
    description="RESTful API for YouTube Course Notes App (AI notes from YouTube, editing, export, sharing, auth)",
    version="1.0.0",
    openapi_tags=[
        {"name": "auth", "description": "User authentication and login"},
        {"name": "notes", "description": "Note creation, editing, listing, deletion"},
        {"name": "youtube", "description": "AI-powered YouTube link processing, transcription, summarization"},
        {"name": "export", "description": "Note exporting to PDF or text"},
        {"name": "share", "description": "Note sharing and public/private mode"}
    ]
)

origins = ["*"]  # In production, be restrictive!

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# --- DB creation ---
Base.metadata.create_all(bind=engine)

# --- AUTH endpoints ---

# PUBLIC_INTERFACE
@app.post("/api/auth/register", response_model=UserOut, tags=["auth"], summary="Register a new user")
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """
    Registers a new user with email & password.
    """
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    db_user = User(email=user.email)
    db_user.set_password(user.password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# PUBLIC_INTERFACE
@app.post("/api/auth/login", response_model=Token, tags=["auth"], summary="User login - returns JWT token")
async def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login with email (username) and password. Returns JWT access token.
    """
    user = authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="Incorrect credentials")
    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

# --- NOTE endpoints ---

# PUBLIC_INTERFACE
@app.post("/api/notes", response_model=NoteOut, tags=["notes"], summary="Create new note")
async def create_note(
    note_in: NoteCreate, 
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Creates a new note for the authenticated user. 
    Optionally kicks off YouTube AI transcript/summarization in background if youtube_url is provided.
    """
    if note_in.youtube_url and not is_valid_youtube_url(note_in.youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    note = Note(
        owner_id=user.id,
        title=note_in.title,
        content=note_in.content,
        youtube_url=note_in.youtube_url,
        is_public=note_in.is_public
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

# PUBLIC_INTERFACE
@app.get("/api/notes", response_model=List[NoteOut], tags=["notes"], summary="List all user notes")
async def list_notes(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Fetch all notes belonging to the authenticated user.
    """
    return db.query(Note).filter(Note.owner_id == user.id).all()

# PUBLIC_INTERFACE
@app.get("/api/notes/{note_id}", response_model=NoteOut, tags=["notes"], summary="Get note by ID")
async def get_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Get a specific note by its ID. Returns only if owned by user or is public.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if note is None or (not note.is_public and note.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Note not found or access denied")
    return note

# PUBLIC_INTERFACE
@app.patch("/api/notes/{note_id}", response_model=NoteOut, tags=["notes"], summary="Edit a note")
async def edit_note(note_id: int, note_edit: NoteEdit, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Edit an existing note belonging to the user.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    # Update fields if provided
    if note_edit.title is not None:
        note.title = note_edit.title
    if note_edit.content is not None:
        note.content = note_edit.content
    if note_edit.is_public is not None:
        note.is_public = note_edit.is_public
    db.commit()
    db.refresh(note)
    return note

# PUBLIC_INTERFACE
@app.delete("/api/notes/{note_id}", response_model=dict, tags=["notes"], summary="Delete a note")
async def delete_note(note_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    """
    Delete a note owned by the user.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()
    return {"detail": "Note deleted"}

# --- YouTube AI-powered endpoints ---

# PUBLIC_INTERFACE
@app.post("/api/youtube/ingest", response_model=NoteOut, tags=["youtube"], summary="AI YouTube: transcribe & summarize, create note")
async def ingest_youtube(
    youtube_url: str = Query(..., description="YouTube video URL"),
    title: str = Query(..., description="Title for the generated note"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    background_tasks: BackgroundTasks = None
):
    """
    Takes a YouTube link, validates it, uses AI (OpenAI) to fetch transcript and summary, creates a new note with result.
    This may take up to several minutes.
    """
    if not is_valid_youtube_url(youtube_url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    try:
        transcript, outline, timestamps = openai_transcribe_and_summarize(youtube_url)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI processor failed: {e}")
    note = Note(
        owner_id=user.id,
        title=title,
        content=outline,
        youtube_url=youtube_url,
        timestamps=timestamps
    )
    db.add(note)
    db.commit()
    db.refresh(note)
    return note

# --- Export endpoints ---

# PUBLIC_INTERFACE
@app.get("/api/notes/{note_id}/export", response_model=None, summary="Export note as PDF/txt", tags=["export"])
async def export_note(
    note_id: int,
    format: NoteExportFormat = Query(..., description="Export format: pdf or txt"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Exports a note as PDF or plain text for download.
    """
    note = db.query(Note).filter(Note.id == note_id).first()
    if not note or (not note.is_public and note.owner_id != user.id):
        raise HTTPException(status_code=404, detail="Note not found or access denied")

    fname = f"note_{note.id}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.{format}"
    if format == NoteExportFormat.pdf:
        fpath = generate_pdf_from_note(note, output_path=f"/tmp/{fname}")
        return FileResponse(
            fpath, filename=fname, media_type="application/pdf"
        )
    elif format == NoteExportFormat.txt:
        fpath = generate_txt_from_note(note, output_path=f"/tmp/{fname}")
        return FileResponse(
            fpath, filename=fname, media_type="text/plain"
        )
    else:
        raise HTTPException(status_code=400, detail="Invalid export format")

# --- Share endpoints (public/private toggle) ---

# PUBLIC_INTERFACE
@app.post("/api/notes/{note_id}/share", tags=["share"], summary="Set note sharing mode (public/private)")
async def share_note(
    note_id: int,
    share_mode: NoteShareMode,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Set whether note is shared public or private.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.owner_id == user.id).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    note.is_public = (share_mode.mode == "public")
    db.commit()
    db.refresh(note)
    return {"note_id": note_id, "public": note.is_public}

# --- Public note reading endpoint (no auth required) ---

# PUBLIC_INTERFACE
@app.get("/api/public/notes/{note_id}", response_model=NoteOut, tags=["share"], summary="Read public note by ID")
async def get_public_note(note_id: int, db: Session = Depends(get_db)):
    """
    View a note if it has been marked public.
    """
    note = db.query(Note).filter(Note.id == note_id, Note.is_public == True).first()
    if not note:
        raise HTTPException(status_code=404, detail="Public note not found")
    return note

# --- Swagger customization: add project-level WebSocket/AI note doc ---
@app.get("/docs", include_in_schema=False)
async def swagger_docs():
    # Only add extra usage notes if required (here just vanilla)
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " - API Docs")

# --- Root ---
@app.get("/", summary="API root", tags=["auth"])
def root():
    return {"message": "NoteGPT: AI-powered YouTube Course Notes API Server"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
