"""Main Streamlit Application"""
import os
import streamlit as st
from dotenv import load_dotenv
from backend.pipeline import NL2SQLPipeline, PipelineConfig
from backend.planner import PlannerAgent
from backend.retriever import RetrieverAgent
from backend.sql_generator import SQLGeneratorAgent
from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent
from backend.logger_config import log_agent_flow, get_agent_flow_data
from frontend.agent_tabs_ui import render_agent_tabs

# Load environment variables
load_dotenv()

# Configuration
DB_PATH = os.getenv("SQLITE_DB_PATH", "banking.db")
CHROMA_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")

# Schema definition
schema_tables = {
    "accounts": ["id", "customer_id", "account_number", "type", "balance", "opened_at", "interest_rate", "status", "branch_id", "created_at", "updated_at"],
    "branches": ["id", "name", "address", "city", "state", "zip_code", "manager_id", "created_at", "updated_at"],
    "employees": ["id", "branch_id", "name", "email", "phone", "position", "hire_date", "salary", "created_at", "updated_at"],
    "transactions": ["id", "account_id", "transaction_date", "amount", "type", "description", "status", "created_at", "updated_at", "employee_id"]
}

# Initialize agents
@log_agent_flow("initialize_pipeline")
def initialize_pipeline():
    """Initialize the NL2SQL pipeline with all agents"""
    generator = SQLGeneratorAgent(temperature=0.1)
    generator.schema_tables = schema_tables

    return NL2SQLPipeline(
        planner=PlannerAgent(schema_tables),
        retriever=RetrieverAgent(db_path=CHROMA_PATH),
        generator=generator,
        validator=ValidatorAgent(schema_tables),
        executor=ExecutorAgent(DB_PATH),
        summarizer=SummarizerAgent(),
        schema_tables=schema_tables,
        config=PipelineConfig()
    )

# Streamlit UI
st.set_page_config(layout="wide")
st.title("🤖 NL→SQL Assistant")

# Create tabs for different views
main_tab, agents_tab = st.tabs(["🔍 Main", "🤖 Agents"])

with main_tab:
    # Initialize session state
    if "conversation_history" not in st.session_state:
        st.session_state.conversation_history = []
    
    if "pipeline" not in st.session_state:
        st.session_state.pipeline = initialize_pipeline()

    # Query input
    query = st.chat_input("Ask about the database...")

    # Handle re-run queries from history
    if "rerun_query" in st.session_state:
        query = st.session_state.rerun_query
        del st.session_state.rerun_query

    # Display conversation history
    if st.session_state.conversation_history:
        st.subheader("📝 Conversation History")
        for i, (user_query, response) in enumerate(st.session_state.conversation_history):
            with st.expander(f"💬 Q{i+1}: {user_query[:50]}{'...' if len(user_query) > 50 else ''}", expanded=False):
                # Re-run button
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
                    st.dataframe(pd.DataFrame(response["table"]))
        
        st.divider()

    # Process new query
    if query:
        st.markdown("---")
        st.markdown(f"### 💬 **Your Question:**")
        st.info(f"**{query}**")
        st.markdown("---")
        
        with st.spinner("🔄 Processing your query..."):
            try:
                resp = st.session_state.pipeline.run(query)
                st.session_state.conversation_history.append((query, resp))
                
                # Show summary
                if resp.get("summary"): 
                    st.markdown("### 📊 **Analysis:**")
                    st.markdown(resp.get("summary"))
                    st.divider()
                
                # Show SQL
                if resp.get("sql"): 
                    with st.expander("🔧 Generated SQL Query", expanded=False):
                        st.code(resp["sql"], language="sql")
                
                # Show results
                if resp.get("table"):
                    st.subheader("📋 Results")
                    import pandas as pd
                    st.dataframe(pd.DataFrame(resp["table"]))
                
                # Show suggestions
                if resp.get("suggestions"):
                    st.divider()
                    st.subheader("💡 Suggested Follow-up Questions")
                    
                    # Create columns for suggestions
                    cols = st.columns(2)
                    for i, suggestion in enumerate(resp["suggestions"]):
                        col = cols[i % 2]
                        if col.button(suggestion, key=f"suggestion_{i}"):
                            st.info(f"💡 You can copy and paste this question: **{suggestion}**")
                    
                    st.markdown("**Or copy these questions:**")
                    for suggestion in resp["suggestions"]:
                        st.markdown(f"• `{suggestion}`")
            
            except Exception as e:
                st.error(f"❌ Error processing query: {str(e)}")
        
        # Clear history button
        if st.button("🗑️ Clear Conversation History"):
            st.session_state.conversation_history = []
            st.rerun()

with agents_tab:
    # Display detailed agent information
    agent_data = get_agent_flow_data()
    render_agent_tabs(agent_data)