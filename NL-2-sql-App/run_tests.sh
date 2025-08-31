#!/bin/bash
# Test runner script for SQL RAG Agent

echo "🧪 Running SQL RAG Agent Tests"
echo "=" * 50

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment not found. Creating one..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install test dependencies if needed
echo "📦 Installing test dependencies..."
pip install pytest unittest2

# Run tests
echo ""
echo "🚀 Running QueryHistory Unit Tests..."
python test_query_history.py

echo ""
echo "🚀 Running Quick QueryHistory Tests..."
python quick_test_query_history.py

echo ""
echo "🚀 Running Backend Workflow Tests..."
python test_backend_workflow.py

echo ""
echo "✅ All tests completed!"
echo "📊 Check the output above for any failures"
