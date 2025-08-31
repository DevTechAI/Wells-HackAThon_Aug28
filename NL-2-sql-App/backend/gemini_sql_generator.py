#!/usr/bin/env python3
"""
Gemini SQL Generator using Google Generative AI
Replaces Claude-based SQL generation with Gemini Pro
"""

import google.generativeai as genai
import time
import threading
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiSQLGenerator:
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-pro", temperature: float = 0.1):
        """
        Initialize Gemini SQL Generator
        
        Args:
            api_key: Google AI API key
            model_name: Gemini model to use
            temperature: Generation temperature
        """
        self.api_key = api_key
        self.model_name = model_name
        self.temperature = temperature
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.schema_tables = {}
        
        logger.info(f"🧠 Initializing Gemini SQL Generator with model: {model_name}")
        
        # Test connection
        self._test_connection()
    
    def _test_connection(self):
        """Test connection to Google AI API"""
        try:
            # Test with a simple query
            test_response = self._call_gemini_with_timeout("Say 'Hello'", timeout_seconds=10)
            if test_response:
                logger.info(f"✅ Connected to Google AI API successfully")
            else:
                logger.error(f"❌ Failed to connect to Google AI API")
        except Exception as e:
            logger.error(f"❌ Error connecting to Google AI API: {e}")
            logger.info("💡 Make sure your API key is valid and has sufficient credits")
    
    def _call_gemini_with_timeout(self, prompt: str, timeout_seconds: int = 30) -> Optional[str]:
        """
        Call Gemini API with timeout to prevent hanging
        
        Args:
            prompt: Prompt to send to Gemini
            timeout_seconds: Timeout in seconds
            
        Returns:
            Gemini response text or None if failed
        """
        result = [None]
        exception = [None]
        
        def gemini_call():
            try:
                response = self.model.generate_content(prompt)
                if response.text:
                    result[0] = response.text
                else:
                    result[0] = None
            except Exception as e:
                exception[0] = e
        
        # Start Gemini call in a separate thread
        thread = threading.Thread(target=gemini_call)
        thread.daemon = True
        thread.start()
        
        # Wait for completion or timeout
        thread.join(timeout=timeout_seconds)
        
        if thread.is_alive():
            logger.warning(f"⚠️ Gemini API call timed out after {timeout_seconds} seconds")
            return None
        
        if exception[0]:
            logger.error(f"❌ Gemini API call failed: {exception[0]}")
            return None
        
        return result[0]
    
    def generate(self, nl_query: str, clarified_values: Dict, gen_ctx: Dict, schema_tables: Dict) -> str:
        """
        Generate SQL from natural language query using Gemini
        
        Args:
            nl_query: Natural language query
            clarified_values: Clarified values from planner
            gen_ctx: Generation context from retriever
            schema_tables: Database schema information
            
        Returns:
            Generated SQL query
        """
        try:
            logger.info(f"🧠 Gemini SQL Generator: Generating SQL for query: {nl_query[:50]}...")
            
            # Build comprehensive prompt
            prompt = self._build_sql_prompt(nl_query, clarified_values, gen_ctx, schema_tables)
            
            # Call Gemini with timeout
            response = self._call_gemini_with_timeout(prompt, timeout_seconds=45)
            
            if response:
                sql = response.strip()
                logger.info(f"✅ Gemini generated SQL: {sql[:100]}...")
                return sql
            else:
                logger.error("❌ Gemini failed to generate SQL")
                return self._generate_fallback_sql(nl_query, schema_tables)
                
        except Exception as e:
            logger.error(f"❌ Error in Gemini SQL generation: {e}")
            return self._generate_fallback_sql(nl_query, schema_tables)
    
    def _build_sql_prompt(self, nl_query: str, clarified_values: Dict, gen_ctx: Dict, schema_tables: Dict) -> str:
        """
        Build comprehensive prompt for Gemini SQL generation
        
        Args:
            nl_query: Natural language query
            clarified_values: Clarified values
            gen_ctx: Generation context
            schema_tables: Schema information
            
        Returns:
            Formatted prompt for Gemini
        """
        # Extract context information
        schema_context = gen_ctx.get('schema_context', '')
        value_hints = gen_ctx.get('value_hints', [])
        exemplars = gen_ctx.get('exemplars', [])
        query_analysis = gen_ctx.get('query_analysis', {})
        
        # Build schema information
        schema_info = []
        for table_name, columns in schema_tables.items():
            schema_info.append(f"Table: {table_name}")
            schema_info.append(f"Columns: {', '.join(columns)}")
            schema_info.append("")
        
        # Build value hints
        value_hints_text = ""
        if value_hints:
            value_hints_text = "\nVALUE HINTS FOR WHERE CONDITIONS:\n"
            for hint in value_hints[:5]:  # Limit to first 5 hints
                value_hints_text += f"- {hint}\n"
        
        # Build exemplars
        exemplars_text = ""
        if exemplars:
            exemplars_text = "\nSIMILAR QUERY EXAMPLES:\n"
            for exemplar in exemplars[:3]:  # Limit to first 3 exemplars
                exemplars_text += f"- {exemplar}\n"
        
        # Build clarified values
        clarified_text = ""
        if clarified_values:
            clarified_text = "\nCLARIFIED VALUES:\n"
            for key, value in clarified_values.items():
                clarified_text += f"- {key}: {value}\n"
        
        prompt = f"""You are an expert SQL assistant. Generate accurate SQL for the given natural language query.

DATABASE SCHEMA:
{chr(10).join(schema_info)}

SCHEMA CONTEXT:
{schema_context}

QUERY ANALYSIS:
{query_analysis}

{clarified_text}{value_hints_text}{exemplars_text}

NATURAL LANGUAGE QUERY:
{nl_query}

INSTRUCTIONS:
1. Analyze the query and identify required tables and columns
2. Use the schema information to understand table relationships
3. Generate SQL that accurately answers the query
4. Use appropriate JOINs, WHERE clauses, and aggregations
5. Return ONLY the SQL query, no explanations

SQL QUERY:"""

        return prompt
    
    def _generate_fallback_sql(self, nl_query: str, schema_tables: Dict) -> str:
        """
        Generate fallback SQL when Gemini fails
        
        Args:
            nl_query: Natural language query
            schema_tables: Schema information
            
        Returns:
            Fallback SQL query
        """
        logger.warning(f"⚠️ Using fallback SQL generation for: {nl_query}")
        
        # Simple fallback logic
        query_lower = nl_query.lower()
        
        if "customer" in query_lower and "account" in query_lower:
            return "SELECT * FROM customers LIMIT 10;"
        elif "branch" in query_lower and "manager" in query_lower:
            return "SELECT b.name, e.name as manager FROM branches b LEFT JOIN employees e ON b.manager_id = e.id;"
        elif "employee" in query_lower:
            return "SELECT * FROM employees LIMIT 10;"
        elif "transaction" in query_lower:
            return "SELECT * FROM transactions LIMIT 10;"
        else:
            # Return first table
            first_table = list(schema_tables.keys())[0] if schema_tables else "customers"
            return f"SELECT * FROM {first_table} LIMIT 10;"
    
    def repair_sql(self, nl_query: str, gen_ctx: Dict, hint: str = None) -> str:
        """
        Repair SQL using Gemini
        
        Args:
            nl_query: Original natural language query
            gen_ctx: Generation context
            hint: Repair hint
            
        Returns:
            Repaired SQL query
        """
        try:
            logger.info(f"🔧 Gemini SQL Generator: Repairing SQL for query: {nl_query[:50]}...")
            
            # Extract context
            schema_context = gen_ctx.get('schema_context', '')
            value_hints = gen_ctx.get('value_hints', [])
            exemplars = gen_ctx.get('exemplars', [])
            query_analysis = gen_ctx.get('query_analysis', {})
            
            # Build repair prompt
            repair_prompt = f"""You are an expert SQL assistant. The following SQL query has an error and needs to be repaired.

ORIGINAL QUERY: {nl_query}

ERROR HINT: {hint or 'SQL syntax or logic error'}

SCHEMA CONTEXT:
{schema_context}

VALUE HINTS:
{chr(10).join(value_hints[:3]) if value_hints else 'None'}

QUERY ANALYSIS:
{query_analysis}

INSTRUCTIONS:
1. Analyze the error and understand what went wrong
2. Use the schema context to identify correct table/column names
3. Generate a corrected SQL query
4. Return ONLY the corrected SQL query, no explanations

CORRECTED SQL QUERY:"""
            
            # Call Gemini for repair
            response = self._call_gemini_with_timeout(repair_prompt, timeout_seconds=30)
            
            if response:
                repaired_sql = response.strip()
                logger.info(f"✅ Gemini repaired SQL: {repaired_sql[:100]}...")
                return repaired_sql
            else:
                logger.error("❌ Gemini failed to repair SQL")
                return self._generate_fallback_sql(nl_query, {})
                
        except Exception as e:
            logger.error(f"❌ Error in Gemini SQL repair: {e}")
            return self._generate_fallback_sql(nl_query, {})
