#!/usr/bin/env python3
"""
Development startup script for the YouTube Course Notes API.
Handles database initialization and starts the FastAPI server.
"""

import os
import sys
import subprocess
import uvicorn
from decouple import config

def check_database():
    """Check if database is accessible and run migrations if needed."""
    try:
        from app.database import engine
        from sqlalchemy import text
        
        # Test database connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection successful")
        
        # Run migrations
        print("🔄 Running database migrations...")
        result = subprocess.run(["alembic", "upgrade", "head"], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Database migrations completed")
        else:
            print(f"⚠️  Migration warning: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("Please ensure PostgreSQL is running and DATABASE_URL is correct")
        sys.exit(1)

def main():
    """Main startup function."""
    print("🚀 Starting YouTube Course Notes API...")
    
    # Check environment variables
    required_vars = ["DATABASE_URL", "SECRET_KEY"]
    missing_vars = [var for var in required_vars if not config(var, default="")]
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        print("Please copy .env.example to .env and configure the required variables")
        sys.exit(1)
    
    # Check database
    check_database()
    
    # Start server
    host = config("HOST", default="0.0.0.0")
    port = config("PORT", default=8000, cast=int)
    reload = config("RELOAD", default=True, cast=bool)
    
    print(f"🌐 Starting server at http://{host}:{port}")
    print("📚 API documentation available at /docs")
    print("🔧 OpenAPI spec available at /openapi.json")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
