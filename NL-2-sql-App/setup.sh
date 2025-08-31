#!/bin/bash
# Setup script for SQL RAG Agent

echo "🚀 Setting up SQL RAG Agent dependencies..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.9+ first."
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "🐍 Python version: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📥 Installing dependencies..."
echo "Choose installation type:"
echo "1) Minimal (core functionality only)"
echo "2) Full (all features including development tools)"
read -p "Enter choice (1 or 2): " choice

case $choice in
    1)
        echo "📦 Installing minimal dependencies..."
        pip install -r requirements-minimal.txt
        ;;
    2)
        echo "📦 Installing full dependencies..."
        pip install -r requirements.txt
        ;;
    *)
        echo "❌ Invalid choice. Installing minimal dependencies..."
        pip install -r requirements-minimal.txt
        ;;
esac

# Create .env file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "🔧 Creating .env file..."
    cp env_template.txt .env
    echo "⚠️ Please edit .env file and add your OpenAI API key"
fi

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p chroma_db
mkdir -p logs

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file and add your OpenAI API key"
echo "2. Run: source .venv/bin/activate"
echo "3. Run: streamlit run app.py"
echo ""
echo "To test the backend:"
echo "python test_backend_workflow.py"
