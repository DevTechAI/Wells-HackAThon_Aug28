#!/usr/bin/env python3
"""
Planner Agent for SQL RAG Agent
Analyzes natural language queries and determines required components
"""

import re
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class PlannerAgent:
    """Planner agent that analyzes queries and determines requirements"""
    
    def __init__(self, schema_tables: Dict[str, Any]):
        self.schema_tables = schema_tables
        self.table_names = list(schema_tables.keys())
        
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze natural language query and determine requirements"""
        logger.info(f"📋 Planner: Analyzing query: {query}")
        
        # Extract entities and requirements
        analysis = {
            "query": query,
            "entities": self._extract_entities(query),
            "tables_needed": self._identify_tables(query),
            "operations": self._identify_operations(query),
            "complexity": self._assess_complexity(query),
            "clarifications": self._check_clarifications(query),
            "estimated_tokens": self._estimate_tokens(query)
        }
        
        logger.info(f"📋 Planner: Analysis complete - {analysis}")
        return analysis
    
    def _extract_entities(self, query: str) -> List[str]:
        """Extract entities mentioned in the query"""
        entities = []
        query_lower = query.lower()
        
        # Common banking entities
        banking_entities = [
            "customer", "customers", "account", "accounts", "transaction", "transactions",
            "branch", "branches", "employee", "employees", "manager", "managers",
            "salary", "salaries", "balance", "balances", "amount", "amounts"
        ]
        
        for entity in banking_entities:
            if entity in query_lower:
                entities.append(entity)
        
        return entities
    
    def _identify_tables(self, query: str) -> List[str]:
        """Identify which tables are needed for the query"""
        tables_needed = []
        query_lower = query.lower()
        
        # Map entities to tables
        entity_table_mapping = {
            "customer": "customers",
            "customers": "customers",
            "account": "accounts",
            "accounts": "accounts",
            "transaction": "transactions",
            "transactions": "transactions",
            "branch": "branches",
            "branches": "branches",
            "employee": "employees",
            "employees": "employees",
            "manager": "employees",
            "managers": "employees"
        }
        
        for entity, table in entity_table_mapping.items():
            if entity in query_lower and table in self.table_names:
                if table not in tables_needed:
                    tables_needed.append(table)
        
        return tables_needed
    
    def _identify_operations(self, query: str) -> List[str]:
        """Identify operations needed for the query"""
        operations = []
        query_lower = query.lower()
        
        # Common operations
        if any(word in query_lower for word in ["count", "number", "how many"]):
            operations.append("COUNT")
        
        if any(word in query_lower for word in ["sum", "total", "sum of"]):
            operations.append("SUM")
        
        if any(word in query_lower for word in ["average", "avg", "mean"]):
            operations.append("AVG")
        
        if any(word in query_lower for word in ["maximum", "max", "highest"]):
            operations.append("MAX")
        
    def plan_with_schema_metadata(self, query: str, schema_context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan SQL generation using rich schema metadata and distinct values"""
        logger.info(f"📋 Planner: Planning with schema metadata for query: {query}")
        
        # Extract schema metadata
        schema_metadata = schema_context.get('schema_metadata', {})
        distinct_values = schema_context.get('distinct_values', {})
        where_suggestions = schema_context.get('where_suggestions', {})
        
        # Basic query analysis
        analysis = self.analyze_query(query)
        
        # Enhance with schema metadata
        enhanced_analysis = {
            **analysis,
            "schema_metadata": schema_metadata,
            "distinct_values": distinct_values,
            "where_suggestions": where_suggestions,
            "table_details": self._extract_table_details(query, schema_metadata),
            "column_mappings": self._extract_column_mappings(query, distinct_values),
            "where_conditions": self._suggest_where_conditions(query, distinct_values),
            "join_requirements": self._identify_join_requirements(query, schema_metadata),
            "value_constraints": self._extract_value_constraints(query, distinct_values)
        }
        
        logger.info(f"📋 Planner: Enhanced analysis complete with schema metadata")
        return enhanced_analysis
    
    def _extract_table_details(self, query: str, schema_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant table details for the query"""
        table_details = {}
        query_lower = query.lower()
        
        for table_name, metadata in schema_metadata.items():
            if table_name.lower() in query_lower or any(word in query_lower for word in table_name.lower().split('_')):
                table_details[table_name] = {
                    'table_name': table_name,
                    'column_count': metadata.get('column_count', 0),
                    'has_primary_key': metadata.get('has_primary_key', False),
                    'distinct_values_count': metadata.get('distinct_values_count', 0),
                    'value_distributions_count': metadata.get('value_distributions_count', 0)
                }
        
        return table_details
    
    def _extract_column_mappings(self, query: str, distinct_values: Dict[str, Dict[str, List[Any]]]) -> Dict[str, List[str]]:
        """Extract column mappings based on query and distinct values"""
        column_mappings = {}
        query_lower = query.lower()
        
        for table_name, columns in distinct_values.items():
            table_columns = []
            
            for column_name, values in columns.items():
                # Check if column name or values are mentioned in query
                if (column_name.lower() in query_lower or 
                    any(str(value).lower() in query_lower for value in values[:5])):
                    table_columns.append(column_name)
            
            if table_columns:
                column_mappings[table_name] = table_columns
        
        return column_mappings
    
    def _suggest_where_conditions(self, query: str, distinct_values: Dict[str, Dict[str, List[Any]]]) -> List[str]:
        """Suggest WHERE conditions based on query and distinct values"""
        where_conditions = []
        query_lower = query.lower()
        
        for table_name, columns in distinct_values.items():
            for column_name, values in columns.items():
                # Look for value mentions in query
                for value in values[:10]:  # Check first 10 values
                    value_str = str(value).lower()
                    if value_str in query_lower:
                        # Generate WHERE condition
                        if isinstance(value, (int, float)):
                            where_conditions.append(f"{table_name}.{column_name} = {value}")
                        else:
                            where_conditions.append(f"{table_name}.{column_name} = '{value}'")
        
        return where_conditions
    
    def _identify_join_requirements(self, query: str, schema_metadata: Dict[str, Any]) -> List[Dict[str, str]]:
        """Identify JOIN requirements based on query and schema"""
        join_requirements = []
        query_lower = query.lower()
        
        # Common join patterns
        join_patterns = [
            ("customer", "account", "customers.id = accounts.customer_id"),
            ("account", "transaction", "accounts.id = transactions.account_id"),
            ("employee", "branch", "employees.branch_id = branches.id"),
            ("customer", "branch", "customers.branch_id = branches.id")
        ]
        
        for pattern in join_patterns:
            table1, table2, join_condition = pattern
            if table1 in query_lower and table2 in query_lower:
                join_requirements.append({
                    "table1": table1,
                    "table2": table2,
                    "join_condition": join_condition,
                    "join_type": "INNER"
                })
        
        return join_requirements
    
    def _extract_value_constraints(self, query: str, distinct_values: Dict[str, Dict[str, List[Any]]]) -> Dict[str, Any]:
        """Extract value constraints from query"""
        constraints = {}
        query_lower = query.lower()
        
        for table_name, columns in distinct_values.items():
            table_constraints = {}
            
            for column_name, values in columns.items():
                column_constraints = []
                
                # Look for value mentions
                for value in values[:5]:
                    value_str = str(value).lower()
                    if value_str in query_lower:
                        column_constraints.append({
                            "column": column_name,
                            "value": value,
                            "operator": "=",
                            "suggested_condition": f"{column_name} = '{value}'" if isinstance(value, str) else f"{column_name} = {value}"
                        })
                
                if column_constraints:
                    table_constraints[column_name] = column_constraints
            
            if table_constraints:
                constraints[table_name] = table_constraints
        
        return constraints
        
        if any(word in query_lower for word in ["group", "grouped", "by"]):
            operations.append("GROUP BY")
        
        if any(word in query_lower for word in ["where", "filter", "condition"]):
            operations.append("WHERE")
        
        if any(word in query_lower for word in ["join", "joined", "with"]):
            operations.append("JOIN")
        
        return operations
    
    def _assess_complexity(self, query: str) -> str:
        """Assess query complexity"""
        complexity_score = 0
        
        # Factors that increase complexity
        if len(query.split()) > 20:
            complexity_score += 2
        
        if len(self._identify_tables(query)) > 2:
            complexity_score += 2
        
        operations = self._identify_operations(query)
        if operations and len(operations) > 3:
            complexity_score += 2
        
        if any(word in query.lower() for word in ["join", "joined", "with"]):
            complexity_score += 1
        
        if any(word in query.lower() for word in ["group", "grouped", "by"]):
            complexity_score += 1
        
        if any(word in query.lower() for word in ["having", "subquery", "nested"]):
            complexity_score += 2
        
        # Determine complexity level
        if complexity_score <= 2:
            return "simple"
        elif complexity_score <= 4:
            return "medium"
        else:
            return "complex"
    
    def _check_clarifications(self, query: str) -> List[Dict[str, Any]]:
        """Check if query needs clarifications"""
        clarifications = []
        query_lower = query.lower()
        
        # Check for ambiguous terms
        if "recent" in query_lower and not re.search(r'\d+', query):
            clarifications.append({
                "type": "time_range",
                "field": "recent",
                "question": "How recent? (e.g., last 30 days, last month, last year)",
                "suggestions": ["last 30 days", "last month", "last quarter", "last year"]
            })
        
        if "high" in query_lower and "salary" in query_lower:
            clarifications.append({
                "type": "threshold",
                "field": "salary_threshold",
                "question": "What do you consider a 'high' salary?",
                "suggestions": ["above average", "top 10%", "above $100,000", "above $75,000"]
            })
        
        if "large" in query_lower and "balance" in query_lower:
            clarifications.append({
                "type": "threshold",
                "field": "balance_threshold",
                "question": "What do you consider a 'large' balance?",
                "suggestions": ["above average", "top 20%", "above $50,000", "above $25,000"]
            })
        
        return clarifications
    
    def _estimate_tokens(self, query: str) -> int:
        """Estimate token usage for the query"""
        # Rough estimation based on query length and complexity
        base_tokens = len(query.split()) * 2  # Rough estimate
        
        complexity = self._assess_complexity(query)
        if complexity == "simple":
            multiplier = 1.0
        elif complexity == "medium":
            multiplier = 1.5
        else:
            multiplier = 2.0
        
        return int(base_tokens * multiplier)
