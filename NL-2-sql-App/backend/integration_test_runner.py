#!/usr/bin/env python3
"""
Integration Test Runner for Developer View
Tests all components and returns status with detailed results
"""

import os
import sys
import time
import sqlite3
from typing import Dict, Any, List
from unittest.mock import Mock, patch

# Add backend to path
sys.path.append('./backend')

class IntegrationTestRunner:
    """Run integration tests for all components"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = time.time()
    
    def test_openai_integration(self) -> Dict[str, Any]:
        """Test OpenAI API integration"""
        result = {
            "name": "OpenAI API Integration",
            "status": "failed",
            "details": "",
            "timestamp": time.time(),
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Check if API key is set
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                result["details"] = "OpenAI API key not found in environment variables"
                return result
            
            # Test OpenAI import
            try:
                import openai
                openai.api_key = api_key
            except ImportError:
                result["details"] = "OpenAI package not installed"
                return result
            
            # Test simple API call
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                
                if response.choices[0].message.content:
                    result["status"] = "passed"
                    result["details"] = f"API call successful. Response: {response.choices[0].message.content[:50]}..."
                else:
                    result["details"] = "API call returned empty response"
                    
            except Exception as e:
                result["details"] = f"API call failed: {str(e)}"
                
        except Exception as e:
            result["details"] = f"Test failed: {str(e)}"
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_sqlite_integration(self) -> Dict[str, Any]:
        """Test SQLite database integration"""
        result = {
            "name": "SQLite Database",
            "status": "failed",
            "details": "",
            "timestamp": time.time(),
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Test database file existence
            db_path = os.getenv("DB_PATH", "banking.db")
            
            if db_path == ":memory:":
                # Test in-memory database
                conn = sqlite3.connect(":memory:")
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)")
                cursor.execute("INSERT INTO test (name) VALUES ('test')")
                cursor.execute("SELECT * FROM test")
                data = cursor.fetchall()
                conn.close()
                
                if data:
                    result["status"] = "passed"
                    result["details"] = "In-memory database working correctly"
                else:
                    result["details"] = "In-memory database query failed"
            else:
                # Test file-based database
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()
                    conn.close()
                    
                    if tables:
                        result["status"] = "passed"
                        result["details"] = f"Database connected. Found {len(tables)} tables"
                    else:
                        result["details"] = "Database connected but no tables found"
                else:
                    result["details"] = f"Database file not found: {db_path}"
                    
        except Exception as e:
            result["details"] = f"Database test failed: {str(e)}"
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_chromadb_integration(self) -> Dict[str, Any]:
        """Test ChromaDB integration"""
        result = {
            "name": "ChromaDB Vector Database",
            "status": "failed",
            "details": "",
            "timestamp": time.time(),
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Test ChromaDB import
            try:
                import chromadb
            except ImportError:
                result["details"] = "ChromaDB package not installed"
                return result
            
            # Test ChromaDB client
            try:
                persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
                client = chromadb.PersistentClient(path=persist_dir)
                
                # Test collection creation
                collection = client.create_collection(
                    name="test_collection",
                    metadata={"description": "Test collection"}
                )
                
                # Test embedding
                collection.add(
                    documents=["This is a test document"],
                    metadatas=[{"source": "test"}],
                    ids=["test_id"]
                )
                
                # Test query
                results = collection.query(
                    query_texts=["test document"],
                    n_results=1
                )
                
                # Clean up
                client.delete_collection("test_collection")
                
                if results and results['documents']:
                    result["status"] = "passed"
                    result["details"] = "ChromaDB working correctly. Test collection created and queried successfully."
                else:
                    result["details"] = "ChromaDB query returned no results"
                    
            except Exception as e:
                result["details"] = f"ChromaDB test failed: {str(e)}"
                
        except Exception as e:
            result["details"] = f"ChromaDB import failed: {str(e)}"
        
        result["duration"] = time.time() - start_time
        return result
    
    def test_llm_sample_query(self) -> Dict[str, Any]:
        """Test LLM with a sample query"""
        result = {
            "name": "LLM Sample Query Test",
            "status": "failed",
            "details": "",
            "timestamp": time.time(),
            "duration": 0
        }
        
        start_time = time.time()
        
        try:
            # Test LLM with a simple query
            from backend.llm_sql_generator import LLMSQLGenerator
            
            generator = LLMSQLGenerator()
            test_query = "Find all customers"
            
            # Mock schema context
            schema_context = {
                "schema_context": [{"table": "customers", "columns": ["id", "name", "email"]}],
                "value_hints": [],
                "exemplars": [],
                "query_analysis": {}
            }
            
            sql_result = generator.generate(test_query, {}, schema_context, {"customers": ["id", "name", "email"]})
            
            if sql_result and "SELECT" in sql_result.upper():
                result["status"] = "passed"
                result["details"] = f"LLM generated SQL: {sql_result[:100]}..."
            else:
                result["details"] = f"LLM failed to generate valid SQL: {sql_result}"
                
        except Exception as e:
            result["details"] = f"LLM test failed: {str(e)}"
        
        result["duration"] = time.time() - start_time
        return result
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        print("🧪 Running Integration Tests...")
        
        tests = [
            self.test_openai_integration,
            self.test_sqlite_integration,
            self.test_chromadb_integration,
            self.test_llm_sample_query
        ]
        
        for test_func in tests:
            test_name = test_func.__name__.replace("test_", "").replace("_", " ").title()
            print(f"  Testing {test_name}...")
            self.test_results[test_name] = test_func()
        
        total_duration = time.time() - self.start_time
        
        return {
            "tests": self.test_results,
            "total_duration": total_duration,
            "passed_count": sum(1 for result in self.test_results.values() if result["status"] == "passed"),
            "failed_count": sum(1 for result in self.test_results.values() if result["status"] == "failed"),
            "timestamp": time.time()
        }

def get_integration_test_results() -> Dict[str, Any]:
    """Get integration test results for the UI"""
    runner = IntegrationTestRunner()
    return runner.run_all_tests()

if __name__ == "__main__":
    results = get_integration_test_results()
    print(f"\n✅ Tests completed in {results['total_duration']:.2f}s")
    print(f"📊 Passed: {results['passed_count']}, Failed: {results['failed_count']}")
    
    for test_name, result in results['tests'].items():
        status_icon = "✅" if result['status'] == 'passed' else "❌"
        print(f"{status_icon} {test_name}: {result['details']}")
