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
from chromadb.config import Settings as ChromaSettings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMEmbedder:
    """
    LLM-neutral embedder that can work with any LLM provider with PII protection
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None, 
                 model_name: str = "text-embedding-ada-002"):
        """
        Initialize embedder with specified provider and PII protection
        
        Args:
            provider: LLM provider ('openai', 'anthropic', 'google', 'local')
            api_key: API key for the provider
            model_name: Model name for embeddings
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.model_name = model_name
        self.client = None
        
        # Initialize security guard for PII protection
        from security_guard import SecurityGuard
        self.security_guard = SecurityGuard()
        
        # Track PII protection events
        self.pii_protection_events = []
        
        # Track API call statistics
        self.api_call_count = 0
        self.batch_api_call_count = 0
        self.total_tokens_processed = 0
        
        logger.info(f"🧠 Initializing LLM Embedder with provider: {provider} and PII protection")
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
        """Generate embedding for a single text with PII protection"""
        
        # Check if PII scanning is enabled before processing
        if self.security_guard.enable_pii_scanning:
            # PII Protection: Scan text before sending to external LLM
            logger.info("🔒 LLM Embedder: Scanning text for PII before embedding generation")
            pii_findings = self.security_guard.detect_pii(text, "embedding_text")
            
            if pii_findings['detected']:
                logger.warning(f"⚠️ LLM Embedder: PII detected in text - {pii_findings['pii_types']} found")
                
                # Log PII protection event
                self.pii_protection_events.append({
                    'timestamp': time.time(),
                    'pii_types': pii_findings['pii_types'],
                    'risk_level': pii_findings['risk_level'],
                    'context': 'embedding_text',
                    'action': 'sanitized'
                })
                
                # Sanitize text before sending to external LLM
                sanitized_text, sanitization_report = self.security_guard.sanitize_content_for_embedding(
                    text, "embedding_text"
                )
                
                logger.info(f"🛡️ LLM Embedder: Text sanitized - {sanitization_report['pii_removed']} removed, {sanitization_report['pii_masked']} masked")
                
                # Use sanitized text for embedding
                text = sanitized_text
            else:
                logger.info("✅ LLM Embedder: No PII detected in text")
        else:
            logger.debug("🔒 LLM Embedder: PII scanning disabled, skipping scan")
        
        try:
            if self.provider == "openai":
                logger.info(f"📤 Sending single request to OpenAI API:")
                logger.info(f"   📊 Model: {self.model_name}")
                logger.info(f"   📝 Text preview: {text[:100]}...")
                
                # Increment API call counter
                self.api_call_count += 1
                self.total_tokens_processed += len(text.split())
                
                # Log the actual request payload
                request_payload = {
                    "input": text,
                    "model": self.model_name
                }
                logger.info(f"📦 Request payload: {request_payload}")
                
                response = self.client.embeddings.create(
                    input=text,
                    model=self.model_name
                )
                logger.info(f"✅ Single API call #{self.api_call_count} completed")
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
    
    def get_pii_protection_events(self) -> List[Dict[str, Any]]:
        """Get all PII protection events from embedding generation"""
        return self.pii_protection_events
    
    def get_pii_protection_summary(self) -> Dict[str, Any]:
        """Get a summary of PII protection events from embedding generation"""
        if not self.pii_protection_events:
            return {
                'total_events': 0,
                'pii_types': {},
                'risk_levels': {},
                'actions_taken': {}
            }
        
        summary = {
            'total_events': len(self.pii_protection_events),
            'pii_types': {},
            'risk_levels': {},
            'actions_taken': {}
        }
        
        for event in self.pii_protection_events:
            # Count PII types
            for pii_type in event.get('pii_types', []):
                summary['pii_types'][pii_type] = summary['pii_types'].get(pii_type, 0) + 1
            
            # Count risk levels
            risk_level = event.get('risk_level', 'unknown')
            summary['risk_levels'][risk_level] = summary['risk_levels'].get(risk_level, 0) + 1
            
            # Count actions
            action = event.get('action', 'unknown')
            summary['actions_taken'][action] = summary['actions_taken'].get(action, 0) + 1
        
        return summary
    
    def get_api_call_statistics(self) -> Dict[str, Any]:
        """Get API call statistics"""
        return {
            'total_api_calls': self.api_call_count + self.batch_api_call_count,
            'single_api_calls': self.api_call_count,
            'batch_api_calls': self.batch_api_call_count,
            'total_tokens_processed': self.total_tokens_processed,
            'average_tokens_per_call': self.total_tokens_processed / max(1, self.api_call_count + self.batch_api_call_count)
        }
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts using batch processing"""
        if not texts:
            return []
        
        logger.info(f"🔄 Generating batch embeddings for {len(texts)} texts")
        
        # Check if PII scanning is enabled before processing
        if self.security_guard.enable_pii_scanning:
            logger.info("🔒 LLM Embedder: Scanning batch texts for PII before embedding generation")
            sanitized_texts = []
            
            for i, text in enumerate(texts):
                pii_findings = self.security_guard.detect_pii(text, f"batch_embedding_text_{i}")
                
                if pii_findings['detected']:
                    logger.warning(f"⚠️ LLM Embedder: PII detected in batch text {i} - {pii_findings['pii_types']} found")
                    
                    # Log PII protection event
                    self.pii_protection_events.append({
                        'timestamp': time.time(),
                        'pii_types': pii_findings['pii_types'],
                        'risk_level': pii_findings['risk_level'],
                        'context': f'batch_embedding_text_{i}',
                        'action': 'sanitized'
                    })
                    
                    # Sanitize text before sending to external LLM
                    sanitized_text, sanitization_report = self.security_guard.sanitize_content_for_embedding(
                        text, f"batch_embedding_text_{i}"
                    )
                    
                    logger.info(f"🛡️ LLM Embedder: Batch text {i} sanitized - {sanitization_report['pii_removed']} removed, {sanitization_report['pii_masked']} masked")
                    sanitized_texts.append(sanitized_text)
                else:
                    sanitized_texts.append(text)
        else:
            logger.debug("🔒 LLM Embedder: PII scanning disabled, using original texts for batch")
            sanitized_texts = texts
        
        try:
            if self.provider == "openai":
                # Use batch processing for OpenAI
                logger.info(f"📤 Sending batch request to OpenAI API:")
                logger.info(f"   📊 Model: {self.model_name}")
                logger.info(f"   📝 Input texts count: {len(sanitized_texts)}")
                logger.info(f"   📄 First text preview: {sanitized_texts[0][:100]}..." if sanitized_texts else "   📄 No texts")
                logger.info(f"   📄 Last text preview: {sanitized_texts[-1][:100]}..." if len(sanitized_texts) > 1 else "")
                
                # Increment batch API call counter
                self.batch_api_call_count += 1
                self.total_tokens_processed += sum(len(text.split()) for text in sanitized_texts)
                
                # Log the actual batch request payload
                request_payload = {
                    "input": sanitized_texts,
                    "model": self.model_name
                }
                logger.info(f"📦 Batch request payload: {request_payload}")
                
                response = self.client.embeddings.create(
                    input=sanitized_texts,
                    model=self.model_name
                )
                embeddings = [data.embedding for data in response.data]
                logger.info(f"✅ Batch API call #{self.batch_api_call_count} completed - {len(embeddings)} embeddings generated")
                return embeddings
                
            elif self.provider == "anthropic":
                # Use batch processing for Anthropic
                response = self.client.embeddings.create(
                    input=sanitized_texts,
                    model=self.model_name
                )
                embeddings = [data.embedding for data in response.data]
                logger.info(f"✅ Generated batch embeddings for {len(embeddings)} texts using Anthropic")
                return embeddings
                
            elif self.provider == "google":
                # Google doesn't support batch embeddings in the same way, so we'll process individually
                logger.warning("⚠️ Google provider doesn't support batch embeddings, processing individually")
                embeddings = []
                for text in sanitized_texts:
                    response = self.client.embed_content(
                        model=self.model_name,
                        content=text
                    )
                    embeddings.append(response.embedding)
                logger.info(f"✅ Generated individual embeddings for {len(embeddings)} texts using Google")
                return embeddings
                
            elif self.provider == "local":
                # For local models, you might use a different approach
                logger.warning("⚠️ Local batch embedding generation not implemented")
                return [[0.0] * 1536 for _ in sanitized_texts]  # Placeholder embeddings
                
        except Exception as e:
            logger.error(f"❌ Error generating batch embeddings: {e}")
            # Fallback to individual processing if batch fails
            logger.info("🔄 Falling back to individual embedding generation")
            embeddings = []
            for text in sanitized_texts:
                try:
                    embedding = self.generate_embedding(text)
                    embeddings.append(embedding)
                except Exception as individual_error:
                    logger.error(f"❌ Error generating individual embedding: {individual_error}")
                    embeddings.append([0.0] * 1536)  # Placeholder embedding
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
        """Initialize ChromaDB client with better error handling for existing instances"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Always try to create a client - ChromaDB handles existing instances gracefully
            self.client = chromadb.PersistentClient(
                path=self.persist_dir,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Test the connection by listing collections
            try:
                collections = self.client.list_collections()
                logger.info(f"✅ ChromaDB client initialized successfully with {len(collections)} existing collections")
                
                # Log existing collections for debugging
                for col in collections:
                    logger.info(f"   📋 Found collection: {col.name} (count: {col.count()})")
                    
            except Exception as list_error:
                logger.warning(f"⚠️ Could not list collections, but client created: {list_error}")
                logger.info("✅ ChromaDB client initialized (collections may be empty)")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB client: {e}")
            logger.warning("⚠️ ChromaDB initialization failed, continuing without vector storage")
            self.client = None
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        """Get or create a collection with better error handling"""
        if self.client is None:
            logger.warning("⚠️ ChromaDB client not available, skipping collection operation")
            return None
            
        try:
            # First try to get existing collection
            try:
                collection = self.client.get_collection(name=name)
                logger.info(f"✅ Using existing collection '{name}'")
                self.collections[name] = collection
                return collection
            except Exception as get_error:
                logger.info(f"ℹ️ Collection '{name}' not found, creating new one: {get_error}")
            
            # If collection doesn't exist, create it
            try:
                collection = self.client.create_collection(name=name)
                logger.info(f"✅ Created new collection '{name}'")
                self.collections[name] = collection
                return collection
            except Exception as create_error:
                # Handle case where collection was created by another process
                if "already exists" in str(create_error).lower():
                    logger.info(f"ℹ️ Collection '{name}' already exists, getting it")
                    try:
                        collection = self.client.get_collection(name=name)
                        logger.info(f"✅ Retrieved existing collection '{name}'")
                        self.collections[name] = collection
                        return collection
                    except Exception as final_error:
                        logger.error(f"❌ Failed to get collection '{name}' after creation error: {final_error}")
                        raise
                else:
                    logger.error(f"❌ Failed to create collection '{name}': {create_error}")
                    raise
                    
        except Exception as e:
            logger.error(f"❌ Error with collection '{name}': {e}")
            # Don't raise the error, return None to allow graceful degradation
            logger.warning(f"⚠️ Continuing without collection '{name}'")
            return None
    
    def add_documents(self, collection_name: str, documents: List[str], 
                     metadatas: List[Dict[str, Any]], ids: List[str]):
        """Add documents to collection with graceful error handling"""
        if self.client is None:
            logger.warning("⚠️ ChromaDB client not available, skipping document addition")
            return
            
        try:
            collection = self.get_or_create_collection(collection_name)
            if collection is None:
                logger.warning(f"⚠️ Collection '{collection_name}' not available, skipping document addition")
                return
                
            # Check if collection is not None before calling add
            if collection is not None:
                try:
                    collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    logger.info(f"✅ Added {len(documents)} documents to collection '{collection_name}'")
                except Exception as add_error:
                    logger.error(f"❌ Error adding documents to collection '{collection_name}': {add_error}")
                    logger.warning(f"⚠️ Continuing without adding documents to collection '{collection_name}'")
            else:
                logger.warning(f"⚠️ Collection '{collection_name}' is None, skipping document addition")
                
        except Exception as e:
            logger.error(f"❌ Error with collection '{collection_name}': {e}")
            logger.warning(f"⚠️ Continuing without collection '{collection_name}'")
    
    def query(self, collection_name: str, query_texts: List[str], 
              n_results: int = 5) -> Dict[str, Any]:
        """Query collection with graceful error handling"""
        if self.client is None:
            logger.warning("⚠️ ChromaDB client not available, skipping query")
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
