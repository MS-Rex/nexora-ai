#!/bin/bash

# Script to set up the nexora_ai database
# This script loads environment variables and runs the database setup

echo "🚀 Setting up nexora_ai database..."

# Check if .env file exists
if [ -f ".env" ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(cat .env | grep -v '#' | sed 's/\r$//' | xargs)
else
    echo "⚠️  No .env file found. Using default values or system environment variables."
fi

# Display the database configuration that will be used
echo ""
echo "📋 Database Configuration:"
echo "  Host: ${DB_HOST:-localhost}"
echo "  Port: ${DB_PORT:-5432}"
echo "  User: ${DB_USER:-postgres}"
echo "  Database: ${DB_NAME:-nexora_ai}"
echo ""

# Run the Python setup script
python3 scripts/setup_database.py 