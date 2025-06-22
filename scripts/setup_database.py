#!/usr/bin/env python3
"""
Script to set up the nexora_ai database on Amazon RDS PostgreSQL and run migrations.
This script will:
1. Create the database if it doesn't exist
2. Run alembic migrations to create tables
"""

import os
import sys
import subprocess
import asyncio
import asyncpg


def get_db_config():
    """Get database configuration from environment variables."""
    return {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': int(os.getenv('DB_PORT', '5432')),
        'user': os.getenv('DB_USER', 'postgres'),
        'password': os.getenv('DB_PASSWORD', 'postgres'),
        'database': os.getenv('DB_NAME', 'nexora_ai')
    }


async def create_database_if_not_exists():
    """Create the nexora_ai database if it doesn't exist."""
    config = get_db_config()
    
    print(f"🔗 Connecting to PostgreSQL at {config['host']}:{config['port']}")
    
    try:
        # Connect to PostgreSQL server (not to a specific database)
        conn = await asyncpg.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database='postgres'  # Connect to default postgres database
        )
        
        # Check if database exists
        result = await conn.fetchval(
            "SELECT 1 FROM pg_catalog.pg_database WHERE datname = $1",
            config['database']
        )
        
        if result:
            print(f"✅ Database '{config['database']}' already exists")
        else:
            # Create database
            print(f"📦 Creating database '{config['database']}'...")
            await conn.execute(f'CREATE DATABASE "{config["database"]}"')
            print(f"✅ Database '{config['database']}' created successfully")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error connecting to PostgreSQL: {e}")
        return False


def run_migrations():
    """Run Alembic migrations to create tables."""
    print("📦 Running database migrations...")
    
    try:
        # Check if we're in the right directory
        if not os.path.exists("alembic.ini"):
            print("❌ alembic.ini not found. Please run this script from the project root directory.")
            return False
        
        # Run migrations
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True
        )
        
        if result.stdout:
            print(result.stdout)
        
        print("✅ Database migrations completed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e.stderr}")
        return False


async def verify_database_setup():
    """Verify that the database and tables were created correctly."""
    config = get_db_config()
    
    try:
        conn = await asyncpg.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            database=config['database']
        )
        
        # Check if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_type = 'BASE TABLE'
        """)
        
        print("📋 Database tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        
        expected_tables = ['conversations', 'messages', 'alembic_version']
        existing_tables = [table['table_name'] for table in tables]
        
        if all(table in existing_tables for table in expected_tables):
            print("✅ All required tables are present")
            return True
        else:
            print("⚠️  Some required tables are missing")
            return False
            
    except Exception as e:
        print(f"❌ Error verifying database setup: {e}")
        return False


async def main():
    """Main function to set up the database."""
    print("🚀 Setting up nexora_ai database...")
    
    # Display current configuration
    config = get_db_config()
    print("\n📋 Database Configuration:")
    print(f"  Host: {config['host']}")
    print(f"  Port: {config['port']}")
    print(f"  User: {config['user']}")
    print(f"  Database: {config['database']}")
    print()
    
    # Step 1: Create database
    if not await create_database_if_not_exists():
        print("❌ Failed to create database. Exiting.")
        sys.exit(1)
    
    # Step 2: Run migrations
    if not run_migrations():
        print("❌ Failed to run migrations. Exiting.")
        sys.exit(1)
    
    # Step 3: Verify setup
    if await verify_database_setup():
        print("\n🎉 Database setup completed successfully!")
        print("\nYou can now start your FastAPI application.")
    else:
        print("\n⚠️  Database setup may have issues. Please check the logs above.")


if __name__ == "__main__":
    asyncio.run(main()) 