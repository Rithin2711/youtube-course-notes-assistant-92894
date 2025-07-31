import os
import re
from typing import Tuple, List, Optional
from fpdf import FPDF

# --- YOUTUBE UTILITIES ---

def is_valid_youtube_url(url: str) -> bool:
    """
    Checks if url matches a YouTube video link.
    """
    # Basic check (not exhaustive)
    pattern = r"(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/)[\w\-]+"
    return bool(re.match(pattern, url or ""))

def extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extracts YouTube video ID from URL.
    """
    regex = (
        r"youtu(?:\.be/|be\.com/watch\?(?:.*&)?v=)([a-zA-Z0-9_-]{11})"
    )
    match = re.search(regex, url)
    return match.group(1) if match else None

# --- OPENAI/A.I. UTILITIES (stub for now, replace as needed) ---

def openai_transcribe_and_summarize(youtube_url: str) -> Tuple[str, str, str]:
    """
    Calls OpenAI API (or other AI service) to transcribe and summarize the YouTube video.
    Returns: (full transcript, summary/outline, timestamps)
    """
    # [Production: replace with actual youtube transcript download and OpenAI calls]
    api_key = os.getenv("OPENAI_API_KEY", None)
    if not api_key:
        raise RuntimeError("OpenAI API key not configured in environment")
    # This function should:
    # - Download the transcript
    # - Use OpenAI to summarize
    # - Parse timestamps for outline
    transcript = f"Transcript for: {youtube_url} (this would come from YouTube+ASR)."
    outline = f"Summary/notes for {youtube_url}.\n- Point 1\n- Point 2\n- ..."
    # Produces a simple list of 'timestamp links' for this mock.
    timestamps = "00:01:02 Topic 1\n00:05:20 Topic 2 (links would be generated in frontend using these markers)"
    return transcript, outline, timestamps

# --- EXPORT UTILITIES ---

def generate_pdf_from_note(note, output_path: str) -> str:
    """
    Exports note content in PDF format.
    """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "", 16)
    pdf.cell(0, 10, note.title, ln=1, align="C")
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, note.content or "")
    pdf.set_font("Arial", "I", 9)
    if note.youtube_url:
        pdf.cell(0, 10, f"YouTube: {note.youtube_url}", ln=1)
    if note.timestamps:
        pdf.multi_cell(0, 8, f"Timestamps:\n{note.timestamps}")
    pdf.output(output_path)
    return output_path

def generate_txt_from_note(note, output_path: str) -> str:
    """
    Exports note as raw plaintext.
    """
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"Title: {note.title}\n")
        f.write(f"Content:\n{note.content or ''}\n")
        if note.youtube_url:
            f.write(f"YouTube URL: {note.youtube_url}\n")
        if note.timestamps:
            f.write(f"Timestamps:\n{note.timestamps}\n")
    return output_path
