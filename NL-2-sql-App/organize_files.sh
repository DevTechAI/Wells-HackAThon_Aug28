#!/bin/bash
# File organization script

echo "Moving test files to tests/ folder..."

# Move test files
mv test_integration_runner.py tests/ 2>/dev/null || echo "test_integration_runner.py not found or already moved"
mv quick_test_query_history.py tests/ 2>/dev/null || echo "quick_test_query_history.py not found or already moved"
mv test_query_history.py tests/ 2>/dev/null || echo "test_query_history.py not found or already moved"
mv test_backend_workflow.py tests/ 2>/dev/null || echo "test_backend_workflow.py not found or already moved"
mv test_system.py tests/ 2>/dev/null || echo "test_system.py not found or already moved"
mv quick_openai_test.py tests/ 2>/dev/null || echo "quick_openai_test.py not found or already moved"
mv test_env_config.py tests/ 2>/dev/null || echo "test_env_config.py not found or already moved"
mv test_openai_integration.py tests/ 2>/dev/null || echo "test_openai_integration.py not found or already moved"
mv test_gemini_integration.py tests/ 2>/dev/null || echo "test_gemini_integration.py not found or already moved"
mv token_analysis.py tests/ 2>/dev/null || echo "token_analysis.py not found or already moved"
mv repopulate_vector_db.py tests/ 2>/dev/null || echo "repopulate_vector_db.py not found or already moved"
mv cleanup_vectorstore.py tests/ 2>/dev/null || echo "cleanup_vectorstore.py not found or already moved"

echo "Moving .md files to docs/ folder..."

# Move markdown files
mv UV_SETUP_GUIDE.md docs/ 2>/dev/null || echo "UV_SETUP_GUIDE.md not found or already moved"
mv INITIALIZATION_CHECKLIST.md docs/ 2>/dev/null || echo "INITIALIZATION_CHECKLIST.md not found or already moved"
mv CONFIGURATION_GUIDE.md docs/ 2>/dev/null || echo "CONFIGURATION_GUIDE.md not found or already moved"
mv GEMINI_MIGRATION_GUIDE.md docs/ 2>/dev/null || echo "GEMINI_MIGRATION_GUIDE.md not found or already moved"
mv README.md docs/ 2>/dev/null || echo "README.md not found or already moved"

echo "Removing redundant files..."

# Remove redundant files
rm system_initializer.py 2>/dev/null || echo "system_initializer.py not found or already removed"
rm streamlit_app.py 2>/dev/null || echo "streamlit_app.py not found or already removed"

echo "File organization completed!"
