#!/usr/bin/env python3
"""
LLM-Neutral Embedder for SQL RAG Agent
Supports multiple LLM providers for embeddings
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMEmbedder:
    """
    LLM-neutral embedder that can work with any LLM provider
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, 
                 model_name: str = "text-embedding-ada-002"):
        """
        Initialize embedder with specified provider
        
        Args:
            provider: LLM provider ('openai', 'anthropic', 'google', 'local')
            api_key: API key for the provider
            model_name: Model name for embeddings
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.model_name = model_name
        self.client = None
        
        logger.info(f"🧠 Initializing LLM Embedder with provider: {provider}")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        try:
            if self.provider == "openai":
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
                logger.info("✅ OpenAI client initialized")
                
            elif self.provider == "anthropic":
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("✅ Anthropic client initialized")
                
            elif self.provider == "google":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai
                logger.info("✅ Google Generative AI client initialized")
                
            elif self.provider == "local":
                # For local models like Ollama
                self.client = None  # Will be handled differently
                logger.info("✅ Local LLM client initialized")
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.provider} client: {e}")
            raise
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        try:
            if self.provider == "openai":
                response = self.client.embeddings.create(
                    input=text,
                    model=self.model_name
                )
                return response.data[0].embedding
                
            elif self.provider == "anthropic":
                response = self.client.embeddings.create(
                    input=text,
                    model=self.model_name
                )
                return response.data[0].embedding
                
            elif self.provider == "google":
                response = self.client.embed_content(
                    model=self.model_name,
                    content=text
                )
                return response.embedding
                
            elif self.provider == "local":
                # For local models, you might use a different approach
                # This is a placeholder for local embedding generation
                logger.warning("⚠️ Local embedding generation not implemented")
                return [0.0] * 1536  # Placeholder embedding
                
        except Exception as e:
            logger.error(f"❌ Error generating embedding: {e}")
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        embeddings = []
        for text in texts:
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
        return embeddings

class ChromaDBManager:
    """ChromaDB manager for vector storage"""
    
    def __init__(self, persist_dir: str = "./chroma_db"):
        self.persist_dir = persist_dir
        self.client = None
        self.collections = {}
        
        logger.info(f"🗄️ Initializing ChromaDB manager with persist_dir: {persist_dir}")
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize ChromaDB client"""
        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            logger.info("✅ ChromaDB client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB client: {e}")
            raise
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a collection"""
        try:
            collection = self.client.get_or_create_collection(name=name)
            self.collections[name] = collection
            logger.info(f"✅ Collection '{name}' ready")
            return collection
        except Exception as e:
            logger.error(f"❌ Error getting/creating collection '{name}': {e}")
            raise
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict[str, Any]], ids: List[str]):
        """Add documents to collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
        except Exception as e:
            logger.error(f"❌ Error adding documents to collection '{collection_name}': {e}")
            raise
    
    def query(self, collection_name: str, query_texts: List[str], 
              n_results: int = 5) -> Dict[str, Any]:
        """Query collection"""
        try:
            collection = self.get_or_create_collection(collection_name)
            results = collection.query(
                query_texts=query_texts,
                n_results=n_results
            )
            logger.info(f"✅ Queried collection '{collection_name}' with {len(query_texts)} queries")
            return results
        except Exception as e:
            logger.error(f"❌ Error querying collection '{collection_name}': {e}")
            raise

class EnhancedRetriever:
    """
    Enhanced retriever using LLM-neutral embeddings
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None,
                 model_name: str = "text-embedding-ada-002", 
                 chroma_persist_dir: str = "./chroma_db"):
        """
        Initialize enhanced retriever
        
        Args:
            provider: LLM provider for embeddings
            api_key: API key for the provider
            model_name: Model name for embeddings
            chroma_persist_dir: ChromaDB persistence directory
        """
        self.embedder = LLMEmbedder(provider, api_key, model_name)
        self.chroma_manager = ChromaDBManager(chroma_persist_dir)
        
        logger.info(f"🔍 Enhanced Retriever initialized with {provider} embeddings")
    
    def populate_vector_db(self, schema_data: List[Dict[str, Any]], 
                          collection_name: str = "banking_schema"):
        """Populate vector database with schema information"""
        try:
            documents = []
            metadatas = []
            ids = []
            
            for i, item in enumerate(schema_data):
                content = item.get("content", "")
                metadata = item.get("metadata", {})
                
                documents.append(content)
                metadatas.append(metadata)
                ids.append(f"doc_{i}")
            
            # Generate embeddings
            embeddings = self.embedder.generate_embeddings_batch(documents)
            
            # Add to ChromaDB
            self.chroma_manager.add_documents(
                collection_name=collection_name,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            logger.info(f"✅ Populated vector DB with {len(documents)} documents")
            
        except Exception as e:
            logger.error(f"❌ Error populating vector DB: {e}")
            raise
    
    def retrieve_context(self, query: str, collection_name: str = "banking_schema", 
                        n_results: int = 5) -> List[Dict[str, Any]]:
        """Retrieve relevant context for a query"""
        try:
            # Generate query embedding
            query_embedding = self.embedder.generate_embedding(query)
            
            # Query ChromaDB
            results = self.chroma_manager.query(
                collection_name=collection_name,
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            context = []
            if results.get("documents"):
                for i, doc in enumerate(results["documents"][0]):
                    context.append({
                        "content": doc,
                        "metadata": results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {},
                        "distance": results.get("distances", [[]])[0][i] if results.get("distances") else 0.0
                    })
            
            logger.info(f"✅ Retrieved {len(context)} context items for query")
            return context
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            raise
    
    def retrieve_context_with_details(self, query: str, collection_name: str = "banking_schema",
                                     n_results: int = 5) -> Dict[str, Any]:
        """Retrieve context with detailed information"""
        try:
            context = self.retrieve_context(query, collection_name, n_results)
            
            # Analyze query for required components
            query_analysis = self._analyze_query(query)
            
            # Get value hints
            value_hints = self._get_value_hints(query_analysis, context)
            
            # Get exemplars
            exemplars = self._get_exemplars(query, context)
            
            result = {
                "schema_context": context,
                "query_analysis": query_analysis,
                "value_hints": value_hints,
                "exemplars": exemplars,
                "chromadb_interactions": {
                    "collection": collection_name,
                    "query": query,
                    "results_count": len(context)
                }
            }
            
            logger.info(f"✅ Enhanced context retrieval completed")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error in enhanced context retrieval: {e}")
            raise
    
    def _analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query to identify required components"""
        # This is a simplified analysis - can be enhanced
        analysis = {
            "required_tables": [],
            "required_columns": [],
            "operations": [],
            "conditions": [],
            "where_conditions": []
        }
        
        query_lower = query.lower()
        
        # Detect tables (simplified)
        table_keywords = ["customer", "account", "transaction", "branch", "employee"]
        for keyword in table_keywords:
            if keyword in query_lower:
                analysis["required_tables"].append(keyword + "s")
        
        # Detect operations
        if any(word in query_lower for word in ["count", "sum", "average", "avg"]):
            analysis["operations"].append("aggregate")
        
        if "where" in query_lower or any(word in query_lower for word in ["with", "having"]):
            analysis["conditions"].append("filter")
        
        return analysis
    
    def _get_value_hints(self, query_analysis: Dict[str, Any], context: List[Dict[str, Any]]) -> List[str]:
        """Extract value hints from context"""
        hints = []
        for item in context:
            metadata = item.get("metadata", {})
            if "distinct_values" in metadata:
                hints.extend(metadata["distinct_values"][:5])  # Limit to 5 values
        return hints[:10]  # Limit total hints
    
    def _get_exemplars(self, query: str, context: List[Dict[str, Any]]) -> List[str]:
        """Get similar query exemplars"""
        exemplars = []
        for item in context:
            metadata = item.get("metadata", {})
            if "exemplar_query" in metadata:
                exemplars.append(metadata["exemplar_query"])
        return exemplars[:3]  # Limit to 3 exemplars
