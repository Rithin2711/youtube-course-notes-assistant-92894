# PUBLIC_INTERFACE
"""
Export router for generating PDF, DOCX, and text exports of notes.
Handles note export with various formatting options and timestamped links.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from docx import Document
import json

from app.database import get_db
from app.models import User, Note
from app.schemas import ExportRequest
from app.middleware.auth import get_current_user

router = APIRouter()


def generate_pdf_export(note: Note, include_timestamps: bool = True) -> BytesIO:
    """
    Generate PDF export of a note.
    
    Args:
        note: Note to export
        include_timestamps: Whether to include timestamped links
        
    Returns:
        BytesIO: PDF file content
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph(f"<b>{note.title}</b>", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 12))
    
    # Video info
    if note.video_title:
        video_info = Paragraph(f"<b>Video:</b> {note.video_title}", styles['Normal'])
        story.append(video_info)
    
    video_url = Paragraph(f"<b>URL:</b> {note.youtube_url}", styles['Normal'])
    story.append(video_url)
    story.append(Spacer(1, 12))
    
    # Summary
    if note.summary:
        summary_title = Paragraph("<b>Summary</b>", styles['Heading2'])
        story.append(summary_title)
        summary_content = Paragraph(note.summary, styles['Normal'])
        story.append(summary_content)
        story.append(Spacer(1, 12))
    
    # Timestamped notes
    if include_timestamps and note.timestamps:
        timestamps_title = Paragraph("<b>Timestamped Notes</b>", styles['Heading2'])
        story.append(timestamps_title)
        
        for ts in note.timestamps:
            timestamp_text = f"[{ts['timestamp']}s] {ts['text']}"
            timestamp_para = Paragraph(timestamp_text, styles['Normal'])
            story.append(timestamp_para)
            story.append(Spacer(1, 6))
    
    # Full transcript
    if note.transcript:
        transcript_title = Paragraph("<b>Full Transcript</b>", styles['Heading2'])
        story.append(transcript_title)
        transcript_content = Paragraph(note.transcript[:2000] + "..." if len(note.transcript) > 2000 else note.transcript, styles['Normal'])
        story.append(transcript_content)
    
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_docx_export(note: Note, include_timestamps: bool = True) -> BytesIO:
    """
    Generate DOCX export of a note.
    
    Args:
        note: Note to export
        include_timestamps: Whether to include timestamped links
        
    Returns:
        BytesIO: DOCX file content
    """
    doc = Document()
    
    # Title
    title = doc.add_heading(note.title, 0)
    
    # Video info
    if note.video_title:
        doc.add_paragraph(f"Video: {note.video_title}")
    doc.add_paragraph(f"URL: {note.youtube_url}")
    
    # Summary
    if note.summary:
        doc.add_heading("Summary", level=1)
        doc.add_paragraph(note.summary)
    
    # Timestamped notes
    if include_timestamps and note.timestamps:
        doc.add_heading("Timestamped Notes", level=1)
        for ts in note.timestamps:
            doc.add_paragraph(f"[{ts['timestamp']}s] {ts['text']}")
    
    # Full transcript
    if note.transcript:
        doc.add_heading("Full Transcript", level=1)
        doc.add_paragraph(note.transcript)
    
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer


def generate_text_export(note: Note, include_timestamps: bool = True) -> str:
    """
    Generate plain text export of a note.
    
    Args:
        note: Note to export
        include_timestamps: Whether to include timestamped links
        
    Returns:
        str: Plain text content
    """
    content = []
    
    # Title
    content.append(f"# {note.title}")
    content.append("")
    
    # Video info
    if note.video_title:
        content.append(f"Video: {note.video_title}")
    content.append(f"URL: {note.youtube_url}")
    content.append("")
    
    # Summary
    if note.summary:
        content.append("## Summary")
        content.append(note.summary)
        content.append("")
    
    # Timestamped notes
    if include_timestamps and note.timestamps:
        content.append("## Timestamped Notes")
        for ts in note.timestamps:
            content.append(f"[{ts['timestamp']}s] {ts['text']}")
            content.append(f"Link: {ts.get('video_url_with_timestamp', '')}")
        content.append("")
    
    # Full transcript
    if note.transcript:
        content.append("## Full Transcript")
        content.append(note.transcript)
    
    return "\n".join(content)


@router.post("/{note_id}", summary="Export Note")
async def export_note(
    note_id: int,
    export_request: ExportRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export a note in the specified format.
    
    Args:
        note_id: Note ID to export
        export_request: Export configuration
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        StreamingResponse: File download response
        
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
    
    # Check access (owner or public note)
    if note.owner_id != current_user.id and not note.is_public:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Generate export based on format
    filename = f"{note.title.replace(' ', '_')}"
    
    if export_request.format == "pdf":
        buffer = generate_pdf_export(note, export_request.include_timestamps)
        media_type = "application/pdf"
        filename += ".pdf"
        
        return StreamingResponse(
            BytesIO(buffer.read()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif export_request.format == "docx":
        buffer = generate_docx_export(note, export_request.include_timestamps)
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        filename += ".docx"
        
        return StreamingResponse(
            BytesIO(buffer.read()),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    elif export_request.format == "txt":
        content = generate_text_export(note, export_request.include_timestamps)
        media_type = "text/plain"
        filename += ".txt"
        
        return StreamingResponse(
            BytesIO(content.encode('utf-8')),
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported export format"
        )


@router.get("/formats", summary="Get Available Export Formats")
async def get_export_formats():
    """
    Get list of available export formats.
    
    Returns:
        dict: Available export formats and their descriptions
    """
    return {
        "formats": [
            {
                "format": "pdf",
                "name": "PDF",
                "description": "Portable Document Format with formatting"
            },
            {
                "format": "docx",
                "name": "Word Document",
                "description": "Microsoft Word document format"
            },
            {
                "format": "txt",
                "name": "Plain Text",
                "description": "Simple text format"
            }
        ]
    }
