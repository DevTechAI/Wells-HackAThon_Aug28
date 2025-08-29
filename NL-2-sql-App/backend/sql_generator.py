import typing

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


class SQLGeneratorAgent:
    def __init__(self, model_path: str = "./models/llama-7b.gguf", temperature: float = 0.1):
        self.model_path = model_path
        self.temperature = temperature
        self.llm = None
        
        if Llama is not None:
            try:
                self.llm = Llama(
                    model_path=model_path,
                    n_ctx=2048,  # Context window
                    n_threads=4,  # Adjust based on your CPU
                    temperature=temperature,
                )
            except Exception as e:
                print(f"Failed to load Llama model: {e}")
                self.llm = None

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
        schema_context = retrieval_context.get("schema_context", [])
        prompt = self.build_prompt(user_query, schema_context)

        if self.llm is None:
            # Fallback if Llama not available
            first_table = next(iter(schema_tables.keys())) if schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 10;" if first_table else "SELECT 1;"

        try:
            output = self.llm(
                prompt,
                max_tokens=512,
                temperature=self.temperature,
                stop=["Q:", "\n\n"],  # Stop at next question or double newline
                echo=False
            )

            if output and "choices" in output and len(output["choices"]) > 0:
                sql = output["choices"][0]["text"].strip()
                # Extract SQL from code blocks if present
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                return sql
            else:
                # Fallback
                first_table = next(iter(schema_tables.keys())) if schema_tables else ""
                return f"SELECT * FROM {first_table} LIMIT 10;" if first_table else "SELECT 1;"
                
        except Exception as e:
            print(f"Llama generation failed: {e}")
            # Fallback
            first_table = next(iter(schema_tables.keys())) if schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 10;" if first_table else "SELECT 1;"

    # Old API method that pipeline.py expects
    def generate_sql(self, nl_query: str, gen_ctx: dict) -> str:
        """Old API method that pipeline.py expects."""
        schema_context = gen_ctx.get("schema_context", [])
        
        # Build prompt using schema context
        prompt = self.build_prompt(nl_query, schema_context)
        
        if self.llm is None:
            # Fallback if Llama not available
            return "SELECT 1;"

        try:
            output = self.llm(
                prompt,
                max_tokens=512,
                temperature=self.temperature,
                stop=["Q:", "\n\n"],
                echo=False
            )
            
            if output and "choices" in output and len(output["choices"]) > 0:
                sql = output["choices"][0]["text"].strip()
                # Extract SQL from code blocks if present
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                return sql
            else:
                return "SELECT 1;"
                
        except Exception as e:
            print(f"Llama generation failed: {e}")
            return "SELECT 1;"

    def repair_sql(self, nl_query: str, gen_ctx: dict, hint: str = "") -> str:
        """Repair SQL based on validation error hint."""
        schema_context = gen_ctx.get("schema_context", [])
        
        # Add hint to the prompt
        repair_prompt = f"""
Previous attempt failed with error: {hint}

Please generate a corrected SQL query for:
{nl_query}

Schema: {chr(10).join(schema_context)}
"""
        
        if self.llm is None:
            return "SELECT 1;"

        try:
            output = self.llm(
                repair_prompt,
                max_tokens=512,
                temperature=self.temperature,
                stop=["Q:", "\n\n"],
                echo=False
            )
            
            if output and "choices" in output and len(output["choices"]) > 0:
                sql = output["choices"][0]["text"].strip()
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                return sql
            else:
                return "SELECT 1;"
                
        except Exception as e:
            print(f"Llama repair failed: {e}")
            return "SELECT 1;"
                
      
