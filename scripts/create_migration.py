#!/usr/bin/env python3
"""
Script to create initial database migration for conversation history.
Run this script after setting up your PostgreSQL database.
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def main():
    """Create initial migration for conversation history."""
    print("🚀 Creating database migration for conversation history...")
    
    # Check if we're in the right directory
    if not os.path.exists("alembic.ini"):
        print("❌ alembic.ini not found. Please run this script from the project root directory.")
        sys.exit(1)
    
    # Generate initial migration
    success = run_command(
        "alembic revision --autogenerate -m 'Create conversation and message tables'",
        "Generating initial migration"
    )
    
    if success:
        print("\n🎉 Migration created successfully!")
        print("\nNext steps:")
        print("1. Make sure PostgreSQL is running (docker run --name postgres -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d postgres)")
        print("2. Create the database: createdb nexora_ai")
        print("3. Run the migration: alembic upgrade head")
        print("4. Start your FastAPI application")
    else:
        print("\n❌ Failed to create migration. Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 