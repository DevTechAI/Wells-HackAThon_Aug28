#!/usr/bin/env python3
"""
Backend Test Runner
Runs all backend tests and provides detailed reports
"""

import os
import sys
import time
import unittest
from typing import Dict, Any, List
import logging

# Add backend to path
sys.path.append('./backend')

from tests.integration_tests import run_integration_tests
from system_initializer import run_system_initialization

logger = logging.getLogger(__name__)

class BackendTestRunner:
    """Comprehensive backend test runner"""
    
    def __init__(self):
        self.test_results = {}
        self.overall_status = "pending"
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all backend tests"""
        self.start_time = time.time()
        logger.info("🧪 Starting Backend Test Suite")
        
        # Run different test categories
        self._run_unit_tests()
        self._run_integration_tests()
        self._run_system_tests()
        self._run_performance_tests()
        
        self.end_time = time.time()
        self._calculate_overall_status()
        
        return self._generate_test_report()
    
    def _run_unit_tests(self):
        """Run unit tests for individual components"""
        logger.info("🔬 Running Unit Tests")
        
        # Test individual components
        unit_tests = {
            "llm_config": self._test_llm_config,
            "database_manager": self._test_database_manager,
            "embedder": self._test_embedder,
            "sql_generator": self._test_sql_generator,
            "agents": self._test_agents,
            "pdf_exporter": self._test_pdf_exporter
        }
        
        for test_name, test_func in unit_tests.items():
            try:
                result = test_func()
                self.test_results[f"unit_{test_name}"] = result
            except Exception as e:
                self.test_results[f"unit_{test_name}"] = {
                    "status": "error",
                    "message": f"Unit test failed: {str(e)}",
                    "details": {"error": str(e)}
                }
    
    def _run_integration_tests(self):
        """Run integration tests"""
        logger.info("🔗 Running Integration Tests")
        
        try:
            integration_report = run_integration_tests()
            self.test_results["integration"] = {
                "status": integration_report["overall_status"],
                "message": f"Integration tests completed",
                "details": integration_report["summary"],
                "duration": integration_report["test_duration"]
            }
        except Exception as e:
            self.test_results["integration"] = {
                "status": "error",
                "message": f"Integration tests failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _run_system_tests(self):
        """Run system initialization tests"""
        logger.info("🚀 Running System Tests")
        
        try:
            system_report = run_system_initialization()
            self.test_results["system"] = {
                "status": system_report["overall_status"],
                "message": f"System initialization completed",
                "details": system_report["summary"],
                "duration": system_report["initialization_duration"]
            }
        except Exception as e:
            self.test_results["system"] = {
                "status": "error",
                "message": f"System tests failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _run_performance_tests(self):
        """Run performance tests"""
        logger.info("📊 Running Performance Tests")
        
        performance_tests = {
            "response_time": self._test_response_time,
            "memory_usage": self._test_memory_usage,
            "concurrent_queries": self._test_concurrent_queries
        }
        
        for test_name, test_func in performance_tests.items():
            try:
                result = test_func()
                self.test_results[f"performance_{test_name}"] = result
            except Exception as e:
                self.test_results[f"performance_{test_name}"] = {
                    "status": "error",
                    "message": f"Performance test failed: {str(e)}",
                    "details": {"error": str(e)}
                }
    
    def _test_llm_config(self) -> Dict[str, Any]:
        """Test LLM configuration"""
        try:
            from backend.llm_config import llm_config
            
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_model()
            
            if provider and api_key and model:
                return {
                    "status": "passed",
                    "message": "LLM configuration valid",
                    "details": {"provider": provider, "model": model}
                }
            else:
                return {
                    "status": "failed",
                    "message": "LLM configuration incomplete",
                    "details": {"provider": provider, "has_api_key": bool(api_key), "model": model}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"LLM config test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_database_manager(self) -> Dict[str, Any]:
        """Test database manager"""
        try:
            from backend.db_manager import get_db_manager
            
            db_manager = get_db_manager(":memory:")
            conn = db_manager.get_connection()
            
            if conn:
                return {
                    "status": "passed",
                    "message": "Database manager working",
                    "details": {"connection_created": True}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Database manager failed",
                    "details": {}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database manager test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_embedder(self) -> Dict[str, Any]:
        """Test embedder functionality"""
        try:
            from backend.llm_embedder import LLMEmbedder
            from backend.llm_config import llm_config
            
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_embedding_model()
            
            embedder = LLMEmbedder(provider, api_key, model)
            test_embedding = embedder.generate_embedding("Test embedding")
            
            if test_embedding and len(test_embedding) > 0:
                return {
                    "status": "passed",
                    "message": "Embedder working",
                    "details": {"dimensions": len(test_embedding)}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Embedder failed",
                    "details": {}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Embedder test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_sql_generator(self) -> Dict[str, Any]:
        """Test SQL generator"""
        try:
            from backend.llm_sql_generator import LLMSQLGenerator
            from backend.llm_config import llm_config
            
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_model()
            
            generator = LLMSQLGenerator(provider, api_key, model)
            test_context = {"schema_tables": {"customers": ["id", "name"]}}
            sql = generator.generate_sql("Find customers", test_context)
            
            if sql and "SELECT" in sql.upper():
                return {
                    "status": "passed",
                    "message": "SQL generator working",
                    "details": {"generated_sql": sql[:50] + "..."}
                }
            else:
                return {
                    "status": "failed",
                    "message": "SQL generator failed",
                    "details": {"generated_sql": sql}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"SQL generator test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_agents(self) -> Dict[str, Any]:
        """Test individual agents"""
        try:
            from backend.planner import PlannerAgent
            from backend.validator import ValidatorAgent
            from backend.executor import ExecutorAgent
            from backend.summarizer import SummarizerAgent
            
            schema_tables = {"customers": ["id", "name"]}
            
            # Test planner
            planner = PlannerAgent(schema_tables)
            plan = planner.analyze_query("Find customers")
            
            # Test validator
            validator = ValidatorAgent(schema_tables)
            is_safe, _ = validator.is_safe_sql("SELECT * FROM customers LIMIT 10")
            
            # Test executor
            executor = ExecutorAgent(":memory:")
            result = executor.run_query("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            
            # Test summarizer
            summarizer = SummarizerAgent()
            summary = summarizer.summarize_results([{"name": "Test"}], "Test query")
            
            if plan and is_safe and result.get("success") and summary:
                return {
                    "status": "passed",
                    "message": "All agents working",
                    "details": {"agents_tested": 4}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Some agents failed",
                    "details": {"plan": bool(plan), "is_safe": is_safe, "result": bool(result.get("success")), "summary": bool(summary)}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Agents test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_pdf_exporter(self) -> Dict[str, Any]:
        """Test PDF exporter"""
        try:
            from backend.pdf_exporter import PDFExporter
            
            pdf_exporter = PDFExporter()
            test_data = {
                "timestamp": "2025-01-01T00:00:00",
                "user": "test_user",
                "query": "Test query",
                "sql": "SELECT * FROM test",
                "summary": "Test summary",
                "results": [{"name": "Test"}],
                "results_count": 1,
                "query_time": 0.1,
                "guards": {"total_guards": 0},
                "guards_count": 0,
                "agent_timings": {},
                "llm_interactions": [],
                "total_time": 0.1,
                "total_time_ms": 100,
                "total_llm_time": 0.05,
                "total_llm_time_ms": 50,
                "total_vectordb_time": 0.02,
                "total_vectordb_time_ms": 20,
                "total_database_time": 0.03,
                "total_database_time_ms": 30
            }
            
            pdf_content = pdf_exporter.generate_query_report(test_data)
            
            if pdf_content and len(pdf_content) > 1000:
                return {
                    "status": "passed",
                    "message": "PDF exporter working",
                    "details": {"pdf_size_bytes": len(pdf_content)}
                }
            else:
                return {
                    "status": "failed",
                    "message": "PDF exporter failed",
                    "details": {"pdf_size_bytes": len(pdf_content) if pdf_content else 0}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"PDF exporter test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_response_time(self) -> Dict[str, Any]:
        """Test response time"""
        try:
            import time
            
            start_time = time.time()
            
            # Simulate a quick operation
            from backend.planner import PlannerAgent
            schema_tables = {"customers": ["id", "name"]}
            planner = PlannerAgent(schema_tables)
            planner.analyze_query("Find customers")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if duration < 1.0:
                return {
                    "status": "passed",
                    "message": f"Response time acceptable ({duration:.3f}s)",
                    "details": {"duration": duration}
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Response time too slow ({duration:.3f}s)",
                    "details": {"duration": duration}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Response time test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_memory_usage(self) -> Dict[str, Any]:
        """Test memory usage"""
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb < 500:  # Less than 500MB
                return {
                    "status": "passed",
                    "message": f"Memory usage acceptable ({memory_mb:.1f}MB)",
                    "details": {"memory_mb": memory_mb}
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Memory usage too high ({memory_mb:.1f}MB)",
                    "details": {"memory_mb": memory_mb}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Memory usage test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_concurrent_queries(self) -> Dict[str, Any]:
        """Test concurrent query handling"""
        try:
            import threading
            import time
            
            results = []
            errors = []
            
            def run_query():
                try:
                    from backend.planner import PlannerAgent
                    schema_tables = {"customers": ["id", "name"]}
                    planner = PlannerAgent(schema_tables)
                    result = planner.analyze_query("Find customers")
                    results.append(result)
                except Exception as e:
                    errors.append(str(e))
            
            # Run 3 concurrent queries
            threads = []
            for i in range(3):
                thread = threading.Thread(target=run_query)
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            if len(errors) == 0 and len(results) == 3:
                return {
                    "status": "passed",
                    "message": "Concurrent queries handled successfully",
                    "details": {"queries_completed": len(results), "errors": len(errors)}
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Concurrent queries failed ({len(errors)} errors)",
                    "details": {"queries_completed": len(results), "errors": errors}
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Concurrent queries test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _calculate_overall_status(self):
        """Calculate overall test status"""
        passed_count = 0
        failed_count = 0
        error_count = 0
        total_count = 0
        
        for test_name, result in self.test_results.items():
            total_count += 1
            status = result.get("status", "unknown")
            
            if status == "passed":
                passed_count += 1
            elif status == "failed":
                failed_count += 1
            elif status == "error":
                error_count += 1
        
        if error_count > 0:
            self.overall_status = "error"
        elif failed_count > 0:
            self.overall_status = "failed"
        elif passed_count == total_count:
            self.overall_status = "passed"
        else:
            self.overall_status = "partial"
    
    def _generate_test_report(self) -> Dict[str, Any]:
        """Generate comprehensive test report"""
        return {
            "overall_status": self.overall_status,
            "test_duration": self.end_time - self.start_time if self.end_time else 0,
            "test_results": self.test_results,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": sum(1 for r in self.test_results.values() if r.get("status") == "passed"),
                "failed": sum(1 for r in self.test_results.values() if r.get("status") == "failed"),
                "errors": sum(1 for r in self.test_results.values() if r.get("status") == "error")
            }
        }

def run_backend_tests() -> Dict[str, Any]:
    """Run all backend tests and return report"""
    test_runner = BackendTestRunner()
    return test_runner.run_all_tests()

if __name__ == "__main__":
    # Run tests and print results
    report = run_backend_tests()
    print("Backend Test Report:")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Duration: {report['test_duration']:.2f} seconds")
    print(f"Summary: {report['summary']}")
    
    # Print detailed results
    for test_name, result in report['test_results'].items():
        status_icon = {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(result.get("status"), "❓")
        print(f"{status_icon} {test_name}: {result.get('message', 'No message')}")
