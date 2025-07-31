# PUBLIC_INTERFACE
"""
YouTube processing router for URL validation, video information extraction,
and transcript retrieval functionality.
"""

from fastapi import APIRouter, HTTPException, status, Depends
from pytube import YouTube
from youtube_transcript_api import YouTubeTranscriptApi
import re
from typing import Optional

from app.schemas import YouTubeURLValidation, YouTubeVideoInfo, TranscriptionResult
from app.middleware.auth import get_current_user
from app.models import User
from app.services.ai_service import AIService

router = APIRouter()
ai_service = AIService()


def extract_video_id(url: str) -> str:
    """
    Extract YouTube video ID from URL.
    
    Args:
        url: YouTube video URL
        
    Returns:
        str: YouTube video ID
        
    Raises:
        ValueError: If URL format is invalid
    """
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    match = youtube_regex.match(url)
    if not match:
        raise ValueError("Invalid YouTube URL format")
    return match.group(6)


@router.post("/validate", response_model=YouTubeVideoInfo, summary="Validate YouTube URL")
async def validate_youtube_url(
    url_data: YouTubeURLValidation,
    current_user: User = Depends(get_current_user)
):
    """
    Validate YouTube URL and extract video information.
    
    Args:
        url_data: YouTube URL validation request
        current_user: Current authenticated user
        
    Returns:
        YouTubeVideoInfo: Video information including title, duration, etc.
        
    Raises:
        HTTPException: If URL is invalid or video cannot be accessed
    """
    try:
        video_id = extract_video_id(url_data.url)
        yt = YouTube(url_data.url)
        
        return YouTubeVideoInfo(
            url=url_data.url,
            video_id=video_id,
            title=yt.title,
            duration=yt.length,
            description=yt.description[:500] if yt.description else None,
            thumbnail_url=yt.thumbnail_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YouTube URL or video not accessible: {str(e)}"
        )


@router.post("/transcript/{video_id}", response_model=TranscriptionResult, summary="Get Video Transcript")
async def get_video_transcript(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get transcript for YouTube video and generate AI summary.
    
    Args:
        video_id: YouTube video ID
        current_user: Current authenticated user
        
    Returns:
        TranscriptionResult: Transcript, summary, and timestamped notes
        
    Raises:
        HTTPException: If transcript is not available or processing fails
    """
    try:
        # Get transcript from YouTube
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Combine transcript text
        full_transcript = " ".join([entry['text'] for entry in transcript_list])
        
        # Generate AI summary (stub implementation)
        summary = await ai_service.generate_summary(full_transcript)
        
        # Create timestamped notes
        timestamps = []
        for entry in transcript_list[:10]:  # Limit to first 10 entries for demo
            timestamp_url = f"https://youtube.com/watch?v={video_id}&t={int(entry['start'])}s"
            timestamps.append({
                "timestamp": int(entry['start']),
                "text": entry['text'][:100] + "..." if len(entry['text']) > 100 else entry['text'],
                "video_url_with_timestamp": timestamp_url
            })
        
        return TranscriptionResult(
            transcript=full_transcript,
            summary=summary,
            timestamps=timestamps
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not retrieve transcript: {str(e)}"
        )


@router.get("/info/{video_id}", response_model=YouTubeVideoInfo, summary="Get Video Info")
async def get_video_info(
    video_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get YouTube video information by video ID.
    
    Args:
        video_id: YouTube video ID
        current_user: Current authenticated user
        
    Returns:
        YouTubeVideoInfo: Video information
        
    Raises:
        HTTPException: If video cannot be accessed
    """
    try:
        url = f"https://youtube.com/watch?v={video_id}"
        yt = YouTube(url)
        
        return YouTubeVideoInfo(
            url=url,
            video_id=video_id,
            title=yt.title,
            duration=yt.length,
            description=yt.description[:500] if yt.description else None,
            thumbnail_url=yt.thumbnail_url
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Video not accessible: {str(e)}"
        )
