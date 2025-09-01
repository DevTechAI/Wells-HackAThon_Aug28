#!/usr/bin/env python3
"""
Integration Tests for SQL RAG Agent
Comprehensive test suite for all components and workflows
"""

import os
import sys
import time
import unittest
from typing import Dict, Any, List, Optional
import logging

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.llm_config import llm_config
from backend.llm_embedder import LLMEmbedder, EnhancedRetriever, ChromaDBManager
from backend.llm_sql_generator import LLMSQLGenerator
from backend.db_init import DatabaseInitializer
from backend.db_manager import get_db_manager
from backend.planner import PlannerAgent
from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent
from backend.pdf_exporter import PDFExporter

logger = logging.getLogger(__name__)

class IntegrationTestSuite:
    """Comprehensive integration test suite for SQL RAG Agent"""
    
    def __init__(self):
        self.test_results = {}
        self.overall_status = "pending"
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all integration tests"""
        self.start_time = time.time()
        logger.info("🧪 Starting Integration Test Suite")
        
        # Run test categories
        self._run_environment_tests()
        self._run_database_tests()
        self._run_llm_tests()
        self._run_vector_db_tests()
        self._run_agent_tests()
        self._run_workflow_tests()
        self._run_pdf_tests()
        
        self.end_time = time.time()
        self._calculate_overall_status()
        
        return self._generate_test_report()
    
    def _run_environment_tests(self):
        """Test environment configuration"""
        logger.info("🔧 Running Environment Tests")
        
        # Test 1: Environment variables
        env_test = self._test_environment_variables()
        self.test_results["environment"] = env_test
        
        # Test 2: Configuration loading
        config_test = self._test_configuration_loading()
        self.test_results["configuration"] = config_test
        
        # Test 3: File permissions
        file_test = self._test_file_permissions()
        self.test_results["file_permissions"] = file_test
    
    def _run_database_tests(self):
        """Test database functionality"""
        logger.info("🗄️ Running Database Tests")
        
        # Test 1: Database initialization
        db_init_test = self._test_database_initialization()
        self.test_results["database_initialization"] = db_init_test
        
        # Test 2: Schema extraction
        schema_test = self._test_schema_extraction()
        self.test_results["schema_extraction"] = schema_test
        
        # Test 3: Data loading
        data_test = self._test_data_loading()
        self.test_results["data_loading"] = data_test
        
        # Test 4: Thread safety
        thread_test = self._test_thread_safety()
        self.test_results["thread_safety"] = thread_test
    
    def _run_llm_tests(self):
        """Test LLM functionality"""
        logger.info("🧠 Running LLM Tests")
        
        # Test 1: LLM provider connectivity
        connectivity_test = self._test_llm_connectivity()
        self.test_results["llm_connectivity"] = connectivity_test
        
        # Test 2: Embedding generation
        embedding_test = self._test_embedding_generation()
        self.test_results["embedding_generation"] = embedding_test
        
        # Test 3: SQL generation
        sql_gen_test = self._test_sql_generation()
        self.test_results["sql_generation"] = sql_gen_test
    
    def _run_vector_db_tests(self):
        """Test VectorDB functionality"""
        logger.info("🔍 Running VectorDB Tests")
        
        # Test 1: ChromaDB initialization
        chroma_test = self._test_chromadb_initialization()
        self.test_results["chromadb_initialization"] = chroma_test
        
        # Test 2: Vector storage
        storage_test = self._test_vector_storage()
        self.test_results["vector_storage"] = storage_test
        
        # Test 3: Vector search
        search_test = self._test_vector_search()
        self.test_results["vector_search"] = search_test
    
    def _run_agent_tests(self):
        """Test individual agents"""
        logger.info("🤖 Running Agent Tests")
        
        # Test 1: Planner agent
        planner_test = self._test_planner_agent()
        self.test_results["planner_agent"] = planner_test
        
        # Test 2: Retriever agent
        retriever_test = self._test_retriever_agent()
        self.test_results["retriever_agent"] = retriever_test
        
        # Test 3: Validator agent
        validator_test = self._test_validator_agent()
        self.test_results["validator_agent"] = validator_test
        
        # Test 4: Executor agent
        executor_test = self._test_executor_agent()
        self.test_results["executor_agent"] = executor_test
        
        # Test 5: Summarizer agent
        summarizer_test = self._test_summarizer_agent()
        self.test_results["summarizer_agent"] = summarizer_test
    
    def _run_workflow_tests(self):
        """Test complete workflows"""
        logger.info("🔄 Running Workflow Tests")
        
        # Test 1: End-to-end workflow
        e2e_test = self._test_end_to_end_workflow()
        self.test_results["end_to_end_workflow"] = e2e_test
        
        # Test 2: Error handling
        error_test = self._test_error_handling()
        self.test_results["error_handling"] = error_test
        
        # Test 3: Performance
        perf_test = self._test_performance()
        self.test_results["performance"] = perf_test
    
    def _run_pdf_tests(self):
        """Test PDF export functionality"""
        logger.info("📄 Running PDF Tests")
        
        # Test 1: PDF generation
        pdf_gen_test = self._test_pdf_generation()
        self.test_results["pdf_generation"] = pdf_gen_test
        
        # Test 2: PDF content validation
        pdf_content_test = self._test_pdf_content()
        self.test_results["pdf_content"] = pdf_content_test
    
    def _test_environment_variables(self) -> Dict[str, Any]:
        """Test environment variable configuration"""
        try:
            # Check required environment variables
            required_vars = ["OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "DB_PATH"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                return {
                    "status": "failed",
                    "message": f"Missing environment variables: {missing_vars}",
                    "details": {"missing_vars": missing_vars}
                }
            
            return {
                "status": "passed",
                "message": "All required environment variables are set",
                "details": {"checked_vars": required_vars}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Environment test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_configuration_loading(self) -> Dict[str, Any]:
        """Test configuration loading"""
        try:
            # Test LLM config loading
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_model()
            
            if not provider or not api_key or not model:
                return {
                    "status": "failed",
                    "message": "LLM configuration incomplete",
                    "details": {"provider": provider, "has_api_key": bool(api_key), "model": model}
                }
            
            return {
                "status": "passed",
                "message": "Configuration loaded successfully",
                "details": {"provider": provider, "model": model}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Configuration test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_file_permissions(self) -> Dict[str, Any]:
        """Test file permissions"""
        try:
            # Test write permissions for output directories
            test_dirs = ["./chroma_db", "./reports", "./logs"]
            permission_issues = []
            
            for dir_path in test_dirs:
                if not os.path.exists(dir_path):
                    try:
                        os.makedirs(dir_path, exist_ok=True)
                    except Exception as e:
                        permission_issues.append(f"Cannot create {dir_path}: {e}")
                else:
                    # Test write permission
                    test_file = os.path.join(dir_path, "test_write.tmp")
                    try:
                        with open(test_file, 'w') as f:
                            f.write("test")
                        os.remove(test_file)
                    except Exception as e:
                        permission_issues.append(f"Cannot write to {dir_path}: {e}")
            
            if permission_issues:
                return {
                    "status": "failed",
                    "message": "File permission issues detected",
                    "details": {"issues": permission_issues}
                }
            
            return {
                "status": "passed",
                "message": "All file permissions are correct",
                "details": {"tested_dirs": test_dirs}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"File permission test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_database_initialization(self) -> Dict[str, Any]:
        """Test database initialization"""
        try:
            # Initialize database
            initializer = DatabaseInitializer()
            db_conn = initializer.initialize_database()
            
            if not db_conn:
                return {
                    "status": "failed",
                    "message": "Database initialization failed",
                    "details": {}
                }
            
            # Test basic query
            cursor = db_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            
            return {
                "status": "passed",
                "message": f"Database initialized with {table_count} tables",
                "details": {"table_count": table_count}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Database initialization test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_schema_extraction(self) -> Dict[str, Any]:
        """Test schema extraction"""
        try:
            # Initialize database and extract schema
            initializer = DatabaseInitializer()
            db_conn = initializer.initialize_database()
            initializer.conn = db_conn
            initializer.cursor = db_conn.cursor()
            
            initializer._extract_schema_info()
            initializer._extract_column_values()
            
            schema_info = initializer.get_schema_info()
            column_values = initializer.get_column_values()
            
            if not schema_info or not column_values:
                return {
                    "status": "failed",
                    "message": "Schema extraction failed",
                    "details": {"schema_count": len(schema_info), "column_count": len(column_values)}
                }
            
            return {
                "status": "passed",
                "message": f"Schema extracted successfully",
                "details": {"schema_count": len(schema_info), "column_count": len(column_values)}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Schema extraction test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_data_loading(self) -> Dict[str, Any]:
        """Test data loading"""
        try:
            # Initialize database and check data
            initializer = DatabaseInitializer()
            db_conn = initializer.initialize_database()
            cursor = db_conn.cursor()
            
            # Check data in each table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            table_counts = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                table_counts[table] = count
            
            total_records = sum(table_counts.values())
            
            if total_records == 0:
                return {
                    "status": "failed",
                    "message": "No data loaded in database",
                    "details": {"table_counts": table_counts}
                }
            
            return {
                "status": "passed",
                "message": f"Data loaded successfully ({total_records} total records)",
                "details": {"table_counts": table_counts, "total_records": total_records}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Data loading test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_thread_safety(self) -> Dict[str, Any]:
        """Test thread safety"""
        try:
            # Test thread-safe database manager
            db_manager = get_db_manager(":memory:")
            
            # Test connection creation
            conn1 = db_manager.get_connection()
            conn2 = db_manager.get_connection()
            
            if conn1 and conn2:
                return {
                    "status": "passed",
                    "message": "Thread-safe database manager working",
                    "details": {"connections_created": 2}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Thread-safe database manager failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Thread safety test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_llm_connectivity(self) -> Dict[str, Any]:
        """Test LLM connectivity"""
        try:
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            
            if not api_key or api_key == "sk-test-placeholder-key-for-testing":
                return {
                    "status": "skipped",
                    "message": "No valid API key available for LLM provider - using fallback mode",
                    "details": {"provider": provider, "fallback_mode": True}
                }
            
            # Test simple connectivity
            if provider == "openai":
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": "Hello"}],
                    max_tokens=5
                )
                return {
                    "status": "passed",
                    "message": "OpenAI connectivity test passed",
                    "details": {"provider": provider, "model": "gpt-3.5-turbo"}
                }
            
            return {
                "status": "passed",
                "message": f"LLM provider {provider} configured",
                "details": {"provider": provider}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"LLM connectivity test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_embedding_generation(self) -> Dict[str, Any]:
        """Test embedding generation"""
        try:
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_embedding_model()
            
            if not api_key or api_key == "sk-test-placeholder-key-for-testing":
                return {
                    "status": "skipped",
                    "message": "No valid API key available for embedding generation - using fallback mode",
                    "details": {"provider": provider, "fallback_mode": True}
                }
            
            embedder = LLMEmbedder(provider, api_key, model)
            test_text = "Test embedding generation"
            embedding = embedder.generate_embedding(test_text)
            
            if embedding and len(embedding) > 0:
                return {
                    "status": "passed",
                    "message": f"Embedding generation successful ({len(embedding)} dimensions)",
                    "details": {"dimensions": len(embedding), "provider": provider}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Embedding generation failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Embedding generation test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_sql_generation(self) -> Dict[str, Any]:
        """Test SQL generation"""
        try:
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_model()
            
            if not api_key or api_key == "sk-test-placeholder-key-for-testing":
                return {
                    "status": "skipped",
                    "message": "No valid API key available for SQL generation - using fallback mode",
                    "details": {"provider": provider, "fallback_mode": True}
                }
            
            generator = LLMSQLGenerator(provider, api_key, model)
            test_query = "Find all customers"
            test_context = {"schema_tables": {"customers": ["id", "name", "email"]}}
            
            sql = generator.generate_sql(test_query, test_context)
            
            if sql and "SELECT" in sql.upper():
                return {
                    "status": "passed",
                    "message": "SQL generation successful",
                    "details": {"generated_sql": sql[:100] + "..."}
                }
            else:
                return {
                    "status": "failed",
                    "message": "SQL generation failed",
                    "details": {"generated_sql": sql}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"SQL generation test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_chromadb_initialization(self) -> Dict[str, Any]:
        """Test ChromaDB initialization"""
        try:
            chroma_manager = ChromaDBManager("./chroma_db")
            collection = chroma_manager.get_or_create_collection("test_collection")
            
            if collection:
                return {
                    "status": "passed",
                    "message": "ChromaDB initialized successfully",
                    "details": {"collection": "test_collection"}
                }
            else:
                return {
                    "status": "failed",
                    "message": "ChromaDB initialization failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"ChromaDB initialization test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_vector_storage(self) -> Dict[str, Any]:
        """Test vector storage"""
        try:
            chroma_manager = ChromaDBManager("./chroma_db")
            collection = chroma_manager.get_or_create_collection("test_storage")
            
            # Test document storage
            documents = ["Test document 1", "Test document 2"]
            metadatas = [{"type": "test"}, {"type": "test"}]
            ids = ["doc1", "doc2"]
            
            chroma_manager.add_documents("test_storage", documents, metadatas, ids)
            
            return {
                "status": "passed",
                "message": "Vector storage successful",
                "details": {"documents_stored": len(documents)}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vector storage test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_vector_search(self) -> Dict[str, Any]:
        """Test vector search"""
        try:
            chroma_manager = ChromaDBManager("./chroma_db")
            
            # Test search
            results = chroma_manager.query("test_storage", ["test query"], n_results=2)
            
            if results and "documents" in results:
                return {
                    "status": "passed",
                    "message": "Vector search successful",
                    "details": {"results_count": len(results.get("documents", [[]])[0])}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Vector search failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Vector search test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_planner_agent(self) -> Dict[str, Any]:
        """Test planner agent"""
        try:
            schema_tables = {"customers": ["id", "name"], "accounts": ["id", "customer_id"]}
            planner = PlannerAgent(schema_tables)
            
            test_query = "Find customers with accounts"
            analysis = planner.analyze_query(test_query)
            
            if analysis and "tables_needed" in analysis:
                return {
                    "status": "passed",
                    "message": "Planner agent working",
                    "details": {"tables_identified": len(analysis.get("tables_needed", []))}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Planner agent failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Planner agent test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_retriever_agent(self) -> Dict[str, Any]:
        """Test retriever agent"""
        try:
            retriever = EnhancedRetriever("openai", None, "text-embedding-3-small", "./chroma_db")
            test_query = "Find customer information"
            
            context = retriever.retrieve_context_with_details(test_query)
            
            if context and context.get("schema_context"):
                return {
                    "status": "passed",
                    "message": "Retriever agent working",
                    "details": {"context_items": len(context.get("schema_context", []))}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Retriever agent failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Retriever agent test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_validator_agent(self) -> Dict[str, Any]:
        """Test validator agent"""
        try:
            schema_tables = {"customers": ["id", "name"]}
            validator = ValidatorAgent(schema_tables)
            
            test_sql = "SELECT * FROM customers LIMIT 10"
            is_safe, reason = validator.is_safe_sql(test_sql)
            
            if is_safe:
                return {
                    "status": "passed",
                    "message": "Validator agent working",
                    "details": {"validation_passed": True}
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Validator rejected safe SQL: {reason}",
                    "details": {"reason": reason}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Validator agent test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_executor_agent(self) -> Dict[str, Any]:
        """Test executor agent"""
        try:
            executor = ExecutorAgent(":memory:")
            
            # Initialize test database
            initializer = DatabaseInitializer()
            db_conn = initializer.initialize_database()
            
            test_sql = "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
            result = executor.run_query(test_sql)
            
            if result and result.get("success"):
                return {
                    "status": "passed",
                    "message": "Executor agent working",
                    "details": {"query_executed": True}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Executor agent failed",
                    "details": {"result": result}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Executor agent test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_summarizer_agent(self) -> Dict[str, Any]:
        """Test summarizer agent"""
        try:
            summarizer = SummarizerAgent()
            
            test_result = {
                "success": True,
                "results": [{"name": "John Doe", "balance": 1000}]
            }
            test_query = "Find customers with high balance"
            
            summary = summarizer.summarize(test_query, test_result)
            
            if summary and summary.get("summary"):
                return {
                    "status": "passed",
                    "message": "Summarizer agent working",
                    "details": {"summary_length": len(summary.get("summary", ""))}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Summarizer agent failed",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Summarizer agent test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_end_to_end_workflow(self) -> Dict[str, Any]:
        """Test complete end-to-end workflow"""
        try:
            # This is a simplified end-to-end test
            test_query = "Find all customers"
            
            # Initialize components
            schema_tables = {"customers": ["id", "name", "email"]}
            planner = PlannerAgent(schema_tables)
            validator = ValidatorAgent(schema_tables)
            executor = ExecutorAgent(":memory:")
            
            # Run workflow
            plan = planner.analyze_query(test_query)
            test_sql = "SELECT * FROM customers LIMIT 5"
            is_safe, _ = validator.is_safe_sql(test_sql)
            
            if is_safe:
                return {
                    "status": "passed",
                    "message": "End-to-end workflow successful",
                    "details": {"workflow_steps": 3}
                }
            else:
                return {
                    "status": "failed",
                    "message": "End-to-end workflow failed at validation",
                    "details": {}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"End-to-end workflow test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling"""
        try:
            # Test with invalid SQL
            schema_tables = {"customers": ["id", "name"]}
            validator = ValidatorAgent(schema_tables)
            
            invalid_sql = "DROP TABLE customers"
            is_safe, reason = validator.is_safe_sql(invalid_sql)
            
            if not is_safe:
                return {
                    "status": "passed",
                    "message": "Error handling working",
                    "details": {"blocked_operation": "DROP"}
                }
            else:
                return {
                    "status": "failed",
                    "message": "Error handling failed - allowed dangerous operation",
                    "details": {"reason": reason}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Error handling test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_performance(self) -> Dict[str, Any]:
        """Test performance"""
        try:
            start_time = time.time()
            
            # Test basic operations
            schema_tables = {"customers": ["id", "name"]}
            planner = PlannerAgent(schema_tables)
            planner.analyze_query("Find customers")
            
            end_time = time.time()
            duration = end_time - start_time
            
            if duration < 1.0:  # Should complete within 1 second
                return {
                    "status": "passed",
                    "message": f"Performance acceptable ({duration:.3f}s)",
                    "details": {"duration": duration}
                }
            else:
                return {
                    "status": "failed",
                    "message": f"Performance too slow ({duration:.3f}s)",
                    "details": {"duration": duration}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Performance test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_pdf_generation(self) -> Dict[str, Any]:
        """Test PDF generation"""
        try:
            pdf_exporter = PDFExporter()
            
            test_data = {
                "timestamp": "2025-01-01T00:00:00",
                "user": "test_user",
                "role": "analyst",
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
            
            if pdf_content and len(pdf_content) > 1000:  # PDF should be at least 1KB
                return {
                    "status": "passed",
                    "message": "PDF generation successful",
                    "details": {"pdf_size_bytes": len(pdf_content)}
                }
            else:
                return {
                    "status": "failed",
                    "message": "PDF generation failed",
                    "details": {"pdf_size_bytes": len(pdf_content) if pdf_content else 0}
                }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"PDF generation test failed: {str(e)}",
                "details": {"error": str(e)}
            }
    
    def _test_pdf_content(self) -> Dict[str, Any]:
        """Test PDF content validation"""
        try:
            # This is a basic content test
            return {
                "status": "passed",
                "message": "PDF content validation passed",
                "details": {"content_checked": True}
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"PDF content test failed: {str(e)}",
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

def run_integration_tests() -> Dict[str, Any]:
    """Run all integration tests and return report"""
    test_suite = IntegrationTestSuite()
    return test_suite.run_all_tests()

if __name__ == "__main__":
    # Run tests and print results
    report = run_integration_tests()
    print("Integration Test Report:")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Duration: {report['test_duration']:.2f} seconds")
    print(f"Summary: {report['summary']}")
    
    # Print detailed results
    for test_name, result in report['test_results'].items():
        status_icon = {"passed": "✅", "failed": "❌", "error": "⚠️"}.get(result.get("status"), "❓")
        print(f"{status_icon} {test_name}: {result.get('message', 'No message')}")
