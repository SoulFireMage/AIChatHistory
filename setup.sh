#!/bin/bash

# Conversation Vault - Setup Script
# This script helps you set up the application for first-time use

set -e

echo "=========================================="
echo "  Conversation Vault - Setup"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check Python version
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check PostgreSQL
echo "Checking PostgreSQL..."
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}Warning: psql command not found. Make sure PostgreSQL is installed.${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL found${NC}"
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists${NC}"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf venv
        python3 -m venv venv
        echo -e "${GREEN}✓ Virtual environment recreated${NC}"
    fi
else
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup .env file
echo ""
if [ -f ".env" ]; then
    echo -e "${YELLOW}.env file already exists${NC}"
    read -p "Do you want to reconfigure it? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        SKIP_ENV=true
    fi
fi

if [ -z "$SKIP_ENV" ]; then
    echo "Setting up environment configuration..."
    echo ""

    # Database configuration
    read -p "PostgreSQL host [localhost]: " DB_HOST
    DB_HOST=${DB_HOST:-localhost}

    read -p "PostgreSQL port [5432]: " DB_PORT
    DB_PORT=${DB_PORT:-5432}

    read -p "PostgreSQL database name [conversation_vault]: " DB_NAME
    DB_NAME=${DB_NAME:-conversation_vault}

    read -p "PostgreSQL username: " DB_USER
    read -sp "PostgreSQL password: " DB_PASSWORD
    echo ""

    # Generate encryption key
    echo "Generating encryption key..."
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

    # Generate secret key
    SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")

    # Create .env file
    cat > .env << EOF
# Database Configuration
DATABASE_URL=postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DB_NAME}

# Server Configuration
HOST=127.0.0.1
PORT=7025

# Security
SECRET_KEY=${SECRET_KEY}
ENCRYPTION_KEY=${ENCRYPTION_KEY}

# Environment
ENV=development
EOF

    echo -e "${GREEN}✓ .env file created${NC}"
fi

# Create database if it doesn't exist
echo ""
echo "Setting up database..."
if command -v psql &> /dev/null; then
    # Load .env to get database name
    source .env

    # Extract database name from DATABASE_URL
    DB_NAME_FROM_URL=$(echo $DATABASE_URL | sed 's/.*\/\([^?]*\).*/\1/')

    echo "Checking if database '$DB_NAME_FROM_URL' exists..."

    # Try to create database (will fail if already exists, which is fine)
    createdb -h ${DB_HOST:-localhost} -p ${DB_PORT:-5432} -U ${DB_USER} $DB_NAME_FROM_URL 2>/dev/null && \
        echo -e "${GREEN}✓ Database created${NC}" || \
        echo -e "${YELLOW}Database already exists or could not be created. Continuing...${NC}"
else
    echo -e "${YELLOW}Skipping database creation. Please create the database manually.${NC}"
fi

# Run migrations
echo ""
echo "Running database migrations..."
cd backend
alembic upgrade head
cd ..
echo -e "${GREEN}✓ Database migrations completed${NC}"

# Create artifacts directory
echo ""
echo "Creating artifacts directory..."
mkdir -p artifacts
echo -e "${GREEN}✓ Artifacts directory created${NC}"

# Success message
echo ""
echo "=========================================="
echo -e "${GREEN}Setup completed successfully!${NC}"
echo "=========================================="
echo ""
echo "To start the server:"
echo "  1. Activate the virtual environment: source venv/bin/activate"
echo "  2. Run the server: python backend/app/main.py"
echo "  3. Open your browser to: http://localhost:7025"
echo ""
echo "Or use the convenience script:"
echo "  ./run.sh"
echo ""
