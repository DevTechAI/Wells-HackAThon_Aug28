#!/usr/bin/env python3
"""
ChromaDB Singleton Manager
Implements a singleton pattern for ChromaDB client to prevent multiple initializations
"""

import os
import logging
import threading
from typing import Optional, Dict, Any, List
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChromaDBSingleton:
    """
    Singleton class for ChromaDB client management
    Ensures only one ChromaDB client instance exists across the application
    """
    
    _instance = None
    _lock = threading.Lock()
    _client = None
    _collections = {}
    _initialized = False
    
    def __new__(cls, persist_dir: str = "./chroma_db"):
        """Create or return existing singleton instance"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ChromaDBSingleton, cls).__new__(cls)
                    cls._instance._persist_dir = persist_dir
                    cls._instance._initialize_client()
        return cls._instance
    
    def _initialize_client(self):
        """Initialize ChromaDB client (only once)"""
        if self._initialized:
            logger.info("ℹ️ ChromaDB client already initialized, reusing existing instance")
            return
            
        try:
            logger.info(f"🗄️ Initializing ChromaDB singleton client with persist_dir: {self._persist_dir}")
            
            # Create the client
            self._client = chromadb.PersistentClient(
                path=self._persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test the connection by listing collections
            try:
                collections = self._client.list_collections()
                logger.info(f"✅ ChromaDB singleton client initialized successfully with {len(collections)} existing collections")
                
                # Log existing collections for debugging
                for col in collections:
                    logger.info(f"   📋 Found collection: {col.name} (count: {col.count()})")
                    self._collections[col.name] = col
                    
            except Exception as list_error:
                logger.warning(f"⚠️ Could not list collections, but client created: {list_error}")
                logger.info("✅ ChromaDB singleton client initialized (collections may be empty)")
            
            self._initialized = True
            logger.info("✅ ChromaDB singleton client ready for use")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB singleton client: {e}")
            logger.warning("⚠️ ChromaDB singleton initialization failed, continuing without vector storage")
            self._client = None
            self._initialized = True  # Mark as initialized to prevent retry loops
    
    def get_client(self) -> Optional[chromadb.PersistentClient]:
        """Get the ChromaDB client instance"""
        return self._client
    
    def is_initialized(self) -> bool:
        """Check if the client is initialized"""
        return self._initialized and self._client is not None
    
    def get_or_create_collection(self, name: str) -> Optional[chromadb.Collection]:
        """Get or create a collection with singleton client"""
        if not self.is_initialized():
            logger.warning("⚠️ ChromaDB singleton client not available, skipping collection operation")
            return None
        
        # Check if collection is already cached
        if name in self._collections:
            logger.info(f"✅ Using cached collection '{name}'")
            return self._collections[name]
        
        try:
            # First try to get existing collection
            try:
                collection = self._client.get_collection(name=name)
                logger.info(f"✅ Retrieved existing collection '{name}'")
                self._collections[name] = collection
                return collection
            except Exception as get_error:
                logger.info(f"ℹ️ Collection '{name}' not found, creating new one: {get_error}")
            
            # If collection doesn't exist, create it
            try:
                collection = self._client.create_collection(name=name)
                logger.info(f"✅ Created new collection '{name}'")
                self._collections[name] = collection
                return collection
            except Exception as create_error:
                # Handle case where collection was created by another process
                if "already exists" in str(create_error).lower():
                    logger.info(f"ℹ️ Collection '{name}' already exists, getting it")
                    try:
                        collection = self._client.get_collection(name=name)
                        logger.info(f"✅ Retrieved existing collection '{name}'")
                        self._collections[name] = collection
                        return collection
                    except Exception as final_error:
                        logger.error(f"❌ Failed to get collection '{name}' after creation error: {final_error}")
                        return None
                else:
                    logger.error(f"❌ Failed to create collection '{name}': {create_error}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Error with collection '{name}': {e}")
            logger.warning(f"⚠️ Continuing without collection '{name}'")
            return None
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict[str, Any]], ids: List[str]) -> bool:
        """Add documents to collection using singleton client"""
        if not self.is_initialized():
            logger.warning("⚠️ ChromaDB singleton client not available, skipping document addition")
            return False
        
        try:
            collection = self.get_or_create_collection(collection_name)
            if collection is None:
                logger.warning(f"⚠️ Collection '{collection_name}' not available, skipping document addition")
                return False
                
            # Add documents
            try:
                collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                logger.info(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
                return True
            except Exception as add_error:
                logger.error(f"❌ Error adding documents to collection '{collection_name}': {add_error}")
                logger.warning(f"⚠️ Continuing without adding documents to collection '{collection_name}'")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error with collection '{collection_name}': {e}")
            logger.warning(f"⚠️ Continuing without collection '{collection_name}'")
            return False
    
    def query(self, collection_name: str, query_texts: List[str], 
              n_results: int = 5) -> Dict[str, Any]:
        """Query collection using singleton client"""
        if not self.is_initialized():
            logger.warning("⚠️ ChromaDB singleton client not available, skipping query")
            return {"documents": [], "metadatas": [], "distances": []}
        
        try:
            collection = self.get_or_create_collection(collection_name)
            if collection is None:
                logger.warning(f"⚠️ Collection '{collection_name}' not available, skipping query")
                return {"documents": [], "metadatas": [], "distances": []}
                
            try:
                results = collection.query(
                    query_texts=query_texts,
                    n_results=n_results
                )
                logger.info(f"✅ Queried collection '{collection_name}' with {len(query_texts)} queries")
                return results
            except Exception as query_error:
                logger.error(f"❌ Error querying collection '{collection_name}': {query_error}")
                logger.warning(f"⚠️ Returning empty results for collection '{collection_name}'")
                return {"documents": [], "metadatas": [], "distances": []}
                
        except Exception as e:
            logger.error(f"❌ Error with collection '{collection_name}': {e}")
            logger.warning(f"⚠️ Returning empty results for collection '{collection_name}'")
            return {"documents": [], "metadatas": [], "distances": []}
    
    def list_collections(self) -> List[str]:
        """List all collections using singleton client"""
        if not self.is_initialized():
            logger.warning("⚠️ ChromaDB singleton client not available, cannot list collections")
            return []
        
        try:
            collections = self._client.list_collections()
            collection_names = [col.name for col in collections]
            logger.info(f"✅ Listed {len(collection_names)} collections: {collection_names}")
            return collection_names
        except Exception as e:
            logger.error(f"❌ Error listing collections: {e}")
            return []
    
    def get_collection_count(self, collection_name: str) -> int:
        """Get document count for a collection"""
        if not self.is_initialized():
            return 0
        
        try:
            collection = self.get_or_create_collection(collection_name)
            if collection:
                count = collection.count()
                logger.info(f"✅ Collection '{collection_name}' has {count} documents")
                return count
            else:
                return 0
        except Exception as e:
            logger.error(f"❌ Error getting count for collection '{collection_name}': {e}")
            return 0
    
    def reset(self):
        """Reset the singleton instance (for testing purposes)"""
        with self._lock:
            self._instance = None
            self._client = None
            self._collections = {}
            self._initialized = False
            logger.info("🔄 ChromaDB singleton instance reset")

# Global singleton instance
_chromadb_singleton = None

def get_chromadb_singleton(persist_dir: str = "./chroma_db") -> ChromaDBSingleton:
    """Get the global ChromaDB singleton instance"""
    global _chromadb_singleton
    if _chromadb_singleton is None:
        _chromadb_singleton = ChromaDBSingleton(persist_dir)
    return _chromadb_singleton

def reset_chromadb_singleton():
    """Reset the global ChromaDB singleton instance (for testing)"""
    global _chromadb_singleton
    if _chromadb_singleton:
        _chromadb_singleton.reset()
        _chromadb_singleton = None
