#!/usr/bin/env python3
"""
Embedder Module using Ollama for embeddings
Integrates with ChromaDB for vector storage and retrieval
"""

import requests
import json
import time
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaEmbedder:
    def __init__(self, model_name: str = "llama2", base_url: str = "http://localhost:11434"):
        """
        Initialize Ollama embedder
        
        Args:
            model_name: Ollama model to use for embeddings
            base_url: Ollama server URL
        """
        self.model_name = model_name
        self.base_url = base_url
        self.embedding_url = f"{base_url}/api/embeddings"
        self.client = None
        self.collection = None
        
        logger.info(f"🔧 Initializing Ollama embedder with model: {model_name}")
        logger.info(f"🌐 Ollama server URL: {base_url}")
        
        # Test connection
        self._test_connection()
        
    def _test_connection(self):
        """Test connection to Ollama server"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=15)
            if response.status_code == 200:
                models = response.json().get("models", [])
                logger.info(f"✅ Connected to Ollama server")
                logger.info(f"📋 Available models: {[model['name'] for model in models]}")
                
                # Check if our model is available
                model_names = [model['name'] for model in models]
                if self.model_name not in model_names:
                    logger.warning(f"⚠️ Model '{self.model_name}' not found in available models")
                    logger.info(f"📋 Available models: {model_names}")
                    # Try to use first available model
                    if model_names:
                        self.model_name = model_names[0]
                        logger.info(f"🔄 Using available model: {self.model_name}")
            else:
                logger.error(f"❌ Failed to connect to Ollama server: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Error connecting to Ollama server: {e}")
            logger.info("💡 Make sure Ollama is running: ollama serve")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text using Ollama
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            logger.info(f"🧠 Generating embedding for text: {text[:50]}...")
            
            payload = {
                "model": self.model_name,
                "prompt": text
            }
            
            response = requests.post(self.embedding_url, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding")
                if embedding:
                    logger.info(f"✅ Generated embedding: {len(embedding)} dimensions")
                    return embedding
                else:
                    logger.error(f"❌ No embedding in response: {result}")
                    return None
            else:
                logger.error(f"❌ Embedding request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embeddings (None for failed ones)
        """
        logger.info(f"🔄 Generating embeddings for {len(texts)} texts")
        embeddings = []
        
        for i, text in enumerate(texts):
            logger.info(f"📝 Processing text {i+1}/{len(texts)}: {text[:50]}...")
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
            
            # Small delay to avoid overwhelming the server
            time.sleep(0.1)
        
        successful = sum(1 for emb in embeddings if emb is not None)
        logger.info(f"✅ Generated {successful}/{len(texts)} embeddings successfully")
        
        return embeddings

class ChromaDBManager:
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "banking_schema"):
        """
        Initialize ChromaDB manager
        
        Args:
            persist_directory: Directory to persist ChromaDB data
            collection_name: Name of the collection
        """
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
        logger.info(f"🗄️ Initializing ChromaDB manager")
        logger.info(f"📁 Persist directory: {persist_directory}")
        logger.info(f"📋 Collection name: {collection_name}")
        
        self._initialize_chroma()
    
    def _initialize_chroma(self):
        """Initialize ChromaDB client and collection"""
        try:
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            logger.info(f"✅ ChromaDB client initialized")
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"📋 Using existing collection: {self.collection_name}")
            except:
                self.collection = self.client.create_collection(name=self.collection_name)
                logger.info(f"📋 Created new collection: {self.collection_name}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing ChromaDB: {e}")
            raise
    
    def add_documents(self, documents: List[str], metadatas: List[Dict] = None, ids: List[str] = None):
        """
        Add documents to ChromaDB collection
        
        Args:
            documents: List of document texts
            metadatas: List of metadata dictionaries
            ids: List of document IDs
        """
        try:
            logger.info(f"📝 Adding {len(documents)} documents to ChromaDB")
            
            if ids is None:
                ids = [f"doc_{i}" for i in range(len(documents))]
            
            if metadatas is None:
                metadatas = [{"type": "schema_info"} for _ in documents]
            
            self.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Successfully added {len(documents)} documents to ChromaDB")
            
        except Exception as e:
            logger.error(f"❌ Error adding documents to ChromaDB: {e}")
            raise
    
    def query_documents(self, query_text: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Query documents from ChromaDB
        
        Args:
            query_text: Query text
            n_results: Number of results to return
            
        Returns:
            Query results
        """
        try:
            logger.info(f"🔍 Querying ChromaDB for: {query_text[:50]}...")
            
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            logger.info(f"✅ Found {len(results['documents'][0])} results")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error querying ChromaDB: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}

class EnhancedRetriever:
    def __init__(self, ollama_model: str = "llama2", chroma_persist_dir: str = "./chroma_db"):
        """
        Enhanced retriever using Ollama embeddings and ChromaDB
        
        Args:
            ollama_model: Ollama model name for embeddings
            chroma_persist_dir: ChromaDB persist directory
        """
        self.embedder = OllamaEmbedder(model_name=ollama_model)
        self.chroma_manager = ChromaDBManager(persist_directory=chroma_persist_dir)
        
        logger.info(f"🚀 Enhanced retriever initialized")
        logger.info(f"🧠 Using Ollama model: {ollama_model}")
        logger.info(f"🗄️ Using ChromaDB directory: {chroma_persist_dir}")
    
    def populate_vector_db(self, schema_info: Dict, column_values: Dict):
        """
        Populate vector database with schema and column information
        
        Args:
            schema_info: Database schema information
            column_values: Column values dictionary
        """
        try:
            logger.info(f"📊 Populating vector database with schema and column information")
            
            documents = []
            metadatas = []
            ids = []
            
            # Add schema information
            for table_name, schema_data in schema_info.items():
                # CREATE TABLE statement
                create_sql = schema_data['create_sql']
                documents.append(create_sql)
                metadatas.append({
                    "type": "schema",
                    "table": table_name,
                    "content_type": "create_table"
                })
                ids.append(f"schema_{table_name}")
                
                # Column information
                for col_info in schema_data['columns']:
                    col_name, col_type = col_info[1], col_info[2]
                    col_doc = f"Table {table_name} has column {col_name} of type {col_type}"
                    if col_info[5] == 1:  # Primary key
                        col_doc += " (PRIMARY KEY)"
                    
                    documents.append(col_doc)
                    metadatas.append({
                        "type": "schema",
                        "table": table_name,
                        "column": col_name,
                        "content_type": "column_info"
                    })
                    ids.append(f"column_{table_name}_{col_name}")
                
                # Foreign key information
                for fk in schema_data['foreign_keys']:
                    fk_doc = f"Table {table_name} has foreign key {fk[3]} referencing {fk[2]}.{fk[4]}"
                    documents.append(fk_doc)
                    metadatas.append({
                        "type": "schema",
                        "table": table_name,
                        "content_type": "foreign_key"
                    })
                    ids.append(f"fk_{table_name}_{fk[3]}")
            
            # Add column values
            for table_name, columns in column_values.items():
                for col_name, col_data in columns.items():
                    if col_name != 'sample_data':
                        values = col_data['unique_values']
                        value_doc = f"Table {table_name} column {col_name} has values: {', '.join(map(str, values[:10]))}"
                        if len(values) > 10:
                            value_doc += f" and {len(values) - 10} more"
                        
                        documents.append(value_doc)
                        metadatas.append({
                            "type": "column_values",
                            "table": table_name,
                            "column": col_name,
                            "content_type": "unique_values"
                        })
                        ids.append(f"values_{table_name}_{col_name}")
            
            # Add documents to ChromaDB
            if documents:
                self.chroma_manager.add_documents(documents, metadatas, ids)
                logger.info(f"✅ Added {len(documents)} documents to vector database")
            else:
                logger.warning("⚠️ No documents to add to vector database")
                
        except Exception as e:
            logger.error(f"❌ Error populating vector database: {e}")
            raise
    
    def retrieve_context(self, query: str, n_results: int = 5) -> List[str]:
        """
        Retrieve relevant context for a query
        
        Args:
            query: Natural language query
            n_results: Number of results to retrieve
            
        Returns:
            List of relevant context strings
        """
        try:
            logger.info(f"🔍 Retrieving context for query: {query[:50]}...")
            
            # Query ChromaDB
            results = self.chroma_manager.query_documents(query, n_results)
            
            if results and results['documents'] and results['documents'][0]:
                context = results['documents'][0]
                logger.info(f"✅ Retrieved {len(context)} context items")
                
                # Log metadata for debugging
                if results['metadatas'] and results['metadatas'][0]:
                    for i, metadata in enumerate(results['metadatas'][0]):
                        logger.info(f"📋 Context {i+1}: {metadata.get('content_type', 'unknown')} - {metadata.get('table', 'unknown')}")
                
                return context
            else:
                logger.warning("⚠️ No context retrieved from vector database")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return []

    def retrieve_context_with_details(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant context with detailed ChromaDB and Ollama interaction information
        
        Args:
            query: Natural language query
            n_results: Number of results to retrieve
            
        Returns:
            Dictionary containing context items and detailed interaction information
        """
        try:
            logger.info(f"🔍 Retrieving context with details for query: {query[:50]}...")
            
            # Track Ollama interactions
            ollama_interactions = {
                "embedding_generation": {},
                "model_used": self.embedder.model_name,
                "ollama_url": self.embedder.base_url
            }
            
            # Generate embedding for query
            start_time = time.time()
            query_embedding = self.embedder.generate_embedding(query)
            embedding_time = time.time() - start_time
            
            ollama_interactions["embedding_generation"] = {
                "success": query_embedding is not None,
                "embedding_dimensions": len(query_embedding) if query_embedding else 0,
                "generation_time_ms": round(embedding_time * 1000, 2),
                "query_text": query[:100] + "..." if len(query) > 100 else query
            }
            
            # Track ChromaDB interactions
            chromadb_interactions = {
                "query_execution": {},
                "collection_info": {},
                "vector_search": {}
            }
            
            # Get collection info
            try:
                collection_count = self.chroma_manager.collection.count()
                chromadb_interactions["collection_info"] = {
                    "total_documents": collection_count,
                    "collection_name": self.chroma_manager.collection.name
                }
            except Exception as e:
                chromadb_interactions["collection_info"] = {
                    "error": str(e)
                }
            
            # Query ChromaDB with timing
            start_time = time.time()
            results = self.chroma_manager.query_documents(query, n_results)
            query_time = time.time() - start_time
            
            chromadb_interactions["query_execution"] = {
                "success": results is not None,
                "query_time_ms": round(query_time * 1000, 2),
                "requested_results": n_results,
                "actual_results": len(results['documents'][0]) if results and results['documents'] and results['documents'][0] else 0
            }
            
            # Extract vector search details
            vector_search_details = {}
            if results and results['distances'] and results['distances'][0]:
                distances = results['distances'][0]
                vector_search_details = {
                    "similarity_scores": [round(1 - dist, 4) for dist in distances],
                    "average_similarity": round(1 - sum(distances) / len(distances), 4),
                    "best_match_score": round(1 - min(distances), 4),
                    "worst_match_score": round(1 - max(distances), 4)
                }
            
            chromadb_interactions["vector_search"] = vector_search_details
            
            # Extract context items
            context_items = []
            if results and results['documents'] and results['documents'][0]:
                context_items = results['documents'][0]
                logger.info(f"✅ Retrieved {len(context_items)} context items")
                
                # Log metadata for debugging
                if results['metadatas'] and results['metadatas'][0]:
                    for i, metadata in enumerate(results['metadatas'][0]):
                        logger.info(f"📋 Context {i+1}: {metadata.get('content_type', 'unknown')} - {metadata.get('table', 'unknown')}")
            else:
                logger.warning("⚠️ No context retrieved from vector database")
            
            return {
                "context_items": context_items,
                "chromadb_interactions": chromadb_interactions,
                "ollama_interactions": ollama_interactions,
                "vector_search_details": vector_search_details
            }
                
        except Exception as e:
            logger.error(f"❌ Error retrieving context with details: {e}")
            return {
                "context_items": [],
                "chromadb_interactions": {"error": str(e)},
                "ollama_interactions": {"error": str(e)},
                "vector_search_details": {}
            }

def test_enhanced_retriever():
    """Test the enhanced retriever functionality"""
    try:
        logger.info("🧪 Testing Enhanced Retriever")
        
        # Initialize retriever
        retriever = EnhancedRetriever()
        
        # Test embedding generation
        test_text = "Find all customers with checking accounts"
        embedding = retriever.embedder.generate_embedding(test_text)
        
        if embedding:
            logger.info(f"✅ Embedding test successful: {len(embedding)} dimensions")
        else:
            logger.warning("⚠️ Embedding test failed")
        
        # Test ChromaDB
        test_docs = ["This is a test document", "Another test document"]
        retriever.chroma_manager.add_documents(test_docs)
        
        # Test retrieval
        results = retriever.retrieve_context("test document")
        logger.info(f"✅ Retrieval test successful: {len(results)} results")
        
        logger.info("🎉 Enhanced retriever test completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ Enhanced retriever test failed: {e}")

if __name__ == "__main__":
    test_enhanced_retriever()
