
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
        self.schema_tables = {}  # Will be set later
        
        # Skip model loading if model_path is empty or doesn't exist
        if not model_path or model_path.strip() == "":
            print("No Llama model path provided, using fallback mode")
            self.llm = None
        elif Llama is not None:
            try:
                if not os.path.exists(model_path):
                    print(f"Model file not found: {model_path}")
                    print("Using fallback mode without LLM")
                    self.llm = None
                else:
                    self.llm = Llama(
                        model_path=model_path,
                        n_ctx=2048,  # Context window
                        n_threads=4,  # Adjust based on your CPU
                        temperature=temperature,
                    )
            except Exception as e:
                print(f"Failed to load Llama model: {e}")
                print("Using fallback mode without LLM")
                self.llm = None

    def build_prompt(self, query: str, schema_context: typing.List[str]) -> str:
        schema_str = "\n".join(schema_context)

        examples = """
        Q: List all branches in Texas.
        A:
        SELECT id, name, city, state
        FROM branches
        WHERE state = 'TX';

        Q: Show last 5 transactions.
        A:
        SELECT *
        FROM transactions
        ORDER BY transaction_date DESC
        LIMIT 5;

        Q: Maximum transaction making branch.
        A:
        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
        FROM branches b
        LEFT JOIN accounts a ON b.id = a.branch_id
        LEFT JOIN transactions t ON a.id = t.account_id
        GROUP BY b.id, b.name, b.city, b.state
        ORDER BY transaction_count DESC
        LIMIT 1;

        Q: Top 10 branches having maximum transactions.
        A:
        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
        FROM branches b
        LEFT JOIN accounts a ON b.id = a.branch_id
        LEFT JOIN transactions t ON a.id = t.account_id
        GROUP BY b.id, b.name, b.city, b.state
        ORDER BY transaction_count DESC
        LIMIT 10;

        Q: Count of rows by each table.
        A:
        SELECT 'accounts' as table_name, (SELECT COUNT(*) FROM accounts) as row_count
        UNION ALL
        SELECT 'branches' as table_name, (SELECT COUNT(*) FROM branches) as row_count
        UNION ALL
        SELECT 'employees' as table_name, (SELECT COUNT(*) FROM employees) as row_count
        UNION ALL
        SELECT 'transactions' as table_name, (SELECT COUNT(*) FROM transactions) as row_count;

        Q: Show all tables.
        A:
        SELECT 'accounts' as table_name
        UNION ALL
        SELECT 'branches' as table_name
        UNION ALL
        SELECT 'employees' as table_name
        UNION ALL
        SELECT 'transactions' as table_name;
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
            # Enhanced fallback logic for common query patterns
            query_lower = user_query.lower()
            
            # Handle "count of rows by each table" or similar
            if any(word in query_lower for word in ["count", "rows", "each table", "by table", "table count"]):
                if len(schema_tables) > 1:
                    # Create a better query that shows table names with their counts
                    # Use a more explicit approach to avoid UNION issues
                    query_parts = []
                    for table_name in schema_tables.keys():
                        query_parts.append(f"SELECT '{table_name}' as table_name, (SELECT COUNT(*) FROM {table_name}) as row_count")
                    return " UNION ALL ".join(query_parts) + ";"
                else:
                    # Single table
                    table_name = list(schema_tables.keys())[0]
                    return f"SELECT '{table_name}' as table_name, COUNT(*) as row_count FROM {table_name};"
            
            # Handle "show all tables" or "list tables"
            elif any(word in query_lower for word in ["show tables", "list tables", "all tables", "what tables"]):
                tables_list = ", ".join([f"'{table}'" for table in schema_tables.keys()])
                return f"SELECT {tables_list} as tables;"
            
            # Handle "show all [table]" or similar
            elif any(word in query_lower for word in ["show all", "list all", "get all"]):
                for table_name in schema_tables.keys():
                    if table_name.lower() in query_lower or table_name[:-1].lower() in query_lower:  # handle plural/singular
                        return f"SELECT * FROM {table_name} LIMIT 10;"
            
            # Handle complex queries with aggregations and joins
            elif any(word in query_lower for word in ["maximum", "max", "highest", "most", "top", "best"]):
                # Handle "maximum transaction making branch" or similar
                if any(word in query_lower for word in ["transaction", "transactions"]) and any(word in query_lower for word in ["branch", "branches"]):
                    # Check if user wants top N or just the maximum
                    if any(word in query_lower for word in ["top", "10", "5", "3", "first"]):
                        return """
                        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
                        FROM branches b
                        LEFT JOIN accounts a ON b.id = a.branch_id
                        LEFT JOIN transactions t ON a.id = t.account_id
                        GROUP BY b.id, b.name, b.city, b.state
                        ORDER BY transaction_count DESC
                        LIMIT 10;
                        """
                    else:
                        return """
                        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
                        FROM branches b
                        LEFT JOIN accounts a ON b.id = a.branch_id
                        LEFT JOIN transactions t ON a.id = t.account_id
                        GROUP BY b.id, b.name, b.city, b.state
                        ORDER BY transaction_count DESC
                        LIMIT 1;
                        """
                # Handle "maximum balance account" or similar
                elif any(word in query_lower for word in ["balance", "account", "accounts"]):
                    return """
                    SELECT id, account_number, type, balance, customer_id
                    FROM accounts
                    ORDER BY balance DESC
                    LIMIT 1;
                    """
                # Handle "maximum salary employee" or similar
                elif any(word in query_lower for word in ["salary", "employee", "employees"]):
                    return """
                    SELECT id, name, position, salary, branch_id
                    FROM employees
                    ORDER BY salary DESC
                    LIMIT 1;
                    """
            
            # Default fallback
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

    def repair_sql(self, nl_query: str, gen_ctx: dict, hint: str = "") -> str:
        """Repair SQL based on error hint"""
        # Simple repair logic - just regenerate with hint
        schema_context = gen_ctx.get("schema_context", [])
        prompt = self.build_prompt(f"{nl_query} (Error: {hint})", schema_context)
        
        if self.llm is None:
            # Enhanced fallback repair logic
            query_lower = nl_query.lower()
            
            # Handle count queries in repair mode
            if any(word in query_lower for word in ["count", "rows", "each table", "by table", "table count"]):
                if hasattr(self, 'schema_tables') and self.schema_tables:
                    query_parts = []
                    for table_name in self.schema_tables.keys():
                        query_parts.append(f"SELECT '{table_name}' as table_name, (SELECT COUNT(*) FROM {table_name}) as row_count")
                    return " UNION ALL ".join(query_parts) + ";"
            
            # Handle complex queries in repair mode
            elif any(word in query_lower for word in ["maximum", "max", "highest", "most", "top", "best"]):
                if any(word in query_lower for word in ["transaction", "transactions"]) and any(word in query_lower for word in ["branch", "branches"]):
                    # Check if user wants top N or just the maximum
                    if any(word in query_lower for word in ["top", "10", "5", "3", "first"]):
                        return """
                        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
                        FROM branches b
                        LEFT JOIN accounts a ON b.id = a.branch_id
                        LEFT JOIN transactions t ON a.id = t.account_id
                        GROUP BY b.id, b.name, b.city, b.state
                        ORDER BY transaction_count DESC
                        LIMIT 10;
                        """
                    else:
                        return """
                        SELECT b.id, b.name, b.city, b.state, COUNT(t.id) as transaction_count
                        FROM branches b
                        LEFT JOIN accounts a ON b.id = a.branch_id
                        LEFT JOIN transactions t ON a.id = t.account_id
                        GROUP BY b.id, b.name, b.city, b.state
                        ORDER BY transaction_count DESC
                        LIMIT 1;
                        """
            
            # Default fallback repair
            first_table = next(iter(self.schema_tables.keys())) if hasattr(self, 'schema_tables') and self.schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 5;" if first_table else "SELECT 1;"
        
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
                if "```sql" in sql:
                    sql = sql.split("```sql")[1].split("```")[0].strip()
                elif "```" in sql:
                    sql = sql.split("```")[1].split("```")[0].strip()
                return sql
            else:
                # Fallback repair
                first_table = next(iter(self.schema_tables.keys())) if hasattr(self, 'schema_tables') and self.schema_tables else ""
                return f"SELECT * FROM {first_table} LIMIT 5;" if first_table else "SELECT 1;"
                
        except Exception as e:
            print(f"Llama repair failed: {e}")
            # Fallback repair
            first_table = next(iter(self.schema_tables.keys())) if hasattr(self, 'schema_tables') and self.schema_tables else ""
            return f"SELECT * FROM {first_table} LIMIT 5;" if first_table else "SELECT 1;"

from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent

load_dotenv()
DB_PATH = os.getenv("SQLITE_DB", "banking.db")
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "")

schema_tables = {
    "accounts": ["id", "customer_id", "account_number", "type", "balance", "opened_at", "interest_rate", "status", "branch_id", "created_at", "updated_at"],
    "branches": ["id", "name", "address", "city", "state", "zip_code", "manager_id", "created_at", "updated_at"],
    "employees": ["id", "branch_id", "name", "email", "phone", "position", "hire_date", "salary", "created_at", "updated_at"],
    "transactions": ["id", "account_id", "transaction_date", "amount", "type", "description", "status", "created_at", "updated_at", "employee_id"]
}

generator = SQLGeneratorAgent(model_path=LLAMA_MODEL_PATH)
generator.schema_tables = schema_tables

pipeline = NL2SQLPipeline(
    planner=PlannerAgent(schema_tables),
    retriever=RetrieverAgent(db_path=CHROMA_PATH),
    generator=generator,
    validator=ValidatorAgent(schema_tables),
    executor=ExecutorAgent(DB_PATH),
    summarizer=SummarizerAgent(),
    schema_tables=schema_tables,
    config=PipelineConfig()
)

st.title("🤖 NL→SQL Assistant")

# Initialize session state for conversation history
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

query = st.chat_input("Ask about the database…")

# Handle re-run queries from conversation history
if "rerun_query" in st.session_state:
    query = st.session_state.rerun_query
    del st.session_state.rerun_query

# Display conversation history
if st.session_state.conversation_history:
    st.subheader("📝 Conversation History")
    for i, (user_query, response) in enumerate(st.session_state.conversation_history):
        with st.expander(f"💬 Q{i+1}: {user_query[:50]}{'...' if len(user_query) > 50 else ''}", expanded=False):
            # Add a button to re-run this query
            if st.button(f"🔄 Re-run: {user_query[:30]}{'...' if len(user_query) > 30 else ''}", key=f"rerun_{i}"):
                st.session_state.rerun_query = user_query
                st.rerun()
            
            st.markdown(f"**Your Question:** {user_query}")
            st.divider()
            
            if response.get("summary"):
                st.markdown(response.get("summary"))
            
            if response.get("sql"):
                with st.expander("🔧 SQL Query", expanded=False):
                    st.code(response["sql"], language="sql")
            
            if response.get("table"):
                st.subheader("📋 Results")
                import pandas as pd
                st.dataframe(pd.DataFrame(response["table"]), use_container_width=True)
    
    st.divider()

if query:
    # Display current query prominently
    st.markdown("---")
    st.markdown(f"### 💬 **Your Question:**")
    st.info(f"**{query}**")
    st.markdown("---")
    
    resp = pipeline.run(query)
    
    # Store in conversation history
    st.session_state.conversation_history.append((query, resp))
    
    # Show summary prominently at the top
    if resp.get("summary"): 
        st.markdown("### 📊 **Analysis:**")
        st.markdown(resp.get("summary"))
        st.divider()
    
    # Show SQL in an expandable section (for technical users)
    if resp.get("sql"): 
        with st.expander("🔧 Generated SQL Query", expanded=False):
            st.code(resp["sql"], language="sql")
    
    # Show table results
    if resp.get("table"):
        st.subheader("📋 Results")
        import pandas as pd
        st.dataframe(pd.DataFrame(resp["table"]), use_container_width=True)
    
    # Show suggested follow-up questions
    if resp.get("suggestions"):
        st.divider()
        st.subheader("💡 Suggested Follow-up Questions")
        st.markdown("*Click any suggestion to ask it automatically:*")
        
        # Create columns for suggestions
        cols = st.columns(2)
        for i, suggestion in enumerate(resp["suggestions"]):
            col = cols[i % 2]
            if col.button(suggestion, key=f"suggestion_{i}"):
                # This would ideally trigger the query, but Streamlit doesn't support this directly
                st.info(f"💡 You can copy and paste this question: **{suggestion}**")
        
        # Alternative: show as clickable text
        st.markdown("**Or copy these questions:**")
        for suggestion in resp["suggestions"]:
            st.markdown(f"• `{suggestion}`")
    
    # Add a clear conversation button
    if st.button("🗑️ Clear Conversation History"):
        st.session_state.conversation_history = []
        st.rerun()
