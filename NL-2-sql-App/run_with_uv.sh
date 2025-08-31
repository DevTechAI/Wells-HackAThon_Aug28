#!/bin/bash
# Quick start script for NL-2-SQL App

echo "🚀 Starting NL-2-SQL App with UV..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing UV..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source ~/.bashrc
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    uv venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -r requirements.txt

# Set up environment if .env doesn't exist
if [ ! -f ".env" ]; then
    echo "Setting up environment file..."
    cp env_template.txt .env
    echo "⚠️  Please edit .env file with your API keys before running!"
fi

# Run the app
echo "🎯 Starting Streamlit app..."
uv run streamlit run app.py
