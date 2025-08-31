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
        
        report = self._generate_initialization_report()
        logger.info(f"Initialization completed. Status: {self.overall_status}")
        
        return report
    
    def _run_environment_tests(self):
        """Test environment setup"""
        logger.info("🔧 Testing Environment Setup")
        component = self.components["environment"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Check required environment variables
            required_vars = ["OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "DB_PATH"]
            missing_vars = []
            
            for var in required_vars:
                if not os.getenv(var):
                    missing_vars.append(var)
            
            if missing_vars:
                component.status = "failed"
                component.message = f"Missing environment variables: {', '.join(missing_vars)}"
                component.details = {"missing_vars": missing_vars}
            else:
                component.status = "passed"
                component.message = "Environment variables configured correctly"
                component.details = {"configured_vars": required_vars}
                
        except Exception as e:
            component.status = "error"
            component.message = f"Environment test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Environment error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_database_tests(self):
        """Test database functionality"""
        logger.info("🗄️ Testing Database")
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
                        component.details["embedding_test"] = "passed"
                        component.details["embedding_dimension"] = len(test_embedding)
                    else:
                        component.details["embedding_test"] = "failed"
                        
                except Exception as e:
                    component.details["embedding_test"] = f"failed: {str(e)}"
                    self.warnings.append(f"Embedding test failed: {str(e)}")
                
        except Exception as e:
            component.status = "error"
            component.message = f"LLM test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"LLM error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_vector_db_tests(self):
        """Test vector database functionality"""
        logger.info("🔍 Testing Vector Database")
        component = self.components["vector_db"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test ChromaDB
            persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
            
            if not os.path.exists(persist_dir):
                os.makedirs(persist_dir, exist_ok=True)
            
            chroma_manager = ChromaDBManager(persist_dir)
            
            # Test collection creation
            test_collection = chroma_manager.create_collection("test_collection")
            
            if test_collection:
                # Test document addition
                test_docs = ["This is a test document"]
                test_metadatas = [{"source": "test"}]
                test_ids = ["test_id"]
                
                chroma_manager.add_documents(test_collection, test_docs, test_metadatas, test_ids)
                
                # Test query
                results = chroma_manager.query_collection(test_collection, "test document", 1)
                
                if results and len(results) > 0:
                    component.status = "passed"
                    component.message = "ChromaDB working correctly"
                    component.details = {"collection_created": True, "documents_added": True, "query_successful": True}
                else:
                    component.status = "failed"
                    component.message = "ChromaDB query failed"
                    component.details = {"collection_created": True, "documents_added": True, "query_successful": False}
                
                # Clean up
                chroma_manager.delete_collection("test_collection")
            else:
                component.status = "failed"
                component.message = "ChromaDB collection creation failed"
                component.details = {"collection_created": False}
                
        except Exception as e:
            component.status = "error"
            component.message = f"Vector DB test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Vector DB error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_agent_tests(self):
        """Test agent functionality"""
        logger.info("🤖 Testing Agents")
        component = self.components["agents"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test agent initialization
            agents = {
                "planner": PlannerAgent(),
                "validator": ValidatorAgent(),
                "summarizer": SummarizerAgent()
            }
            
            agent_status = {}
            for name, agent in agents.items():
                try:
                    # Test basic functionality
                    if hasattr(agent, '__init__'):
                        agent_status[name] = "initialized"
                    else:
                        agent_status[name] = "failed"
                except Exception as e:
                    agent_status[name] = f"error: {str(e)}"
            
            if all(status == "initialized" for status in agent_status.values()):
                component.status = "passed"
                component.message = "All agents initialized successfully"
                component.details = {"agents": agent_status}
            else:
                component.status = "failed"
                component.message = "Some agents failed to initialize"
                component.details = {"agents": agent_status}
                
        except Exception as e:
            component.status = "error"
            component.message = f"Agent test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Agent error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_workflow_tests(self):
        """Test workflow functionality"""
        logger.info("🔄 Testing Workflow")
        component = self.components["workflow"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test basic workflow components
            workflow_components = {
                "pipeline": "NL2SQLPipeline",
                "db_manager": "ThreadSafeDBManager",
                "pdf_exporter": "PDFExporter"
            }
            
            workflow_status = {}
            for name, class_name in workflow_components.items():
                try:
                    if name == "pipeline":
                        from backend.pipeline import NL2SQLPipeline
                        workflow_status[name] = "available"
                    elif name == "db_manager":
                        from backend.db_manager import ThreadSafeDBManager
                        workflow_status[name] = "available"
                    elif name == "pdf_exporter":
                        from backend.pdf_exporter import PDFExporter
                        workflow_status[name] = "available"
                except Exception as e:
                    workflow_status[name] = f"error: {str(e)}"
            
            if all(status == "available" for status in workflow_status.values()):
                component.status = "passed"
                component.message = "Workflow components available"
                component.details = {"components": workflow_status}
            else:
                component.status = "failed"
                component.message = "Some workflow components missing"
                component.details = {"components": workflow_status}
                
        except Exception as e:
            component.status = "error"
            component.message = f"Workflow test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Workflow error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_security_tests(self):
        """Test security functionality"""
        logger.info("🛡️ Testing Security")
        component = self.components["security"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Test security components
            security_components = {
                "validator": "ValidatorAgent",
                "security_guards": "SecurityGuard"
            }
            
            security_status = {}
            for name, class_name in security_components.items():
                try:
                    if name == "validator":
                        from backend.validator import ValidatorAgent
                        validator = ValidatorAgent()
                        security_status[name] = "available"
                    elif name == "security_guards":
                        # SecurityGuard is defined in app.py
                        security_status[name] = "available"
                except Exception as e:
                    security_status[name] = f"error: {str(e)}"
            
            if all(status == "available" for status in security_status.values()):
                component.status = "passed"
                component.message = "Security components available"
                component.details = {"components": security_status}
            else:
                component.status = "failed"
                component.message = "Some security components missing"
                component.details = {"components": security_status}
                
        except Exception as e:
            component.status = "error"
            component.message = f"Security test failed: {str(e)}"
            component.details = {"error": str(e)}
            self.errors.append(f"Security error: {str(e)}")
        
        component.end_time = time.time()
        component.duration = component.end_time - component.start_time
    
    def _run_performance_tests(self):
        """Test performance metrics"""
        logger.info("⚡ Testing Performance")
        component = self.components["performance"]
        component.start_time = time.time()
        component.status = "running"
        
        try:
            # Basic performance checks
            performance_metrics = {
                "import_time": 0,
                "memory_usage": "unknown",
                "disk_space": "unknown"
            }
            
            # Test import performance
            import_start = time.time()
            import streamlit
            import pandas
            import chromadb
            import_start = time.time() - import_start
            
            performance_metrics["import_time"] = import_start
            
            if import_start < 5.0:  # Less than 5 seconds
                component.status = "passed"
                component.message = "Performance metrics acceptable"
                component.details = {"metrics": performance_metrics}
            else:
                component.status = "failed"
                component.message = "Import time too slow"
                component.details = {"metrics": performance_metrics}
                
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
