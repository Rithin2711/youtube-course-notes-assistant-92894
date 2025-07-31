#!/usr/bin/env python3
"""
Setup script for initializing the YouTube Course Notes API with SQLite.
Creates database tables and performs initial setup.
"""

import os
import sys
import subprocess
from pathlib import Path

def create_database():
    """Create the SQLite database and run migrations."""
    print("🗄️  Setting up SQLite database...")
    
    try:
        # Import after ensuring we're in the right directory
        os.chdir(Path(__file__).parent)
        
        # Create database tables using Alembic
        print("🔄 Running database migrations...")
        result = subprocess.run(["alembic", "upgrade", "head"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database setup completed successfully!")
            print("📁 Database file: youtube_notes.db")
        else:
            print("❌ Migration failed:")
            print(result.stderr)
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please run: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False
    
    return True

def create_env_file():
    """Create .env file from template if it doesn't exist."""
    env_file = Path(".env")
    env_example = Path(".env.example")
    
    if not env_file.exists() and env_example.exists():
        print("📝 Creating .env file from template...")
        env_file.write_text(env_example.read_text())
        print("✅ .env file created. Please review and update as needed.")
    elif env_file.exists():
        print("✅ .env file already exists.")
    else:
        print("⚠️  No .env.example template found.")

def main():
    """Main setup function."""
    print("🚀 YouTube Course Notes API - SQLite Setup")
    print("=" * 50)
    
    # Create .env file
    create_env_file()
    
    # Create database
    if create_database():
        print("\n🎉 Setup completed successfully!")
        print("You can now run the API with: python start.py")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
