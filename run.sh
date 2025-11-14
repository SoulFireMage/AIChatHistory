#!/bin/bash

# Conversation Vault - Run Script
# Convenience script to start the application

set -e

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found. Please run ./setup.sh first."
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found. Please run ./setup.sh first."
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Start the server
echo "Starting Conversation Vault on http://localhost:7025"
echo "Press Ctrl+C to stop the server"
echo ""

cd backend
python -m app.main
