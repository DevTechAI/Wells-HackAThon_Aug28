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
    LLM-neutral SQL generator that can work with any LLM provider with PII protection
    """
    
    def __init__(self, provider: str = "openai", api_key: Optional[str] = None,
                 model_name: str = "gpt-4o-mini", temperature: float = 0.1):
        """
        Initialize SQL generator with specified provider and PII protection
        
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
        
        # Initialize security guard for PII protection
        from security_guard import SecurityGuard
        self.security_guard = SecurityGuard()
        
        # Track PII protection events
        self.pii_protection_events = []
        
        logger.info(f"🧠 Initializing LLM SQL Generator with provider: {provider} and PII protection")
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
    
    def generate_sql_with_schema_context(self, query: str, schema_context: Dict[str, Any], 
                                       planner_analysis: Dict[str, Any]) -> str:
        """Generate SQL using rich schema context and planner analysis"""
        logger.info(f"🧠 LLM: Generating SQL with rich schema context for: {query}")
        
        try:
            # Extract schema metadata and distinct values
            schema_metadata = schema_context.get('schema_metadata', {})
            distinct_values = schema_context.get('distinct_values', {})
            where_suggestions = schema_context.get('where_suggestions', {})
            
            # Extract planner analysis
            table_details = planner_analysis.get('table_details', {})
            column_mappings = planner_analysis.get('column_mappings', {})
            where_conditions = planner_analysis.get('where_conditions', [])
            join_requirements = planner_analysis.get('join_requirements', [])
            value_constraints = planner_analysis.get('value_constraints', {})
            
            # Build enhanced prompt with schema context
            enhanced_prompt = self._build_enhanced_prompt(
                query=query,
                schema_metadata=schema_metadata,
                distinct_values=distinct_values,
                where_suggestions=where_suggestions,
                table_details=table_details,
                column_mappings=column_mappings,
                where_conditions=where_conditions,
                join_requirements=join_requirements,
                value_constraints=value_constraints
            )
            
            # Generate SQL using LLM
            sql_result = self._call_llm_with_timeout(enhanced_prompt)
            
            if sql_result:
                # Clean and validate the generated SQL
                cleaned_sql = self._clean_generated_sql(sql_result)
                logger.info(f"✅ LLM: Generated SQL with schema context: {cleaned_sql[:100]}...")
                return cleaned_sql
            else:
                logger.error("❌ LLM: Failed to generate SQL with schema context")
                return ""
                
        except Exception as e:
            logger.error(f"❌ LLM: Error generating SQL with schema context: {e}")
            return ""
    
    def _build_enhanced_prompt(self, query: str, schema_metadata: Dict[str, Any], 
                             distinct_values: Dict[str, Dict[str, List[Any]]], 
                             where_suggestions: Dict[str, List[str]],
                             table_details: Dict[str, Any], 
                             column_mappings: Dict[str, List[str]],
                             where_conditions: List[str],
                             join_requirements: List[Dict[str, str]],
                             value_constraints: Dict[str, Any]) -> str:
        """Build enhanced prompt with rich schema context"""
        
        prompt = f"""
You are an expert SQL generator for a banking database. Generate precise SQL based on the natural language query and rich schema context.

NATURAL LANGUAGE QUERY:
{query}

SCHEMA METADATA:
"""
        
        # Add table details
        for table_name, details in table_details.items():
            prompt += f"""
Table: {table_name}
- Column Count: {details.get('column_count', 0)}
- Has Primary Key: {details.get('has_primary_key', False)}
- Distinct Values Available: {details.get('distinct_values_count', 0)}
- Value Distributions Available: {details.get('value_distributions_count', 0)}
"""
        
        # Add distinct values for WHERE conditions
        if distinct_values:
            prompt += "\nDISTINCT VALUES FOR WHERE CONDITIONS:\n"
            for table_name, columns in distinct_values.items():
                prompt += f"\nTable: {table_name}\n"
                for column_name, values in columns.items():
                    if values:
                        prompt += f"- {column_name}: {values[:5]}\n"  # Show first 5 values
        
        # Add WHERE suggestions
        if where_suggestions:
            prompt += "\nWHERE CONDITION SUGGESTIONS:\n"
            for table_name, suggestions in where_suggestions.items():
                prompt += f"\nTable: {table_name}\n"
                for suggestion in suggestions[:5]:  # Show first 5 suggestions
                    prompt += f"- {suggestion}\n"
        
        # Add column mappings
        if column_mappings:
            prompt += "\nRELEVANT COLUMNS:\n"
            for table_name, columns in column_mappings.items():
                prompt += f"- {table_name}: {', '.join(columns)}\n"
        
        # Add WHERE conditions
        if where_conditions:
            prompt += "\nSUGGESTED WHERE CONDITIONS:\n"
            for condition in where_conditions[:5]:  # Show first 5 conditions
                prompt += f"- {condition}\n"
        
        # Add JOIN requirements
        if join_requirements:
            prompt += "\nJOIN REQUIREMENTS:\n"
            for join_req in join_requirements:
                prompt += f"- {join_req['table1']} JOIN {join_req['table2']} ON {join_req['join_condition']}\n"
        
        # Add value constraints
        if value_constraints:
            prompt += "\nVALUE CONSTRAINTS:\n"
            for table_name, constraints in value_constraints.items():
                prompt += f"\nTable: {table_name}\n"
                for column_name, column_constraints in constraints.items():
                    for constraint in column_constraints:
                        prompt += f"- {constraint['suggested_condition']}\n"
        
        prompt += """

INSTRUCTIONS:
1. Use the exact table and column names from the schema
2. Use the distinct values provided for precise WHERE conditions
3. Apply the suggested JOIN conditions when multiple tables are needed
4. Use the value constraints to filter data accurately
5. Generate clean, efficient SQL that matches the natural language query
6. Include proper table aliases for readability
7. Use appropriate aggregation functions (COUNT, SUM, AVG, etc.)

Generate only the SQL query without any explanation:
"""
        
        return prompt
    
    def _call_llm_with_timeout(self, prompt: str, timeout_seconds: int = 30) -> Optional[str]:
        """Call LLM with timeout handling and PII protection"""
        if not self.llm_loaded:
            logger.error("❌ LLM not loaded")
            return None
        
        # Check if PII scanning is enabled before processing
        if self.security_guard.enable_pii_scanning:
            # PII Protection: Scan prompt before sending to external LLM
            logger.info("🔒 LLM: Scanning prompt for PII before external API call")
            pii_findings = self.security_guard.detect_pii(prompt, "llm_prompt")
            
            if pii_findings['detected']:
                logger.warning(f"⚠️ LLM: PII detected in prompt - {pii_findings['pii_types']} found")
                
                # Log PII protection event
                self.pii_protection_events.append({
                    'timestamp': time.time(),
                    'pii_types': pii_findings['pii_types'],
                    'risk_level': pii_findings['risk_level'],
                    'context': 'llm_prompt',
                    'action': 'sanitized'
                })
                
                # Sanitize prompt before sending to external LLM
                sanitized_prompt, sanitization_report = self.security_guard.sanitize_content_for_embedding(
                    prompt, "llm_prompt"
                )
                
                logger.info(f"🛡️ LLM: Prompt sanitized - {sanitization_report['pii_removed']} removed, {sanitization_report['pii_masked']} masked")
                
                # Use sanitized prompt for LLM call
                prompt = sanitized_prompt
            else:
                logger.info("✅ LLM: No PII detected in prompt")
        else:
            logger.debug("🔒 LLM: PII scanning disabled, skipping scan")
        
        def llm_call():
            try:
                if self.provider == "openai":
                    logger.info(f"📤 Sending LLM request to OpenAI API:")
                    logger.info(f"   📊 Model: {self.model_name}")
                    logger.info(f"   🌡️ Temperature: {self.temperature}")
                    logger.info(f"   📝 Prompt preview: {prompt[:200]}...")
                    
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
    
    def get_pii_protection_events(self) -> List[Dict[str, Any]]:
        """Get all PII protection events from LLM interactions"""
        return self.pii_protection_events
    
    def get_pii_protection_summary(self) -> Dict[str, Any]:
        """Get a summary of PII protection events"""
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
