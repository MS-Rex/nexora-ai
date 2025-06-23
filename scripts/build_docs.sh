#!/bin/bash

# Nexora AI Documentation Build Script

echo "📚 Building Nexora AI Documentation..."

# Change to docs directory
cd "$(dirname "$0")/../docs" || exit 1

# Install dependencies if needed
echo "🔧 Installing dependencies..."
uv sync --quiet

# Clean previous build
echo "🧹 Cleaning previous build..."
make clean

# Build HTML documentation
echo "🔨 Building HTML documentation..."
make html

# Check if build was successful
if [ $? -eq 0 ]; then
    echo "✅ Documentation built successfully!"
    echo "📖 Open docs/_build/html/index.html in your browser to view the documentation."
    
    # Optionally open documentation in browser (macOS)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        read -p "Would you like to open the documentation in your browser? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            open _build/html/index.html
        fi
    fi
else
    echo "❌ Documentation build failed!"
    exit 1
fi 