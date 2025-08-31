#!/usr/bin/env python3
"""
Gemini Health Checker Module
Monitors the health of SQLite database and Google AI API
"""

import os
import time
import requests
from typing import Dict, Any, Optional
import logging
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HealthStatus(Enum):
    HEALTHY = "healthy"
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class ComponentHealth:
    def __init__(self, name: str, status: HealthStatus, message: str, details: Dict[str, Any] = None):
        self.name = name
        self.status = status
        self.message = message
        self.details = details or {}
        self.timestamp = time.time()

class GeminiHealthChecker:
    def __init__(self, api_key: str, db_connection=None):
        """
        Initialize Gemini health checker
        
        Args:
            api_key: Google AI API key
            db_connection: SQLite database connection
        """
        self.api_key = api_key
        self.db_connection = db_connection
        self.gemini_url = "https://generativelanguage.googleapis.com"
        
        logger.info(f"🔍 Initializing Gemini health checker")
        logger.info(f"🌐 Gemini API URL: {self.gemini_url}")
    
    def check_gemini_health(self) -> ComponentHealth:
        """Check Gemini API health"""
        logger.info(f"🔍 Checking Gemini API health...")
        
        try:
            import google.generativeai as genai
            
            # Test Gemini API connection
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-1.5-pro')
            
            # Test with a simple message
            start_time = time.time()
            response = model.generate_content("Say 'Hello'")
            response_time = time.time() - start_time
            
            if response and response.text:
                return ComponentHealth(
                    name="Gemini API",
                    status=HealthStatus.HEALTHY,
                    message=f"✅ Gemini API healthy - Response time: {response_time:.2f}s",
                    details={
                        "response_time_ms": response_time * 1000,
                        "model": "gemini-1.5-pro",
                        "api_url": self.gemini_url
                    }
                )
            else:
                return ComponentHealth(
                    name="Gemini API",
                    status=HealthStatus.WARNING,
                    message="⚠️ Gemini API responded but no content",
                    details={
                        "api_url": self.gemini_url,
                        "error": "No content in response"
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Gemini API Error: {e}")
            return ComponentHealth(
                name="Gemini API",
                status=HealthStatus.ERROR,
                message=f"❌ Gemini API Error: {str(e)}",
                details={
                    "error": str(e),
                    "api_url": self.gemini_url
                }
            )
    
    def check_gemini_embeddings_health(self) -> ComponentHealth:
        """Check Gemini embeddings API health"""
        logger.info(f"🔍 Checking Gemini embeddings health...")
        
        try:
            import google.generativeai as genai
            
            # Test Gemini embeddings API
            genai.configure(api_key=self.api_key)
            embedding_model = genai.get_model("text-embedding-004")
            
            start_time = time.time()
            result = embedding_model.embed_content("test")
            response_time = time.time() - start_time
            
            if result and 'embedding' in result:
                embedding = result['embedding']
                return ComponentHealth(
                    name="Gemini Embeddings",
                    status=HealthStatus.HEALTHY,
                    message=f"✅ Gemini embeddings healthy - {len(embedding)} dimensions",
                    details={
                        "response_time_ms": response_time * 1000,
                        "model": "text-embedding-004",
                        "dimensions": len(embedding),
                        "api_url": self.gemini_url
                    }
                )
            else:
                return ComponentHealth(
                    name="Gemini Embeddings",
                    status=HealthStatus.WARNING,
                    message="⚠️ Gemini embeddings responded but no embeddings",
                    details={
                        "api_url": self.gemini_url,
                        "error": "No embeddings in response"
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ Gemini Embeddings Error: {e}")
            return ComponentHealth(
                name="Gemini Embeddings",
                status=HealthStatus.ERROR,
                message=f"❌ Gemini Embeddings Error: {str(e)}",
                details={
                    "error": str(e),
                    "api_url": self.gemini_url
                }
            )
    
    def check_sqlite_health(self) -> ComponentHealth:
        """Check SQLite database health"""
        logger.info(f"🔍 Checking SQLite database health...")
        
        try:
            if self.db_connection:
                cursor = self.db_connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
                table_count = cursor.fetchone()[0]
                
                return ComponentHealth(
                    name="SQLite Database",
                    status=HealthStatus.HEALTHY,
                    message=f"✅ SQLite database healthy - {table_count} tables",
                    details={
                        "table_count": table_count,
                        "connection_type": "in-memory"
                    }
                )
            else:
                return ComponentHealth(
                    name="SQLite Database",
                    status=HealthStatus.WARNING,
                    message="⚠️ No database connection available",
                    details={
                        "error": "No database connection"
                    }
                )
                
        except Exception as e:
            logger.error(f"❌ SQLite Database Error: {e}")
            return ComponentHealth(
                name="SQLite Database",
                status=HealthStatus.ERROR,
                message=f"❌ SQLite Database Error: {str(e)}",
                details={
                    "error": str(e)
                }
            )
    
    def check_chromadb_health(self) -> ComponentHealth:
        """Check ChromaDB health"""
        logger.info(f"🔍 Checking ChromaDB health...")
        
        try:
            import chromadb
            
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
            logger.error(f"❌ ChromaDB Error: {e}")
            return ComponentHealth(
                name="ChromaDB",
                status=HealthStatus.ERROR,
                message=f"❌ ChromaDB Error: {str(e)}",
                details={
                    "error": str(e),
                    "path": "./chroma_db"
                }
            )
    
    def check_all_components(self) -> Dict[str, ComponentHealth]:
        """
        Check health of all components
        
        Returns:
            Dictionary of component health status
        """
        logger.info(f"🔍 Checking all component health...")
        
        results = {}
        
        # Check Gemini API
        results["gemini_api"] = self.check_gemini_health()
        
        # Check Gemini Embeddings
        results["gemini_embeddings"] = self.check_gemini_embeddings_health()
        
        # Check SQLite Database
        results["sqlite"] = self.check_sqlite_health()
        
        # Check ChromaDB
        results["chromadb"] = self.check_chromadb_health()
        
        return results
    
    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get overall health summary
        
        Returns:
            Health summary dictionary
        """
        health_results = self.check_all_components()
        
        # Count statuses
        status_counts = {}
        for status in HealthStatus:
            status_counts[status.value] = 0
        
        for component in health_results.values():
            status_counts[component.status.value] += 1
        
        # Determine overall status
        if status_counts[HealthStatus.ERROR.value] > 0:
            overall_status = HealthStatus.ERROR
        elif status_counts[HealthStatus.WARNING.value] > 0:
            overall_status = HealthStatus.WARNING
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "overall_status": overall_status.value,
            "status_counts": status_counts,
            "components": health_results,
            "timestamp": time.time()
        }

def check_gemini_health(api_key: str, db_connection=None) -> Dict[str, Any]:
    """
    Convenience function to check Gemini health
    
    Args:
        api_key: Google AI API key
        db_connection: SQLite database connection
        
    Returns:
        Health summary
    """
    checker = GeminiHealthChecker(api_key=api_key, db_connection=db_connection)
    return checker.get_health_summary()

if __name__ == "__main__":
    # Test the Gemini health checker
    api_key = os.getenv("GOOGLE_AI_API_KEY")
    
    if api_key:
        print("🔍 Testing Gemini health checker...")
        try:
            result = check_gemini_health(api_key)
            print(f"\n🎉 Gemini health check completed!")
            print(f"Overall Status: {result['overall_status']}")
            print(f"Status Counts: {result['status_counts']}")
        except Exception as e:
            print(f"❌ Gemini health check failed: {e}")
    else:
        print("❌ GOOGLE_AI_API_KEY not found in environment variables")
