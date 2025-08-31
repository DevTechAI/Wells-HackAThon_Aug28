#!/usr/bin/env python3
"""
Retriever Agent for SQL RAG Agent
Retrieves relevant schema context using vector search
"""

import logging
from typing import Dict, Any, List, Optional
from .llm_embedder import EnhancedRetriever

logger = logging.getLogger(__name__)

class RetrieverAgent:
    """Retriever agent that retrieves relevant schema context"""
    
    def __init__(self, chroma_path: str):
        self.chroma_path = chroma_path
        self.retriever = None
        self._initialize_retriever()
    
    def _initialize_retriever(self):
        """Initialize the enhanced retriever"""
        try:
            # Initialize with default settings
            self.retriever = EnhancedRetriever(
                provider="openai",  # Will be overridden by config
                api_key=None,  # Will be loaded from config
                model_name="text-embedding-ada-002",
                chroma_persist_dir=self.chroma_path
            )
            logger.info(f"🔍 Retriever: Initialized with ChromaDB path: {self.chroma_path}")
        except Exception as e:
            logger.error(f"❌ Retriever: Failed to initialize: {e}")
            self.retriever = None
    
    def retrieve_context(self, query: str, tables: List[str] = None, n_results: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context for the query"""
        logger.info(f"🔍 Retriever: Retrieving context for query: {query}")
        
        try:
            if not self.retriever:
                logger.warning("⚠️ Retriever: Retriever not initialized, returning empty context")
                return self._get_empty_context()
            
            # Retrieve context using vector search
            context = self.retriever.retrieve_context_with_details(
                query=query,
                collection_name="banking_schema",
                n_results=n_results
            )
            
            # Filter by tables if specified
            if tables:
                context = self._filter_context_by_tables(context, tables)
            
            logger.info(f"✅ Retriever: Retrieved {len(context.get('schema_context', []))} context items")
            return context
            
        except Exception as e:
            logger.error(f"❌ Retriever: Error retrieving context: {e}")
            return self._get_empty_context()
    
    def _filter_context_by_tables(self, context: Dict[str, Any], tables: List[str]) -> Dict[str, Any]:
        """Filter context to only include specified tables"""
        filtered_context = context.copy()
        
        # Filter schema context
        if 'schema_context' in context:
            filtered_schema = []
            for item in context['schema_context']:
                metadata = item.get('metadata', {})
                table_name = metadata.get('table_name', '')
                if table_name in tables:
                    filtered_schema.append(item)
            filtered_context['schema_context'] = filtered_schema
        
        # Filter query analysis
        if 'query_analysis' in context:
            query_analysis = context['query_analysis']
            if 'tables' in query_analysis:
                query_analysis['tables'] = [t for t in query_analysis['tables'] if t in tables]
        
        return filtered_context
    
    def _get_empty_context(self) -> Dict[str, Any]:
        """Return empty context structure"""
        return {
            "schema_context": [],
            "query_analysis": {
                "entities": [],
                "tables": [],
                "columns": [],
                "operations": []
            },
            "value_hints": [],
            "exemplars": [],
            "chromadb_interactions": {
                "collection": "banking_schema",
                "query": "",
                "results_count": 0
            }
        }
    
    def populate_vector_database(self, schema_info: Dict[str, Any], column_values: Dict[str, Any]):
        """Populate vector database with schema information"""
        logger.info("📊 Retriever: Populating vector database")
        
        try:
            if not self.retriever:
                logger.warning("⚠️ Retriever: Retriever not initialized, skipping population")
                return
            
            # Prepare schema data for vector storage
            schema_data = []
            
            # Add table schemas
            for table_name, columns in schema_info.items():
                schema_data.append({
                    "content": f"Table {table_name} has columns: {', '.join(columns)}",
                    "metadata": {
                        "type": "table_schema",
                        "table_name": table_name,
                        "columns": columns
                    }
                })
            
            # Add column values
            for table_name, columns in column_values.items():
                for column_name, values in columns.items():
                    if values:
                        sample_values = values[:5]  # Limit to 5 sample values
                        schema_data.append({
                            "content": f"Column {table_name}.{column_name} has values: {', '.join(map(str, sample_values))}",
                            "metadata": {
                                "type": "column_values",
                                "table_name": table_name,
                                "column_name": column_name,
                                "sample_values": sample_values
                            }
                        })
            
            # Populate vector database
            self.retriever.populate_vector_db(schema_data)
            logger.info(f"✅ Retriever: Populated vector DB with {len(schema_data)} documents")
            
        except Exception as e:
            logger.error(f"❌ Retriever: Error populating vector database: {e}")
