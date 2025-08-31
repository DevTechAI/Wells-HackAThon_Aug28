# 🚀 UV Migration Guide for SQL RAG Agent

## What is UV?

UV is a modern, fast Python package installer and resolver written in Rust. It's designed to be a drop-in replacement for pip and virtual environments, offering:

- **10-100x faster** than pip
- **Reliable dependency resolution**
- **Built-in virtual environment management**
- **Compatible with existing Python projects**

## 🔄 Migration Steps

### Step 1: Install UV

```bash
# Install UV using curl (recommended)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv

# Verify installation
uv --version
```

### Step 2: Remove Old Virtual Environment

```bash
# Deactivate current environment (if active)
deactivate

# Remove old virtual environment
rm -rf .venv
rm -rf .venv2
rm -rf .venv3
rm -rf .venvtest
```

### Step 3: Create New UV Environment

```bash
# Create new UV environment
uv venv

# Activate the environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate     # On Windows
```

### Step 4: Install Dependencies

```bash
# Install all dependencies from requirements.txt
uv pip install -r requirements.txt

# Or install dependencies one by one
uv pip install streamlit
uv pip install chromadb
uv pip install pydantic
uv pip install sqlparse
uv pip install python-dotenv
uv pip install pandas
uv pip install pytest
uv pip install langgraph
uv pip install anthropic
uv pip install openai
uv pip install google-generativeai
uv pip install llama-cpp-python
uv pip install reportlab
```

### Step 5: Verify Installation

```bash
# Check installed packages
uv pip list

# Test the application
python test_system.py
```

## 📁 Updated Project Structure

```
NL-2-sql-App/
├── .venv/                    # UV virtual environment
├── requirements.txt          # Dependencies (unchanged)
├── pyproject.toml           # NEW: UV project configuration
├── app.py                   # Main application
├── system_initializer.py    # System initialization
├── test_system.py          # Test script
├── backend/                 # Backend modules
├── tests/                   # Test files
└── docs/                    # Documentation
```

## 📝 New Configuration Files

### pyproject.toml (NEW)

```toml
[project]
name = "sql-rag-agent"
version = "1.0.0"
description = "Natural Language to SQL with RAG (Retrieval-Augmented Generation)"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
dependencies = [
    "streamlit>=1.28.0",
    "chromadb>=0.4.0",
    "pydantic>=2.0.0",
    "sqlparse>=0.4.0",
    "python-dotenv>=1.0.0",
    "pandas>=2.0.0",
    "pytest>=7.0.0",
    "langgraph>=0.1.0",
    "anthropic>=0.7.0",
    "openai>=1.0.0",
    "google-generativeai>=0.3.0",
    "llama-cpp-python>=0.2.0",
    "reportlab>=4.0.0",
]
requires-python = ">=3.9"

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.uv]
dev-dependencies = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "black>=23.0.0",
    "flake8>=6.0.0",
]
```

## 🔧 Updated Scripts

### run_app.sh (NEW)

```bash
#!/bin/bash
# Run the SQL RAG Agent application

# Activate UV environment
source .venv/bin/activate

# Set environment variables
export OPENAI_API_KEY="your-openai-api-key-here"
export CHROMA_PERSIST_DIR="./chroma_db"
export DB_PATH=":memory:"

# Run the application
streamlit run app.py
```

### run_tests.sh (NEW)

```bash
#!/bin/bash
# Run all tests

# Activate UV environment
source .venv/bin/activate

# Run system tests
python test_system.py

# Run specific test suites
python -m pytest tests/ -v

# Run integration tests
python tests/integration_tests.py

# Run backend tests
python tests/backend_test_runner.py
```

### setup_env.sh (UPDATED)

```bash
#!/bin/bash
# Setup environment for SQL RAG Agent

# Create UV environment
uv venv

# Activate environment
source .venv/bin/activate

# Install dependencies
uv pip install -r requirements.txt

# Create necessary directories
mkdir -p chroma_db
mkdir -p reports
mkdir -p logs

# Set up environment variables
echo "export OPENAI_API_KEY='your-openai-api-key-here'" > .env
echo "export CHROMA_PERSIST_DIR='./chroma_db'" >> .env
echo "export DB_PATH=':memory:'" >> .env

echo "✅ Environment setup complete!"
echo "🔑 Don't forget to add your OpenAI API key to .env file"
echo "🚀 Run: source .venv/bin/activate && streamlit run app.py"
```

## 🚀 Quick Start Commands

```bash
# 1. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Create environment and install dependencies
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt

# 3. Set up environment variables
export OPENAI_API_KEY="your-api-key-here"
export CHROMA_PERSIST_DIR="./chroma_db"
export DB_PATH=":memory:"

# 4. Run tests
python test_system.py

# 5. Start application
streamlit run app.py
```

## 🔄 Migration Checklist

- [ ] Install UV
- [ ] Remove old virtual environments
- [ ] Create new UV environment
- [ ] Install dependencies
- [ ] Create pyproject.toml
- [ ] Update scripts
- [ ] Test installation
- [ ] Update .gitignore
- [ ] Update documentation

## 📋 Updated .gitignore

```gitignore
# UV
.venv/
.uv/

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Environment variables
.env
.env.local
.env.*.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Project specific
chroma_db/
reports/
logs/
*.db
*.sqlite
*.sqlite3

# Test files
test_files/
*.tmp
```

## ⚡ UV Benefits

1. **Speed**: 10-100x faster than pip
2. **Reliability**: Better dependency resolution
3. **Simplicity**: Built-in virtual environment management
4. **Compatibility**: Works with existing Python projects
5. **Modern**: Written in Rust for performance

## 🐛 Troubleshooting

### Common Issues

1. **UV not found**: Make sure UV is in your PATH
2. **Permission errors**: Use `sudo` for system-wide installation
3. **Dependency conflicts**: UV handles these automatically
4. **Environment not activating**: Check the activation script path

### Commands

```bash
# Check UV installation
uv --version

# List installed packages
uv pip list

# Update dependencies
uv pip install --upgrade -r requirements.txt

# Remove environment
rm -rf .venv

# Recreate environment
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

## 🎯 Next Steps

1. **Install UV** using the commands above
2. **Migrate your environment** following the steps
3. **Test the application** with `python test_system.py`
4. **Start the app** with `streamlit run app.py`
5. **Update your workflow** to use UV commands

UV will make your development workflow much faster and more reliable!
