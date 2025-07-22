#!/bin/bash

# Start script for Theo API
# This script sets up the virtual environment and starts the FastAPI server

set -e  # Exit on any error

echo "🚀 Starting Theo API server..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    echo "✅ Virtual environment created."
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
if [ ! -f "venv/pyvenv.cfg" ] || ! pip list | grep -q "fastapi"; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed."
fi

echo "🌐 Starting FastAPI server on http://localhost:8001"
echo "📚 API Documentation available at http://localhost:8001/docs"
echo "❤️  Health check available at http://localhost:8001/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Start the FastAPI server with Uvicorn
uvicorn main:app --host 0.0.0.0 --port 8001 --reload

echo ""
echo "👋 API server stopped."