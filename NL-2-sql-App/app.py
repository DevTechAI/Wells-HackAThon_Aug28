
import os
import streamlit as st
from dotenv import load_dotenv
from backend.pipeline import NL2SQLPipeline, PipelineConfig
from backend.planner import PlannerAgent
from backend.retriever import RetrieverAgent
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

    # New API expected by pipeline
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

from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent

load_dotenv()
DB_PATH = os.getenv("SQLITE_DB", "banking.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "./models/llama-7b.gguf")

schema_tables = {"customers":["id","email","first_name","last_name"],
                 "accounts":["id","customer_id","type"],
                 "transactions":["id","account_id","amount","type","transaction_date"]}

pipeline = NL2SQLPipeline(
    planner=PlannerAgent(schema_tables),
    retriever=RetrieverAgent(db_path=CHROMA_PATH),
    generator=SQLGeneratorAgent(model_path=LLAMA_MODEL_PATH),
    validator=ValidatorAgent(schema_tables),
    executor=ExecutorAgent(DB_PATH),
    summarizer=SummarizerAgent(),
    schema_tables=schema_tables,
    config=PipelineConfig()
)

st.title("🤖 NL→SQL Assistant")
query = st.chat_input("Ask about the database…")
if query:
    resp = pipeline.run(query)
    st.write(resp.get("summary", ""))
    if resp.get("sql"): st.code(resp["sql"], language="sql")
    if resp.get("table"):
        import pandas as pd
        st.dataframe(pd.DataFrame(resp["table"]))
