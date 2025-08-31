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
        
        if any(word in query_lower for word in ["minimum", "min", "lowest"]):
            operations.append("MIN")
        
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
        
        if len(self._identify_operations(query)) > 3:
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
