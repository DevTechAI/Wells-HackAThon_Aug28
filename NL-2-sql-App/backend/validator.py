import sqlparse

class ValidatorAgent:
    def __init__(self, schema_tables: dict):
        """
        schema_tables = {
          "customers": ["id", "first_name", "last_name", "gender", ...],
          "accounts": ["id", "customer_id", "type", "balance", ...],
          ...
        }
        """
        self.schema_tables = schema_tables

    def is_safe_sql(self, sql: str) -> tuple[bool, str]:
        # Normalize SQL
        parsed = sqlparse.parse(sql)
        if not parsed:
            return False, "Invalid SQL syntax"

        stmt = parsed[0]
        tokens = [t.value.upper() for t in stmt.tokens if not t.is_whitespace]

        # 1. Only allow SELECT
        if "SELECT" not in tokens[0]:
            return False, "Only SELECT statements are allowed"

        # 2. Block dangerous keywords
        forbidden = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER"]
        for word in forbidden:
            if word in tokens:
                return False, f"Forbidden operation detected: {word}"

        # 3. Basic table validation (optional - can be enhanced later)
        # For now, just ensure the SQL looks reasonable
        sql_str = sql.upper()
        
        # Check if any known table is mentioned (optional validation)
        table_mentioned = False
        for table in self.schema_tables:
            if table.upper() in sql_str:
                table_mentioned = True
                break
        
        # If no known table is mentioned, it might be a general query like "SELECT 1"
        # We'll allow it for now
        
        return True, "SQL is safe"

    def is_safe(self, sql: str, schema_tables: dict) -> tuple[bool, str]:
        """Wrapper method to match pipeline expectations"""
        return self.is_safe_sql(sql)
