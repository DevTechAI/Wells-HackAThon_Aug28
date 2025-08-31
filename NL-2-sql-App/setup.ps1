# PowerShell Setup script for SQL RAG Agent

Write-Host "🚀 Setting up SQL RAG Agent dependencies..." -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "🐍 Python version: $pythonVersion" -ForegroundColor Cyan
} catch {
    Write-Host "❌ Python is not installed or not in PATH. Please install Python 3.9+ first." -ForegroundColor Red
    exit 1
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path ".venv")) {
    Write-Host "📦 Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "🔧 Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "⬆️ Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "📥 Installing dependencies..." -ForegroundColor Yellow
Write-Host "Choose installation type:" -ForegroundColor Cyan
Write-Host "1) Minimal (core functionality only)" -ForegroundColor White
Write-Host "2) Full (all features including development tools)" -ForegroundColor White

$choice = Read-Host "Enter choice (1 or 2)"

switch ($choice) {
    "1" {
        Write-Host "📦 Installing minimal dependencies..." -ForegroundColor Yellow
        pip install -r requirements-minimal.txt
    }
    "2" {
        Write-Host "📦 Installing full dependencies..." -ForegroundColor Yellow
        pip install -r requirements.txt
    }
    default {
        Write-Host "❌ Invalid choice. Installing minimal dependencies..." -ForegroundColor Red
        pip install -r requirements-minimal.txt
    }
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host "🔧 Creating .env file..." -ForegroundColor Yellow
    Copy-Item env_template.txt .env
    Write-Host "⚠️ Please edit .env file and add your OpenAI API key" -ForegroundColor Yellow
}

# Create necessary directories
Write-Host "📁 Creating necessary directories..." -ForegroundColor Yellow
New-Item -ItemType Directory -Force -Path "chroma_db" | Out-Null
New-Item -ItemType Directory -Force -Path "logs" | Out-Null

Write-Host "✅ Setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Edit .env file and add your OpenAI API key" -ForegroundColor White
Write-Host "2. Run: .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "3. Run: streamlit run app.py" -ForegroundColor White
Write-Host ""
Write-Host "To test the backend:" -ForegroundColor Cyan
Write-Host "python test_backend_workflow.py" -ForegroundColor White
