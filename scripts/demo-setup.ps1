# APEX Demo Setup Script
# Sets up and runs the complete APEX financial operating system demo locally

param(
    [switch]$Clean,
    [switch]$SkipBuild,
    [switch]$Headless
)

Write-Host "🚀 APEX Financial Operating System - Local Demo Setup" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan

# Configuration
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "client\front"

# Colors for output
$Green = "Green"
$Yellow = "Yellow"
$Red = "Red"
$Cyan = "Cyan"

# Global variables for process management
$BackendProcess = $null
$FrontendProcess = $null
$PostgresProcess = $null
$RedisProcess = $null

function Write-Step {
    param([string]$Message)
    Write-Host "`n📋 $Message" -ForegroundColor $Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor $Red
}

# Clean up function
function Invoke-Cleanup {
    Write-Step "Cleaning up previous demo environment..."

    # Kill any running demo processes
    if ($BackendProcess) {
        try { Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    if ($FrontendProcess) {
        try { Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    if ($PostgresProcess) {
        try { Stop-Process -Id $PostgresProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
    }
    if ($RedisProcess) {
        try { Stop-Process -Id $RedisProcess.Id -Force -ErrorAction SilentlyContinue } catch {}
    }

    # Remove demo-specific files
    $demoFiles = @(
        ".env.demo",
        "demo.log",
        "backend\.env",
        "client\front\.env.local"
    )

    foreach ($file in $demoFiles) {
        if (Test-Path $file) {
            Remove-Item $file -Force
        }
    }

    # Clean up ChromaDB data
    $chromaDir = Join-Path $BackendDir "data\chroma_db"
    if (Test-Path $chromaDir) {
        Remove-Item $chromaDir -Recurse -Force
    }

    Write-Success "Cleanup completed"
}

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking prerequisites..."

    # Check Python
    try {
        $pythonVersion = python --version 2>$null
        if ($pythonVersion -match "Python 3\.\d+") {
            Write-Success "Python: $pythonVersion"
        } else {
            Write-Warning "Python version may not be compatible. Recommended: Python 3.10+"
        }
    } catch {
        Write-Error "Python is not installed or not in PATH."
        exit 1
    }

    # Check Node.js
    try {
        $nodeVersion = node --version 2>$null
        Write-Success "Node.js: $nodeVersion"
    } catch {
        Write-Error "Node.js is not installed or not in PATH."
        exit 1
    }

    # Check npm
    try {
        $npmVersion = npm --version 2>$null
        Write-Success "npm: $npmVersion"
    } catch {
        Write-Error "npm is not available."
        exit 1
    }

    # Check pip
    try {
        $pipVersion = pip --version 2>$null
        Write-Success "pip available"
    } catch {
        Write-Error "pip is not available."
        exit 1
    }

    # Check if PostgreSQL is available (try common locations)
    $postgresFound = $false
    try {
        # Try to find PostgreSQL service
        $services = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
        if ($services) {
            Write-Success "PostgreSQL service found"
            $postgresFound = $true
        }
    } catch {}

    if (-not $postgresFound) {
        try {
            # Try command line
            $pgVersion = psql --version 2>$null
            if ($pgVersion) {
                Write-Success "PostgreSQL client found: $pgVersion"
                Write-Warning "Make sure PostgreSQL server is running on localhost:5432"
                $postgresFound = $true
            }
        } catch {}
    }

    if (-not $postgresFound) {
        Write-Warning "PostgreSQL not found. Demo will use SQLite as fallback."
    }

    # Check if Redis is available
    $redisFound = $false
    try {
        $services = Get-Service -Name "*redis*" -ErrorAction SilentlyContinue
        if ($services) {
            Write-Success "Redis service found"
            $redisFound = $true
        }
    } catch {}

    if (-not $redisFound) {
        try {
            $redisVersion = redis-cli --version 2>$null
            if ($redisVersion) {
                Write-Success "Redis client found: $redisVersion"
                Write-Warning "Make sure Redis server is running on localhost:6379"
                $redisFound = $true
            }
        } catch {}
    }

    if (-not $redisFound) {
        Write-Warning "Redis not found. Demo will run with limited functionality."
    }

    # Check if ports are available
    $ports = @(5432, 6379, 8000, 5173)
    foreach ($port in $ports) {
        $connection = Test-NetConnection -ComputerName localhost -Port $port -WarningAction SilentlyContinue
        if ($connection.TcpTestSucceeded) {
            Write-Warning "Port $port is already in use. Demo may not work properly."
        }
    }

    Write-Success "Prerequisites check completed"
}

# Setup environment
function New-DemoEnvironment {
    Write-Step "Setting up demo environment..."

    # Check if PostgreSQL is available, fallback to SQLite
    $databaseUrl = "sqlite+aiosqlite:///./apex_demo.db"
    try {
        $services = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue
        if ($services) {
            $databaseUrl = "postgresql+asyncpg://apex_user:apex_password@localhost:5432/apex_db"
            Write-Success "Using PostgreSQL database"
        } else {
            Write-Warning "Using SQLite as fallback database"
        }
    } catch {
        Write-Warning "Using SQLite as fallback database"
    }

    # Check Redis availability
    $redisEnabled = $false
    try {
        $services = Get-Service -Name "*redis*" -ErrorAction SilentlyContinue
        if ($services) {
            $redisEnabled = $true
            Write-Success "Redis available"
        }
    } catch {
        Write-Warning "Redis not available - some features will be limited"
    }

    # Create demo .env file
    $envContent = @"
# APEX Demo Environment Configuration
# This file contains demo settings - DO NOT use in production

# Application
APP_NAME=APEX Financial OS (Demo)
APP_VERSION=1.0.0
ENVIRONMENT=demo
DEBUG=true

# API Server
API_HOST=0.0.0.0
API_PORT=8000
API_BASE_URL=http://localhost:8000

# CORS (allow all for demo)
CORS_ORIGINS=["*"]
CORS_ALLOW_CREDENTIALS=true

# Database
DATABASE_URL=$databaseUrl

# Redis
REDIS_URL=redis://localhost:6379
REDIS_ENABLED=$($redisEnabled.ToString().ToLower())

# Security (Demo keys - NOT secure!)
JWT_SECRET_KEY=demo_jwt_secret_key_replace_in_production_12345678901234567890
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=60
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# AI/LLM (Demo - limited functionality)
OPENROUTER_API_KEY=demo_key_placeholder
DEFAULT_LLM_MODEL=nvidia/llama-3.1-nemotron-70b-instruct

# Trading (Demo - paper trading only)
ALPACA_API_KEY=demo_alpaca_key_placeholder
ALPACA_SECRET_KEY=demo_alpaca_secret_placeholder
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_PAPER_TRADING=true

# Banking (Mock data for demo)
PLAID_CLIENT_ID=demo_plaid_client_placeholder
PLAID_SECRET=demo_plaid_secret_placeholder
PLAID_ENVIRONMENT=sandbox
PLAID_ENABLED=false

# Vector Database (Local ChromaDB)
CHROMA_PERSIST_DIRECTORY=./data/chroma_db
CHROMA_COLLECTION_NAME=apex_financial_knowledge

# Voice (Disabled for demo)
VOICE_ENABLED=false

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=text

# Agent Settings
AGENT_TIMEOUT_SECONDS=30
DEBATE_MAX_ROUNDS=3
CONSENSUS_THRESHOLD=0.7

# GPU (Disabled for demo)
ENABLE_GPU=false

# Feature Flags
ENABLE_CRASH_SIMULATOR=true
ENABLE_SUBSCRIPTION_DETECTION=true
"@

    $envContent | Out-File -FilePath ".env.demo" -Encoding UTF8
    Write-Success "Demo environment file created"

    # Copy demo env to backend
    Copy-Item ".env.demo" "$BackendDir\.env" -Force
    Write-Success "Environment file copied to backend"

    # Create frontend env file
    $frontendEnv = @"
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_ENV=demo
"@
    $frontendEnv | Out-File -FilePath "$FrontendDir\.env.local" -Encoding UTF8
    Write-Success "Frontend environment file created"
}

# Build services
function Invoke-Build {
    Write-Step "Building APEX services..."

    # Build backend
    Write-Host "Setting up backend dependencies..." -ForegroundColor $Yellow
    Push-Location $BackendDir

    # Install Python dependencies
    if (Test-Path "requirements.txt") {
        Write-Host "Installing Python dependencies..." -ForegroundColor $Yellow
        pip install -r requirements.txt 2>$null
    } elseif (Test-Path "requirements.in") {
        Write-Host "Installing Python dependencies from requirements.in..." -ForegroundColor $Yellow
        pip install -r requirements.in 2>$null
    } else {
        Write-Host "Installing basic Python packages..." -ForegroundColor $Yellow
        pip install fastapi uvicorn sqlalchemy chromadb 2>$null
    }

    Pop-Location
    Write-Success "Backend dependencies installed"

    # Build frontend
    Write-Host "Setting up frontend dependencies..." -ForegroundColor $Yellow
    Push-Location $FrontendDir

    if (Test-Path "node_modules") {
        Write-Host "Installing frontend dependencies..." -ForegroundColor $Yellow
        npm ci 2>$null
    } else {
        Write-Host "Installing frontend dependencies..." -ForegroundColor $Yellow
        npm install 2>$null
    }

    Pop-Location
    Write-Success "Frontend dependencies installed"
}

# Start services
function Start-DemoServices {
    Write-Step "Starting APEX demo services..."

    # Start backend server
    Write-Host "Starting backend server..." -ForegroundColor $Yellow
    Push-Location $BackendDir
    try {
        $script:BackendProcess = Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -NoNewWindow -PassThru
        Write-Success "Backend server started (PID: $($BackendProcess.Id))"
    } catch {
        Write-Error "Failed to start backend server: $($_.Exception.Message)"
        Pop-Location
        exit 1
    }
    Pop-Location

    # Wait for backend to be ready
    Write-Host "Waiting for backend API..." -ForegroundColor $Yellow
    $retryCount = 0
    while ($retryCount -lt 20) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Backend API is ready"
                break
            }
        } catch {
            # Continue trying
        }
        Start-Sleep -Seconds 2
        $retryCount++
    }

    if ($retryCount -eq 20) {
        Write-Warning "Backend API may not be ready, but continuing with demo..."
    }

    # Start frontend development server
    Write-Host "Starting frontend development server..." -ForegroundColor $Yellow
    Push-Location $FrontendDir
    try {
        $script:FrontendProcess = Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow -PassThru
        Write-Success "Frontend server started (PID: $($FrontendProcess.Id))"
    } catch {
        Write-Error "Failed to start frontend server: $($_.Exception.Message)"
        Pop-Location
        exit 1
    }
    Pop-Location

    # Wait for frontend to be ready
    Write-Host "Waiting for frontend..." -ForegroundColor $Yellow
    Start-Sleep -Seconds 5  # Give npm time to start

    $retryCount = 0
    while ($retryCount -lt 10) {
        try {
            $response = Invoke-WebRequest -Uri "http://localhost:5173" -TimeoutSec 5 -ErrorAction SilentlyContinue
            if ($response.StatusCode -eq 200) {
                Write-Success "Frontend is ready"
                break
            }
        } catch {
            # Continue trying
        }
        Start-Sleep -Seconds 3
        $retryCount++
    }

    if ($retryCount -eq 10) {
        Write-Warning "Frontend may not be ready, but continuing with demo..."
    }

    Write-Success "All services started"
}

# Run demo
function Invoke-Demo {
    Write-Step "🎉 APEX Demo is now running!"

    Write-Host ""
    Write-Host "🌐 Frontend (React):   http://localhost:5173" -ForegroundColor $Cyan
    Write-Host "🚀 Backend API:        http://localhost:8000" -ForegroundColor $Cyan
    Write-Host "📚 API Docs:           http://localhost:8000/docs" -ForegroundColor $Cyan
    Write-Host "💚 Health Check:       http://localhost:8000/health" -ForegroundColor $Cyan
    Write-Host ""

    Write-Host "🔑 Demo Configuration:" -ForegroundColor $Yellow
    Write-Host "   • Environment: Demo mode (limited functionality)"
    Write-Host "   • Database: SQLite (fallback) or PostgreSQL if available"
    Write-Host "   • AI: Mock responses (no real API calls)"
    Write-Host "   • Trading: Paper trading simulation"
    Write-Host ""

    Write-Host "📋 Available Demo Features:" -ForegroundColor $Green
    Write-Host "   ✅ Market Agent Analysis (mock data)"
    Write-Host "   ✅ Portfolio Management (demo accounts)"
    Write-Host "   ✅ Crash Scenario Simulator"
    Write-Host "   ✅ War Room Agent Discussion (basic)"
    Write-Host "   ✅ API Documentation & Testing"
    Write-Host ""

    if (-not $Headless) {
        Write-Host "💡 Tips:" -ForegroundColor $Cyan
        Write-Host "   • Backend logs are shown in this terminal"
        Write-Host "   • Frontend dev server auto-reloads on changes"
        Write-Host "   • Check API docs for available endpoints"
        Write-Host "   • Press Ctrl+C to stop all services"
        Write-Host ""

        Write-Host "Press Ctrl+C to stop the demo..." -ForegroundColor $Yellow
        try {
            # Keep script running
            while ($true) {
                Start-Sleep -Seconds 1
            }
        } catch {
            Write-Step "Stopping demo..."
        }
    }
}

# Stop demo
function Stop-Demo {
    Write-Step "Stopping APEX demo..."

    # Kill backend process
    if ($BackendProcess) {
        try {
            Stop-Process -Id $BackendProcess.Id -Force -ErrorAction SilentlyContinue
            Write-Success "Backend server stopped"
        } catch {
            Write-Warning "Could not stop backend process"
        }
    }

    # Kill frontend process
    if ($FrontendProcess) {
        try {
            Stop-Process -Id $FrontendProcess.Id -Force -ErrorAction SilentlyContinue
            Write-Success "Frontend server stopped"
        } catch {
            Write-Warning "Could not stop frontend process"
        }
    }

    Write-Success "Demo stopped"
}

# Main execution
try {
    if ($Clean) {
        Invoke-Cleanup
        exit 0
    }

    Test-Prerequisites
    New-DemoEnvironment

    if (-not $SkipBuild) {
        Invoke-Build
    }

    Start-DemoServices
    Invoke-Demo

} catch {
    Write-Error "Demo setup failed: $($_.Exception.Message)"
    Write-Error "Check the troubleshooting section in README.md"
    exit 1
} finally {
    if (-not $Headless) {
        Stop-Demo
    }
}
