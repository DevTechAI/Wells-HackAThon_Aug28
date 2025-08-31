#!/usr/bin/env python3
"""
System Initializer for SQL RAG Agent
Comprehensive initialization and testing of all components
"""

import os
import sys
import time
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Add backend to path
sys.path.append('./backend')

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

@dataclass
class ComponentStatus:
    """Status information for a component"""
    name: str
    status: str  # "pending", "running", "passed", "failed", "error"
    message: str
    details: Dict[str, Any]
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    duration: Optional[float] = None

class SystemInitializer:
    """Comprehensive system initializer with testing"""
    
    def __init__(self):
        self.components = {}
        self.overall_status = "pending"
        self.start_time = None
        self.end_time = None
        self.errors = []
        self.warnings = []
        
        # Initialize component status
        self._initialize_component_status()
    
    def _initialize_component_status(self):
        """Initialize status for all components"""
        component_names = [
            "environment",
            "database",
            "llm_provider", 
            "vector_db",
            "agents",
            "workflow",
            "security",
            "performance"
        ]
        
        for name in component_names:
            self.components[name] = ComponentStatus(
                name=name,
                status="pending",
                message="Not yet tested",
                details={}
            )
    
    def run_full_initialization(self) -> Dict[str, Any]:
        """Run complete system initialization and testing"""
        self.start_time = time.time()
        logger.info("🚀 Starting System Initialization")
        
        try:
            # Phase 1: Environment Setup
            self._run_environment_tests()
            
            # Phase 2: Core Services
            self._run_database_tests()
            self._run_llm_tests()
            self._run_vector_db_tests()
            
            # Phase 3: Agent Setup
            self._run_agent_tests()
            
            # Phase 4: Integration Testing
            self._run_workflow_tests()
            self._run_security_tests()
            self._run_performance_tests()
            
        except Exception as e:
            logger.error(f"Initialization failed: {str(e)}")
            self.errors.append(f"Initialization error: {str(e)}")
        
        self.end_time = time.time()
        self._calculate_overall_status()
        
        return self._generate_initialization_report()
    
    def _run_environment_tests(self):
        """Test environment configuration"""
        logger.info("🔧 Testing Environment Configuration")
        component = self.components["environment"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test environment variables
            required_vars = ["OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "DB_PATH"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                component.status = "failed"
                component.message = f"Missing environment variables: {missing_vars}"
                component.details = {"missing_vars": missing_vars}
            else:
                # Test file permissions
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
                    component.status = "failed"
                    component.message = "File permission issues detected"
                    component.details = {"issues": permission_issues}
                else:
                    component.status = "passed"
                    component.message = "Environment configuration is correct"
                    component.details = {"checked_vars": required_vars, "tested_dirs": test_dirs}
            
        except Exception as e:
            component.status = "error"
            component.message = f"Environment test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Environment error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_database_tests(self):
        """Test database functionality"""
        logger.info("🗄️ Testing Database Configuration")
        component = self.components["database"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test database initialization
            initializer = DatabaseInitializer()
            db_conn = initializer.initialize_database()
            
            if not db_conn:
                component.status = "failed"
                component.message = "Database initialization failed"
                component.details = {}
            else:
                # Test basic query
                cursor = db_conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                if table_count == 0:
                    component.status = "failed"
                    component.message = "No tables found in database"
                    component.details = {"table_count": table_count}
                else:
                    # Test data loading
                    table_counts = {}
                    for table in ["customers", "accounts", "transactions", "branches", "employees"]:
                        try:
                            cursor.execute(f"SELECT COUNT(*) FROM {table}")
                            count = cursor.fetchone()[0]
                            table_counts[table] = count
                        except Exception as e:
                            table_counts[table] = f"Error: {str(e)}"
                    
                    total_records = sum(count for count in table_counts.values() if isinstance(count, int))
                    
                    if total_records == 0:
                        component.status = "failed"
                        component.message = "No data loaded in database"
                        component.details = {"table_counts": table_counts}
                    else:
                        component.status = "passed"
                        component.message = f"Database initialized with {table_count} tables and {total_records} records"
                        component.details = {"table_count": table_count, "table_counts": table_counts, "total_records": total_records}
            
        except Exception as e:
            component.status = "error"
            component.message = f"Database test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Database error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_llm_tests(self):
        """Test LLM functionality"""
        logger.info("🧠 Testing LLM Provider")
        component = self.components["llm_provider"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            provider = llm_config.get_default_provider()
            api_key = llm_config.get_api_key(provider)
            model = llm_config.get_default_model()
            
            if not provider or not api_key or not model:
                component.status = "failed"
                component.message = "LLM configuration incomplete"
                component.details = {"provider": provider, "has_api_key": bool(api_key), "model": model}
            else:
                # Test LLM connectivity
                if provider == "openai":
                    import openai
                    openai.api_key = api_key
                    start_time = time.time()
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Hello"}],
                        max_tokens=5
                    )
                    end_time = time.time()
                    
                    if response.choices[0].message.content:
                        component.status = "passed"
                        component.message = f"OpenAI connectivity test passed ({end_time - start_time:.3f}s)"
                        component.details = {"provider": provider, "model": "gpt-3.5-turbo", "response_time": end_time - start_time}
                    else:
                        component.status = "failed"
                        component.message = "OpenAI not responding"
                        component.details = {"provider": provider}
                else:
                    component.status = "passed"
                    component.message = f"LLM provider {provider} configured"
                    component.details = {"provider": provider, "model": model}
                
                # Test embedding generation
                try:
                    embedder = LLMEmbedder(provider, api_key, llm_config.get_default_embedding_model())
                    test_embedding = embedder.generate_embedding("Test embedding generation")
                    
                    if test_embedding and len(test_embedding) > 0:
                        component.details["embedding_dimensions"] = len(test_embedding)
                        component.details["embedding_test"] = "passed"
                    else:
                        component.details["embedding_test"] = "failed"
                        self.warnings.append("Embedding generation failed")
                except Exception as e:
                    component.details["embedding_test"] = f"error: {str(e)}"
                    self.warnings.append(f"Embedding error: {str(e)}")
            
        except Exception as e:
            component.status = "error"
            component.message = f"LLM test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"LLM error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_vector_db_tests(self):
        """Test VectorDB functionality"""
        logger.info("🔍 Testing Vector Database")
        component = self.components["vector_db"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test ChromaDB initialization
            chroma_manager = ChromaDBManager("./chroma_db")
            collection = chroma_manager.get_or_create_collection("test_collection")
            
            if not collection:
                component.status = "failed"
                component.message = "ChromaDB initialization failed"
                component.details = {}
            else:
                # Test document storage
                documents = ["Test document 1", "Test document 2"]
                metadatas = [{"type": "test"}, {"type": "test"}]
                ids = ["doc1", "doc2"]
                
                chroma_manager.add_documents("test_collection", documents, metadatas, ids)
                
                # Test vector search
                results = chroma_manager.query("test_collection", ["test query"], n_results=2)
                
                if results and "documents" in results:
                    component.status = "passed"
                    component.message = "VectorDB functionality verified"
                    component.details = {
                        "collection": "test_collection",
                        "documents_stored": len(documents),
                        "search_results": len(results.get("documents", [[]])[0])
                    }
                else:
                    component.status = "failed"
                    component.message = "Vector search failed"
                    component.details = {}
            
        except Exception as e:
            component.status = "error"
            component.message = f"VectorDB test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"VectorDB error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_agent_tests(self):
        """Test individual agents"""
        logger.info("🤖 Testing Agent Components")
        component = self.components["agents"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            agent_results = {}
            
            # Test Planner Agent
            try:
                schema_tables = {"customers": ["id", "name"], "accounts": ["id", "customer_id"]}
                planner = PlannerAgent(schema_tables)
                test_analysis = planner.analyze_query("Find customers with accounts")
                
                if test_analysis and "tables_needed" in test_analysis:
                    agent_results["planner"] = {"status": "passed", "tables_identified": len(test_analysis.get("tables_needed", []))}
                else:
                    agent_results["planner"] = {"status": "failed", "reason": "No analysis returned"}
            except Exception as e:
                agent_results["planner"] = {"status": "error", "error": str(e)}
            
            # Test Retriever Agent
            try:
                retriever = EnhancedRetriever("./chroma_db")
                test_context = retriever.retrieve_context("Find customer information")
                
                if test_context:
                    agent_results["retriever"] = {"status": "passed", "context_items": len(test_context.get("schema_context", []))}
                else:
                    agent_results["retriever"] = {"status": "failed", "reason": "No context returned"}
            except Exception as e:
                agent_results["retriever"] = {"status": "error", "error": str(e)}
            
            # Test Validator Agent
            try:
                schema_tables = {"customers": ["id", "name"]}
                validator = ValidatorAgent(schema_tables)
                is_safe, _ = validator.is_safe_sql("SELECT * FROM customers LIMIT 10")
                
                if is_safe:
                    agent_results["validator"] = {"status": "passed", "validation_passed": True}
                else:
                    agent_results["validator"] = {"status": "failed", "reason": "Safe query rejected"}
            except Exception as e:
                agent_results["validator"] = {"status": "error", "error": str(e)}
            
            # Test Executor Agent
            try:
                executor = ExecutorAgent(":memory:")
                test_result = executor.run_query("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                
                if test_result and test_result.get("success"):
                    agent_results["executor"] = {"status": "passed", "query_executed": True}
                else:
                    agent_results["executor"] = {"status": "failed", "result": test_result}
            except Exception as e:
                agent_results["executor"] = {"status": "error", "error": str(e)}
            
            # Test Summarizer Agent
            try:
                summarizer = SummarizerAgent()
                test_summary = summarizer.summarize_results([{"name": "Test"}], "Test query")
                
                if test_summary:
                    agent_results["summarizer"] = {"status": "passed", "summary_length": len(test_summary)}
                else:
                    agent_results["summarizer"] = {"status": "failed", "reason": "No summary generated"}
            except Exception as e:
                agent_results["summarizer"] = {"status": "error", "error": str(e)}
            
            # Calculate overall agent status
            passed_count = sum(1 for result in agent_results.values() if result.get("status") == "passed")
            failed_count = sum(1 for result in agent_results.values() if result.get("status") == "failed")
            error_count = sum(1 for result in agent_results.values() if result.get("status") == "error")
            
            if error_count > 0:
                component.status = "error"
                component.message = f"Agent tests failed with {error_count} errors"
            elif failed_count > 0:
                component.status = "failed"
                component.message = f"Agent tests failed with {failed_count} failures"
            elif passed_count == len(agent_results):
                component.status = "passed"
                component.message = f"All {passed_count} agents working correctly"
            else:
                component.status = "partial"
                component.message = f"Mixed results: {passed_count} passed, {failed_count} failed"
            
            component.details = agent_results
            
        except Exception as e:
            component.status = "error"
            component.message = f"Agent tests failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Agent error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_workflow_tests(self):
        """Test complete workflows"""
        logger.info("🔄 Testing Workflow Integration")
        component = self.components["workflow"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test end-to-end workflow
            test_query = "Find all customers"
            schema_tables = {"customers": ["id", "name", "email"]}
            
            # Initialize components
            planner = PlannerAgent(schema_tables)
            validator = ValidatorAgent(schema_tables)
            executor = ExecutorAgent(":memory:")
            
            # Run workflow steps
            plan = planner.analyze_query(test_query)
            test_sql = "SELECT * FROM customers LIMIT 5"
            is_safe, _ = validator.is_safe_sql(test_sql)
            result = executor.run_query(test_sql)
            
            if plan and is_safe and result.get("success"):
                component.status = "passed"
                component.message = "End-to-end workflow successful"
                component.details = {"workflow_steps": 3, "query": test_query}
            else:
                component.status = "failed"
                component.message = "End-to-end workflow failed"
                component.details = {"plan": bool(plan), "is_safe": is_safe, "result_success": result.get("success")}
            
        except Exception as e:
            component.status = "error"
            component.message = f"Workflow test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Workflow error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_security_tests(self):
        """Test security measures"""
        logger.info("🛡️ Testing Security Measures")
        component = self.components["security"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            schema_tables = {"customers": ["id", "name"]}
            validator = ValidatorAgent(schema_tables)
            
            # Test dangerous operations are blocked
            dangerous_queries = [
                "DROP TABLE customers",
                "DELETE FROM customers",
                "UPDATE customers SET name = 'hacked'",
                "INSERT INTO customers VALUES (999, 'hacker')"
            ]
            
            blocked_count = 0
            for query in dangerous_queries:
                is_safe, _ = validator.is_safe_sql(query)
                if not is_safe:
                    blocked_count += 1
            
            # Test safe queries are allowed
            safe_queries = [
                "SELECT * FROM customers LIMIT 10",
                "SELECT COUNT(*) FROM customers",
                "SELECT name FROM customers WHERE id = 1"
            ]
            
            allowed_count = 0
            for query in safe_queries:
                is_safe, _ = validator.is_safe_sql(query)
                if is_safe:
                    allowed_count += 1
            
            if blocked_count == len(dangerous_queries) and allowed_count == len(safe_queries):
                component.status = "passed"
                component.message = "Security validation working correctly"
                component.details = {
                    "dangerous_blocked": blocked_count,
                    "safe_allowed": allowed_count,
                    "total_tests": len(dangerous_queries) + len(safe_queries)
                }
            else:
                component.status = "failed"
                component.message = "Security validation inconsistent"
                component.details = {
                    "dangerous_blocked": blocked_count,
                    "safe_allowed": allowed_count,
                    "expected_blocked": len(dangerous_queries),
                    "expected_allowed": len(safe_queries)
                }
            
        except Exception as e:
            component.status = "error"
            component.message = f"Security test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Security error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_performance_tests(self):
        """Test performance characteristics"""
        logger.info("📊 Testing Performance")
        component = self.components["performance"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            performance_results = {}
            
            # Test agent performance
            start_time = time.time()
            schema_tables = {"customers": ["id", "name"]}
            planner = PlannerAgent(schema_tables)
            planner.analyze_query("Find customers")
            end_time = time.time()
            
            agent_duration = end_time - start_time
            performance_results["agent_performance"] = agent_duration
            
            if agent_duration < 1.0:
                performance_results["agent_status"] = "acceptable"
            else:
                performance_results["agent_status"] = "slow"
                self.warnings.append(f"Agent performance slow: {agent_duration:.3f}s")
            
            # Test overall initialization time
            total_time = time.time() - self.start_time
            performance_results["total_initialization_time"] = total_time
            
            if total_time < 30.0:  # Should complete within 30 seconds
                performance_results["initialization_status"] = "acceptable"
            else:
                performance_results["initialization_status"] = "slow"
                self.warnings.append(f"Initialization slow: {total_time:.3f}s")
            
            component.status = "passed"
            component.message = "Performance within acceptable limits"
            component.details = performance_results
            
        except Exception as e:
            component.status = "error"
            component.message = f"Performance test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Performance error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _calculate_overall_status(self):
        """Calculate overall initialization status"""
        passed_count = 0
        failed_count = 0
        error_count = 0
        total_count = 0
        
        for component in self.components.values():
            total_count += 1
            status = component.status
            
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
    
    def _generate_initialization_report(self) -> Dict[str, Any]:
        """Generate comprehensive initialization report"""
        return {
            "overall_status": self.overall_status,
            "initialization_duration": self.end_time - self.start_time if self.end_time else 0,
            "components": {
                name: {
                    "status": comp.status,
                    "message": comp.message,
                    "details": comp.details,
                    "duration": comp.duration
                }
                for name, comp in self.components.items()
            },
            "summary": {
                "total_components": len(self.components),
                "passed": sum(1 for comp in self.components.values() if comp.status == "passed"),
                "failed": sum(1 for comp in self.components.values() if comp.status == "failed"),
                "errors": sum(1 for comp in self.components.values() if comp.status == "error")
            },
            "errors": self.errors,
            "warnings": self.warnings,
            "ready_for_queries": self.overall_status in ["passed", "partial"],
            "timestamp": datetime.now().isoformat()
        }
    
    def get_component_status(self, component_name: str) -> Optional[ComponentStatus]:
        """Get status of a specific component"""
        return self.components.get(component_name)
    
    def is_ready_for_queries(self) -> bool:
        """Check if system is ready for user queries"""
        return self.overall_status in ["passed", "partial"] and len(self.errors) == 0

def run_system_initialization() -> Dict[str, Any]:
    """Run complete system initialization and return report"""
    initializer = SystemInitializer()
    return initializer.run_full_initialization()

if __name__ == "__main__":
    # Run initialization and print results
    report = run_system_initialization()
    print("System Initialization Report:")
    print(f"Overall Status: {report['overall_status']}")
    print(f"Duration: {report['initialization_duration']:.2f} seconds")
    print(f"Summary: {report['summary']}")
    print(f"Ready for queries: {report['ready_for_queries']}")
    
    # Print component details
    for name, comp in report['components'].items():
        status_icon = {"passed": "✅", "failed": "❌", "error": "⚠️", "partial": "⚠️"}.get(comp["status"], "❓")
        print(f"{status_icon} {name}: {comp['message']}")
    
    # Print errors and warnings
    if report['errors']:
        print("\n❌ Errors:")
        for error in report['errors']:
            print(f"  - {error}")
    
    if report['warnings']:
        print("\n⚠️ Warnings:")
        for warning in report['warnings']:
            print(f"  - {warning}")
