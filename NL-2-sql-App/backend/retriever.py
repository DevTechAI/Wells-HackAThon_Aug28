#!/usr/bin/env python3
"""
Retriever Agent for SQL RAG Agent
Retrieves relevant schema context using vector search
"""

import logging
from typing import Dict, Any, List, Optional
from llm_embedder import EnhancedRetriever

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
    
    def retrieve_context_with_schema_metadata(self, query: str, tables: List[str] = None, n_results: int = 5) -> Dict[str, Any]:
        """Retrieve context with rich schema metadata and distinct values for SQL generation"""
        logger.info(f"🔍 Retriever: Retrieving rich context for query: {query}")
        
        try:
            if not self.retriever:
                logger.warning("⚠️ Retriever: Retriever not initialized, returning empty context")
                return self._get_empty_context()
            
            # Retrieve from multiple collections for comprehensive context
            context = {}
            
            # 1. Get database schema context (table structures, distinct values)
            schema_context = self.retriever.retrieve_context_with_details(
                query=query,
                collection_name="database_schema",
                n_results=n_results
            )
            context.update(schema_context)
            
            # 2. Get SQL schema context (table definitions) - SKIPPED DUE TO EMBEDDING OPTIMIZATION
            logger.info("⏭️ Retriever: Skipping sql_schema collection (embeddings disabled)")
            context['sql_schema_context'] = "SQL schema embeddings disabled for performance optimization"
            
            # 3. Get sample data context (real data examples) - SKIPPED DUE TO EMBEDDING OPTIMIZATION  
            logger.info("⏭️ Retriever: Skipping sql_sample_data collection (embeddings disabled)")
            context['sample_data_context'] = "Sample data embeddings disabled for performance optimization"
            
            # 4. Get entity relationships context - SKIPPED FOR ESSENTIAL SCHEMA ONLY
            logger.info("⏭️ Retriever: Skipping entity_relationships collection (focusing on essential schema only)")
            context['relationship_context'] = "Entity relationships disabled to focus on schema structure and distinct values"
            
            # Extract and structure schema metadata
            context['schema_metadata'] = self._extract_schema_metadata(context)
            
            # Extract distinct values for WHERE conditions
            context['distinct_values'] = self._extract_distinct_values(context)
            
            # Filter by tables if specified
            if tables:
                context = self._filter_context_by_tables(context, tables)
            
            logger.info(f"✅ Retriever: Retrieved rich context with {len(context.get('schema_context', []))} schema items")
            logger.info(f"✅ Retriever: Extracted metadata for {len(context.get('schema_metadata', {}))} tables")
            logger.info(f"✅ Retriever: Found distinct values for {len(context.get('distinct_values', {}))} columns")
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Retriever: Error retrieving rich context: {e}")
            return self._get_empty_context()
    
    def _extract_schema_metadata(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured schema metadata from retrieved context"""
        schema_metadata = {}
        
        for item in context.get('schema_context', []):
            metadata = item.get('metadata', {})
            table_name = metadata.get('table_name', '')
            
            if table_name and table_name not in schema_metadata:
                schema_metadata[table_name] = {
                    'table_name': table_name,
                    'column_count': metadata.get('column_count', 0),
                    'has_primary_key': metadata.get('has_primary_key', False),
                    'unique_constraints_count': metadata.get('unique_constraints_count', 0),
                    'distinct_values_count': metadata.get('distinct_values_count', 0),
                    'value_distributions_count': metadata.get('value_distributions_count', 0),
                    'content': item.get('content', ''),
                    'metadata': metadata
                }
        
        return schema_metadata
    
    def _extract_distinct_values(self, context: Dict[str, Any]) -> Dict[str, Dict[str, List[Any]]]:
        """Extract distinct values for WHERE conditions from retrieved context"""
        distinct_values = {}
        
        for item in context.get('schema_context', []):
            content = item.get('content', '')
            metadata = item.get('metadata', {})
            table_name = metadata.get('table_name', '')
            
            if not table_name or not content:
                continue
            
            # Parse distinct values from content
            table_values = {}
            
            # Look for "Distinct Values (for WHERE conditions):" section
            if "Distinct Values (for WHERE conditions):" in content:
                lines = content.split('\n')
                in_distinct_section = False
                
                for line in lines:
                    line = line.strip()
                    
                    if "Distinct Values (for WHERE conditions):" in line:
                        in_distinct_section = True
                        continue
                    
                    if in_distinct_section:
                        if line.startswith('- ') and ':' in line:
                            # Parse column and values
                            parts = line[2:].split(': ', 1)  # Remove "- " and split on first ": "
                            if len(parts) == 2:
                                column_name = parts[0].strip()
                                values_str = parts[1].strip()
                                
                                # Parse values (handle lists, ranges, etc.)
                                try:
                                    if values_str.startswith('[') and values_str.endswith(']'):
                                        # Handle list format
                                        values = eval(values_str)
                                    elif ',' in values_str:
                                        # Handle comma-separated values
                                        values = [v.strip().strip("'\"") for v in values_str.split(',')]
                                    else:
                                        # Single value
                                        values = [values_str.strip("'\"")]
                                    
                                    table_values[column_name] = values
                                except:
                                    # Fallback: treat as single value
                                    table_values[column_name] = [values_str]
                        
                        elif line.startswith('Value Distributions') or line.startswith('Sample Data'):
                            # End of distinct values section
                            break
            
            if table_values:
                distinct_values[table_name] = table_values
        
        return distinct_values
    
    def get_where_condition_suggestions(self, query: str, table_name: str, column_name: str) -> List[str]:
        """Get suggested WHERE conditions for a specific table and column"""
        logger.info(f"🔍 Retriever: Getting WHERE suggestions for {table_name}.{column_name}")
        
        try:
            # Retrieve context for this specific column
            column_query = f"{table_name} {column_name} values"
            context = self.retrieve_context_with_schema_metadata(column_query, [table_name], n_results=3)
            
            suggestions = []
            
            # Get distinct values for this column
            distinct_values = context.get('distinct_values', {}).get(table_name, {}).get(column_name, [])
            
            if distinct_values:
                # Generate WHERE condition suggestions
                for value in distinct_values[:5]:  # Limit to 5 suggestions
                    if isinstance(value, (int, float)):
                        suggestions.append(f"{column_name} = {value}")
                        suggestions.append(f"{column_name} > {value}")
                        suggestions.append(f"{column_name} < {value}")
                    else:
                        suggestions.append(f"{column_name} = '{value}'")
                        suggestions.append(f"{column_name} LIKE '%{value}%'")
            
            logger.info(f"✅ Retriever: Generated {len(suggestions)} WHERE suggestions for {table_name}.{column_name}")
            return suggestions
            
        except Exception as e:
            logger.error(f"❌ Retriever: Error getting WHERE suggestions: {e}")
            return []
    
    def retrieve_context(self, query: str, tables: List[str] = None, n_results: int = 5) -> Dict[str, Any]:
        """Retrieve relevant context for the query (enhanced with schema metadata)"""
        logger.info(f"🔍 Retriever: Retrieving context for query: {query}")
        
        try:
            # Use the enhanced method for rich context
            rich_context = self.retrieve_context_with_schema_metadata(query, tables, n_results)
            
            # Add WHERE condition suggestions to the context
            if rich_context.get('distinct_values'):
                rich_context['where_suggestions'] = self._generate_where_suggestions(rich_context['distinct_values'])
            
            logger.info(f"✅ Retriever: Retrieved enhanced context with {len(rich_context.get('schema_context', []))} items")
            return rich_context
            
        except Exception as e:
            logger.error(f"❌ Retriever: Error retrieving context: {e}")
            return self._get_empty_context()
    
    def _generate_where_suggestions(self, distinct_values: Dict[str, Dict[str, List[Any]]]) -> Dict[str, List[str]]:
        """Generate WHERE condition suggestions from distinct values"""
        where_suggestions = {}
        
        for table_name, columns in distinct_values.items():
            table_suggestions = []
            
            for column_name, values in columns.items():
                if not values:
                    continue
                
                # Generate suggestions for each value
                for value in values[:3]:  # Limit to 3 values per column
                    if isinstance(value, (int, float)):
                        table_suggestions.append(f"{column_name} = {value}")
                        table_suggestions.append(f"{column_name} > {value}")
                    else:
                        table_suggestions.append(f"{column_name} = '{value}'")
                        table_suggestions.append(f"{column_name} LIKE '%{value}%'")
            
            if table_suggestions:
                where_suggestions[table_name] = table_suggestions
        
        return where_suggestions
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
