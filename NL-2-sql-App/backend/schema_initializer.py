#!/usr/bin/env python3
"""
ChromaDB Schema Initializer with LangGraph
Initializes ChromaDB with schema embeddings and entity relationship diagrams
"""

import os
import sys
import logging
import json
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import asyncio

# Add backend to path
sys.path.append('./backend')

from chromadb_singleton import get_chromadb_singleton
from llm_embedder import LLMEmbedder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableSchema:
    """Represents a database table schema"""
    table_name: str
    columns: List[Dict[str, Any]]
    primary_key: Optional[str] = None
    foreign_keys: List[Dict[str, str]] = None
    unique_constraints: List[List[str]] = None
    sample_data: List[Dict[str, Any]] = None
    distinct_values: Dict[str, List[Any]] = None  # Column name -> list of distinct values
    value_distributions: Dict[str, Dict[str, int]] = None  # Column name -> value -> count

@dataclass
class EntityRelationship:
    """Represents entity relationships"""
    source_table: str
    target_table: str
    relationship_type: str  # "one-to-one", "one-to-many", "many-to-many"
    source_column: str
    target_column: str
    description: str

class SchemaAnalyzer:
    """Analyzes database schema and extracts metadata"""
    
    def __init__(self, db_path: str = "./banking.db"):
        self.db_path = db_path
        self.connection = None
        
    def connect(self):
        """Connect to SQLite database"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            logger.info(f"✅ Connected to database: {self.db_path}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to database: {e}")
            raise
    
    def get_table_schemas(self) -> List[TableSchema]:
        """Extract table schemas from database"""
        if not self.connection:
            self.connect()
        
        schemas = []
        
        try:
            cursor = self.connection.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            
            for (table_name,) in tables:
                if table_name == 'sqlite_sequence':  # Skip system table
                    continue
                
                # Get table schema
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns_info = cursor.fetchall()
                
                # Get sample data
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                
                # Get column names for sample data
                cursor.execute(f"PRAGMA table_info({table_name})")
                column_names = [row[1] for row in cursor.fetchall()]
                
                # Convert sample data to dict
                sample_dicts = []
                for row in sample_data:
                    sample_dicts.append(dict(zip(column_names, row)))
                
                # Extract column details
                columns = []
                primary_key = None
                
                for col_info in columns_info:
                    col_id, col_name, col_type, not_null, default_val, pk = col_info
                    
                    column = {
                        "name": col_name,
                        "type": col_type,
                        "not_null": bool(not_null),
                        "default": default_val,
                        "primary_key": bool(pk)
                    }
                    
                    if pk:
                        primary_key = col_name
                    
                    columns.append(column)
                
                # Get unique constraints
                cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = cursor.fetchall()
                
                unique_constraints = []
                for index in indexes:
                    index_name = index[1]
                    if index_name.startswith('sqlite_autoindex_'):
                        continue
                    
                    cursor.execute(f"PRAGMA index_info({index_name})")
                    index_columns = cursor.fetchall()
                    
                    if len(index_columns) > 1:  # Composite unique constraint
                        constraint_cols = []
                        for idx_col in index_columns:
                            constraint_cols.append(columns[idx_col[1]]["name"])
                        unique_constraints.append(constraint_cols)
                
                # Analyze distinct values and distributions
                distinct_values, value_distributions = self.analyze_column_values(table_name, columns)
                
                schema = TableSchema(
                    table_name=table_name,
                    columns=columns,
                    primary_key=primary_key,
                    unique_constraints=unique_constraints,
                    sample_data=sample_dicts,
                    distinct_values=distinct_values,
                    value_distributions=value_distributions
                )
                
                schemas.append(schema)
                logger.info(f"📋 Extracted schema for table: {table_name} ({len(columns)} columns)")
            
            return schemas
            
        except Exception as e:
            logger.error(f"❌ Error extracting table schemas: {e}")
            raise
    
    def get_distinct_values(self, table_name: str, column_name: str, limit: int = 50) -> List[Any]:
        """Get distinct values for a specific column"""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Get distinct values with limit
            query = f"SELECT DISTINCT {column_name} FROM {table_name} WHERE {column_name} IS NOT NULL LIMIT {limit}"
            cursor.execute(query)
            distinct_values = [row[0] for row in cursor.fetchall()]
            
            logger.info(f"📊 Found {len(distinct_values)} distinct values for {table_name}.{column_name}")
            return distinct_values
            
        except Exception as e:
            logger.error(f"❌ Error getting distinct values for {table_name}.{column_name}: {e}")
            return []
    
    def get_value_distribution(self, table_name: str, column_name: str, limit: int = 20) -> Dict[str, int]:
        """Get value distribution (count) for a specific column"""
        if not self.connection:
            self.connect()
        
        try:
            cursor = self.connection.cursor()
            
            # Get value counts
            query = f"SELECT {column_name}, COUNT(*) as count FROM {table_name} WHERE {column_name} IS NOT NULL GROUP BY {column_name} ORDER BY count DESC LIMIT {limit}"
            cursor.execute(query)
            distribution = {str(row[0]): row[1] for row in cursor.fetchall()}
            
            logger.info(f"📊 Found value distribution for {table_name}.{column_name}: {len(distribution)} unique values")
            return distribution
            
        except Exception as e:
            logger.error(f"❌ Error getting value distribution for {table_name}.{column_name}: {e}")
            return {}
    
    def analyze_column_values(self, table_name: str, columns: List[Dict[str, Any]]) -> Tuple[Dict[str, List[Any]], Dict[str, Dict[str, int]]]:
        """Analyze distinct values and distributions for all columns"""
        distinct_values = {}
        value_distributions = {}
        
        for column in columns:
            column_name = column["name"]
            column_type = column["type"].upper()
            
            # Skip certain column types that don't need distinct value analysis
            if column_type in ["TIMESTAMP", "DATE", "DATETIME"]:
                continue
            
            # Get distinct values for text and numeric columns
            if column_type in ["TEXT", "VARCHAR", "CHAR", "STRING"] or "INT" in column_type or "REAL" in column_type or "DECIMAL" in column_type:
                try:
                    # Get distinct values
                    distinct_vals = self.get_distinct_values(table_name, column_name, limit=30)
                    if distinct_vals:
                        distinct_values[column_name] = distinct_vals
                    
                    # Get value distribution for text columns (not for IDs or numeric columns)
                    if column_type in ["TEXT", "VARCHAR", "CHAR", "STRING"] and not column_name.endswith("_id") and not column_name == "id":
                        distribution = self.get_value_distribution(table_name, column_name, limit=15)
                        if distribution:
                            value_distributions[column_name] = distribution
                            
                except Exception as e:
                    logger.warning(f"⚠️ Could not analyze values for {table_name}.{column_name}: {e}")
        
        logger.info(f"📊 Analyzed values for {len(distinct_values)} columns in {table_name}")
        return distinct_values, value_distributions
    
    def get_entity_relationships(self, schemas: List[TableSchema]) -> List[EntityRelationship]:
        """Extract entity relationships from foreign keys"""
        relationships = []
        
        try:
            cursor = self.connection.cursor()
            
            for schema in schemas:
                # Get foreign key information
                cursor.execute(f"PRAGMA foreign_key_list({schema.table_name})")
                foreign_keys = cursor.fetchall()
                
                for fk_info in foreign_keys:
                    # fk_info: (id, seq, table, from, to, on_update, on_delete, match)
                    target_table = fk_info[2]
                    source_column = fk_info[3]
                    target_column = fk_info[4]
                    
                    # Determine relationship type based on unique constraints
                    source_unique = any(source_column in constraint for constraint in schema.unique_constraints or [])
                    target_schema = next((s for s in schemas if s.table_name == target_table), None)
                    target_unique = target_schema and any(target_column in constraint for constraint in target_schema.unique_constraints or [])
                    
                    if source_unique and target_unique:
                        relationship_type = "one-to-one"
                    elif source_unique:
                        relationship_type = "many-to-one"
                    else:
                        relationship_type = "many-to-many"
                    
                    relationship = EntityRelationship(
                        source_table=schema.table_name,
                        target_table=target_table,
                        relationship_type=relationship_type,
                        source_column=source_column,
                        target_column=target_column,
                        description=f"{schema.table_name}.{source_column} references {target_table}.{target_column}"
                    )
                    
                    relationships.append(relationship)
            
            logger.info(f"🔗 Extracted {len(relationships)} entity relationships")
            return relationships
            
        except Exception as e:
            logger.error(f"❌ Error extracting entity relationships: {e}")
            return []

class SQLFileProcessor:
    """Processes SQL schema and sample data files for embeddings"""
    
    def __init__(self, db_folder: str = "./db"):
        self.db_folder = db_folder
        
    def read_sql_file(self, filename: str) -> str:
        """Read SQL file content"""
        try:
            file_path = os.path.join(self.db_folder, filename)
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            logger.info(f"📄 Read SQL file: {filename} ({len(content)} characters)")
            return content
        except Exception as e:
            logger.error(f"❌ Error reading SQL file {filename}: {e}")
            return ""
    
    def chunk_sql_content(self, content: str, chunk_size: int = 2000, overlap: int = 200) -> List[Dict[str, Any]]:
        """Split SQL content into chunks for embedding"""
        chunks = []
        
        if not content:
            return chunks
        
        # Split by SQL statements (semicolons)
        statements = content.split(';')
        
        current_chunk = ""
        chunk_id = 0
        
        for statement in statements:
            statement = statement.strip()
            if not statement:
                continue
            
            # If adding this statement would exceed chunk size, save current chunk
            if len(current_chunk) + len(statement) > chunk_size and current_chunk:
                chunks.append({
                    "id": f"sql_chunk_{chunk_id}",
                    "content": current_chunk.strip(),
                    "type": "sql_schema",
                    "metadata": {
                        "chunk_size": len(current_chunk),
                        "chunk_id": chunk_id
                    }
                })
                chunk_id += 1
                
                # Start new chunk with overlap
                if overlap > 0 and current_chunk:
                    current_chunk = current_chunk[-overlap:] + "\n\n"
                else:
                    current_chunk = ""
            
            current_chunk += statement + ";\n\n"
        
        # Add the last chunk if it has content
        if current_chunk.strip():
            chunks.append({
                "id": f"sql_chunk_{chunk_id}",
                "content": current_chunk.strip(),
                "type": "sql_schema",
                "metadata": {
                    "chunk_size": len(current_chunk),
                    "chunk_id": chunk_id
                }
            })
        
        logger.info(f"📄 Created {len(chunks)} SQL chunks from content")
        return chunks
    
    def process_schema_file(self, filename: str = "schema.sql") -> List[Dict[str, Any]]:
        """Process schema.sql file into chunks"""
        content = self.read_sql_file(filename)
        if not content:
            return []
        
        # Add context to schema content
        enhanced_content = f"""
        Database Schema Definition:
        
        {content}
        
        This schema defines the structure of the banking system database with tables for branches, customers, employees, accounts, and transactions.
        """
        
        chunks = self.chunk_sql_content(enhanced_content)
        
        # Add schema-specific metadata
        for chunk in chunks:
            chunk["metadata"]["file_type"] = "schema"
            chunk["metadata"]["filename"] = filename
            chunk["metadata"]["content_type"] = "database_schema"
        
        logger.info(f"📄 Processed schema file into {len(chunks)} chunks")
        return chunks
    
    def process_sample_data_file(self, filename: str = "sample_data.sql") -> List[Dict[str, Any]]:
        """Process sample_data.sql file into chunks"""
        content = self.read_sql_file(filename)
        if not content:
            return []
        
        # Add context to sample data content
        enhanced_content = f"""
        Sample Data for Banking System:
        
        {content}
        
        This sample data provides realistic examples of banking transactions, customer information, and account details.
        """
        
        chunks = self.chunk_sql_content(enhanced_content, chunk_size=3000, overlap=300)
        
        # Add sample data-specific metadata
        for chunk in chunks:
            chunk["metadata"]["file_type"] = "sample_data"
            chunk["metadata"]["filename"] = filename
            chunk["metadata"]["content_type"] = "sample_data"
        
        logger.info(f"📄 Processed sample data file into {len(chunks)} chunks")
        return chunks
    
    def process_all_sql_files(self) -> Dict[str, List[Dict[str, Any]]]:
        """Process all SQL files in the db folder"""
        all_chunks = {}
        
        # Process schema file
        schema_chunks = self.process_schema_file("schema.sql")
        if schema_chunks:
            all_chunks["schema"] = schema_chunks
        
        # Process sample data file
        sample_chunks = self.process_sample_data_file("sample_data.sql")
        if sample_chunks:
            all_chunks["sample_data"] = sample_chunks
        
        logger.info(f"📄 Processed {len(all_chunks)} SQL file types")
        return all_chunks

class MermaidDiagramGenerator:
    """Generates Mermaid entity relationship diagrams"""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        
    def generate_er_diagram(self, schemas: List[TableSchema], relationships: List[EntityRelationship]) -> str:
        """Generate Mermaid ER diagram from schemas and relationships"""
        
        mermaid_code = "erDiagram\n"
        
        # Add tables
        for schema in schemas:
            mermaid_code += f"    {schema.table_name} {{\n"
            
            for column in schema.columns:
                col_type = column["type"].upper()
                pk_marker = " PK" if column["primary_key"] else ""
                mermaid_code += f"        {col_type} {column['name']}{pk_marker}\n"
            
            mermaid_code += "    }\n"
        
        # Add relationships
        for rel in relationships:
            source_card = "||" if rel.relationship_type in ["one-to-one", "many-to-one"] else "}"
            target_card = "||" if rel.relationship_type in ["one-to-one", "one-to-many"] else "{"
            
            mermaid_code += f"    {rel.source_table} {source_card}--{target_card} {rel.target_table} : \"{rel.description}\"\n"
        
        return mermaid_code

class LangGraphSchemaProcessor:
    """LangGraph-based schema processing pipeline with PII protection"""
    
    def __init__(self, openai_api_key: str, chromadb_persist_dir: str = "./chroma_db"):
        self.openai_api_key = openai_api_key
        self.chromadb_persist_dir = chromadb_persist_dir
        self.embedder = LLMEmbedder(openai_api_key)
        self.chromadb = get_chromadb_singleton(chromadb_persist_dir)
        self.sql_processor = SQLFileProcessor("./db")
        
        # Initialize security guard for PII detection
        from security_guard import SecurityGuard
        self.security_guard = SecurityGuard()
        
        # Track PII findings across the pipeline
        self.pii_findings = []
        
    async def process_schema_node(self, schemas: List[TableSchema]) -> List[Dict[str, Any]]:
        """Node 1: Preprocess schema data"""
        logger.info("🔄 Node 1: Preprocessing schema data...")
        
        schema_chunks = []
        
        for schema in schemas:
            # Create detailed schema description
            schema_text = f"""
            Table: {schema.table_name}
            
            Columns:
            """
            
            for column in schema.columns:
                pk_marker = " (Primary Key)" if column["primary_key"] else ""
                null_marker = " NOT NULL" if column["not_null"] else ""
                default_marker = f" DEFAULT {column['default']}" if column["default"] else ""
                
                schema_text += f"- {column['name']}: {column['type']}{pk_marker}{null_marker}{default_marker}\n"
            
            if schema.unique_constraints:
                schema_text += "\nUnique Constraints:\n"
                for constraint in schema.unique_constraints:
                    schema_text += f"- {', '.join(constraint)}\n"
            
            # Add distinct values information
            if schema.distinct_values:
                schema_text += "\nDistinct Values (for WHERE conditions):\n"
                for column_name, values in schema.distinct_values.items():
                    if values:
                        # Format values nicely
                        if len(values) <= 10:
                            formatted_values = [str(v) for v in values]
                        else:
                            formatted_values = [str(v) for v in values[:10]] + [f"... and {len(values) - 10} more"]
                        
                        schema_text += f"- {column_name}: {', '.join(formatted_values)}\n"
            
            # Add value distributions for categorical data
            if schema.value_distributions:
                schema_text += "\nValue Distributions (common values):\n"
                for column_name, distribution in schema.value_distributions.items():
                    if distribution:
                        top_values = list(distribution.items())[:5]  # Top 5 values
                        formatted_dist = [f"'{val}' ({count})" for val, count in top_values]
                        schema_text += f"- {column_name}: {', '.join(formatted_dist)}\n"
            
            if schema.sample_data:
                schema_text += "\nSample Data:\n"
                for i, row in enumerate(schema.sample_data[:3]):  # Limit to 3 samples
                    schema_text += f"Row {i+1}: {row}\n"
            
            # PII Detection and Sanitization
            pii_findings = self.security_guard.detect_pii(schema_text, f"schema_{schema.table_name}")
            if pii_findings['detected']:
                logger.warning(f"⚠️ PII detected in schema for table {schema.table_name}: {pii_findings['pii_types']}")
                self.pii_findings.append(pii_findings)
                
                # Sanitize content before embedding
                sanitized_content, sanitization_report = self.security_guard.sanitize_content_for_embedding(
                    schema_text, f"schema_{schema.table_name}"
                )
                
                # Use sanitized content for embedding
                schema_text = sanitized_content
                
                # Add PII warning to metadata
                metadata = {
                    "table_name": schema.table_name,
                    "column_count": len(schema.columns),
                    "has_primary_key": schema.primary_key is not None,
                    "unique_constraints_count": len(schema.unique_constraints or []),
                    "pii_detected": True,
                    "pii_types": pii_findings['pii_types'],
                    "risk_level": pii_findings['risk_level'],
                    "sanitization_applied": sanitization_report['sanitization_applied']
                }
            else:
                metadata = {
                    "table_name": schema.table_name,
                    "column_count": len(schema.columns),
                    "has_primary_key": schema.primary_key is not None,
                    "unique_constraints_count": len(schema.unique_constraints or [])
                }
            
            schema_chunks.append({
                "table_name": schema.table_name,
                "content": schema_text,
                "type": "schema",
                "metadata": metadata
            })
        
        logger.info(f"✅ Preprocessed {len(schema_chunks)} schema chunks")
        return schema_chunks
    
    async def generate_embeddings_node(self, schema_chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Node 2: Generate embeddings for schema chunks"""
        logger.info("🔄 Node 2: Generating embeddings...")
        
        embedded_chunks = []
        
        for chunk in schema_chunks:
            try:
                # Generate embedding
                embedding = self.embedder.generate_embedding(chunk["content"])
                
                if embedding:
                    embedded_chunk = {
                        **chunk,
                        "embedding": embedding,
                        "embedding_generated": True
                    }
                    embedded_chunks.append(embedded_chunk)
                    logger.info(f"✅ Generated embedding for {chunk['table_name']}")
                else:
                    logger.warning(f"⚠️ Failed to generate embedding for {chunk['table_name']}")
                    
            except Exception as e:
                logger.error(f"❌ Error generating embedding for {chunk['table_name']}: {e}")
        
        logger.info(f"✅ Generated embeddings for {len(embedded_chunks)} chunks")
        return embedded_chunks
    
    async def store_embeddings_node(self, embedded_chunks: List[Dict[str, Any]]) -> bool:
        """Node 3: Store embeddings in ChromaDB"""
        logger.info("🔄 Node 3: Storing embeddings in ChromaDB...")
        
        try:
            # Prepare data for ChromaDB
            documents = [chunk["content"] for chunk in embedded_chunks]
            metadatas = [chunk["metadata"] for chunk in embedded_chunks]
            ids = [f"schema_{chunk['table_name']}" for chunk in embedded_chunks]
            
            # Store in ChromaDB
            success = self.chromadb.add_documents(
                collection_name="database_schema",
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            
            if success:
                logger.info(f"✅ Stored {len(embedded_chunks)} schema embeddings in ChromaDB")
                return True
            else:
                logger.error("❌ Failed to store schema embeddings in ChromaDB")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error storing embeddings: {e}")
            return False
    
    async def process_sql_files_node(self) -> Dict[str, List[Dict[str, Any]]]:
        """Node 5: Process SQL schema and sample data files with PII protection"""
        logger.info("🔄 Node 5: Processing SQL files with PII protection...")
        
        try:
            # Process all SQL files
            sql_chunks = self.sql_processor.process_all_sql_files()
            
            # PII Detection for SQL files
            if sql_chunks:
                for file_type, chunks in sql_chunks.items():
                    # Detect PII in each chunk
                    for chunk in chunks:
                        pii_findings = self.security_guard.detect_pii(
                            chunk['content'], 
                            f"{file_type}_sql_{chunk.get('metadata', {}).get('chunk_id', 0)}"
                        )
                        
                        if pii_findings['detected']:
                            logger.warning(f"⚠️ PII detected in {file_type} SQL chunk: {pii_findings['pii_types']}")
                            self.pii_findings.append(pii_findings)
                            
                            # Sanitize content
                            sanitized_content, sanitization_report = self.security_guard.sanitize_content_for_embedding(
                                chunk['content'], 
                                f"{file_type}_sql_{chunk.get('metadata', {}).get('chunk_id', 0)}"
                            )
                            
                            # Update chunk with sanitized content
                            chunk['content'] = sanitized_content
                            chunk['metadata']['pii_detected'] = True
                            chunk['metadata']['pii_types'] = pii_findings['pii_types']
                            chunk['metadata']['risk_level'] = pii_findings['risk_level']
                            chunk['metadata']['sanitization_applied'] = sanitization_report['sanitization_applied']
                
                logger.info(f"✅ Processed SQL files with PII protection: {list(sql_chunks.keys())}")
                for file_type, chunks in sql_chunks.items():
                    logger.info(f"   📄 {file_type}: {len(chunks)} chunks")
            else:
                logger.warning("⚠️ No SQL files processed")
            
            return sql_chunks
            
        except Exception as e:
            logger.error(f"❌ Error processing SQL files: {e}")
            return {}
    
    async def store_sql_embeddings_node(self, sql_chunks: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Node 6: Store SQL file embeddings in ChromaDB"""
        logger.info("🔄 Node 6: Storing SQL file embeddings...")
        
        try:
            total_stored = 0
            
            for file_type, chunks in sql_chunks.items():
                if not chunks:
                    continue
                
                # Generate embeddings for each chunk
                embedded_chunks = []
                for chunk in chunks:
                    try:
                        embedding = self.embedder.generate_embedding(chunk["content"])
                        if embedding:
                            embedded_chunk = {
                                **chunk,
                                "embedding": embedding,
                                "embedding_generated": True
                            }
                            embedded_chunks.append(embedded_chunk)
                    except Exception as e:
                        logger.error(f"❌ Error generating embedding for {chunk['id']}: {e}")
                
                if embedded_chunks:
                    # Prepare data for ChromaDB
                    documents = [chunk["content"] for chunk in embedded_chunks]
                    metadatas = [chunk["metadata"] for chunk in embedded_chunks]
                    ids = [chunk["id"] for chunk in embedded_chunks]
                    
                    # Store in ChromaDB
                    collection_name = f"sql_{file_type}"
                    success = self.chromadb.add_documents(
                        collection_name=collection_name,
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    
                    if success:
                        logger.info(f"✅ Stored {len(embedded_chunks)} {file_type} embeddings in ChromaDB")
                        total_stored += len(embedded_chunks)
                    else:
                        logger.error(f"❌ Failed to store {file_type} embeddings")
            
            logger.info(f"✅ Total SQL embeddings stored: {total_stored}")
            return total_stored > 0
    
    def get_pii_findings(self) -> List[Dict[str, Any]]:
        """Get all PII findings from the pipeline"""
        return self.pii_findings
    
    def get_pii_summary(self) -> Dict[str, Any]:
        """Get a summary of PII findings"""
        if not self.pii_findings:
            return {
                'total_findings': 0,
                'risk_levels': {},
                'pii_types': {},
                'contexts': []
            }
        
        summary = {
            'total_findings': len(self.pii_findings),
            'risk_levels': {},
            'pii_types': {},
            'contexts': []
        }
        
        for finding in self.pii_findings:
            # Count risk levels
            risk_level = finding.get('risk_level', 'unknown')
            summary['risk_levels'][risk_level] = summary['risk_levels'].get(risk_level, 0) + 1
            
            # Count PII types
            for pii_type in finding.get('pii_types', []):
                summary['pii_types'][pii_type] = summary['pii_types'].get(pii_type, 0) + 1
            
            # Collect contexts
            context = finding.get('context', 'unknown')
            if context not in summary['contexts']:
                summary['contexts'].append(context)
        
        return summary
            
        except Exception as e:
            logger.error(f"❌ Error storing SQL embeddings: {e}")
            return False
    
    async def process_relationships_node(self, relationships: List[EntityRelationship]) -> bool:
        logger.info("🔄 Processing entity relationships...")
        
        try:
            # Generate Mermaid diagram
            diagram_generator = MermaidDiagramGenerator(self.openai_api_key)
            
            # Get schemas for diagram generation
            analyzer = SchemaAnalyzer()
            schemas = analyzer.get_table_schemas()
            
            mermaid_diagram = diagram_generator.generate_er_diagram(schemas, relationships)
            
            # Create relationship descriptions
            relationship_chunks = []
            
            for rel in relationships:
                rel_text = f"""
                Entity Relationship:
                Source Table: {rel.source_table}
                Target Table: {rel.target_table}
                Relationship Type: {rel.relationship_type}
                Source Column: {rel.source_column}
                Target Column: {rel.target_column}
                Description: {rel.description}
                """
                
                relationship_chunks.append({
                    "content": rel_text,
                    "type": "relationship",
                    "metadata": {
                        "source_table": rel.source_table,
                        "target_table": rel.target_table,
                        "relationship_type": rel.relationship_type,
                        "source_column": rel.source_column,
                        "target_column": rel.target_column
                    }
                })
            
            # Add Mermaid diagram
            diagram_chunk = {
                "content": f"Entity Relationship Diagram:\n```mermaid\n{mermaid_diagram}\n```",
                "type": "mermaid_diagram",
                "metadata": {
                    "diagram_type": "entity_relationship",
                    "tables_count": len(schemas),
                    "relationships_count": len(relationships)
                }
            }
            
            relationship_chunks.append(diagram_chunk)
            
            # Generate embeddings for relationships
            embedded_relationships = []
            for chunk in relationship_chunks:
                try:
                    embedding = self.embedder.generate_embedding(chunk["content"])
                    if embedding:
                        embedded_chunk = {
                            **chunk,
                            "embedding": embedding,
                            "embedding_generated": True
                        }
                        embedded_relationships.append(embedded_chunk)
                except Exception as e:
                    logger.error(f"❌ Error generating relationship embedding: {e}")
            
            # Store relationship embeddings
            if embedded_relationships:
                documents = [chunk["content"] for chunk in embedded_relationships]
                metadatas = [chunk["metadata"] for chunk in embedded_relationships]
                ids = [f"relationship_{i}" for i in range(len(embedded_relationships))]
                
                success = self.chromadb.add_documents(
                    collection_name="entity_relationships",
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                
                if success:
                    logger.info(f"✅ Stored {len(embedded_relationships)} relationship embeddings")
                    return True
                else:
                    logger.error("❌ Failed to store relationship embeddings")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing relationships: {e}")
            return False
    
    async def run_pipeline(self, db_path: str = "./banking.db") -> bool:
        """Run the complete LangGraph pipeline"""
        logger.info("🚀 Starting LangGraph Schema Processing Pipeline...")
        
        try:
            # Step 1: Analyze database schema
            analyzer = SchemaAnalyzer(db_path)
            schemas = analyzer.get_table_schemas()
            relationships = analyzer.get_entity_relationships(schemas)
            
            logger.info(f"📊 Analyzed {len(schemas)} tables and {len(relationships)} relationships")
            
            # Step 2: Process schemas through LangGraph nodes
            schema_chunks = await self.process_schema_node(schemas)
            embedded_chunks = await self.generate_embeddings_node(schema_chunks)
            schema_stored = await self.store_embeddings_node(embedded_chunks)
            
            # Step 3: Process relationships
            relationships_stored = await self.process_relationships_node(relationships)
            
            # Step 4: Process SQL files
            sql_chunks = await self.process_sql_files_node()
            sql_stored = await self.store_sql_embeddings_node(sql_chunks)
            
            if schema_stored and relationships_stored and sql_stored:
                logger.info("🎉 LangGraph Schema Processing Pipeline completed successfully!")
                return True
            else:
                logger.error("❌ LangGraph Schema Processing Pipeline failed")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error in LangGraph pipeline: {e}")
            return False

def initialize_chromadb_with_schema(openai_api_key: str, db_path: str = "./banking.db", chromadb_persist_dir: str = "./chroma_db"):
    """Initialize ChromaDB with schema embeddings using LangGraph"""
    
    async def run_initialization():
        processor = LangGraphSchemaProcessor(openai_api_key, chromadb_persist_dir)
        return await processor.run_pipeline(db_path)
    
    # Run the async pipeline
    try:
        result = asyncio.run(run_initialization())
        return result
    except Exception as e:
        logger.error(f"❌ Error initializing ChromaDB with schema: {e}")
        return False

if __name__ == "__main__":
    # Test the schema initialization
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key:
        print("❌ OPENAI_API_KEY not found in environment variables")
        sys.exit(1)
    
    success = initialize_chromadb_with_schema(openai_api_key)
    if success:
        print("✅ ChromaDB schema initialization completed successfully!")
    else:
        print("❌ ChromaDB schema initialization failed!")
        sys.exit(1)
