# PUBLIC_INTERFACE
"""
YouTube Course Notes App - FastAPI Backend
Main application entry point with all routes and middleware setup.
"""

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer
from contextlib import asynccontextmanager
import uvicorn
from decouple import config

from app.database import engine, Base
from app.routers import auth, notes, export, share, youtube
from app.middleware.auth import get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context manager"""
    # Create database tables on startup
    Base.metadata.create_all(bind=engine)
    yield
    # Cleanup on shutdown if needed


app = FastAPI(
    title="YouTube Course Notes API",
    description="API for generating, managing, and sharing notes from YouTube course videos",
    version="1.0.0",
    lifespan=lifespan,
    openapi_tags=[
        {
            "name": "authentication",
            "description": "User authentication and authorization operations"
        },
        {
            "name": "youtube",
            "description": "YouTube video processing and validation"
        },
        {
            "name": "notes", 
            "description": "Note creation, retrieval, and management"
        },
        {
            "name": "export",
            "description": "Note export functionality (PDF, text)"
        },
        {
            "name": "sharing",
            "description": "Note sharing and collaboration features"
        }
    ]
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config("ALLOWED_ORIGINS", default="*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["authentication"])
app.include_router(youtube.router, prefix="/api/youtube", tags=["youtube"])
app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
app.include_router(export.router, prefix="/api/export", tags=["export"])
app.include_router(share.router, prefix="/api/share", tags=["sharing"])


@app.get("/", summary="Health Check")
async def root():
    """
    Health check endpoint to verify API is running.
    
    Returns:
        dict: Status message confirming API is operational
    """
    return {"message": "YouTube Course Notes API is running"}


@app.get("/health", summary="Detailed Health Check")
async def health_check():
    """
    Detailed health check with system status.
    
    Returns:
        dict: Detailed system health information
    """
    return {
        "status": "healthy",
        "service": "YouTube Course Notes API",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=config("HOST", default="0.0.0.0"),
        port=config("PORT", default=8000, cast=int),
        reload=config("RELOAD", default=True, cast=bool)
    )
