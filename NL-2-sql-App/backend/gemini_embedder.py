#!/usr/bin/env python3
"""
Gemini Embedder Module using Google Generative AI for embeddings
Integrates with ChromaDB for vector storage and retrieval
"""

import google.generativeai as genai
import time
from typing import List, Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiEmbedder:
    def __init__(self, api_key: str, model_name: str = "text-embedding-004"):
        """
        Initialize Gemini embedder
        
        Args:
            api_key: Google AI API key
            model_name: Gemini model to use for embeddings
        """
        self.api_key = api_key
        self.model_name = model_name
        genai.configure(api_key=api_key)
        
        logger.info(f"🔧 Initializing Gemini embedder with model: {model_name}")
        
        # Test connection
        self._test_connection()
        
    def _test_connection(self):
        """Test connection to Google AI API"""
        try:
            # Test with a simple embedding
            test_embedding = self.generate_embedding("test")
            if test_embedding:
                logger.info(f"✅ Connected to Google AI API successfully")
            else:
                logger.error(f"❌ Failed to connect to Google AI API")
        except Exception as e:
            logger.error(f"❌ Error connecting to Google AI API: {e}")
            logger.info("💡 Make sure your API key is valid and has sufficient credits")
    
    def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a text using Gemini
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector or None if failed
        """
        try:
            logger.info(f"🧠 Generating Gemini embedding for text: {text[:50]}...")
            
            # Use Gemini's embedding model
            embedding_model = genai.get_model(self.model_name)
            result = embedding_model.embed_content(text)
            
            embedding = result['embedding']
            logger.info(f"✅ Generated Gemini embedding: {len(embedding)} dimensions")
            return embedding
            
        except Exception as e:
            logger.error(f"❌ Error generating Gemini embedding: {e}")
            return None
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            logger.info(f"🧠 Generating embedding {i+1}/{len(texts)}: {text[:50]}...")
            embedding = self.generate_embedding(text)
            embeddings.append(embedding)
            
            # Small delay to avoid rate limiting
            time.sleep(0.1)
        
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
            import chromadb
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

class GeminiEnhancedRetriever:
    def __init__(self, api_key: str, chroma_persist_dir: str = "./chroma_db"):
        """
        Enhanced retriever using Gemini embeddings and ChromaDB
        
        Args:
            api_key: Google AI API key
            chroma_persist_dir: ChromaDB persist directory
        """
        self.embedder = GeminiEmbedder(api_key=api_key)
        self.chroma_manager = ChromaDBManager(persist_directory=chroma_persist_dir)
        
        logger.info(f"🚀 Gemini Enhanced retriever initialized")
        logger.info(f"🧠 Using Gemini model: {self.embedder.model_name}")
        logger.info(f"🗄️ Using ChromaDB directory: {chroma_persist_dir}")
    
    def populate_vector_db(self, schema_info: Dict, column_values: Dict):
        """
        Populate vector database with schema and column information
        
        Args:
            schema_info: Database schema information
            column_values: Column values dictionary
        """
        try:
            logger.info(f"📊 Populating vector database with Gemini embeddings...")
            
            documents = []
            metadatas = []
            ids = []
            
            # Add schema information
            for table_name, table_info in schema_info.items():
                # Table schema
                schema_doc = f"Table {table_name}: {table_info.get('schema', '')}"
                documents.append(schema_doc)
                metadatas.append({
                    "content_type": "create_table",
                    "table": table_name,
                    "description": table_info.get('description', '')
                })
                ids.append(f"schema_{table_name}")
                
                # Column information
                for column_name, column_info in table_info.get('columns', {}).items():
                    col_doc = f"Column {table_name}.{column_name}: {column_info.get('type', '')} - {column_info.get('description', '')}"
                    documents.append(col_doc)
                    metadatas.append({
                        "content_type": "column_info",
                        "table": table_name,
                        "column": column_name,
                        "type": column_info.get('type', ''),
                        "description": column_info.get('description', '')
                    })
                    ids.append(f"column_{table_name}_{column_name}")
            
            # Add column values
            for table_name, columns in column_values.items():
                for column_name, values_info in columns.items():
                    if values_info.get('unique_values'):
                        values_text = f"Values for {table_name}.{column_name}: {', '.join(values_info['unique_values'][:10])}"
                        documents.append(values_text)
                        metadatas.append({
                            "content_type": "unique_values",
                            "table": table_name,
                            "column": column_name,
                            "count": values_info.get('count', 0)
                        })
                        ids.append(f"values_{table_name}_{column_name}")
            
            # Generate embeddings using Gemini
            logger.info(f"🧠 Generating Gemini embeddings for {len(documents)} documents...")
            embeddings = self.embedder.generate_embeddings_batch(documents)
            
            # Filter out None embeddings
            valid_docs = []
            valid_metadatas = []
            valid_ids = []
            
            for i, embedding in enumerate(embeddings):
                if embedding is not None:
                    valid_docs.append(documents[i])
                    valid_metadatas.append(metadatas[i])
                    valid_ids.append(ids[i])
            
            # Add to ChromaDB
            if valid_docs:
                self.chroma_manager.add_documents(valid_docs, valid_metadatas, valid_ids)
                logger.info(f"✅ Successfully populated vector database with {len(valid_docs)} documents")
            else:
                logger.warning(f"⚠️ No valid embeddings generated")
                
        except Exception as e:
            logger.error(f"❌ Error populating vector database: {e}")
            raise
    
    def retrieve_context_with_details(self, query: str, n_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve relevant context with detailed ChromaDB and Gemini interaction information
        
        Args:
            query: Query text
            n_results: Number of results to return
            
        Returns:
            Context with detailed interaction information
        """
        try:
            logger.info(f"🔍 Retrieving context with Gemini for query: {query[:50]}...")
            
            # Track Gemini interactions
            gemini_interactions = {
                "embedding_generation": {},
                "model_used": self.embedder.model_name
            }
            
            start_time = time.time()
            
            # Generate query embedding using Gemini
            query_embedding = self.embedder.generate_embedding(query)
            embedding_time = time.time() - start_time
            
            if query_embedding is None:
                logger.error(f"❌ Failed to generate query embedding")
                return {
                    "context_items": [],
                    "gemini_interactions": {"error": "Failed to generate embedding"},
                    "chromadb_interactions": {},
                    "vector_search_details": {}
                }
            
            # Track embedding generation details
            gemini_interactions["embedding_generation"] = {
                "time_ms": embedding_time * 1000,
                "embedding_dimensions": len(query_embedding),
                "model": self.embedder.model_name
            }
            
            # Query ChromaDB
            chroma_start = time.time()
            results = self.chroma_manager.query_documents(query, n_results)
            chroma_time = time.time() - chroma_start
            
            # Extract context items
            context_items = []
            if results and results.get('documents') and results['documents'][0]:
                context_items = results['documents'][0]
            
            # Track ChromaDB interactions
            chromadb_interactions = {
                "query_time_ms": chroma_time * 1000,
                "results_count": len(context_items),
                "collection_name": self.chroma_manager.collection_name
            }
            
            # Vector search details
            vector_search_details = {
                "similarity_scores": results.get('distances', [[]])[0] if results.get('distances') else [],
                "total_time_ms": (embedding_time + chroma_time) * 1000,
                "embedding_time_ms": embedding_time * 1000,
                "search_time_ms": chroma_time * 1000
            }
            
            logger.info(f"✅ Retrieved {len(context_items)} context items")
            
            return {
                "context_items": context_items,
                "gemini_interactions": gemini_interactions,
                "chromadb_interactions": chromadb_interactions,
                "vector_search_details": vector_search_details
            }
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return {
                "context_items": [],
                "gemini_interactions": {"error": str(e)},
                "chromadb_interactions": {},
                "vector_search_details": {}
            }
