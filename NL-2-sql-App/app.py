
import os
import streamlit as st
from dotenv import load_dotenv
from backend.pipeline import NL2SQLPipeline, PipelineConfig
from backend.planner import PlannerAgent
from backend.retriever import RetrieverAgent
from backend.sql_generator import SQLGeneratorAgent
import typing
import sqlite3
from backend.db_init import initialize_database
from frontend.health_dashboard import create_health_dashboard, create_mini_health_status

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None


from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent
import time

load_dotenv()

def custom_pipeline_run_with_status(pipeline, nl_query: str, status_area, progress_bar, clarified_values=None) -> dict:
    """
    Custom pipeline execution that updates the UI with real-time status
    """
    from backend.pipeline import PipelineDiagnostics
    diag = PipelineDiagnostics()
    start_all = time.time()
    
    # Store agent flow for detailed logging
    agent_flow = []
    
    # Step 1: Plan
    status_area.info("📋 **Step 1:** Analyzing your query and planning the approach...")
    progress_bar.progress(20)
    
    t0 = time.time()
    plan = pipeline.planner.analyze_query(nl_query)
    diag.timings_ms["planning"] = int((time.time() - t0) * 1000)
    diag.chosen_tables = plan.get("tables", [])
    
    # Log planner agent flow
    planner_output = {
        "agent": "PLANNER",
        "input": {"query": nl_query},
        "output": {
            "tables": plan.get("tables", []),
            "capabilities": plan.get("capabilities", []),
            "clarifications": plan.get("clarifications", []),
            "follow_up_suggestions": plan.get("follow_up_suggestions", [])
        },
        "timing_ms": diag.timings_ms["planning"]
    }
    agent_flow.append(planner_output)
    
    status_area.success(f"✅ **Planning Complete:** Identified relevant tables: {', '.join(diag.chosen_tables)}")
    progress_bar.progress(30)
    
    # Check for clarifications
    clar = plan.get("clarifications", [])
    if clar:
        status_area.warning("❓ **Clarification Needed:** Please provide additional details")
        return {"needs_clarification": True, "clarifications": clar, "diagnostics": diag.__dict__, "success": False, "agent_flow": agent_flow}
    
    # Step 2: Retrieve context
    status_area.info("🔍 **Processing.... please wait** - Finding relevant database information...")
    progress_bar.progress(40)
    
    t1 = time.time()
    print(f"🔍 RETRIEVER AGENT: About to call retrieve method...")
    ctx_bundle = pipeline.retriever.retrieve(nl_query, pipeline.schema_tables)
    print(f"🔍 RETRIEVER AGENT: Retrieve method completed successfully")
    diag.timings_ms["retrieval"] = int((time.time() - t1) * 1000)
    
    # Log retriever agent flow
    retriever_output = {
        "agent": "RETRIEVER",
        "input": {
            "query": nl_query,
            "available_tables": list(pipeline.schema_tables.keys())
        },
        "output": {
            "schema_context_count": len(ctx_bundle.get('schema_context', [])),
            "schema_context_preview": ctx_bundle.get('schema_context', [])[:3],  # First 3 items
            "value_hints_count": len(ctx_bundle.get('value_hints', {})),
            "exemplars_count": len(ctx_bundle.get('exemplars', [])),
            "retrieval_method": ctx_bundle.get('retrieval_method', 'unknown')
        },
        "timing_ms": diag.timings_ms["retrieval"]
    }
    agent_flow.append(retriever_output)
    
    status_area.success(f"✅ **Context Retrieved:** Found {len(ctx_bundle.get('schema_context', []))} schema items")
    progress_bar.progress(50)
    
    # Create comprehensive schema context with all table information
    comprehensive_schema = []
    
    # Add all table schemas directly
    table_schemas = {
        "branches": "CREATE TABLE branches (id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT, city TEXT, state TEXT, zip_code TEXT, manager_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
        "employees": "CREATE TABLE employees (id TEXT PRIMARY KEY, branch_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, position TEXT, hire_date DATE, salary REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (branch_id) REFERENCES branches(id));",
        "customers": "CREATE TABLE customers (id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, phone TEXT, address TEXT, first_name TEXT NOT NULL, last_name TEXT NOT NULL, date_of_birth DATE, gender TEXT, national_id TEXT UNIQUE, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, branch_id TEXT, FOREIGN KEY (branch_id) REFERENCES branches(id));",
        "accounts": "CREATE TABLE accounts (id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, account_number TEXT UNIQUE NOT NULL, type TEXT NOT NULL, balance REAL DEFAULT 0.00, opened_at DATE NOT NULL, interest_rate REAL, status TEXT DEFAULT 'active', branch_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (customer_id) REFERENCES customers(id), FOREIGN KEY (branch_id) REFERENCES branches(id));",
        "transactions": "CREATE TABLE transactions (id TEXT PRIMARY KEY, account_id TEXT NOT NULL, transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, amount REAL NOT NULL, type TEXT NOT NULL, description TEXT, status TEXT DEFAULT 'completed', created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, employee_id TEXT, FOREIGN KEY (account_id) REFERENCES accounts(id), FOREIGN KEY (employee_id) REFERENCES employees(id));"
    }
    
    # Add table descriptions
    table_descriptions = {
        "branches": "Branches table contains bank branch information including location, manager, and contact details. Each branch can have multiple employees and customers.",
        "employees": "Employees table contains staff information including their position, salary, and which branch they work at. The manager_id in branches table references employees.id.",
        "customers": "Customers table contains customer personal information and is linked to branches through branch_id.",
        "accounts": "Accounts table contains bank account information including type, balance, and is linked to customers and branches.",
        "transactions": "Transactions table contains all financial transactions linked to accounts and processed by employees."
    }
    
    # Build comprehensive schema context
    for table_name, schema in table_schemas.items():
        comprehensive_schema.append(f"Table: {table_name}")
        comprehensive_schema.append(f"Schema: {schema}")
        comprehensive_schema.append(f"Description: {table_descriptions[table_name]}")
        comprehensive_schema.append("")
    
    # Add relationship information
    comprehensive_schema.append("Key Relationships:")
    comprehensive_schema.append("- branches.manager_id → employees.id (branch managers)")
    comprehensive_schema.append("- customers.branch_id → branches.id (customer's branch)")
    comprehensive_schema.append("- accounts.customer_id → customers.id (account owner)")
    comprehensive_schema.append("- accounts.branch_id → branches.id (account's branch)")
    comprehensive_schema.append("- transactions.account_id → accounts.id (transaction's account)")
    comprehensive_schema.append("- transactions.employee_id → employees.id (transaction processor)")
    comprehensive_schema.append("")
    
    # Add enhanced schema and column information
    if 'schema_info' in st.session_state and 'column_values' in st.session_state:
        comprehensive_schema.append("")
        comprehensive_schema.append("=== ENHANCED SCHEMA INFORMATION ===")
        
        for table_name, schema_data in st.session_state.schema_info.items():
            comprehensive_schema.append(f"")
            comprehensive_schema.append(f"TABLE: {table_name}")
            comprehensive_schema.append(f"CREATE TABLE: {schema_data['create_sql']}")
            
            # Add column information
            comprehensive_schema.append(f"COLUMNS:")
            for col_info in schema_data['columns']:
                col_name, col_type, nullable = col_info[1], col_info[2], col_info[3]
                pk = " (PRIMARY KEY)" if col_info[5] == 1 else ""
                comprehensive_schema.append(f"  - {col_name}: {col_type}{pk}")
            
            # Add foreign key information
            if schema_data['foreign_keys']:
                comprehensive_schema.append(f"FOREIGN KEYS:")
                for fk in schema_data['foreign_keys']:
                    comprehensive_schema.append(f"  - {fk[3]} -> {fk[2]}.{fk[4]}")
            
            # Add column values if available
            if table_name in st.session_state.column_values:
                comprehensive_schema.append(f"COLUMN VALUES:")
                for col_name, col_data in st.session_state.column_values[table_name].items():
                    if col_name != 'sample_data':
                        values = col_data['unique_values'][:10]  # Limit to first 10 values
                        comprehensive_schema.append(f"  - {col_name}: {', '.join(map(str, values))}")
                        if len(col_data['unique_values']) > 10:
                            comprehensive_schema.append(f"    (and {len(col_data['unique_values']) - 10} more values)")
        
        comprehensive_schema.append("")
        comprehensive_schema.append("=== SAMPLE DATA ===")
        for table_name, col_data in st.session_state.column_values.items():
            if 'sample_data' in col_data:
                comprehensive_schema.append(f"{table_name} sample data:")
                for i, row in enumerate(col_data['sample_data'][:2]):  # Show first 2 rows
                    comprehensive_schema.append(f"  Row {i+1}: {row}")
                comprehensive_schema.append("")
    else:
        # Fallback to basic information
        try:
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            for table_name in table_schemas.keys():
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                comprehensive_schema.append(f"Sample data: {table_name} has {count} records")
                
                # Add sample values for key columns
                if table_name == "accounts":
                    cursor.execute("SELECT DISTINCT type FROM accounts LIMIT 5")
                    types = [row[0] for row in cursor.fetchall()]
                    comprehensive_schema.append(f"Account types available: {', '.join(types)}")
            conn.close()
        except:
            pass
    
    # Add validation checklist
    comprehensive_schema.append("")
    comprehensive_schema.append("VALIDATION CHECKLIST:")
    comprehensive_schema.append("- Does the query use the correct table names?")
    comprehensive_schema.append("- Are the JOIN conditions using the right foreign keys?")
    comprehensive_schema.append("- Are all required columns included in the SELECT?")
    comprehensive_schema.append("- Are the WHERE conditions using the correct column names?")
    comprehensive_schema.append("- Is the query logically sound for the requested data?")
    
    st_print(f"📚 Comprehensive schema context created with {len(comprehensive_schema)} items")
    st_print(f"🔍 Schema context preview:")
    for i, item in enumerate(comprehensive_schema[:10]):  # Show first 10 items
        st_print(f"  {i+1}. {item}")
    if len(comprehensive_schema) > 10:
        st_print(f"  ... and {len(comprehensive_schema) - 10} more items")
    
    gen_ctx = {
        "schema_context": comprehensive_schema,
        "value_hints": ctx_bundle.get("value_hints", {}),
        "exemplars": ctx_bundle.get("exemplars", []),
        "clarified_values": {}
    }
    
    # Step 3: Generate SQL
    status_area.info("🧠 **Processing.... please wait** - Creating SQL query with AI...")
    progress_bar.progress(60)
    
    t2 = time.time()
    print(f"🧠 SQL GENERATOR AGENT: About to call generate method...")
    sql = pipeline.generator.generate(nl_query, {}, gen_ctx, pipeline.schema_tables)
    print(f"🧠 SQL GENERATOR AGENT: Generate method completed successfully")
    diag.generated_sql = sql
    diag.timings_ms["generation"] = int((time.time() - t2) * 1000)
    
    # Log SQL generator agent flow
    sql_generator_output = {
        "agent": "SQL_GENERATOR",
        "input": {
            "query": nl_query,
            "schema_context_count": len(gen_ctx.get('schema_context', [])),
            "value_hints_count": len(gen_ctx.get('value_hints', {})),
            "exemplars_count": len(gen_ctx.get('exemplars', [])),
            "clarified_values": gen_ctx.get('clarified_values', {})
        },
        "output": {
            "generated_sql": sql,
            "sql_length": len(sql),
            "used_special_handler": "employee" in nl_query.lower() and "transaction" in nl_query.lower() and "customer" in nl_query.lower(),
            "used_fallback": "LIMIT 10" in sql and ("SELECT * FROM" in sql)
        },
        "timing_ms": diag.timings_ms["generation"]
    }
    agent_flow.append(sql_generator_output)
    
    status_area.success("✅ **SQL Generated:** Query created successfully")
    # Show a preview of the generated SQL
    with st.expander("🔍 **Generated SQL Preview**", expanded=False):
        st.code(sql, language="sql")
    progress_bar.progress(70)
    
    attempts = 0
    last_error = None
    
    while attempts <= pipeline.cfg.max_retries:
        # Step 4: Validate
        status_area.info(f"🔍 **Processing.... please wait** - Checking query safety (attempt {attempts + 1})...")
        progress_bar.progress(75)
        
        t3 = time.time()
        ok, reason = pipeline.validator.is_safe(sql, pipeline.schema_tables)
        diag.timings_ms.setdefault("validation", 0)
        diag.timings_ms["validation"] += int((time.time() - t3) * 1000)
        
        # Log validator agent flow
        validator_output = {
            "agent": "VALIDATOR",
            "attempt": attempts + 1,
            "input": {
                "sql": sql,
                "schema_tables": list(pipeline.schema_tables.keys())
            },
            "output": {
                "is_safe": ok,
                "reason": reason,
                "validation_passed": ok
            },
            "timing_ms": diag.timings_ms["validation"]
        }
        agent_flow.append(validator_output)
        
        if not ok:
            status_area.warning(f"⚠️ **Validation Failed:** {reason}")
            status_area.info("🔄 **Processing.... please wait** - Improving the query...")
            
            diag.validator_fail_reasons.append(reason or "unknown")
            attempts += 1
            diag.retries = attempts
            if attempts > pipeline.cfg.max_retries:
                status_area.error("❌ **Max Retries Reached:** Could not generate valid SQL")
                break
            
            sql = pipeline.generator.repair_sql(nl_query, gen_ctx, hint=reason)
            continue
        
        status_area.success("✅ **Validation Passed:** SQL query is safe to execute")
        progress_bar.progress(80)
        
        # Step 5: Execute
        status_area.info("⚡ **Processing.... please wait** - Running query to get your results...")
        progress_bar.progress(85)
        
        t4 = time.time()
        exec_result = pipeline.executor.run_query(sql, limit=pipeline.cfg.sql_row_limit)
        diag.timings_ms["execution"] = int((time.time() - t4) * 1000)
        
        # Log executor agent flow
        executor_output = {
            "agent": "EXECUTOR",
            "input": {
                "sql": sql,
                "limit": pipeline.cfg.sql_row_limit
            },
            "output": {
                "success": exec_result.get("success", False),
                "results_count": len(exec_result.get("results", [])),
                "error": exec_result.get("error", None),
                "execution_time_ms": diag.timings_ms["execution"]
            },
            "timing_ms": diag.timings_ms["execution"]
        }
        agent_flow.append(executor_output)
        
        if exec_result.get("success"):
            status_area.success(f"✅ **Execution Successful:** Found {len(exec_result.get('results', []))} results")
            progress_bar.progress(90)
            
            diag.final_sql = sql
            diag.retries = attempts
            
            # Step 6: Summarize
            status_area.info("📝 **Processing.... please wait** - Preparing your results summary...")
            progress_bar.progress(95)
            
            t5 = time.time()
            out = pipeline.summarizer.summarize(nl_query, exec_result)
            diag.timings_ms["summarization"] = int((time.time() - t5) * 1000)
            
            # Log summarizer agent flow
            summarizer_output = {
                "agent": "SUMMARIZER",
                "input": {
                    "query": nl_query,
                    "results_count": len(exec_result.get('results', [])),
                    "execution_success": exec_result.get("success", False)
                },
                "output": {
                    "summary_length": len(out.get("summary", "")),
                    "has_suggestions": "suggestions" in out,
                    "suggestions_count": len(out.get("suggestions", []))
                },
                "timing_ms": diag.timings_ms["summarization"]
            }
            agent_flow.append(summarizer_output)
            
            out["sql"] = sql
            out["diagnostics"] = diag.__dict__
            out["success"] = True
            out["generated_sql"] = diag.generated_sql
            out["agent_flow"] = agent_flow  # Add agent flow to output
            
            # Add planner suggestions if available
            if hasattr(pipeline, 'planner') and hasattr(pipeline.planner, 'analyze_query'):
                plan = pipeline.planner.analyze_query(nl_query)
                if plan.get("follow_up_suggestions"):
                    out["suggestions"] = plan["follow_up_suggestions"]
            
            total_time = int((time.time() - start_all) * 1000)
            status_area.success(f"🎉 **Pipeline Complete:** Successfully processed in {total_time}ms")
            
            # Show timing breakdown
            with st.expander("⏱️ **Processing Time Breakdown**", expanded=False):
                timing_text = f"""
                - **Planning:** {diag.timings_ms.get('planning', 0)}ms
                - **Context Retrieval:** {diag.timings_ms.get('retrieval', 0)}ms
                - **SQL Generation:** {diag.timings_ms.get('generation', 0)}ms
                - **Validation:** {diag.timings_ms.get('validation', 0)}ms
                - **Execution:** {diag.timings_ms.get('execution', 0)}ms
                - **Summarization:** {diag.timings_ms.get('summarization', 0)}ms
                - **Total Time:** {total_time}ms
                """
                st.markdown(timing_text)
            
            progress_bar.progress(100)
            
            return out
        
                # If execution failed, try repair
        err = exec_result.get("error", "unknown")
        status_area.warning(f"⚠️ **Execution Failed:** {err}")
        status_area.info("🔄 **Processing.... please wait** - Improving the query...")
        
        diag.executor_errors.append(err)
        last_error = err
        attempts += 1
        diag.retries = attempts
        if attempts > pipeline.cfg.max_retries:
            status_area.error("❌ **Max Retries Reached:** Could not execute SQL successfully")
            break
        
        sql = pipeline.generator.repair_sql(nl_query, gen_ctx, hint=err)

    # Failed after retries
    total_ms = int((time.time() - start_all) * 1000)
    diag.timings_ms["total"] = total_ms
    
    status_area.error(f"❌ **Pipeline Failed:** Could not complete after {total_ms}ms")
    
    return {
        "success": False,
        "error": last_error or "Could not produce safe SQL",
        "sql": sql,
        "diagnostics": diag.__dict__,
    }

# Initialize in-memory database
@st.cache_resource
def initialize_in_memory_database():
    """Initialize the in-memory database with schema and data"""
    try:
        print("🚀 Starting Database Initialization...")
        conn, stats = initialize_database()
        
        # Store database stats in session state
        st.session_state.db_stats = stats
        st.session_state.db_initialized = True
        
        print(f"✅ Database initialized with {stats['total_tables']} tables and {stats['total_rows']:,} total rows")
        return conn
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        st.error(f"Database initialization failed: {e}")
        return None

# Validate embeddings at startup
@st.cache_resource
def validate_embeddings():
    """Validate that Ollama is available and can generate embeddings"""
    try:
        print("🧠 Validating Ollama embeddings...")
        
        # Import the embedder
        from backend.embedder import OllamaEmbedder
        
        # Test embedding generation
        embedder = OllamaEmbedder()
        
        # Test with a simple text
        test_text = "This is a test for embedding validation"
        embedding = embedder.generate_embedding(test_text)
        
        if embedding:
            print(f"✅ Embedding validation successful: {len(embedding)} dimensions")
            st.session_state.embeddings_validated = True
            return True
                    else:
            print("❌ Embedding validation failed: No embedding generated")
            st.session_state.embeddings_validated = False
            return False
            
    except Exception as e:
        print(f"❌ Embedding validation failed: {e}")
        st.session_state.embeddings_validated = False
        return False

# Initialize database on first load
if 'db_initialized' not in st.session_state:
    # Show initialization progress
    st.markdown("## 🚀 **System Initialization**")
    st.info("🔄 **System starting up.... please wait** This may take a few moments while we prepare everything for you.")
    
    # Create progress indicators
    init_progress = st.progress(0)
    init_status = st.empty()
    
    # Step 1: Validate embeddings
    init_status.info("🧠 **Setting up.... please wait** - Checking AI embedding system...")
    init_progress.progress(20)
    print("🔍 Validating embeddings at startup...")
    embeddings_valid = validate_embeddings()
    
    # Step 2: Initialize database
    init_status.info("🗄️ **Setting up.... please wait** - Loading database into memory...")
    init_progress.progress(40)
    db_conn = initialize_in_memory_database()
    
    if db_conn:
        st.session_state.db_connection = db_conn
        
        # Step 3: Extract schema and column information
        init_status.info("📋 **Setting up.... please wait** - Learning database structure...")
        init_progress.progress(60)
        
        from backend.db_init import DatabaseInitializer
        initializer = DatabaseInitializer()
        initializer.conn = db_conn
        initializer.cursor = db_conn.cursor()
        
        # Extract schema and column information
        initializer._extract_schema_info()
        initializer._extract_column_values()
        
        # Store in session state
        st.session_state.schema_info = initializer.get_schema_info()
        st.session_state.column_values = initializer.get_column_values()
        
        print("✅ Enhanced database information extracted and stored")
        
        # Step 4: Populate vector database
        init_status.info("📊 **Setting up.... please wait** - Preparing AI knowledge base...")
        init_progress.progress(80)
        
        try:
            print("📊 Populating vector database with schema and column information...")
            retriever = RetrieverAgent(CHROMA_PATH)
            retriever.populate_vector_database(st.session_state.schema_info, st.session_state.column_values)
            print("✅ Vector database populated successfully")
        except Exception as e:
            print(f"⚠️ Warning: Failed to populate vector database: {e}")
            print("🔄 Continuing without vector database population")
        
        # Step 5: Finalize initialization
        init_status.info("⚙️ **Setting up.... please wait** - Finalizing system startup...")
        init_progress.progress(90)
        
        # Check if embeddings are working for vector search
        if 'embeddings_validated' in st.session_state and not st.session_state.embeddings_validated:
            print("⚠️ Embeddings not working - vector search will be disabled")
            st.session_state.vector_search_disabled = True
        else:
            st.session_state.vector_search_disabled = False
        
        # Complete initialization
        init_progress.progress(100)
        init_status.success("✅ **System initialization complete!** Ready to process queries.")
        
        # Clear the initialization UI after a moment
        time.sleep(2)
        init_progress.empty()
        init_status.empty()
        
    else:
        init_status.error("❌ **Initialization Failed:** Database initialization failed. Please check the console for errors.")
        st.stop()

# Use in-memory database connection
DB_PATH = ":memory:"  # In-memory database
CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")
LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "./models/llama-2-7b-chat.Q4_K_M.gguf")

# Get schema from the initialized database
if 'db_connection' in st.session_state:
    cursor = st.session_state.db_connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema_tables = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        schema_tables[table] = [col[1] for col in columns]
    
    print(f"📋 Schema loaded from in-memory database: {list(schema_tables.keys())}")
else:
    # Fallback schema if database not initialized
schema_tables = {
    "accounts": ["id", "customer_id", "account_number", "type", "balance", "opened_at", "interest_rate", "status", "branch_id", "created_at", "updated_at"],
    "branches": ["id", "name", "address", "city", "state", "zip_code", "manager_id", "created_at", "updated_at"],
        "customers": ["id", "email", "phone", "address", "first_name", "last_name", "date_of_birth", "gender", "national_id", "created_at", "updated_at", "branch_id"],
    "employees": ["id", "branch_id", "name", "email", "phone", "position", "hire_date", "salary", "created_at", "updated_at"],
    "transactions": ["id", "account_id", "transaction_date", "amount", "type", "description", "status", "created_at", "updated_at", "employee_id"]
}

# Initialize pipeline components with progress indicator
if 'pipeline_initialized' not in st.session_state:
    pipeline_status = st.empty()
    pipeline_status.info("🔧 **Setting up.... please wait** - Preparing AI agents...")
    
    print(f"🧠 Initializing SQL Generator with model path: {LLAMA_MODEL_PATH}")
generator = SQLGeneratorAgent(model_path=LLAMA_MODEL_PATH)
generator.schema_tables = schema_tables

    pipeline_status.info("🔧 **Setting up.... please wait** - Connecting all AI components...")
pipeline = NL2SQLPipeline(
    planner=PlannerAgent(schema_tables),
    retriever=RetrieverAgent(db_path=CHROMA_PATH),
    generator=generator,
    validator=ValidatorAgent(schema_tables),
        executor=ExecutorAgent(DB_PATH, db_connection=st.session_state.get('db_connection')),
    summarizer=SummarizerAgent(),
    schema_tables=schema_tables,
    config=PipelineConfig()
)
    
    st.session_state.pipeline = pipeline
    st.session_state.pipeline_initialized = True
    pipeline_status.success("✅ **Pipeline initialized successfully!**")
    
    # Clear the pipeline status after a moment
    time.sleep(1)
    pipeline_status.empty()
else:
    pipeline = st.session_state.pipeline

# Show startup message if this is the first load
if 'app_started' not in st.session_state:
    st.markdown("""
    ## 🎉 **Welcome to NL→SQL Assistant!**
    
    This application converts natural language queries into SQL using advanced AI agents.
    
    **Key Features:**
    - 🤖 **Intelligent Query Analysis**: Understands complex business questions
    - 🧠 **LLM-Powered Generation**: Uses local Llama model for SQL generation
    - 🔍 **Vector Search**: Enhanced context retrieval with Ollama embeddings
    - 🗄️ **In-Memory Database**: Fast SQLite database with banking data
    - 🔧 **Thread-Safe Execution**: Handles multiple queries without conflicts
    
    **Ready to start!** Enter your query below.
    """)
    st.session_state.app_started = True

st.title("🤖 NL→SQL Assistant")

# Display database initialization information
if 'db_stats' in st.session_state:
    st.markdown("---")
    st.subheader("🗄️ **Database Information**")
    
    stats = st.session_state.db_stats
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Total Tables", stats['total_tables'])
    
    with col2:
        st.metric("📈 Total Rows", f"{stats['total_rows']:,}")
    
    with col3:
        st.metric("💾 Database Type", "In-Memory SQLite")
    
    # Show table details in an expander
    with st.expander("📋 **Table Details**", expanded=False):
        for table_name, table_stats in stats['tables'].items():
            st.write(f"**{table_name}**: {table_stats['rows']:,} rows, {table_stats['columns']} columns")
    
    st.markdown("---")

# Add health dashboard
st.subheader("🔍 **System Health Dashboard**")

# Show embedding validation status
if 'embeddings_validated' in st.session_state:
    if st.session_state.embeddings_validated:
        st.success("✅ **Embeddings Validated**: Ollama is working correctly")
        if 'vector_search_disabled' in st.session_state and not st.session_state.vector_search_disabled:
            st.success("🔍 **Vector Search**: Available for enhanced context retrieval")
    else:
        st.error("❌ **Embeddings Failed**: Ollama validation failed - vector search disabled")
        st.info("ℹ️ **Note**: App will work with basic SQL generation, but context retrieval may be limited")
else:
    st.info("⏳ **Embeddings**: Validation in progress...")

# Create health dashboard
health_results = create_health_dashboard(st.session_state.get('db_connection'))

# Store health results in session state for sidebar
st.session_state.health_results = health_results

st.markdown("---")

# Initialize session state for conversation history and execution logs
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []
if "execution_logs" not in st.session_state:
    st.session_state.execution_logs = []

# Create a custom print function that also logs to Streamlit
def st_print(message):
    """Print to console and also log to Streamlit execution view"""
    print(message)
    st.session_state.execution_logs.append(message)
    # Keep only last 100 logs to prevent memory issues
    if len(st.session_state.execution_logs) > 100:
        st.session_state.execution_logs = st.session_state.execution_logs[-100:]

# Create sidebar for execution view
with st.sidebar:
    st.header("🔍 **Execution View**")
    st.markdown("Real-time control flow and agent interactions")
    
    # Add mode toggle
    st.subheader("⚙️ **Settings**")
    use_llm = st.checkbox("🧠 Use LLM (slower but smarter)", value=True)
    if not use_llm:
        st.warning("🔄 Fallback mode enabled - faster responses")
    
    # Add a clear logs button
    if st.button("🗑️ Clear Logs"):
        st.session_state.execution_logs = []
        st.rerun()
    
    # Add a toggle for auto-scroll
    auto_scroll = st.checkbox("📜 Auto-scroll to latest", value=True)
    
    # Add mini health status
    if 'health_results' in st.session_state:
        st.markdown("---")
        st.subheader("🔍 **System Health**")
        
        # Overall status
        from health_checker import HealthStatus
        healthy_count = sum(1 for h in st.session_state.health_results.values() if h.status == HealthStatus.HEALTHY)
        error_count = sum(1 for h in st.session_state.health_results.values() if h.status == HealthStatus.ERROR)
        
        if error_count == 0:
            st.success(f"✅ All systems healthy ({healthy_count}/{len(st.session_state.health_results)})")
        elif error_count > 0:
            st.error(f"❌ {error_count} system(s) have issues")
        else:
            st.warning(f"⚠️ Some systems need attention")
        
        # Component status
        for component_name, health in st.session_state.health_results.items():
            status_emoji = "✅" if health.status == HealthStatus.HEALTHY else "⚠️" if health.status == HealthStatus.WARNING else "❌"
            st.markdown(f"**{component_name.title()}:** {status_emoji}")
        
        # Embedding validation status
        if 'embeddings_validated' in st.session_state:
            embed_status = "✅" if st.session_state.embeddings_validated else "❌"
            st.markdown(f"**Embeddings:** {embed_status}")
        
        # Refresh health check button
        if st.button("🔄 Refresh Health"):
            # Clear health results to force refresh
            if 'health_results' in st.session_state:
                del st.session_state.health_results
            st.rerun()
    
    # Display execution logs
    if st.session_state.execution_logs:
        st.subheader("📋 **Live Execution Logs**")
        
        # Create a container for logs with custom styling
        log_container = st.container()
        with log_container:
            for i, log in enumerate(st.session_state.execution_logs):
                # Color code different types of logs
                if "ORCHESTRATOR" in log:
                    st.markdown(f"🎯 **{log}**")
                elif "PLANNER AGENT" in log:
                    st.markdown(f"📋 {log}")
                elif "RETRIEVER AGENT" in log:
                    st.markdown(f"🔍 {log}")
                elif "SQL GENERATOR AGENT" in log or "Generating SQL" in log:
                    st.markdown(f"🧠 {log}")
                elif "VALIDATOR AGENT" in log:
                    st.markdown(f"🔍 {log}")
                elif "EXECUTOR AGENT" in log:
                    st.markdown(f"⚡ {log}")
                elif "SUMMARIZER AGENT" in log:
                    st.markdown(f"📝 {log}")
                elif "LOCAL LLM" in log:
                    st.markdown(f"💻 {log}")
                elif "REMOTE LLM" in log:
                    st.markdown(f"🌐 {log}")
                elif "ERROR" in log or "❌" in log:
                    st.error(log)
                elif "SUCCESS" in log or "✅" in log:
                    st.success(log)
                elif "WARNING" in log or "⚠️" in log:
                    st.warning(log)
                else:
                    st.text(log)
                
                # Add a small separator between logs
                if i < len(st.session_state.execution_logs) - 1:
                    st.markdown("---")
    else:
        st.info("📋 No execution logs yet. Start a query to see real-time control flow!")

query = st.chat_input("Ask about the database…")

# Handle clarification responses from user
if "pending_clarifications" in st.session_state and query:
    st.markdown("### 🔄 **Processing Clarification Response**")
    st.info(f"**Original Query:** {st.session_state.original_query}")
    st.info(f"**Your Clarification Response:** {query}")
    
    # Parse the clarification response
    clarification_values = {}
    pending_clarifications = st.session_state.pending_clarifications
    
    # Extract clarification values from user input
    for clarification in pending_clarifications:
        field_name = clarification.get("field", "")
        prompt = clarification.get("prompt", "")
        default_value = clarification.get("default", "")
        
        # Try to extract the value from user input
        if field_name.lower() in query.lower():
            # Look for patterns like "Q1: value" or "date range: value"
            import re
            patterns = [
                rf"{field_name}:\s*([^,\n]+)",
                rf"{field_name}\s*=\s*([^,\n]+)",
                rf"{field_name}\s*([^,\n]+)"
            ]
            
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    clarification_values[field_name] = match.group(1).strip()
                    break
            
            # If no pattern match, use default value
            if field_name not in clarification_values and default_value:
                clarification_values[field_name] = default_value
    
    # If we couldn't extract specific values, try to use the entire input as clarification
    if not clarification_values and pending_clarifications:
        # Use the entire query as the clarification for the first field
        first_clarification = pending_clarifications[0]
        field_name = first_clarification.get("field", "clarification")
        clarification_values[field_name] = query
    
    st.success(f"✅ **Clarifications extracted:** {clarification_values}")
    
    # Store clarification values for pipeline processing
    st.session_state.clarification_values = clarification_values
    
    # Now process the original query with clarifications
    original_query = st.session_state.original_query
    pipeline_response = st.session_state.pipeline_response
    
    # Create enhanced query with clarifications
    enhanced_query = original_query
    for field_name, value in clarification_values.items():
        enhanced_query += f" ({field_name}: {value})"
    
    # Use the enhanced query for processing
    query = enhanced_query
    
    # Clear the pending clarifications from session state but keep clarification_values
    del st.session_state.pending_clarifications
    del st.session_state.original_query
    del st.session_state.pipeline_response
    
    st.success("✅ **Enhanced query ready for processing!**")

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
                import pandas as pd
                df = pd.DataFrame(response["table"])
                record_count = len(df)
                st.subheader(f"📋 Results ({record_count:,} records)")
                st.dataframe(df, use_container_width=True)
    
    st.divider()

if query:
    st_print(f"\n=== NEW QUERY: {query} ===")
    
    # Display current query prominently
    st.markdown("---")
    st.markdown(f"### 💬 **Your Question:**")
    st.info(f"**{query}**")
    st.markdown("---")
    
    # Enhanced loading display with CSS animation
    loading_css = """
    <style>
    .processing-container {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        color: white;
        margin: 10px 0;
    }
    
    .loading-spinner {
        display: inline-block;
        width: 20px;
        height: 20px;
        border: 3px solid rgba(255,255,255,0.3);
        border-radius: 50%;
        border-top-color: #fff;
        animation: spin 1s ease-in-out infinite;
        margin-left: 10px;
    }
    
    @keyframes spin {
        to { transform: rotate(360deg); }
    }
    </style>
    """
    st.markdown(loading_css, unsafe_allow_html=True)
    # Create status display area
    st.markdown("---")
    st.markdown("""
    <div class="processing-container">
        <div style="font-size: 24px; margin-bottom: 10px;">🔄</div>
        <div style="font-size: 18px; margin-bottom: 10px;">Processing.... please wait</div>
        <div style="font-size: 14px; opacity: 0.9;">Our AI agents are working on your request</div>
        <div class="loading-spinner"></div>
    </div>
    """, unsafe_allow_html=True)
    
    # Create a dedicated status area
    status_area = st.empty()
    progress_bar = st.progress(0)
    
    with st.spinner("🤖 AI is working on your query.... please wait, this may take a moment..."):
        # Initialize status
        status_area.info("🔄 **Processing.... please wait** - Starting up the AI system...")
        progress_bar.progress(10)
        
        # Custom pipeline execution with real-time updates
    try:
        # Check if we have clarification values from previous interaction
        clarification_values = {}
        if "pending_clarifications" in st.session_state and "clarification_values" in st.session_state:
            clarification_values = st.session_state.clarification_values
        
        # Custom pipeline execution with real-time updates
        resp = custom_pipeline_run_with_status(pipeline, query, status_area, progress_bar, clarification_values)
    except Exception as e:
        st.error(f"❌ **Processing Error:** {str(e)}")
        resp = {"success": False, "error": str(e), "agent_flow": []}
        st_print(f"Pipeline failed with error: {str(e)}")
        resp = custom_pipeline_run_with_status(pipeline, query, status_area, progress_bar, clarification_values)
    
    # Clear the status area after completion
    status_area.empty()
    progress_bar.empty()
    
    st_print(f"Pipeline result: Success={resp.get('success', False)}")
    
    # Handle clarification responses in main UI
    if resp.get("needs_clarification"):
        st.markdown("### ❓ **Clarification Needed**")
        st.warning("The AI needs more information to process your query properly.")
        
        clarifications = resp.get("clarifications", [])
        if clarifications:
            st.markdown("**Please provide the following details:**")
            for i, clarification in enumerate(clarifications, 1):
                field_name = clarification.get("field", f"clarification_{i}")
                prompt = clarification.get("prompt", f"Clarification {i+1}")
                default_value = clarification.get("default", "")
                st.markdown(f"**{i+1}. {prompt}**")
                st.info(f"**Suggested answer:** {default_value}")
                st.markdown("---")
            
            # Store clarifications in session state for processing
            st.session_state.pending_clarifications = clarifications
            st.session_state.original_query = query
            st.session_state.pipeline_response = resp
            
            st.markdown("**💡 How to provide clarifications:**")
            st.markdown("**Option 1:** Type your clarifications in the chat box below")
            st.markdown("**Option 2:** Use the suggested answers above")
            st.markdown("**Option 3:** Combine with your original query")
            
            st.markdown("**📝 Examples:**")
            st.markdown("- `Q1: 2025-01-01 to 2025-03-31`")
            st.markdown("- `date range: 2025-01-01..2025-03-31`")
            st.markdown("- `Show me Q1 performance (Q1: 2025-01-01 to 2025-03-31)`")
            
            # Show agent flow if available
            if resp.get("agent_flow"):
                st.markdown("---")
                st.subheader("🤖 **Agent Flow Analysis**")
                st.markdown("*What the AI understood so far*")
                
                agent_flow = resp["agent_flow"]
                for flow in agent_flow:
                    with st.expander(f"📋 {flow['agent']}", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**📥 Input:**")
                            st.json(flow["input"])
                        with col2:
                            st.markdown("**📤 Output:**")
                            st.json(flow["output"])
            
            # Skip further processing when clarifications are needed
            st.stop()
    
    # Store in conversation history
    st.session_state.conversation_history.append((query, resp))
    
    # Show summary prominently at the top
    if resp.get("summary"): 
        st.markdown("### 📊 **Analysis:**")
        st.markdown(resp.get("summary"))
        st.divider()
    
    # Show record count prominently
    if resp.get("table"):
        import pandas as pd
        df = pd.DataFrame(resp["table"])
        record_count = len(df)
        st.markdown("### 📈 **Query Results:**")
        st.success(f"✅ **Found {record_count:,} records**")
        st.divider()
    
    # Show SQL in an expandable section (for technical users)
    if resp.get("sql"): 
        with st.expander("🔧 Generated SQL Query", expanded=False):
            st.code(resp["sql"], language="sql")
    
    # Show table results
    if resp.get("table"):
        import pandas as pd
        df = pd.DataFrame(resp["table"])
        record_count = len(df)
        st.subheader(f"📋 Results ({record_count:,} records)")
        st.dataframe(df, use_container_width=True)
    
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
    
    # Display Agent Flow Analysis
    if resp.get("agent_flow"):
        st.markdown("---")
        st.subheader("🤖 **Agent Flow Analysis**")
        st.markdown("*Detailed breakdown of each agent's input and output*")
        
        agent_flow = resp["agent_flow"]
        
        # Create tabs for each agent
        agent_tabs = st.tabs([f"📋 {flow['agent']}" for flow in agent_flow])
        
        for i, (flow, tab) in enumerate(zip(agent_flow, agent_tabs)):
            with tab:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**📥 Input:**")
                    st.json(flow["input"])
                
                with col2:
                    st.markdown("**📤 Output:**")
                    st.json(flow["output"])
                
                # Show timing information
                st.markdown(f"**⏱️ Processing Time:** {flow['timing_ms']}ms")
                
                # Add specific insights for each agent
                if flow["agent"] == "PLANNER":
                    if flow["output"].get("tables"):
                        st.success(f"✅ Identified {len(flow['output']['tables'])} relevant tables")
                    if flow["output"].get("clarifications"):
                        st.warning(f"⚠️ {len(flow['output']['clarifications'])} clarifications needed")
                
                elif flow["agent"] == "RETRIEVER":
                    context_count = flow["output"].get("schema_context_count", 0)
                    st.info(f"🔍 Retrieved {context_count} schema context items")
                    
                    # Show ChromaDB and Ollama interactions
                    if flow["output"].get("chromadb_interactions"):
                        with st.expander("🗄️ ChromaDB Interactions", expanded=False):
                            chroma_data = flow["output"]["chromadb_interactions"]
                            
                            # Collection info
                            if chroma_data.get("collection_info"):
                                col_info = chroma_data["collection_info"]
                                if "error" not in col_info:
                                    st.success(f"📊 Collection: {col_info.get('collection_name', 'Unknown')}")
                                    st.info(f"📈 Total Documents: {col_info.get('total_documents', 0)}")
                                else:
                                    st.error(f"❌ Collection Error: {col_info['error']}")
                            
                            # Query execution
                            if chroma_data.get("query_execution"):
                                query_exec = chroma_data["query_execution"]
                                st.info(f"⚡ Query Time: {query_exec.get('query_time_ms', 0)}ms")
                                st.info(f"📊 Results: {query_exec.get('actual_results', 0)}/{query_exec.get('requested_results', 0)}")
                            
                            # Vector search details
                            if chroma_data.get("vector_search"):
                                vector_data = chroma_data["vector_search"]
                                if vector_data.get("similarity_scores"):
                                    st.info(f"🎯 Best Match: {vector_data.get('best_match_score', 0):.3f}")
                                    st.info(f"📊 Average Similarity: {vector_data.get('average_similarity', 0):.3f}")
                                    st.info(f"📈 Similarity Scores: {vector_data.get('similarity_scores', [])}")
                    
                    # Show Ollama interactions
                    if flow["output"].get("ollama_interactions"):
                        with st.expander("🧠 Ollama Interactions", expanded=False):
                            ollama_data = flow["output"]["ollama_interactions"]
                            
                            st.info(f"🤖 Model: {ollama_data.get('model_used', 'Unknown')}")
                            st.info(f"🌐 Server: {ollama_data.get('ollama_url', 'Unknown')}")
                            
                            if ollama_data.get("embedding_generation"):
                                embed_data = ollama_data["embedding_generation"]
                                if embed_data.get("success"):
                                    st.success(f"✅ Embedding Generated")
                                    st.info(f"📏 Dimensions: {embed_data.get('embedding_dimensions', 0)}")
                                    st.info(f"⏱️ Generation Time: {embed_data.get('generation_time_ms', 0)}ms")
                                    st.info(f"📝 Query: {embed_data.get('query_text', 'Unknown')}")
                                else:
                                    st.error("❌ Embedding Generation Failed")
                
                elif flow["agent"] == "SQL_GENERATOR":
                    sql = flow["output"].get("generated_sql", "")
                    if "LIMIT 10" in sql and "SELECT * FROM" in sql:
                        st.warning("⚠️ Used fallback SQL generation")
                    else:
                        st.success("✅ Generated custom SQL query")
                
                elif flow["agent"] == "VALIDATOR":
                    if flow["output"].get("validation_passed"):
                        st.success("✅ SQL validation passed")
                    else:
                        st.error(f"❌ Validation failed: {flow['output'].get('reason', 'Unknown')}")
                
                elif flow["agent"] == "EXECUTOR":
                    if flow["output"].get("success"):
                        st.success(f"✅ Executed successfully: {flow['output'].get('results_count', 0)} results")
                    else:
                        st.error(f"❌ Execution failed: {flow['output'].get('error', 'Unknown')}")
                
                elif flow["agent"] == "SUMMARIZER":
                    summary_length = flow["output"].get("summary_length", 0)
                    st.info(f"📝 Generated {summary_length} character summary")
