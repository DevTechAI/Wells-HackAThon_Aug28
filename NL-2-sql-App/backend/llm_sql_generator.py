#!/usr/bin/env python3
"""
LLM-Neutral SQL Generator for SQL RAG Agent
Supports multiple LLM providers for SQL generation
"""

import os
import time
import threading
import logging
from typing import Dict, Any, Optional, List
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMSQLGenerator:
    """
    LLM-neutral SQL generator that can work with any LLM provider
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None,
                 model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize SQL generator with specified provider
        
        Args:
            provider: LLM provider ('openai', 'anthropic', 'google', 'local')
            api_key: API key for the provider
            model_name: Model name for generation
            temperature: Generation temperature
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.model_name = model_name
        self.temperature = temperature
        self.client = None
        self.llm_loaded = False
        self.llm_error = None
        
        logger.info(f"🧠 Initializing LLM SQL Generator with provider: {provider}")
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
                self.client = genai.GenerativeModel(self.model_name)
                logger.info("✅ Google Generative AI client initialized")
                
            elif self.provider == "local":
                # For local models like Ollama or llama-cpp
                try:
                    from llama_cpp import Llama
                    # This would need a model path - placeholder for now
                    logger.info("✅ Local LLM client initialized")
                except ImportError:
                    logger.warning("⚠️ llama-cpp-python not available for local models")
                    self.client = None
                
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            self.llm_loaded = True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.provider} client: {e}")
            self.llm_error = str(e)
            self.llm_loaded = False
    
    def _call_llm_with_timeout(self, prompt: str, timeout_seconds: int = 30) -> Optional[str]:
        """Call LLM with timeout handling"""
        if not self.llm_loaded:
            logger.error("❌ LLM not loaded")
            return None
        
        def llm_call():
            try:
                if self.provider == "openai":
                    response = self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=self.temperature,
                        max_tokens=1024
                    )
                    return response.choices[0].message.content
                    
                elif self.provider == "anthropic":
                    response = self.client.messages.create(
                        model=self.model_name,
                        max_tokens=1024,
                        temperature=self.temperature,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    return response.content[0].text
                    
                elif self.provider == "google":
                    response = self.client.generate_content(
                        prompt,
                        generation_config={
                            "temperature": self.temperature,
                            "max_output_tokens": 1024
                        }
                    )
                    return response.text
                    
                elif self.provider == "local":
                    # Placeholder for local model calls
                    logger.warning("⚠️ Local LLM calls not implemented")
                    return None
                    
            except Exception as e:
                logger.error(f"❌ Error calling {self.provider} LLM: {e}")
                return None
        
        # Run with timeout
        thread = threading.Thread(target=llm_call)
        thread.daemon = True
        thread.start()
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            logger.error(f"❌ LLM call timed out after {timeout_seconds} seconds")
            return None
        
        return llm_call()
    
    def generate(self, nl_query: str, clarified_values: Dict, gen_ctx: Dict, schema_tables: Dict) -> str:
        """Generate SQL from natural language query - alias for generate_sql for compatibility"""
        return self.generate_sql(nl_query, gen_ctx)
    
    def generate_sql(self, nl_query: str, gen_ctx: Dict[str, Any]) -> str:
        """Generate SQL from natural language query"""
        logger.info(f"🔧 LLM SQL Generator: Starting SQL generation for query: {nl_query}")
        
        schema_context = gen_ctx.get("schema_context", [])
        value_hints = gen_ctx.get("value_hints", [])
        exemplars = gen_ctx.get("exemplars", [])
        query_analysis = gen_ctx.get("query_analysis", {})
        schema_tables = gen_ctx.get("schema_tables", {})
        
        # Build enhanced generation prompt
        prompt = self._build_enhanced_generation_prompt(
            nl_query, schema_context, value_hints, exemplars, query_analysis, schema_tables
        )
        
        # Try LLM generation first
        try:
            sql = self._call_llm_with_timeout(prompt, timeout_seconds=45)
            if sql:
                # Clean and validate SQL
                sql = self._clean_sql_output(sql)
                logger.info(f"✅ LLM SQL Generator: Generated SQL successfully")
                return sql
        except Exception as e:
            logger.warning(f"⚠️ LLM SQL Generator: LLM generation failed: {e}")
        
        # Fallback to pattern-based generation
        logger.info(f"🔄 LLM SQL Generator: Using pattern-based fallback")
        return self._intelligent_pattern_generation(nl_query, query_analysis, schema_tables)
    
    def repair_sql(self, nl_query: str, gen_ctx: Dict[str, Any], hint: str = "") -> str:
        """Repair SQL using LLM and context"""
        logger.info(f"🔧 LLM SQL Generator: Starting SQL repair for query: {nl_query}")
        
        schema_context = gen_ctx.get("schema_context", [])
        value_hints = gen_ctx.get("value_hints", [])
        exemplars = gen_ctx.get("exemplars", [])
        query_analysis = gen_ctx.get("query_analysis", {})
        schema_tables = gen_ctx.get("schema_tables", {})
        
        # Analyze the error
        error_analysis = self._analyze_sql_error(hint, nl_query)
        
        # Generate enhanced repair context
        enhanced_context = self._generate_enhanced_repair_context(
            nl_query, schema_context, query_analysis, error_analysis
        )
        
        # Create intelligent repair prompt
        repair_prompt = self._create_intelligent_repair_prompt(
            nl_query, enhanced_context, error_analysis, query_analysis, value_hints, exemplars
        )
        
        # Try LLM repair
        try:
            repaired_sql = self._call_llm_with_timeout(repair_prompt, timeout_seconds=45)
            if repaired_sql:
                repaired_sql = self._clean_sql_output(repaired_sql)
                logger.info(f"✅ LLM SQL Generator: SQL repair successful")
                return repaired_sql
        except Exception as e:
            logger.warning(f"⚠️ LLM SQL Generator: LLM repair failed: {e}")
        
        # Fallback to pattern-based repair
        logger.info(f"🔄 LLM SQL Generator: Using pattern-based repair fallback")
        return self._intelligent_pattern_repair(nl_query, query_analysis, schema_tables, error_analysis)
    
    def _build_enhanced_generation_prompt(self, nl_query: str, schema_context: List[Dict[str, Any]],
                                         value_hints: List[str], exemplars: List[str],
                                         query_analysis: Dict[str, Any], schema_tables: Dict[str, Any]) -> str:
        """Build enhanced prompt for SQL generation"""
        
        # Schema context
        schema_text = "\n".join([item.get("content", "") for item in schema_context[:5]])
        
        # Value hints
        value_hints_text = "\n".join([f"• {hint}" for hint in value_hints[:5]])
        
        # Exemplars
        exemplars_text = "\n".join([f"• {exemplar}" for exemplar in exemplars[:3]])
        
        # Query analysis
        analysis_text = f"""
        Required Tables: {', '.join(query_analysis.get('required_tables', []))}
        Operations: {', '.join(query_analysis.get('operations', []))}
        Conditions: {', '.join(query_analysis.get('conditions', []))}
        """
        
        prompt = f"""
        You are an expert SQL generator. Generate accurate SQL for the given natural language query.

        DATABASE SCHEMA:
        {schema_text}

        QUERY ANALYSIS:
        {analysis_text}

        VALUE HINTS FOR WHERE CONDITIONS:
        {value_hints_text}

        SIMILAR QUERY EXAMPLES:
        {exemplars_text}

        NATURAL LANGUAGE QUERY:
        {nl_query}

        Generate a SQL query that:
        1. Uses only SELECT statements (no INSERT, UPDATE, DELETE, DROP)
        2. References the correct tables and columns
        3. Uses appropriate WHERE conditions with the provided value hints
        4. Follows the patterns shown in the exemplars
        5. Returns only the SQL query, no explanations

        SQL QUERY:
        """
        
        return prompt.strip()
    
    def _create_intelligent_repair_prompt(self, nl_query: str, enhanced_context: str,
                                         error_analysis: Dict[str, Any], query_analysis: Dict[str, Any],
                                         value_hints: List[str], exemplars: List[str]) -> str:
        """Create intelligent repair prompt"""
        
        value_hints_text = "\n".join([f"• {hint}" for hint in value_hints[:5]])
        exemplars_text = "\n".join([f"• {exemplar}" for exemplar in exemplars[:3]])
        
        prompt = f"""
        You are an expert SQL repair agent. Fix the SQL query based on the error analysis.

        ORIGINAL QUERY: {nl_query}
        
        ERROR ANALYSIS: {error_analysis.get('error_type', 'Unknown error')}
        ERROR DETAILS: {error_analysis.get('details', 'No details provided')}
        
        REQUIRED COMPONENTS:
        Tables: {', '.join(query_analysis.get('required_tables', []))}
        Operations: {', '.join(query_analysis.get('operations', []))}
        
        VALUE HINTS: {value_hints_text}
        
        EXEMPLARS: {exemplars_text}
        
        CONTEXT: {enhanced_context}
        
        Generate a corrected SQL query that:
        1. Fixes the identified error
        2. Uses the correct tables and columns
        3. Incorporates the value hints appropriately
        4. Follows the patterns in the exemplars
        5. Returns only the SQL query, no explanations

        CORRECTED SQL QUERY:
        """
        
        return prompt.strip()
    
    def _analyze_sql_error(self, hint: str, nl_query: str) -> Dict[str, Any]:
        """Analyze SQL error for repair"""
        error_analysis = {
            "error_type": "unknown",
            "details": hint,
            "suggested_fixes": []
        }
        
        hint_lower = hint.lower()
        
        if "table" in hint_lower and "not found" in hint_lower:
            error_analysis["error_type"] = "missing_table"
            error_analysis["suggested_fixes"].append("Check table names in schema")
        elif "column" in hint_lower and "not found" in hint_lower:
            error_analysis["error_type"] = "missing_column"
            error_analysis["suggested_fixes"].append("Check column names in schema")
        elif "syntax" in hint_lower:
            error_analysis["error_type"] = "syntax_error"
            error_analysis["suggested_fixes"].append("Fix SQL syntax")
        
        return error_analysis
    
    def _generate_enhanced_repair_context(self, nl_query: str, schema_context: List[Dict[str, Any]],
                                        query_analysis: Dict[str, Any], error_analysis: Dict[str, Any]) -> str:
        """Generate enhanced context for repair"""
        context_parts = []
        
        # Add schema context
        for item in schema_context[:3]:
            context_parts.append(item.get("content", ""))
        
        # Add query analysis
        context_parts.append(f"Query requires: {', '.join(query_analysis.get('required_tables', []))}")
        
        # Add error context
        context_parts.append(f"Error type: {error_analysis.get('error_type', 'unknown')}")
        
        return "\n".join(context_parts)
    
    def _intelligent_pattern_generation(self, nl_query: str, query_analysis: Dict[str, Any],
                                      schema_tables: Dict[str, Any]) -> str:
        """Generate SQL using intelligent patterns"""
        query_lower = nl_query.lower()
        
        # Pattern-based generation
        if "count" in query_lower:
            tables = query_analysis.get("required_tables", ["customers"])
            return f"SELECT COUNT(*) FROM {tables[0]} LIMIT 10;"
        
        elif "both" in query_lower and ("checking" in query_lower or "savings" in query_lower):
            return """
            SELECT DISTINCT c.id, c.first_name, c.last_name
            FROM customers c
            JOIN accounts a1 ON c.id = a1.customer_id AND a1.type = 'checking'
            JOIN accounts a2 ON c.id = a2.customer_id AND a2.type = 'savings'
            LIMIT 10;
            """.strip()
        
        elif "branch" in query_lower and "transaction" in query_lower:
            return """
            SELECT b.name, b.city, b.state, COUNT(t.id) as transaction_count
            FROM branches b
            LEFT JOIN transactions t ON b.id = t.branch_id
            GROUP BY b.id, b.name, b.city, b.state
            ORDER BY transaction_count DESC
            LIMIT 10;
            """.strip()
        
        else:
            # Generic fallback
            tables = query_analysis.get("required_tables", ["customers"])
            return f"SELECT * FROM {tables[0]} LIMIT 10;"
    
    def _intelligent_pattern_repair(self, nl_query: str, query_analysis: Dict[str, Any],
                                  schema_tables: Dict[str, Any], error_analysis: Dict[str, Any]) -> str:
        """Repair SQL using intelligent patterns"""
        error_type = error_analysis.get("error_type", "unknown")
        
        if error_type == "missing_table":
            # Try to find the correct table
            tables = query_analysis.get("required_tables", ["customers"])
            return f"SELECT * FROM {tables[0]} LIMIT 10;"
        
        elif error_type == "missing_column":
            # Use a simple query with basic columns
            tables = query_analysis.get("required_tables", ["customers"])
            return f"SELECT id, name FROM {tables[0]} LIMIT 10;"
        
        else:
            # Generic repair
            return self._intelligent_pattern_generation(nl_query, query_analysis, schema_tables)
    
    def _clean_sql_output(self, sql: str) -> str:
        """Clean and validate SQL output"""
        if not sql:
            return ""
        
        # Remove markdown code blocks
        sql = re.sub(r'```sql\s*', '', sql)
        sql = re.sub(r'```\s*$', '', sql)
        
        # Remove extra whitespace
        sql = sql.strip()
        
        # Ensure it ends with semicolon
        if not sql.endswith(';'):
            sql += ';'
        
        return sql
