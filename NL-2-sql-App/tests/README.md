# Test Files Directory

This directory contains all the test Python files for the NL2SQL application.

## Test Files Overview

### Core Functionality Tests
- **test_fallback.py** - Tests fallback logic for branch/manager queries
- **test_fix.py** - Tests fixes for special handler override issues
- **test_fixed_logic.py** - Tests the fixed SQL generator logic
- **test_sql_generation.py** - Tests SQL generation for specific queries
- **test_sql_generator.py** - Tests SQL generator logic and fallback conditions

### System Integration Tests
- **test_llm_loading.py** - Tests LLM loading and timeout functionality
- **test_connectivity.py** - Tests system connectivity (SQL DB, LLM, ChromaDB)
- **test_chromadb.py** - Tests ChromaDB contents and schema information
- **test_loading_indicators.py** - Tests loading indicators for initialization
- **verify_vector_db.py** - Comprehensive VectorDB verification and dataset coverage analysis

### Query-Specific Tests
- **test_query.py** - Tests database connection and query execution
- **test_schema_context.py** - Tests comprehensive schema context generation
- **test_customer_query.py** - Tests customer account query logic

### Performance and Configuration Tests
- **test_1024_tokens.py** - Tests benefits of 1024 tokens for SQL generation
- **test_advanced_prompting.py** - Tests advanced prompting techniques

## Usage

Each test file can be run independently:

```bash
python test_files/test_fallback.py
python test_files/test_connectivity.py
python test_files/test_llm_loading.py
python test_files/verify_vector_db.py
```

## Purpose

These test files help:
- Debug specific functionality issues
- Verify system components are working correctly
- Test query logic and SQL generation
- Validate system connectivity and performance
- Document expected behavior for complex queries

## Notes

- All test files are self-contained and can be run independently
- Tests include detailed logging and debugging information
- Some tests simulate the actual application logic for debugging
- Tests help identify issues with LLM, database, and vector store components
