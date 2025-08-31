import typing
import re
from backend.embedder import EnhancedRetriever

class RetrieverAgent:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.enhanced_retriever = None
        
        print(f"🔍 RETRIEVER AGENT: Initializing with db_path: {db_path}")
        
        try:
            # Initialize enhanced retriever with Ollama embeddings
            self.enhanced_retriever = EnhancedRetriever(
                ollama_model="llama2",
                chroma_persist_dir=db_path
            )
            print(f"✅ RETRIEVER AGENT: Enhanced retriever initialized successfully")
        except Exception as e:
            print(f"❌ RETRIEVER AGENT: Failed to initialize enhanced retriever: {e}")
            print(f"🔄 RETRIEVER AGENT: Falling back to basic retrieval")
            self.enhanced_retriever = None

    def retrieve(self, query: str, schema_tables: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Retrieve relevant context for a query using enhanced retriever with intelligent analysis
        
        Args:
            query: Natural language query
            schema_tables: Database schema information
            
        Returns:
            Dictionary containing retrieved context with intelligent analysis
        """
        print(f"🔍 RETRIEVER AGENT: Starting intelligent retrieval for query: {query}")
        
        # Step 1: Analyze query to detect required tables and columns
        query_analysis = self._analyze_query(query, schema_tables)
        print(f"🎯 RETRIEVER AGENT: Query analysis: {query_analysis}")
        
        # Step 2: Get enhanced context from VectorDB
        enhanced_context = self._get_enhanced_context(query, query_analysis)
        
        # Step 3: Get distinct values for WHERE conditions
        value_hints = self._get_value_hints(query_analysis, enhanced_context)
        
        # Step 4: Get exemplars (similar queries)
        exemplars = self._get_exemplars(query, enhanced_context)
        
        # Step 5: Build comprehensive output
        result = {
            "schema_context": enhanced_context.get("schema_context", []),
            "schema_context_count": len(enhanced_context.get("schema_context", [])),
            "schema_context_preview": enhanced_context.get("schema_context", [])[:3],  # First 3 items
            "value_hints_count": len(value_hints),
            "value_hints": value_hints,
            "exemplars_count": len(exemplars),
            "exemplars": exemplars,
            "retrieval_method": enhanced_context.get("retrieval_method", "fallback"),
            "query_analysis": query_analysis,
            "chromadb_interactions": enhanced_context.get("chromadb_interactions", {}),
            "ollama_interactions": enhanced_context.get("ollama_interactions", {}),
            "vector_search_details": enhanced_context.get("vector_search_details", {})
        }
        
        print(f"✅ RETRIEVER AGENT: Intelligent retrieval completed")
        print(f"📊 RETRIEVER AGENT: Schema context: {result['schema_context_count']} items")
        print(f"🎯 RETRIEVER AGENT: Value hints: {result['value_hints_count']} items")
        print(f"📚 RETRIEVER AGENT: Exemplars: {result['exemplars_count']} items")
        
        return result

    def _fallback_retrieval(self, query: str, schema_tables: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Fallback retrieval method when enhanced retriever is not available
        
        Args:
            query: Natural language query
            schema_tables: Database schema information
            
        Returns:
            Dictionary containing basic context
        """
        print(f"🔄 RETRIEVER AGENT: Using fallback retrieval method")
        
        # Basic context based on query keywords
        context = []
        
        # Add table information based on query keywords
        query_lower = query.lower()
        
        if "customer" in query_lower:
            context.append("Table customers contains customer information")
            context.append("Customers have id, first_name, last_name, email, phone, address, date_of_birth, gender, national_id, branch_id")
        
        if "account" in query_lower:
            context.append("Table accounts contains account information")
            context.append("Accounts have id, customer_id, account_number, type, balance, opened_at, interest_rate, status, branch_id")
            context.append("Account types include: checking, savings, credit, loan")
        
        if "branch" in query_lower:
            context.append("Table branches contains branch information")
            context.append("Branches have id, name, address, city, state, zip_code, manager_id")
        
        if "employee" in query_lower:
            context.append("Table employees contains employee information")
            context.append("Employees have id, branch_id, name, email, phone, position, hire_date, salary")
        
        if "transaction" in query_lower:
            context.append("Table transactions contains transaction information")
            context.append("Transactions have id, account_id, transaction_date, amount, type, description, status, employee_id")
            context.append("Transaction types include: deposit, withdrawal, transfer, fee, interest")
        
        # Add relationships
        context.append("Customers can have multiple accounts (one-to-many relationship)")
        context.append("Accounts belong to customers (foreign key: customer_id)")
        context.append("Branches can have multiple employees (one-to-many relationship)")
        context.append("Employees belong to branches (foreign key: branch_id)")
        context.append("Accounts can have multiple transactions (one-to-many relationship)")
        context.append("Transactions belong to accounts (foreign key: account_id)")
        
        print(f"✅ RETRIEVER AGENT: Generated {len(context)} fallback context items")
        
        return {
            "schema_context": context,
            "retrieval_method": "fallback_keyword_based",
            "context_count": len(context)
        }

    def _analyze_query(self, query: str, schema_tables: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Analyze query to detect required tables, columns, and operations
        
        Args:
            query: Natural language query
            schema_tables: Database schema information
            
        Returns:
            Dictionary containing query analysis
        """
        query_lower = query.lower()
        
        analysis = {
            "required_tables": [],
            "required_columns": [],
            "operations": [],
            "conditions": [],
            "aggregations": [],
            "joins_needed": [],
            "where_conditions": {}
        }
        
        # Detect tables
        table_keywords = {
            "customers": ["customer", "client", "person"],
            "accounts": ["account", "banking", "balance"],
            "transactions": ["transaction", "payment", "transfer", "deposit", "withdrawal"],
            "employees": ["employee", "staff", "worker", "position", "salary"],
            "branches": ["branch", "location", "office", "city", "state"]
        }
        
        for table, keywords in table_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                analysis["required_tables"].append(table)
        
        # Detect columns
        column_patterns = {
            "position": ["position", "job", "role", "title"],
            "salary": ["salary", "pay", "wage", "income"],
            "name": ["name", "first_name", "last_name"],
            "email": ["email", "mail"],
            "phone": ["phone", "telephone"],
            "type": ["type", "account_type", "transaction_type"],
            "amount": ["amount", "money", "balance"],
            "date": ["date", "hire_date", "transaction_date", "opened_at"],
            "gender": ["gender", "sex"],
            "city": ["city", "location"],
            "state": ["state", "region"]
        }
        
        for column, patterns in column_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                analysis["required_columns"].append(column)
        
        # Detect operations
        if any(word in query_lower for word in ["count", "total", "number", "how many"]):
            analysis["operations"].append("COUNT")
        if any(word in query_lower for word in ["average", "avg", "mean"]):
            analysis["operations"].append("AVG")
        if any(word in query_lower for word in ["sum", "total", "sum of"]):
            analysis["operations"].append("SUM")
        if any(word in query_lower for word in ["maximum", "max", "highest"]):
            analysis["operations"].append("MAX")
        if any(word in query_lower for word in ["minimum", "min", "lowest"]):
            analysis["operations"].append("MIN")
        
        # Detect conditions
        if any(word in query_lower for word in ["above", "greater than", "more than", ">"]):
            analysis["conditions"].append("greater_than")
        if any(word in query_lower for word in ["below", "less than", "<"]):
            analysis["conditions"].append("less_than")
        if any(word in query_lower for word in ["equal", "=", "is"]):
            analysis["conditions"].append("equal")
        if any(word in query_lower for word in ["between", "range"]):
            analysis["conditions"].append("between")
        
        # Detect joins
        if len(analysis["required_tables"]) > 1:
            analysis["joins_needed"] = True
        
        # Extract specific values for WHERE conditions
        where_conditions = self._extract_where_conditions(query)
        analysis["where_conditions"] = where_conditions
        
        return analysis
    
    def _extract_where_conditions(self, query: str) -> typing.Dict[str, typing.Any]:
        """
        Extract specific values that might be used in WHERE conditions
        
        Args:
            query: Natural language query
            
        Returns:
            Dictionary of potential WHERE conditions
        """
        conditions = {}
        query_lower = query.lower()
        
        # Extract numeric values
        numeric_patterns = [
            r'above (\d+)',
            r'greater than (\d+)',
            r'more than (\d+)',
            r'(\d+) or more',
            r'(\d+) and above'
        ]
        
        for pattern in numeric_patterns:
            matches = re.findall(pattern, query_lower)
            if matches:
                conditions["numeric_threshold"] = int(matches[0])
                break
        
        # Extract specific values
        value_patterns = {
            "position": r'position[s]?\s+(?:of\s+)?([a-zA-Z\s]+)',
            "type": r'type[s]?\s+(?:of\s+)?([a-zA-Z\s]+)',
            "status": r'status[s]?\s+(?:of\s+)?([a-zA-Z\s]+)',
            "gender": r'gender[s]?\s+(?:of\s+)?([a-zA-Z\s]+)'
        }
        
        for key, pattern in value_patterns.items():
            matches = re.findall(pattern, query_lower)
            if matches:
                conditions[key] = matches[0].strip()
        
        return conditions
    
    def _get_enhanced_context(self, query: str, query_analysis: typing.Dict[str, typing.Any]) -> typing.Dict[str, typing.Any]:
        """
        Get enhanced context from VectorDB based on query analysis
        
        Args:
            query: Natural language query
            query_analysis: Query analysis results
            
        Returns:
            Dictionary containing enhanced context
        """
        try:
            if self.enhanced_retriever:
                print(f"🧠 RETRIEVER AGENT: Using enhanced retriever with Ollama embeddings")
                
                # Retrieve context using vector database
                retrieval_result = self.enhanced_retriever.retrieve_context_with_details(query, n_results=8)
                
                if retrieval_result and retrieval_result.get('context_items'):
                    context_items = retrieval_result['context_items']
                    print(f"✅ RETRIEVER AGENT: Retrieved {len(context_items)} context items from vector database")
                    
                    return {
                        "schema_context": context_items,
                        "retrieval_method": "enhanced_vector_db",
                        "chromadb_interactions": retrieval_result.get('chromadb_interactions', {}),
                        "ollama_interactions": retrieval_result.get('ollama_interactions', {}),
                        "vector_search_details": retrieval_result.get('vector_search_details', {})
                    }
                else:
                    print(f"⚠️ RETRIEVER AGENT: No context retrieved from vector database, using fallback")
                    return self._fallback_retrieval(query, {})
            else:
                print(f"🔄 RETRIEVER AGENT: Using fallback retrieval method")
                return self._fallback_retrieval(query, {})
                
        except Exception as e:
            print(f"❌ RETRIEVER AGENT: Error in enhanced retrieval: {e}")
            print(f"🔄 RETRIEVER AGENT: Falling back to basic retrieval")
            return self._fallback_retrieval(query, {})
    
    def _get_value_hints(self, query_analysis: typing.Dict[str, typing.Any], enhanced_context: typing.Dict[str, typing.Any]) -> typing.List[typing.Dict[str, typing.Any]]:
        """
        Get distinct values for columns that might be used in WHERE conditions
        
        Args:
            query_analysis: Query analysis results
            enhanced_context: Enhanced context from VectorDB
            
        Returns:
            List of value hints for WHERE conditions
        """
        value_hints = []
        
        try:
            # Extract value hints from VectorDB context
            context_items = enhanced_context.get("schema_context", [])
            
            for item in context_items:
                if "has values:" in item:
                    # Extract table, column, and values
                    parts = item.split(" column ")
                    if len(parts) == 2:
                        table_part = parts[0].replace("Table ", "")
                        column_part = parts[1].split(" has values:")[0]
                        values_part = item.split(" has values: ")[1]
                        
                        # Parse values
                        values = []
                        if " and " in values_part:
                            values_text = values_part.split(" and ")[0]
                            values = [v.strip() for v in values_text.split(", ")]
                        else:
                            values = [v.strip() for v in values_part.split(", ")]
                        
                        value_hints.append({
                            "table": table_part,
                            "column": column_part,
                            "values": values[:10],  # Limit to first 10 values
                            "total_count": len(values)
                        })
            
            # Add specific hints based on query analysis
            where_conditions = query_analysis.get("where_conditions", {})
            
            if "numeric_threshold" in where_conditions:
                value_hints.append({
                    "type": "numeric_threshold",
                    "value": where_conditions["numeric_threshold"],
                    "description": f"Use values greater than {where_conditions['numeric_threshold']}"
                })
            
            for key, value in where_conditions.items():
                if key != "numeric_threshold":
                    value_hints.append({
                        "type": "specific_value",
                        "column": key,
                        "value": value,
                        "description": f"Filter by {key} = '{value}'"
                    })
            
        except Exception as e:
            print(f"⚠️ RETRIEVER AGENT: Error extracting value hints: {e}")
        
        return value_hints
    
    def _get_exemplars(self, query: str, enhanced_context: typing.Dict[str, typing.Any]) -> typing.List[str]:
        """
        Get exemplars (similar queries) from VectorDB context
        
        Args:
            query: Natural language query
            enhanced_context: Enhanced context from VectorDB
            
        Returns:
            List of exemplar queries
        """
        exemplars = []
        
        try:
            # Extract exemplars from context items that contain similar patterns
            context_items = enhanced_context.get("schema_context", [])
            query_lower = query.lower()
            
            # Look for similar patterns in the context
            if "average" in query_lower or "avg" in query_lower:
                exemplars.append("Find average salary by employee position")
                exemplars.append("Calculate average balance by account type")
            
            if "count" in query_lower or "total" in query_lower:
                exemplars.append("Count customers by gender")
                exemplars.append("Count transactions by type")
            
            if "position" in query_lower and "salary" in query_lower:
                exemplars.append("Find employees by position with salary above threshold")
                exemplars.append("Group employees by position and calculate average salary")
            
            # Add more exemplars based on detected patterns
            if len(exemplars) == 0:
                exemplars.append("Example: Find all customers with checking accounts")
                exemplars.append("Example: List employees by branch location")
                exemplars.append("Example: Show transaction history for specific account")
            
        except Exception as e:
            print(f"⚠️ RETRIEVER AGENT: Error extracting exemplars: {e}")
        
        return exemplars

    def populate_vector_database(self, schema_info: typing.Dict, column_values: typing.Dict):
        """
        Populate the vector database with schema and column information
        
        Args:
            schema_info: Database schema information
            column_values: Column values dictionary
        """
        print(f"📊 RETRIEVER AGENT: Populating vector database with schema and column information")
        
        try:
            if self.enhanced_retriever:
                self.enhanced_retriever.populate_vector_db(schema_info, column_values)
                print(f"✅ RETRIEVER AGENT: Vector database populated successfully")
            else:
                print(f"⚠️ RETRIEVER AGENT: Enhanced retriever not available, skipping vector database population")
        except Exception as e:
            print(f"❌ RETRIEVER AGENT: Error populating vector database: {e}")
            print(f"🔄 RETRIEVER AGENT: Continuing without vector database population")
