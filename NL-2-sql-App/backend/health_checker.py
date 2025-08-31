#!/usr/bin/env python3
"""
Health Checker Module
Monitors the health of SQLite database and Ollama server
Provides detailed status information and visual indicators
"""

import sqlite3
import requests
import time
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    """Health status enumeration"""
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

@dataclass
class ComponentHealth:
    """Health information for a component"""
    name: str
    status: HealthStatus
    message: str
    details: Dict = None
    last_check: float = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}
        if self.last_check is None:
            self.last_check = time.time()

class HealthChecker:
    def __init__(self, db_connection=None, ollama_url="http://localhost:11434"):
        """
        Initialize health checker
        
        Args:
            db_connection: SQLite database connection
            ollama_url: Ollama server URL
        """
        self.db_connection = db_connection
        self.ollama_url = ollama_url
        self.components = {}
        
        logger.info(f"🔧 Initializing Health Checker")
        logger.info(f"🗄️ Database connection: {'Connected' if db_connection else 'Not provided'}")
        logger.info(f"🧠 Ollama URL: {ollama_url}")
    
    def check_sqlite_health(self) -> ComponentHealth:
        """Check SQLite database health"""
        logger.info(f"🔍 Checking SQLite database health...")
        
        try:
            if not self.db_connection:
                return ComponentHealth(
                    name="SQLite Database",
                    status=HealthStatus.ERROR,
                    message="❌ No database connection provided",
                    details={"error": "Database connection not initialized"}
                )
            
            # Test basic connectivity
            cursor = self.db_connection.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
            if result and result[0] == 1:
                # Get database statistics
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Count total rows
                total_rows = 0
                table_stats = {}
                for table in tables:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_stats[table] = count
                    total_rows += count
                
                # Check for key tables
                key_tables = ['customers', 'accounts', 'branches', 'employees', 'transactions']
                missing_tables = [table for table in key_tables if table not in tables]
                
                if missing_tables:
                    return ComponentHealth(
                        name="SQLite Database",
                        status=HealthStatus.WARNING,
                        message=f"⚠️ Database accessible but missing tables: {', '.join(missing_tables)}",
                        details={
                            "tables": tables,
                            "total_rows": total_rows,
                            "table_stats": table_stats,
                            "missing_tables": missing_tables
                        }
                    )
                else:
                    return ComponentHealth(
                        name="SQLite Database",
                        status=HealthStatus.HEALTHY,
                        message=f"✅ Database healthy - {len(tables)} tables, {total_rows:,} total rows",
                        details={
                            "tables": tables,
                            "total_rows": total_rows,
                            "table_stats": table_stats,
                            "connection_type": "In-Memory SQLite"
                        }
                    )
            else:
                return ComponentHealth(
                    name="SQLite Database",
                    status=HealthStatus.ERROR,
                    message="❌ Database query test failed",
                    details={"error": "Basic query test failed"}
                )
                
        except Exception as e:
            logger.error(f"❌ SQLite health check failed: {e}")
            return ComponentHealth(
                name="SQLite Database",
                status=HealthStatus.ERROR,
                message=f"❌ Database error: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_ollama_health(self) -> ComponentHealth:
        """Check Ollama server health"""
        logger.info(f"🔍 Checking Ollama server health...")
        
        try:
            # Test basic connectivity
            response = requests.get(f"{self.ollama_url}/api/tags", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                
                # Check for required model
                required_model = "llama2"
                has_required_model = any(required_model in model for model in models)
                
                if has_required_model:
                    # Test embedding generation
                    test_payload = {
                        "model": "llama2",
                        "prompt": "test"
                    }
                    
                    embedding_response = requests.post(
                        f"{self.ollama_url}/api/embeddings",
                        json=test_payload,
                        timeout=30  # Increased timeout for embedding generation
                    )
                    
                    if embedding_response.status_code == 200:
                        embedding_data = embedding_response.json()
                        embedding = embedding_data.get("embedding")
                        
                        return ComponentHealth(
                            name="Ollama Server",
                            status=HealthStatus.HEALTHY,
                            message=f"✅ Ollama healthy - {len(models)} models, embeddings working",
                            details={
                                "models": models,
                                "required_model": required_model,
                                "embedding_dimensions": len(embedding) if embedding else 0,
                                "server_url": self.ollama_url
                            }
                        )
                    else:
                        return ComponentHealth(
                            name="Ollama Server",
                            status=HealthStatus.WARNING,
                            message=f"⚠️ Server running but embedding test failed",
                            details={
                                "models": models,
                                "required_model": required_model,
                                "embedding_error": f"Status {embedding_response.status_code}"
                            }
                        )
                else:
                    return ComponentHealth(
                        name="Ollama Server",
                        status=HealthStatus.WARNING,
                        message=f"⚠️ Server running but missing required model '{required_model}'",
                        details={
                            "models": models,
                            "required_model": required_model,
                            "missing_model": True
                        }
                    )
            else:
                return ComponentHealth(
                    name="Ollama Server",
                    status=HealthStatus.ERROR,
                    message=f"❌ Server responded with status {response.status_code}",
                    details={"error": f"HTTP {response.status_code}"}
                )
                
        except requests.exceptions.ConnectionError:
            return ComponentHealth(
                name="Ollama Server",
                status=HealthStatus.ERROR,
                message="❌ Cannot connect to Ollama server",
                details={"error": "Connection refused"}
            )
        except Exception as e:
            logger.error(f"❌ Ollama health check failed: {e}")
            return ComponentHealth(
                name="Ollama Server",
                status=HealthStatus.ERROR,
                message=f"❌ Ollama error: {str(e)}",
                details={"error": str(e)}
            )
    
    def check_chromadb_health(self) -> ComponentHealth:
        """Check ChromaDB health"""
        logger.info(f"🔍 Checking ChromaDB health...")
        
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Try to connect to ChromaDB
            client = chromadb.PersistentClient(path="./chroma_db")
            
            # Get collections
            collections = client.list_collections()
            
            if collections:
                # Check if our collection exists
                collection_names = [col.name for col in collections]
                has_banking_collection = any("banking" in name.lower() for name in collection_names)
                
                if has_banking_collection:
                    return ComponentHealth(
                        name="ChromaDB",
                        status=HealthStatus.HEALTHY,
                        message=f"✅ ChromaDB healthy - {len(collections)} collections",
                        details={
                            "collections": collection_names,
                            "path": "./chroma_db"
                        }
                    )
                else:
                    return ComponentHealth(
                        name="ChromaDB",
                        status=HealthStatus.WARNING,
                        message=f"⚠️ ChromaDB accessible but no banking collection found",
                        details={
                            "collections": collection_names,
                            "path": "./chroma_db"
                        }
                    )
            else:
                return ComponentHealth(
                    name="ChromaDB",
                    status=HealthStatus.WARNING,
                    message="⚠️ ChromaDB accessible but no collections found",
                    details={
                        "collections": [],
                        "path": "./chroma_db"
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ ChromaDB health check failed: {e}")
            return ComponentHealth(
                name="ChromaDB",
                status=HealthStatus.ERROR,
                message=f"❌ ChromaDB error: {str(e)}",
                details={"error": str(e)}
            )
    
    def run_full_health_check(self) -> Dict[str, ComponentHealth]:
        """Run comprehensive health check on all components"""
        logger.info(f"🚀 Running full health check...")
        
        health_results = {}
        
        # Check SQLite
        health_results["sqlite"] = self.check_sqlite_health()
        
        # Check Ollama
        health_results["ollama"] = self.check_ollama_health()
        
        # Check ChromaDB
        health_results["chromadb"] = self.check_chromadb_health()
        
        # Store results
        self.components = health_results
        
        # Log summary
        healthy_count = sum(1 for h in health_results.values() if h.status == HealthStatus.HEALTHY)
        warning_count = sum(1 for h in health_results.values() if h.status == HealthStatus.WARNING)
        error_count = sum(1 for h in health_results.values() if h.status == HealthStatus.ERROR)
        
        logger.info(f"📊 Health Check Summary:")
        logger.info(f"  ✅ Healthy: {healthy_count}")
        logger.info(f"  ⚠️ Warnings: {warning_count}")
        logger.info(f"  ❌ Errors: {error_count}")
        
        return health_results
    
    def get_overall_status(self) -> HealthStatus:
        """Get overall system health status"""
        if not self.components:
            return HealthStatus.UNKNOWN
        
        # If any component has an error, overall status is error
        if any(h.status == HealthStatus.ERROR for h in self.components.values()):
            return HealthStatus.ERROR
        
        # If any component has a warning, overall status is warning
        if any(h.status == HealthStatus.WARNING for h in self.components.values()):
            return HealthStatus.WARNING
        
        # All components are healthy
        return HealthStatus.HEALTHY
    
    def get_status_summary(self) -> Dict:
        """Get a summary of all component statuses"""
        return {
            "overall_status": self.get_overall_status().value,
            "components": {
                name: {
                    "status": health.status.value,
                    "message": health.message,
                    "details": health.details
                }
                for name, health in self.components.items()
            },
            "last_check": time.time()
        }

def create_health_checker(db_connection=None) -> HealthChecker:
    """Convenience function to create a health checker"""
    return HealthChecker(db_connection=db_connection)

if __name__ == "__main__":
    # Test the health checker
    try:
        checker = HealthChecker()
        results = checker.run_full_health_check()
        
        print(f"\n🎉 Health Check Test Completed!")
        print(f"📊 Overall Status: {checker.get_overall_status().value}")
        
        for name, health in results.items():
            print(f"\n{name.upper()}:")
            print(f"  Status: {health.status.value}")
            print(f"  Message: {health.message}")
            if health.details:
                print(f"  Details: {health.details}")
        
    except Exception as e:
        print(f"❌ Health check test failed: {e}")
        import traceback
        traceback.print_exc()
