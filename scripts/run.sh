#!/bin/bash
# APEX Demo Run Script (macOS/Linux)
# Starts backend + frontend for local demo

set -e

echo "========================================"
echo "  APEX Demo - Starting Services"
echo "========================================"
echo ""

# Check if setup was run
if [ ! -d "src/backend/venv" ]; then
    echo "✗ Backend not set up. Run: ./scripts/setup.sh"
    exit 1
fi

if [ ! -d "client/front/node_modules" ]; then
    echo "✗ Frontend not set up. Run: ./scripts/setup.sh"
    exit 1
fi

echo "Starting backend on http://localhost:8000 ..."
echo "Starting frontend on http://localhost:5173 ..."
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Trap Ctrl+C to clean up
cleanup() {
    echo ""
    echo "Stopping services..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "✓ Services stopped"
    exit 0
}
trap cleanup INT TERM

# Start backend
cd src/backend
source venv/bin/activate
export PYTHONUNBUFFERED=1
uvicorn server:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ../..

# Wait for backend to start
sleep 3

# Start frontend
cd client/front
npm run dev &
FRONTEND_PID=$!
cd ../..

# Wait a bit for frontend to start
sleep 2

echo "========================================"
echo "  Services Running!"
echo "========================================"
echo ""
echo "  Backend:  http://localhost:8000"
echo "  API Docs: http://localhost:8000/docs"
echo "  Frontend: http://localhost:5173"
echo "  Demo:     http://localhost:5173/demo"
echo ""
echo "Press Ctrl+C to stop..."
echo ""

# Wait for processes
wait
