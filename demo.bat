@echo off
REM APEX Financial Operating System - Quick Demo Launcher
REM This batch file provides a simple way to start the APEX demo

echo 🚀 Starting APEX Financial Operating System Demo...
echo.

echo 📋 Checking prerequisites...

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH.
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Check if Node.js is available
node --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Node.js is not installed or not in PATH.
    echo Please install Node.js 18+ from https://nodejs.org
    pause
    exit /b 1
)

echo ✅ Prerequisites OK
echo.

echo 📦 Installing dependencies...

REM Install backend dependencies
echo Installing backend dependencies...
cd backend
pip install -r requirements.txt >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ Some backend dependencies may have failed to install
)

REM Install frontend dependencies
echo Installing frontend dependencies...
cd ../client/front
if not exist node_modules (
    npm install >nul 2>&1
    if %errorlevel% neq 0 (
        echo ⚠️ Frontend dependencies installation may have issues
    )
)

echo ✅ Dependencies installed
echo.

echo 🚀 Starting services...

REM Start backend in background
echo Starting backend server...
cd ../../backend
start "APEX Backend" cmd /c "python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

REM Start frontend in background
echo Starting frontend server...
cd ../client/front
start "APEX Frontend" cmd /c "npm run dev"

echo.
echo 🎉 APEX Demo is starting up!
echo.
echo 🌐 Frontend will be available at: http://localhost:5173
echo 🚀 Backend API will be available at: http://localhost:8000
echo 📚 API Documentation: http://localhost:8000/docs
echo 💚 Health Check: http://localhost:8000/health
echo.
echo ⏳ Services are starting... Please wait 10-15 seconds for them to be ready.
echo.
echo Press any key to open the demo in your browser...
pause >nul

REM Open browser
start http://localhost:5173

echo.
echo Demo is running! Press Ctrl+C in the terminal windows to stop services.
echo Or press any key here to exit (services will continue running)...
pause >nul
