# YouTube Course Notes Assistant

A full-stack application that generates AI-powered notes from YouTube course videos using transcription and summarization technology.

## Features

- **YouTube Integration**: Input any YouTube course video URL
- **AI-Powered Notes**: Automatic transcription and summarization
- **Rich Text Editor**: Edit and enhance generated notes
- **Timestamped Links**: Jump to specific video moments
- **Export Options**: PDF, DOCX, and text formats
- **Note Sharing**: Public/private sharing with permission control
- **User Authentication**: Secure user accounts and note ownership

## Backend API (notes_backend_api)

### Quick Start with SQLite

The backend now uses SQLite for out-of-the-box functionality - no external database required!

```bash
cd notes_backend_api

# Install dependencies
pip install -r requirements.txt

# Setup environment (optional - defaults provided)
cp .env.example .env

# Initialize database and start server
python setup.py
python start.py
```

The API will be available at: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- OpenAPI Spec: http://localhost:8000/openapi.json

### Database Migration from PostgreSQL

The backend has been converted from PostgreSQL to SQLite for easier setup:

**Key Changes:**
- ✅ Removed PostgreSQL dependency (psycopg2-binary)
- ✅ Updated SQLAlchemy configuration for SQLite
- ✅ Modified Alembic migrations for SQLite compatibility
- ✅ JSON fields now use TEXT with automatic serialization
- ✅ Removed timezone-aware datetime (SQLite limitation)
- ✅ Updated Docker configuration

### Environment Variables

Create a `.env` file (or use defaults):

```bash
# Database (SQLite default)
DATABASE_URL=sqlite:///./youtube_notes.db

# Security
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=True

# CORS
ALLOWED_ORIGINS=http://localhost:3000

# AI Configuration (Optional)
OPENAI_API_KEY=your-openai-key
USE_MOCK_AI=True
```

### Docker Support

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build Docker image directly
docker build -t youtube-notes-api .
docker run -p 8000:8000 youtube-notes-api
```

### Development

```bash
# Run tests
pytest

# Code formatting
black .

# Linting
flake8

# Generate OpenAPI spec
python generate_openapi.py
```

### API Endpoints

- **Authentication**: `/api/auth/` - User registration, login, profile
- **YouTube Processing**: `/api/youtube/` - URL validation, video info, transcripts
- **Notes Management**: `/api/notes/` - CRUD operations for notes
- **Export**: `/api/export/` - PDF, DOCX, text export
- **Sharing**: `/api/share/` - Note sharing and collaboration

### Database Schema

**Users Table:**
- User authentication and profile information
- Email/username based authentication

**Notes Table:**
- YouTube video metadata and generated content
- Rich text content stored as JSON
- Timestamped notes with video links
- Public/private sharing settings

**Shared Notes Table:**
- Note sharing permissions and access control
- Read/write permission levels

## Architecture

- **Framework**: FastAPI with SQLAlchemy ORM
- **Database**: SQLite (file-based, no server required)
- **Authentication**: JWT tokens with bcrypt password hashing
- **AI Integration**: OpenAI API with mock fallback
- **Export**: ReportLab (PDF), python-docx (Word)
- **YouTube**: pytube and youtube-transcript-api

## Migration Notes

If upgrading from PostgreSQL version:

1. **Backup Data**: Export existing PostgreSQL data if needed
2. **Update Dependencies**: Remove PostgreSQL packages
3. **Run Migration**: The new setup automatically creates SQLite tables
4. **Data Import**: Manual data migration required if preserving data

The SQLite version provides the same functionality with easier deployment and development setup.