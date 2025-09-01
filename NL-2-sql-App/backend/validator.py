#!/usr/bin/env python3
"""
Validator Agent with integrated SecurityGuard
Enhanced SQL validation with security checks
"""

import sqlparse
import logging
from typing import Dict, Any, Tuple, Optional
from .security_guard import SecurityGuard

logger = logging.getLogger(__name__)

class ValidatorAgent:
    """Enhanced validator agent with integrated security guard"""
    
    def __init__(self, schema_tables: dict, security_guard: Optional[SecurityGuard] = None):
        """
        Initialize validator with schema and optional security guard
        
        Args:
            schema_tables: Dictionary of table schemas
            security_guard: Optional SecurityGuard instance for enhanced validation
        """
        self.schema_tables = schema_tables
        self.security_guard = security_guard or SecurityGuard()
        logger.info(f"🔍 ValidatorAgent initialized with {len(schema_tables)} tables")

    def is_safe_sql(self, sql: str, user: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Enhanced SQL validation with security checks
        
        Returns:
            Tuple of (is_safe, message, validation_details)
        """
        logger.info(f"🔍 Starting enhanced SQL validation")
        
        # Step 1: Basic SQL syntax validation
        syntax_valid, syntax_msg = self._validate_sql_syntax(sql)
        if not syntax_valid:
            return False, syntax_msg, {"validation_step": "syntax", "error": syntax_msg}
        
        # Step 2: Security validation using SecurityGuard
        security_valid, security_msg, security_action = self.security_guard.validate_sql(sql, user, ip_address)
        if not security_valid:
            return False, security_msg, {
                "validation_step": "security", 
                "error": security_msg, 
                "action": security_action,
                "threat_level": "HIGH"
            }
        
        # Step 3: Schema validation
        schema_valid, schema_msg = self._validate_schema_compliance(sql)
        if not schema_valid:
            return False, schema_msg, {"validation_step": "schema", "error": schema_msg}
        
        # Step 4: Performance validation
        performance_valid, performance_msg = self._validate_performance(sql)
        if not performance_valid:
            logger.warning(f"⚠️ Performance warning: {performance_msg}")
            # Don't block, just warn
        
        # All validations passed
        validation_details = {
            "validation_step": "complete",
            "syntax_valid": syntax_valid,
            "security_valid": security_valid,
            "schema_valid": schema_valid,
            "performance_warning": performance_msg if not performance_valid else None,
            "security_action": security_action
        }
        
        logger.info(f"✅ SQL validation passed: {security_msg}")
        return True, "SQL validation passed", validation_details

    def _validate_sql_syntax(self, sql: str) -> Tuple[bool, str]:
        """Validate basic SQL syntax"""
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return False, "Invalid SQL syntax"
            
            stmt = parsed[0]
            tokens = [t.value.upper() for t in stmt.tokens if not t.is_whitespace]
            
            # Check if it starts with SELECT
            if not tokens or "SELECT" not in tokens[0]:
                return False, "Only SELECT statements are allowed"
            
            return True, "SQL syntax is valid"
            
        except Exception as e:
            return False, f"SQL parsing error: {str(e)}"

    def _validate_schema_compliance(self, sql: str) -> Tuple[bool, str]:
        """Validate SQL against known schema"""
        try:
            sql_upper = sql.upper()
            
            # Check for table references
            referenced_tables = []
            for table in self.schema_tables:
                if table.upper() in sql_upper:
                    referenced_tables.append(table)
            
            # If no tables referenced, it might be a general query like "SELECT 1"
            # We'll allow it but log it
            if not referenced_tables:
                logger.info("ℹ️ No specific tables referenced in query")
                return True, "Query doesn't reference specific tables"
            
            # Check if all referenced tables exist in schema
            for table in referenced_tables:
                if table not in self.schema_tables:
                    return False, f"Unknown table referenced: {table}"
            
            return True, f"Schema validation passed for tables: {', '.join(referenced_tables)}"
            
        except Exception as e:
            return False, f"Schema validation error: {str(e)}"

    def _validate_performance(self, sql: str) -> Tuple[bool, str]:
        """Basic performance validation"""
        try:
            sql_upper = sql.upper()
            
            # Check for potential performance issues
            warnings = []
            
            # Check for SELECT * without LIMIT
            if "SELECT *" in sql_upper and "LIMIT" not in sql_upper:
                warnings.append("SELECT * without LIMIT may return large datasets")
            
            # Check for multiple JOINs
            join_count = sql_upper.count("JOIN")
            if join_count > 3:
                warnings.append(f"Multiple JOINs ({join_count}) may impact performance")
            
            # Check for complex subqueries
            if sql_upper.count("SELECT") > 2:
                warnings.append("Complex nested queries may impact performance")
            
            if warnings:
                return False, "; ".join(warnings)
            
            return True, "Performance validation passed"
            
        except Exception as e:
            return False, f"Performance validation error: {str(e)}"

    def is_safe(self, sql: str, schema_tables: dict = None, user: Optional[str] = None, ip_address: Optional[str] = None) -> Tuple[bool, str]:
        """
        Wrapper method to match pipeline expectations
        
        Returns:
            Tuple of (is_safe, message)
        """
        logger.info(f"🔍 VALIDATOR AGENT: Starting SQL validation")
        logger.info(f"🔧 VALIDATOR AGENT: Validating SQL: {sql}")
        
        # Use provided schema_tables or fall back to instance schema
        validation_schema = schema_tables or self.schema_tables
        logger.info(f"📋 VALIDATOR AGENT: Available tables: {list(validation_schema.keys())}")
        
        # Update schema if provided
        if schema_tables:
            self.schema_tables = schema_tables
        
        # Perform enhanced validation
        is_safe, message, details = self.is_safe_sql(sql, user, ip_address)
        
        if is_safe:
            logger.info(f"✅ VALIDATOR AGENT: SQL validation passed")
            logger.info(f"🔍 VALIDATOR AGENT: Reason: {message}")
        else:
            logger.error(f"❌ VALIDATOR AGENT: SQL validation failed")
            logger.error(f"⚠️ VALIDATOR AGENT: Reason: {message}")
            logger.error(f"🔍 VALIDATOR AGENT: Details: {details}")
        
        return is_safe, message

    def get_validation_report(self, sql: str, user: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive validation report"""
        try:
            is_safe, message, details = self.is_safe_sql(sql, user, ip_address)
            
            return {
                "is_safe": is_safe,
                "message": message,
                "details": details,
                "timestamp": self._get_timestamp(),
                "sql_length": len(sql),
                "schema_tables_count": len(self.schema_tables),
                "security_events": self.security_guard.get_recent_events(limit=5)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate validation report: {e}")
            return {
                "is_safe": False,
                "message": f"Validation report error: {str(e)}",
                "details": {"error": str(e)},
                "timestamp": self._get_timestamp()
            }

    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

    def update_schema(self, new_schema: dict):
        """Update the schema tables"""
        self.schema_tables = new_schema
        logger.info(f"📋 Schema updated with {len(new_schema)} tables")

    def get_schema_info(self) -> Dict[str, Any]:
        """Get schema information"""
        return {
            "table_count": len(self.schema_tables),
            "tables": list(self.schema_tables.keys()),
            "total_columns": sum(len(columns) for columns in self.schema_tables.values())
        }
