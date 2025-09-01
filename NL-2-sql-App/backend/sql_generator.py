"""SQL Generator Agent using LLM abstraction"""
import typing
from typing import Dict, Any, Optional
import logging
from .llm_provider import get_llm_provider
from .logger_config import log_agent_flow

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SQLGeneratorAgent:
    """SQL Generator Agent that uses LLM for query generation"""
    
    @log_agent_flow("SQLGeneratorAgent")
    def __init__(self, temperature: float = 0.1):
        self.temperature = temperature
        self.schema_tables = {}
        self.llm = get_llm_provider()
        logger.info("Initialized SQLGeneratorAgent")

    @log_agent_flow("SQLGeneratorAgent.build_prompt")
    def build_prompt(self, query: str, schema_context: typing.List[str]) -> str:
        """Build prompt for SQL generation"""
        schema_str = "\n".join(schema_context)

        examples = """
        Q: List all branches in Texas.
        A: SELECT id, name, city, state FROM branches WHERE state = 'TX';

        Q: Show last 5 transactions.
        A: SELECT * FROM transactions ORDER BY transaction_date DESC LIMIT 5;

        Q: Maximum transaction making branch.
        A: 
        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
        FROM branches b
        LEFT JOIN accounts a ON b.id = a.branch_id
        LEFT JOIN transactions t ON a.id = t.account_id
        GROUP BY b.id, b.name, b.city, b.state
        ORDER BY transaction_count DESC
        LIMIT 1;
        """

        system = """
        You are a SQL assistant.
        Rules:
        - Only generate SELECT queries
        - Only use provided schema
        - Never modify data (no UPDATE/DELETE/DROP)
        - Return SQL only, no explanations
        - Use proper table aliases in JOINs
        - Include appropriate WHERE clauses
        - Use clear column names
        """

        return f"""{system}

Schema:
{schema_str}

Examples:
{examples}

Generate SQL for this question:
{query}"""

    @log_agent_flow("SQLGeneratorAgent.generate")
    def generate(
        self,
        user_query: str,
        constraints: Dict[str, Any],
        retrieval_context: Dict[str, Any],
        schema_tables: Dict[str, Any],
    ) -> str:
        """Generate SQL using LLM"""
        try:
            self.schema_tables = schema_tables
            schema_context = retrieval_context.get("schema_context", [])
            prompt = self.build_prompt(user_query, schema_context)
            
            # Generate SQL using LLM
            sql = self.llm.generate_text(
                prompt,
                temperature=self.temperature,
                max_tokens=512
            )
            
            # Clean up the response
            sql = sql.strip()
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()
            
            logger.info(f"Generated SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"SQL generation failed: {str(e)}")
            # Fallback to simple query
            first_table = next(iter(schema_tables.keys())) if schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 10;" if first_table else "SELECT 1;"

    @log_agent_flow("SQLGeneratorAgent.repair_sql")
    def repair_sql(self, nl_query: str, gen_ctx: dict, hint: str = "") -> str:
        """Repair SQL based on error hint"""
        try:
            schema_context = gen_ctx.get("schema_context", [])
            repair_prompt = f"""
            Original question: {nl_query}
            Error: {hint}
            
            Generate a corrected SQL query that fixes this error.
            Use the schema context below:
            
            {schema_context}
            """
            
            # Generate repaired SQL
            sql = self.llm.generate_text(
                repair_prompt,
                temperature=0.1,  # Lower temperature for repairs
                max_tokens=512
            )
            
            # Clean up the response
            sql = sql.strip()
            if "```sql" in sql:
                sql = sql.split("```sql")[1].split("```")[0].strip()
            elif "```" in sql:
                sql = sql.split("```")[1].split("```")[0].strip()
            
            logger.info(f"Repaired SQL: {sql}")
            return sql
            
        except Exception as e:
            logger.error(f"SQL repair failed: {str(e)}")
            # Fallback to simple query
            first_table = next(iter(self.schema_tables.keys())) if self.schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 5;" if first_table else "SELECT 1;"