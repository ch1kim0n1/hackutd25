# APEX Demo Setup Script (Windows PowerShell)
# Sets up backend + frontend for local demo

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  APEX Demo Setup (Windows)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "  ✓ Found: $pythonVersion" -ForegroundColor Green

    # Extract version number
    if ($pythonVersion -match "Python (\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -lt 3 -or ($major -eq 3 -and $minor -lt 10)) {
            Write-Host "  ✗ Python 3.10+ required, found $major.$minor" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  ✗ Python not found. Install Python 3.10+ from https://python.org" -ForegroundColor Red
    exit 1
}

# Check Node version
Write-Host "[2/6] Checking Node.js version..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "  ✓ Found: $nodeVersion" -ForegroundColor Green

    if ($nodeVersion -match "v(\d+)\.") {
        $nodeMajor = [int]$matches[1]
        if ($nodeMajor -lt 18) {
            Write-Host "  ✗ Node.js 18+ required, found v$nodeMajor" -ForegroundColor Red
            exit 1
        }
    }
} catch {
    Write-Host "  ✗ Node.js not found. Install Node.js 18+ from https://nodejs.org" -ForegroundColor Red
    exit 1
}

# Create .env if missing
Write-Host "[3/6] Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "  ✓ .env already exists" -ForegroundColor Green
}

# Setup backend
Write-Host "[4/6] Setting up backend (Python)..." -ForegroundColor Yellow
Push-Location "src\backend"
try {
    # Create venv if missing
    if (-not (Test-Path "venv")) {
        Write-Host "  Creating Python virtual environment..." -ForegroundColor Gray
        python -m venv venv
    }

    # Activate venv
    Write-Host "  Activating virtual environment..." -ForegroundColor Gray
    & ".\venv\Scripts\Activate.ps1"

    # Install dependencies
    Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
    python -m pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet

    # Create data directory
    if (-not (Test-Path "..\..\data")) {
        New-Item -ItemType Directory -Path "..\..\data" -Force | Out-Null
    }

    # Run migrations
    Write-Host "  Running database migrations..." -ForegroundColor Gray
    alembic upgrade head 2>&1 | Out-Null

    Write-Host "  ✓ Backend setup complete" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Backend setup failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# Setup frontend
Write-Host "[5/6] Setting up frontend (Node.js)..." -ForegroundColor Yellow
Push-Location "client\front"
try {
    Write-Host "  Installing Node dependencies..." -ForegroundColor Gray
    npm install --silent

    Write-Host "  ✓ Frontend setup complete" -ForegroundColor Green
} catch {
    Write-Host "  ✗ Frontend setup failed: $_" -ForegroundColor Red
    Pop-Location
    exit 1
} finally {
    Pop-Location
}

# Final check
Write-Host "[6/6] Setup verification..." -ForegroundColor Yellow
Write-Host "  ✓ All components ready" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Setup Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Run the demo: .\scripts\run.ps1" -ForegroundColor White
Write-Host "  2. Visit: http://localhost:5173" -ForegroundColor White
Write-Host ""
