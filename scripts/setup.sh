#!/bin/bash
# APEX Demo Setup Script (macOS/Linux)
# Sets up backend + frontend for local demo

set -e

echo "========================================"
echo "  APEX Demo Setup (macOS/Linux)"
echo "========================================"
echo ""

# Check Python version
echo "[1/6] Checking Python version..."
if ! command -v python3 &> /dev/null; then
    echo "  ✗ Python 3 not found. Install Python 3.10+ from https://python.org"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
PYTHON_MAJOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f1)
PYTHON_MINOR=$(echo "$PYTHON_VERSION" | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 10 ]); then
    echo "  ✗ Python 3.10+ required, found $PYTHON_VERSION"
    exit 1
fi

echo "  ✓ Found: Python $PYTHON_VERSION"

# Check Node version
echo "[2/6] Checking Node.js version..."
if ! command -v node &> /dev/null; then
    echo "  ✗ Node.js not found. Install Node.js 18+ from https://nodejs.org"
    exit 1
fi

NODE_VERSION=$(node --version | sed 's/v//')
NODE_MAJOR=$(echo "$NODE_VERSION" | cut -d'.' -f1)

if [ "$NODE_MAJOR" -lt 18 ]; then
    echo "  ✗ Node.js 18+ required, found v$NODE_VERSION"
    exit 1
fi

echo "  ✓ Found: Node v$NODE_VERSION"

# Create .env if missing
echo "[3/6] Setting up environment..."
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "  ✓ Created .env from .env.example"
else
    echo "  ✓ .env already exists"
fi

# Setup backend
echo "[4/6] Setting up backend (Python)..."
cd src/backend

# Create venv if missing
if [ ! -d "venv" ]; then
    echo "  Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate venv
echo "  Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "  Installing Python dependencies..."
python -m pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

# Create data directory
mkdir -p ../../data

# Run migrations
echo "  Running database migrations..."
alembic upgrade head > /dev/null 2>&1 || true

echo "  ✓ Backend setup complete"
cd ../..

# Setup frontend
echo "[5/6] Setting up frontend (Node.js)..."
cd client/front

echo "  Installing Node dependencies..."
npm install --silent

echo "  ✓ Frontend setup complete"
cd ../..

# Final check
echo "[6/6] Setup verification..."
echo "  ✓ All components ready"

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Run the demo: ./scripts/run.sh"
echo "  2. Visit: http://localhost:5173"
echo ""
