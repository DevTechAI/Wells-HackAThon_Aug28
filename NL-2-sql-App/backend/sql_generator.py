import typing
import os
import time
import threading

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


class SQLGeneratorAgent:
    def __init__(self, model_path: str = "./models/llama-2-7b-chat.Q4_K_M.gguf", temperature: float = 0.1):
        self.model_path = model_path
        self.temperature = temperature
        self.llm = None
        self.llm_loaded = False
        self.llm_error = None
        
        # Check if model file exists
        if not os.path.exists(model_path):
            print(f"❌ Model file not found: {model_path}")
            self.llm_error = f"Model file not found: {model_path}"
            return
        
        if Llama is not None:
            try:
                print(f"🔄 Loading LLM model: {model_path}")
                start_time = time.time()
                
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # Increased context window for better performance
                    n_threads=4,  # Reduced threads to prevent overload
                    n_gpu_layers=1,  # Use GPU if available
                    n_batch=512,  # Batch size
                    temperature=temperature,
                    verbose=False,  # Reduce verbose output
                )
                
                load_time = time.time() - start_time
                print(f"✅ LLM loaded successfully in {load_time:.2f}s")
                self.llm_loaded = True
                
                # Test the LLM with a simple query
                try:
                    test_output = self.llm(
                        "Say 'Hello'",
                        max_tokens=10,
                        temperature=0.1,
                        stop=["\n"],
                        echo=False
                    )
                    if test_output and "choices" in test_output:
                        print(f"✅ LLM test successful: {test_output['choices'][0]['text'].strip()}")
                    else:
                        print(f"⚠️ LLM test failed: No output")
                        self.llm_loaded = False
                except Exception as test_e:
                    print(f"⚠️ LLM test failed: {test_e}")
                    self.llm_loaded = False
                    
            except Exception as e:
                print(f"❌ Failed to load Llama model: {e}")
                import traceback
                traceback.print_exc()
                self.llm = None
                self.llm_error = str(e)
        else:
            print(f"❌ Llama-cpp-python not available")
            self.llm_error = "Llama-cpp-python not installed"

    def _call_llm_with_timeout(self, prompt: str, timeout_seconds: int = 30) -> dict:
        """Call LLM with timeout to prevent hanging"""
        if not self.llm_loaded or self.llm is None:
            return None
            
        result = [None]
        exception = [None]
        
        def llm_call():
            try:
                result[0] = self.llm(
                    prompt,
                    max_tokens=1024,
                    temperature=self.temperature,
                    stop=["Q:", "\n\n", "```"],
                    top_p=0.95,
                    repeat_penalty=1.2,
                    top_k=50,
                    echo=False
                )
            except Exception as e:
                exception[0] = e
        
        # Start LLM call in a separate thread
        thread = threading.Thread(target=llm_call)
        thread.daemon = True
        thread.start()
        
        # Wait for completion or timeout
        thread.join(timeout_seconds)
        
        if thread.is_alive():
            print(f"⏰ LLM call timed out after {timeout_seconds}s")
            return None
        
        if exception[0]:
            print(f"❌ LLM call failed: {exception[0]}")
            return None
            
        return result[0]

    def build_prompt(self, query: str, schema_context: typing.List[str]) -> str:
        schema_str = "\n".join(schema_context)

        examples = """
        Q: List all customers in Hyderabad.
        A:
        SELECT id, first_name, last_name
        FROM customers
        WHERE address LIKE '%Hyderabad%';

        Q: Show last 5 transactions.
        A:
        SELECT *
        FROM transactions
        ORDER BY transaction_date DESC
        LIMIT 5;
        """

        system = """
        You are a SQL assistant.
        Rules:
        - Only generate SELECT queries.
        - Only use provided schema.
        - Never modify data (no UPDATE/DELETE/DROP).
        - Return SQL only inside code block.
        """

        return f"""{system}

Database Schema:
{schema_str}

Examples:
{examples}

Now answer this:
Q: {query}
A:
"""

    # New API method
    def generate(
        self,
        user_query: str,
        constraints: typing.Dict[str, typing.Any],
        retrieval_context: typing.Dict[str, typing.Any],
        schema_tables: typing.Dict[str, typing.Any],
    ) -> str:
        """Intelligent SQL generation using LLM and VectorDB context."""
        print(f"🧠 INTELLIGENT GENERATION: Starting generation for query: {user_query}")
        
        schema_context = retrieval_context.get("schema_context", [])
        value_hints = retrieval_context.get("value_hints", [])
        exemplars = retrieval_context.get("exemplars", [])
        query_analysis = retrieval_context.get("query_analysis", {})
        
        print(f"📊 RETRIEVER CONTEXT: Schema items={len(schema_context)}, Value hints={len(value_hints)}, Exemplars={len(exemplars)}")
        
        # Show actual value hints being used
        if value_hints:
            print(f"🎯 ACTUAL VALUE HINTS RECEIVED:")
            for i, hint in enumerate(value_hints[:5]):  # Show first 5
                if isinstance(hint, dict):
                    if 'table' in hint and 'column' in hint:
                        values_str = ', '.join(hint.get('values', [])[:5])
                        print(f"  {i+1}. {hint['table']}.{hint['column']}: {values_str}...")
                    elif 'type' in hint and hint['type'] == 'numeric_threshold':
                        print(f"  {i+1}. Numeric threshold: {hint.get('value', 'N/A')}")
                    elif 'description' in hint:
                        print(f"  {i+1}. {hint['description']}")
        
        # Show exemplars being used
        if exemplars:
            print(f"📚 EXEMPLARS RECEIVED:")
            for i, exemplar in enumerate(exemplars[:3]):  # Show first 3
                print(f"  {i+1}. {exemplar}")
        
        # Step 1: Analyze query requirements (use retriever's analysis if available)
        if query_analysis:
            required_entities = query_analysis
            print(f"🎯 USING RETRIEVER ANALYSIS: {required_entities}")
        else:
            required_entities = self._identify_required_entities(user_query, schema_context, {})
            print(f"🎯 GENERATION ANALYSIS: Required entities: {required_entities}")
        
        # Step 2: Build enhanced prompt with comprehensive context including value hints and exemplars
        enhanced_prompt = self._build_enhanced_generation_prompt(
            user_query, 
            schema_context, 
            required_entities,
            value_hints,
            exemplars
        )
        
        # Step 3: Attempt LLM generation with enhanced context
        if self.llm_loaded:
            print(f"🧠 INTELLIGENT GENERATION: Attempting LLM generation with enhanced context...")
            start_time = time.time()
            
            output = self._call_llm_with_timeout(enhanced_prompt, timeout_seconds=45)
            
            generation_time = time.time() - start_time
            print(f"⏱️ INTELLIGENT GENERATION: LLM generation took {generation_time:.2f}s")

            if output and "choices" in output and len(output["choices"]) > 0:
                sql = output["choices"][0]["text"].strip()
                # Extract SQL from code blocks if present
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                
                if sql and len(sql) > 10:
                    print(f"✅ INTELLIGENT GENERATION: LLM generation successful")
                    print(f"🔧 GENERATED SQL: {sql}")
                return sql
                else:
                    print(f"⚠️ INTELLIGENT GENERATION: LLM output too short: '{sql}'")
            else:
                print(f"⚠️ INTELLIGENT GENERATION: LLM generation failed - no output")
        
        # Step 4: Fallback to intelligent pattern-based generation with value hints
        print(f"🔄 INTELLIGENT GENERATION: Falling back to pattern-based generation...")
        return self._intelligent_pattern_generation(user_query, required_entities, value_hints)
    
    def _build_enhanced_generation_prompt(self, user_query: str, schema_context: list, required_entities: dict, value_hints: list = None, exemplars: list = None) -> str:
        """Build enhanced generation prompt with comprehensive context including value hints and exemplars."""
        
        # Format value hints for the prompt
        value_hints_text = ""
        if value_hints:
            value_hints_text = "\n=== VALUE HINTS FOR WHERE CONDITIONS ===\n"
            for i, hint in enumerate(value_hints, 1):
                if isinstance(hint, dict):
                    if 'table' in hint and 'column' in hint:
                        values_str = ', '.join(hint.get('values', [])[:5])  # Show first 5 values
                        value_hints_text += f"{i}. {hint['table']}.{hint['column']}: {values_str}...\n"
                    elif 'type' in hint and hint['type'] == 'numeric_threshold':
                        value_hints_text += f"{i}. Numeric threshold: {hint.get('value', 'N/A')}\n"
                    elif 'description' in hint:
                        value_hints_text += f"{i}. {hint['description']}\n"
        
        # Format exemplars for the prompt
        exemplars_text = ""
        if exemplars:
            exemplars_text = "\n=== SIMILAR QUERY EXAMPLES ===\n"
            for i, exemplar in enumerate(exemplars, 1):
                exemplars_text += f"{i}. {exemplar}\n"
        
        prompt = f"""
You are an expert SQL generation assistant. Your task is to generate a SQL query from natural language.

=== QUERY REQUIREMENTS ===
Natural Language Query: {user_query}
Required Tables: {', '.join(required_entities.get('required_tables', []))}
Required Columns: {', '.join(required_entities.get('required_columns', []))}
Operations: {', '.join(required_entities.get('operations', []))}
Conditions: {', '.join(required_entities.get('conditions', []))}
Joins Needed: {required_entities.get('joins_needed', False)}

=== COMPREHENSIVE SCHEMA CONTEXT ===
{chr(10).join(schema_context)}

=== TABLE RELATIONSHIPS ===
customers.id → accounts.customer_id
accounts.id → transactions.account_id
employees.id → branches.manager_id
customers.branch_id → branches.id
employees.branch_id → branches.id

{value_hints_text}

{exemplars_text}

=== GENERATION INSTRUCTIONS ===
1. Analyze the natural language query to understand the intent
2. Use the value hints to create precise WHERE conditions with actual values from the database
3. Identify the appropriate tables and columns from the schema
4. Create proper JOIN conditions between related tables
5. Apply appropriate WHERE conditions based on the query requirements and value hints
6. Use correct aggregation functions if needed (COUNT, SUM, AVG, etc.)
7. Add proper ORDER BY clauses if sorting is required
8. Generate a complete, executable SQL query

=== OUTPUT FORMAT ===
Generate only the SQL query without any explanations or markdown formatting.

SQL Query:
"""
        return prompt
    
    def _intelligent_pattern_generation(self, user_query: str, required_entities: dict, value_hints: list = None) -> str:
        """Intelligent pattern-based generation when LLM is not available."""
        print(f"🔄 INTELLIGENT PATTERN GENERATION: Using pattern-based approach...")
        
        query_lower = user_query.lower()
        required_tables = required_entities.get("required_tables", [])
        operations = required_entities.get("operations", [])
        conditions = required_entities.get("conditions", [])
        where_conditions = required_entities.get("where_conditions", {})
        
        print(f"🎯 PATTERN GENERATION: Operations={operations}, Conditions={conditions}, WHERE={where_conditions}")
        
        # If we have identified required tables, use them
        if required_tables:
            primary_table = required_tables[0]
            print(f"🎯 PATTERN GENERATION: Using primary table '{primary_table}'")
            
            # Check for specific patterns with value hints
            if "employees" in required_tables and "position" in required_entities.get("required_columns", []):
                if "AVG" in operations and "salary" in required_entities.get("required_columns", []):
                    # Employee position average salary query
                    threshold = where_conditions.get("numeric_threshold", 80000)
                    return f"""
                    SELECT position, AVG(salary) as average_salary
                    FROM employees
                    GROUP BY position
                    HAVING AVG(salary) > {threshold}
                    ORDER BY average_salary DESC;
                    """
            
            if "customers" in required_tables and "accounts" in required_tables:
                if "checking" in query_lower and "savings" in query_lower:
                    # Customers with both checking and savings accounts
                    return """
                    SELECT DISTINCT c.id, c.first_name, c.last_name
                    FROM customers c
                    INNER JOIN accounts a1 ON c.id = a1.customer_id AND a1.type = 'checking'
                    INNER JOIN accounts a2 ON c.id = a2.customer_id AND a2.type = 'savings'
                    ORDER BY c.last_name, c.first_name;
                    """
            
            if "accounts" in required_tables and "transactions" in required_tables:
                if "COUNT" in operations and "type" in required_entities.get("required_columns", []):
                    threshold = where_conditions.get("numeric_threshold", 1000000)
                    return f"""
                    SELECT t.type, COUNT(*) as transaction_count
                    FROM transactions t
                    INNER JOIN accounts a ON t.account_id = a.id
                    WHERE a.balance > {threshold}
                    GROUP BY t.type
                    ORDER BY transaction_count DESC;
                    """
            
            # Generate basic query with identified table
            if operations:
                if "COUNT" in operations:
                    return f"SELECT COUNT(*) as total_count FROM {primary_table};"
                elif "AVG" in operations:
                    return f"SELECT AVG(id) as average_value FROM {primary_table};"
                elif "SUM" in operations:
                    return f"SELECT SUM(id) as total_sum FROM {primary_table};"
            
            # Basic select query
            return f"SELECT * FROM {primary_table} LIMIT 10;"
        
        # Fallback to keyword-based table selection
        print(f"⚠️ PATTERN GENERATION: No specific tables identified, using keyword fallback")
        return self._intelligent_fallback(user_query, {})

    def _intelligent_fallback(self, user_query: str, schema_tables: dict) -> str:
        """Intelligent fallback when LLM is not available"""
        print(f"🎯 Using intelligent fallback for: {user_query}")
        
        # Use the new entity identification method for consistency
        required_entities = self._identify_required_entities(user_query, [], {})
        required_tables = required_entities.get("required_tables", [])
        
        # Use the first relevant table, or fall back to first available table
        if required_tables:
            target_table = required_tables[0]
            print(f"🎯 Intelligent fallback: Using table '{target_table}' based on entity analysis")
            return f"SELECT * FROM {target_table} LIMIT 10;"
        else:
            # Last resort: use first table alphabetically
            first_table = next(iter(schema_tables.keys())) if schema_tables else ""
            print(f"⚠️ No relevant tables found, using first available: '{first_table}'")
            return f"SELECT * FROM {first_table} LIMIT 10;" if first_table else "SELECT 1;"

    # Old API method that pipeline.py expects
    def generate_sql(self, nl_query: str, gen_ctx: dict) -> str:
        """Old API method that pipeline.py expects - now uses intelligent generation."""
        print(f"🔧 LEGACY GENERATE_SQL: Using intelligent generation for: {nl_query}")
        
        # Use the new intelligent generation approach
        return self.generate(
            user_query=nl_query,
            constraints={},
            retrieval_context=gen_ctx,
            schema_tables=gen_ctx.get("schema_tables", {})
        )

    def repair_sql(self, nl_query: str, gen_ctx: dict, hint: str = "") -> str:
        """Intelligent SQL repair using LLM and VectorDB for schema validation and table/column identification."""
        print(f"🔧 INTELLIGENT REPAIR: Starting repair for query: {nl_query}")
        print(f"🔧 INTELLIGENT REPAIR: Error hint: {hint}")
        
        schema_context = gen_ctx.get("schema_context", [])
        value_hints = gen_ctx.get("value_hints", [])
        exemplars = gen_ctx.get("exemplars", [])
        query_analysis = gen_ctx.get("query_analysis", {})
        schema_tables = gen_ctx.get("schema_tables", {})
        
        print(f"📊 REPAIR CONTEXT: Schema items={len(schema_context)}, Value hints={len(value_hints)}, Exemplars={len(exemplars)}")
        
        # Step 1: Analyze the error and extract required information
        error_analysis = self._analyze_sql_error(hint, nl_query)
        print(f"🔍 ERROR ANALYSIS: {error_analysis}")
        
        # Step 2: Identify required tables and columns using VectorDB (use retriever's analysis if available)
        if query_analysis:
            required_entities = query_analysis
            print(f"🎯 USING RETRIEVER ANALYSIS FOR REPAIR: {required_entities}")
        else:
            required_entities = self._identify_required_entities(nl_query, schema_context, error_analysis)
            print(f"🎯 REQUIRED ENTITIES: {required_entities}")
        
        # Step 3: Generate enhanced context for repair
        enhanced_context = self._generate_enhanced_repair_context(
            nl_query, schema_context, required_entities, error_analysis
        )
        
        # Step 4: Create intelligent repair prompt with value hints and exemplars
        repair_prompt = self._create_intelligent_repair_prompt(
            nl_query, enhanced_context, error_analysis, required_entities, value_hints, exemplars
        )
        
        # Step 5: Attempt LLM repair with enhanced context
        if self.llm_loaded:
            print(f"🧠 INTELLIGENT REPAIR: Attempting LLM repair with enhanced context...")
            start_time = time.time()
            
            output = self._call_llm_with_timeout(repair_prompt, timeout_seconds=45)
            
            repair_time = time.time() - start_time
            print(f"⏱️ INTELLIGENT REPAIR: LLM repair took {repair_time:.2f}s")
            
            if output and "choices" in output and len(output["choices"]) > 0:
                sql = output["choices"][0]["text"].strip()
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                
                if sql and len(sql) > 10:
                    print(f"✅ INTELLIGENT REPAIR: LLM repair successful")
                    print(f"🔧 REPAIRED SQL: {sql}")
                return sql
                else:
                    print(f"⚠️ INTELLIGENT REPAIR: LLM output too short: '{sql}'")
            else:
                print(f"⚠️ INTELLIGENT REPAIR: LLM repair failed - no output")
        
        # Step 6: Fallback to intelligent pattern-based repair
        print(f"🔄 INTELLIGENT REPAIR: Falling back to pattern-based repair...")
        return self._intelligent_pattern_repair(nl_query, required_entities, error_analysis)
    
    def _analyze_sql_error(self, error_hint: str, nl_query: str) -> dict:
        """Analyze SQL error to understand what went wrong and what needs to be fixed."""
        error_lower = error_hint.lower()
        query_lower = nl_query.lower()
        
        analysis = {
            "error_type": "unknown",
            "missing_tables": [],
            "missing_columns": [],
            "join_issues": False,
            "syntax_issues": False,
            "data_type_issues": False,
            "suggested_fixes": []
        }
        
        # Identify error types
        if "no such table" in error_lower:
            analysis["error_type"] = "missing_table"
            # Extract table name from error
            import re
            table_match = re.search(r"no such table: (\w+)", error_lower)
            if table_match:
                analysis["missing_tables"].append(table_match.group(1))
        
        elif "no such column" in error_lower:
            analysis["error_type"] = "missing_column"
            # Extract column name from error
            import re
            column_match = re.search(r"no such column: (\w+)", error_lower)
            if column_match:
                analysis["missing_columns"].append(column_match.group(1))
        
        elif "syntax error" in error_lower:
            analysis["error_type"] = "syntax_error"
            analysis["syntax_issues"] = True
        
        elif "foreign key" in error_lower:
            analysis["error_type"] = "foreign_key_error"
            analysis["join_issues"] = True
        
        # Generate suggested fixes based on error type and query
        if analysis["error_type"] == "missing_table":
            analysis["suggested_fixes"].append("Identify correct table names from schema")
            analysis["suggested_fixes"].append("Check table relationships and joins")
        
        elif analysis["error_type"] == "missing_column":
            analysis["suggested_fixes"].append("Verify column names exist in referenced tables")
            analysis["suggested_fixes"].append("Check for column aliases or table prefixes")
        
        elif analysis["error_type"] == "syntax_error":
            analysis["suggested_fixes"].append("Review SQL syntax and structure")
            analysis["suggested_fixes"].append("Check for missing keywords or operators")
        
        return analysis
    
    def _identify_required_entities(self, nl_query: str, schema_context: list, error_analysis: dict) -> dict:
        """Identify required tables and columns using semantic analysis and VectorDB context."""
        query_lower = nl_query.lower()
        
        entities = {
            "required_tables": [],
            "required_columns": [],
            "join_conditions": [],
            "where_conditions": {},
            "aggregation_needed": False,
            "ordering_needed": False
        }
        
        # Extract table requirements from query keywords
        table_keywords = {
            "customers": ["customer", "client", "person", "name", "email", "phone"],
            "accounts": ["account", "banking", "balance", "type", "checking", "savings"],
            "transactions": ["transaction", "payment", "transfer", "amount", "date"],
            "employees": ["employee", "staff", "worker", "manager", "position"],
            "branches": ["branch", "location", "office", "city", "state"]
        }
        
        for table, keywords in table_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                entities["required_tables"].append(table)
        
        # Extract column requirements
        column_patterns = {
            "name": ["name", "first_name", "last_name"],
            "email": ["email", "mail"],
            "phone": ["phone", "telephone"],
            "balance": ["balance", "amount", "money"],
            "type": ["type", "account_type"],
            "date": ["date", "birth", "hire", "opened"],
            "gender": ["gender", "sex"],
            "position": ["position", "job", "role"]
        }
        
        for column, patterns in column_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                entities["required_columns"].append(column)
        
        # Identify aggregation needs
        if any(word in query_lower for word in ["count", "total", "number", "how many", "sum", "average"]):
            entities["aggregation_needed"] = True
        
        # Identify ordering needs
        if any(word in query_lower for word in ["order", "sort", "first", "last", "top", "bottom"]):
            entities["ordering_needed"] = True
        
        # Add missing entities from error analysis
        if error_analysis.get("missing_tables"):
            entities["required_tables"].extend(error_analysis["missing_tables"])
        
        if error_analysis.get("missing_columns"):
            entities["required_columns"].extend(error_analysis["missing_columns"])
        
        # Remove duplicates
        entities["required_tables"] = list(set(entities["required_tables"]))
        entities["required_columns"] = list(set(entities["required_columns"]))
        
        return entities
    
    def _generate_enhanced_repair_context(self, nl_query: str, schema_context: list, 
                                        required_entities: dict, error_analysis: dict) -> str:
        """Generate enhanced context for repair using schema information and error analysis."""
        
        enhanced_context = []
        enhanced_context.append("=== ENHANCED REPAIR CONTEXT ===")
        enhanced_context.append(f"Original Query: {nl_query}")
        enhanced_context.append(f"Error Type: {error_analysis.get('error_type', 'unknown')}")
        enhanced_context.append("")
        
        # Add schema context
        enhanced_context.append("=== SCHEMA INFORMATION ===")
        enhanced_context.extend(schema_context)
        enhanced_context.append("")
        
        # Add required entities analysis
        enhanced_context.append("=== REQUIRED ENTITIES ANALYSIS ===")
        enhanced_context.append(f"Required Tables: {', '.join(required_entities.get('required_tables', []))}")
        enhanced_context.append(f"Required Columns: {', '.join(required_entities.get('required_columns', []))}")
        enhanced_context.append(f"Aggregation Needed: {required_entities.get('aggregation_needed', False)}")
        enhanced_context.append(f"Ordering Needed: {required_entities.get('ordering_needed', False)}")
        enhanced_context.append("")
        
        # Add suggested fixes
        if error_analysis.get("suggested_fixes"):
            enhanced_context.append("=== SUGGESTED FIXES ===")
            for i, fix in enumerate(error_analysis["suggested_fixes"], 1):
                enhanced_context.append(f"{i}. {fix}")
            enhanced_context.append("")
        
        # Add table relationships
        enhanced_context.append("=== TABLE RELATIONSHIPS ===")
        enhanced_context.append("customers.id → accounts.customer_id")
        enhanced_context.append("accounts.id → transactions.account_id")
        enhanced_context.append("employees.id → branches.manager_id")
        enhanced_context.append("customers.branch_id → branches.id")
        enhanced_context.append("employees.branch_id → branches.id")
        enhanced_context.append("")
        
        return "\n".join(enhanced_context)
    
    def _create_intelligent_repair_prompt(self, nl_query: str, enhanced_context: str, 
                                        error_analysis: dict, required_entities: dict, 
                                        value_hints: list = None, exemplars: list = None) -> str:
        """Create an intelligent repair prompt with comprehensive context including value hints and exemplars."""
        
        # Format value hints for the repair prompt
        value_hints_text = ""
        if value_hints:
            value_hints_text = "\n=== VALUE HINTS FOR WHERE CONDITIONS ===\n"
            for i, hint in enumerate(value_hints, 1):
                if isinstance(hint, dict):
                    if 'table' in hint and 'column' in hint:
                        values_str = ', '.join(hint.get('values', [])[:5])  # Show first 5 values
                        value_hints_text += f"{i}. {hint['table']}.{hint['column']}: {values_str}...\n"
                    elif 'type' in hint and hint['type'] == 'numeric_threshold':
                        value_hints_text += f"{i}. Numeric threshold: {hint.get('value', 'N/A')}\n"
                    elif 'description' in hint:
                        value_hints_text += f"{i}. {hint['description']}\n"
        
        # Format exemplars for the repair prompt
        exemplars_text = ""
        if exemplars:
            exemplars_text = "\n=== SIMILAR QUERY EXAMPLES ===\n"
            for i, exemplar in enumerate(exemplars, 1):
                exemplars_text += f"{i}. {exemplar}\n"
        
        prompt = f"""
You are an expert SQL repair assistant. Your task is to fix a SQL query that failed execution.

=== ERROR ANALYSIS ===
Error Type: {error_analysis.get('error_type', 'unknown')}
Error Details: {error_analysis.get('suggested_fixes', [])}

=== QUERY REQUIREMENTS ===
Natural Language Query: {nl_query}
Required Tables: {', '.join(required_entities.get('required_tables', []))}
Required Columns: {', '.join(required_entities.get('required_columns', []))}
Operations: {', '.join(required_entities.get('operations', []))}
Conditions: {', '.join(required_entities.get('conditions', []))}
Joins Needed: {required_entities.get('joins_needed', False)}

=== COMPREHENSIVE SCHEMA CONTEXT ===
{enhanced_context}

{value_hints_text}

{exemplars_text}

=== REPAIR INSTRUCTIONS ===
1. Analyze the error and identify the root cause
2. Use the value hints to create precise WHERE conditions with actual values from the database
3. Use the schema information to identify correct table and column names
4. Ensure proper JOIN conditions between tables
5. Apply appropriate WHERE conditions based on the natural language query and value hints
6. Use correct aggregation functions if needed (COUNT, SUM, AVG, etc.)
7. Add proper ORDER BY clauses if sorting is required
8. Generate a complete, executable SQL query

=== OUTPUT FORMAT ===
Generate only the SQL query without any explanations or markdown formatting.

SQL Query:
"""
        return prompt
    
    def _intelligent_pattern_repair(self, nl_query: str, required_entities: dict, error_analysis: dict) -> str:
        """Intelligent pattern-based repair when LLM is not available."""
        print(f"🔄 INTELLIGENT PATTERN REPAIR: Using pattern-based approach...")
        
        query_lower = nl_query.lower()
        required_tables = required_entities.get("required_tables", [])
        
        # If we have identified required tables, use them
        if required_tables:
            primary_table = required_tables[0]
            print(f"🎯 PATTERN REPAIR: Using primary table '{primary_table}'")
            
            # Generate basic query with identified table
            if required_entities.get("aggregation_needed"):
                # Aggregation query
                if "count" in query_lower or "total" in query_lower or "number" in query_lower:
                    if "customer" in query_lower and "account" in query_lower:
                        return """
                        SELECT c.gender, COUNT(a.id) as total_accounts
                        FROM customers c
                        LEFT JOIN accounts a ON c.id = a.customer_id
                        WHERE c.gender IS NOT NULL
                        GROUP BY c.gender
                        ORDER BY total_accounts DESC;
                        """
                    else:
                        return f"SELECT COUNT(*) as total_count FROM {primary_table};"
            
            # Basic select query
            return f"SELECT * FROM {primary_table} LIMIT 10;"
        
        # Fallback to keyword-based table selection
        print(f"⚠️ PATTERN REPAIR: No specific tables identified, using keyword fallback")
        return self._intelligent_fallback(nl_query, {})
