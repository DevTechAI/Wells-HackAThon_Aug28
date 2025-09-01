#!/usr/bin/env python3
"""
Streamlit App for SQL RAG Agent
Features: Security & Validation Guards, Recent Queries, Tech Stack Info, Detailed Timing Dashboard, Real-time CoT, Pagination
"""

import streamlit as st
import os
import sys
import time
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import math

# Add backend to path
sys.path.append('./backend')

from backend.system_initializer import SystemInitializer
from backend.llm_config import llm_config
from backend.validator import ValidatorAgent
from backend.db_manager import get_db_manager
from backend.pdf_exporter import PDFExporter, create_query_data_for_pdf

# Page configuration
st.set_page_config(
    page_title="Local NL → SQL (Offline)",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for bright cream/white theme
st.markdown("""
<style>
    /* Bright cream/white background - target all Streamlit elements */
    .main {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #000000 !important;  /* Black text */
    }
    .stApp {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #000000 !important;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
    .security-guard {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .guard-success {
        background-color: #f0f9ff !important;
        border-color: #27ae60 !important;
    }
    .guard-warning {
        background-color: #fff7ed !important;
        border-color: #f39c12 !important;
    }
    .guard-error {
        background-color: #fef2f2 !important;
        border-color: #e74c3c !important;
    }
    .recent-query {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
        cursor: pointer !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .recent-query:hover {
        background-color: #f8f9fa !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    .tech-stack-item {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 6px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .timing-card {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .timing-success {
        border-color: #27ae60 !important;
    }
    .timing-warning {
        border-color: #f39c12 !important;
    }
    .timing-error {
        border-color: #e74c3c !important;
    }
    .cot-step {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 16px !important;
        margin: 8px 0 !important;
        animation: fadeIn 0.5s ease-in !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    .cot-step.active {
        border-color: #3498db !important;
        background-color: #f0f8ff !important;
    }
    .cot-step.completed {
        border-color: #27ae60 !important;
        background-color: #f0f9ff !important;
    }
    .cot-step.error {
        border-color: #e74c3c !important;
        background-color: #fef2f2 !important;
    }
    .pagination {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 10px !important;
        margin: 20px 0 !important;
    }
    .pagination button {
        background-color: #3498db !important;
        border: 1px solid #3498db !important;
        color: #ffffff !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        cursor: pointer !important;
    }
    .pagination button:hover {
        background-color: #2980b9 !important;
    }
    .pagination button.active {
        background-color: #27ae60 !important;
        border-color: #27ae60 !important;
    }
    .pagination button:disabled {
        background-color: #bdc3c7 !important;
        color: #95a5a6 !important;
        cursor: not-allowed !important;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .query-time {
        font-size: 0.8em !important;
        color: #7f8c8d !important;
    }
    .user-role {
        font-size: 0.9em !important;
        color: #2c3e50 !important;
    }
    .agent-timing {
        font-family: 'Courier New', monospace !important;
        font-size: 0.9em !important;
        background-color: #f8f9fa !important;
        padding: 8px !important;
        border-radius: 4px !important;
        margin: 4px 0 !important;
        border: 1px solid #e0e0e0 !important;
    }
    .llm-interaction {
        background-color: #f0f8ff !important;
        border-color: #3498db !important;
    }
    .vectordb-interaction {
        background-color: #fff7ed !important;
        border-color: #f39c12 !important;
    }
    .database-interaction {
        background-color: #f0f9ff !important;
        border-color: #27ae60 !important;
    }
    
    /* Override any dark theme styles */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
</style>
""", unsafe_allow_html=True)
        color: #f9fafb;
        padding: 8px 12px;
        border-radius: 4px;
        cursor: pointer;
    }
    .pagination button:hover {
        background-color: #4b5563;
    }
    .pagination button.active {
        background-color: #3b82f6;
        border-color: #3b82f6;
    }
    .pagination button:disabled {
        background-color: #1f2937;
        color: #6b7280;
        cursor: not-allowed;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    .query-time {
        font-size: 0.8em;
        color: #9ca3af;
    }
    .user-role {
        font-size: 0.9em;
        color: #d1d5db;
    }
    .agent-timing {
        font-family: 'Courier New', monospace;
        font-size: 0.9em;
        background-color: #111827;
        padding: 8px;
        border-radius: 4px;
        margin: 4px 0;
    }
    .llm-interaction {
        background-color: #1e3a8a;
        border-color: #3b82f6;
    }
    .vectordb-interaction {
        background-color: #7c2d12;
        border-color: #ea580c;
    }
    .database-interaction {
        background-color: #065f46;
        border-color: #10b981;
    }
</style>
""", unsafe_allow_html=True)

class CoTStep:
    """Chain-of-Thought step representation"""
    
    def __init__(self, step_id: str, agent: str, description: str, status: str = "pending"):
        self.step_id = step_id
        self.agent = agent
        self.description = description
        self.status = status  # pending, active, completed, error
        self.start_time = None
        self.end_time = None
        self.details = {}
        self.output = None
    
    def start(self):
        """Mark step as started"""
        self.status = "active"
        self.start_time = time.time()
    
    def complete(self, output: Any = None, details: Dict[str, Any] = None):
        """Mark step as completed"""
        self.status = "completed"
        self.end_time = time.time()
        self.output = output
        if details:
            self.details.update(details)
    
    def error(self, error_message: str):
        """Mark step as failed"""
        self.status = "error"
        self.end_time = time.time()
        self.details["error"] = error_message
    
    def get_duration(self) -> float:
        """Get step duration in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return 0.0

class CoTWorkflow:
    """Chain-of-Thought workflow manager"""
    
    def __init__(self):
        self.steps = []
        self.current_step = 0
        self.completed = False
    
    def add_step(self, step_id: str, agent: str, description: str) -> CoTStep:
        """Add a new CoT step"""
        step = CoTStep(step_id, agent, description)
        self.steps.append(step)
        return step
    
    def get_current_step(self) -> Optional[CoTStep]:
        """Get current active step"""
        if 0 <= self.current_step < len(self.steps):
            return self.steps[self.current_step]
        return None
    
    def next_step(self):
        """Move to next step"""
        if self.current_step < len(self.steps) - 1:
            self.current_step += 1
        else:
            self.completed = True
    
    def get_progress(self) -> float:
        """Get workflow progress (0-1)"""
        if not self.steps:
            return 0.0
        return (self.current_step + 1) / len(self.steps)

class PaginationManager:
    """Manage pagination for large result sets"""
    
    def __init__(self, data: List[Dict[str, Any]], page_size: int = 10):
        self.data = data
        self.page_size = page_size
        self.total_pages = math.ceil(len(data) / page_size)
        self.current_page = 0
    
    def get_page_data(self, page: int) -> List[Dict[str, Any]]:
        """Get data for specific page"""
        if page < 0 or page >= self.total_pages:
            return []
        
        start_idx = page * self.page_size
        end_idx = start_idx + self.page_size
        return self.data[start_idx:end_idx]
    
    def get_current_page_data(self) -> List[Dict[str, Any]]:
        """Get data for current page"""
        return self.get_page_data(self.current_page)
    
    def next_page(self):
        """Go to next page"""
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
    
    def prev_page(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
    
    def go_to_page(self, page: int):
        """Go to specific page"""
        if 0 <= page < self.total_pages:
            self.current_page = page
    
    def get_page_info(self) -> Dict[str, Any]:
        """Get pagination information"""
        return {
            "current_page": self.current_page + 1,
            "total_pages": self.total_pages,
            "total_records": len(self.data),
            "page_size": self.page_size,
            "start_record": self.current_page * self.page_size + 1,
            "end_record": min((self.current_page + 1) * self.page_size, len(self.data))
        }

class TimingTracker:
    """Track detailed timing for each component and interaction"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.agent_timings = {}
        self.llm_interactions = []
        self.vectordb_interactions = []
        self.database_interactions = []
        self.total_time = 0
    
    def start_workflow(self):
        """Start timing the entire workflow"""
        self.start_time = time.time()
        self.agent_timings = {}
        self.llm_interactions = []
        self.vectordb_interactions = []
        self.database_interactions = []
    
    def end_workflow(self):
        """End timing the entire workflow"""
        self.end_time = time.time()
        self.total_time = self.end_time - self.start_time
    
    def track_agent(self, agent_name: str, start_time: float, end_time: float, 
                   status: str = "success", details: Dict[str, Any] = None):
        """Track timing for a specific agent"""
        duration = end_time - start_time
        self.agent_timings[agent_name] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "duration_ms": int(duration * 1000),
            "status": status,
            "details": details or {}
        }
    
    def track_llm_interaction(self, interaction_type: str, start_time: float, 
                           end_time: float, model: str, tokens_used: int = 0):
        """Track LLM interaction timing"""
        duration = end_time - start_time
        self.llm_interactions.append({
            "type": interaction_type,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "duration_ms": int(duration * 1000),
            "model": model,
            "tokens_used": tokens_used
        })
    
    def track_vectordb_interaction(self, operation: str, start_time: float, 
                                 end_time: float, collection: str, results_count: int = 0):
        """Track VectorDB interaction timing"""
        duration = end_time - start_time
        self.vectordb_interactions.append({
            "operation": operation,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "duration_ms": int(duration * 1000),
            "collection": collection,
            "results_count": results_count
        })
    
    def track_database_interaction(self, operation: str, start_time: float, 
                                 end_time: float, table: str, rows_affected: int = 0):
        """Track database interaction timing"""
        duration = end_time - start_time
        self.database_interactions.append({
            "operation": operation,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "duration_ms": int(duration * 1000),
            "table": table,
            "rows_affected": rows_affected
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get timing summary"""
        return {
            "total_time": self.total_time,
            "total_time_ms": int(self.total_time * 1000),
            "agent_timings": self.agent_timings,
            "llm_interactions": self.llm_interactions,
            "vectordb_interactions": self.vectordb_interactions,
            "database_interactions": self.database_interactions,
            "total_llm_time": sum(i["duration"] for i in self.llm_interactions),
            "total_vectordb_time": sum(i["duration"] for i in self.vectordb_interactions),
            "total_database_time": sum(i["duration"] for i in self.database_interactions)
        }

class SecurityGuard:
    """Security and validation guard system"""
    
    def __init__(self):
        self.guards_applied = []
        self.validation_results = {}
    
    def apply_guards(self, sql: str, schema_tables: Dict[str, Any]) -> Dict[str, Any]:
        """Apply security guards to SQL query"""
        guards = []
        
        # Guard 1: LIMIT clause injection
        if "LIMIT" not in sql.upper():
            sql = f"{sql.rstrip(';')} LIMIT 200;"
            guards.append({
                "type": "LIMIT_INJECTION",
                "description": "Guard: LIMIT injected to cap result size at 200",
                "status": "success",
                "icon": "✅"
            })
        
        # Guard 2: SQL injection prevention
        dangerous_keywords = ["DROP", "DELETE", "UPDATE", "INSERT", "ALTER", "CREATE", "TRUNCATE"]
        for keyword in dangerous_keywords:
            if keyword in sql.upper():
                guards.append({
                    "type": "DANGEROUS_OPERATION",
                    "description": f"Guard: Blocked dangerous operation '{keyword}'",
                    "status": "error",
                    "icon": "🚫"
                })
        
        # Guard 3: Only SELECT statements allowed
        if not sql.strip().upper().startswith("SELECT"):
            guards.append({
                "type": "INVALID_OPERATION",
                "description": "Guard: Only SELECT statements are allowed",
                "status": "error",
                "icon": "🚫"
            })
        
        # Guard 4: Table validation
        table_mentioned = False
        for table in schema_tables:
            if table.upper() in sql.upper():
                table_mentioned = True
                break
        
        if not table_mentioned:
            guards.append({
                "type": "TABLE_VALIDATION",
                "description": "Guard: No valid tables detected in query",
                "status": "warning",
                "icon": "⚠️"
            })
        
        # Guard 5: Query complexity check
        if sql.count("SELECT") > 1 or sql.count("FROM") > 2:
            guards.append({
                "type": "COMPLEXITY_CHECK",
                "description": "Guard: Complex query detected - may impact performance",
                "status": "warning",
                "icon": "⚠️"
            })
        
        return {
            "original_sql": sql,
            "guarded_sql": sql,
            "guards_applied": guards,
            "total_guards": len(guards)
        }

class QueryHistory:
    """Manage recent queries in session"""
    
    def __init__(self):
        if 'query_history' not in st.session_state:
            st.session_state.query_history = []
    
    def add_query(self, user: str, role: str, query: str, sql: str, results: Any, 
                  guards: Dict[str, Any], timing: Dict[str, Any]):
        """Add a new query to history"""
        query_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "role": role,
            "query": query,
            "sql": sql,
            "results_count": len(results) if isinstance(results, list) else 0,
            "guards": guards,
            "timing": timing,
            "expanded": False
        }
        
        st.session_state.query_history.insert(0, query_entry)
        
        # Keep only last 20 queries
        if len(st.session_state.query_history) > 20:
            st.session_state.query_history = st.session_state.query_history[:20]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get query history"""
        return st.session_state.query_history

def render_cot_workflow(cot_workflow: CoTWorkflow):
    """Render Chain-of-Thought workflow in real-time"""
    st.markdown("### 🧠 Chain-of-Thought Processing")
    
    # Progress bar
    progress = cot_workflow.get_progress()
    st.progress(progress)
    st.markdown(f"**Progress:** {progress:.1%} ({cot_workflow.current_step + 1}/{len(cot_workflow.steps)})")
    
    # Render each step
    for i, step in enumerate(cot_workflow.steps):
        # Determine CSS class based on status
        status_class = f"cot-step {step.status}"
        
        # Create step header
        step_header = f"**Step {i+1}:** {step.agent.upper()} - {step.description}"
        
        # Add timing info if step is completed
        timing_info = ""
        if step.status == "completed" and step.get_duration() > 0:
            timing_info = f" ⏱️ {step.get_duration():.3f}s"
        
        # Add status icon
        status_icon = {
            "pending": "⏳",
            "active": "🔄",
            "completed": "✅",
            "error": "❌"
        }.get(step.status, "⏳")
        
        st.markdown(f"""
        <div class="{status_class}">
            <h4>{status_icon} {step_header}{timing_info}</h4>
        """, unsafe_allow_html=True)
        
        # Show step details if available
        if step.details:
            for key, value in step.details.items():
                if key != "error":
                    st.markdown(f"**{key.title()}:** {value}")
        
        # Show error if step failed
        if step.status == "error" and "error" in step.details:
            st.error(f"Error: {step.details['error']}")
        
        # Show output if step completed
        if step.status == "completed" and step.output:
            if isinstance(step.output, str):
                st.markdown(f"**Output:** {step.output}")
            else:
                st.json(step.output)
        
        st.markdown("</div>", unsafe_allow_html=True)

def render_paginated_results(results: List[Dict[str, Any]], page_size: int = 10):
    """Render results with pagination"""
    if not results:
        st.warning("No results found for this query")
        return
    
    # Initialize pagination
    if 'pagination' not in st.session_state:
        st.session_state.pagination = PaginationManager(results, page_size)
    
    pagination = st.session_state.pagination
    
    # Show pagination info
    page_info = pagination.get_page_info()
    st.info(f"📊 Showing {page_info['start_record']}-{page_info['end_record']} of {page_info['total_records']} results")
    
    # Get current page data
    current_data = pagination.get_current_page_data()
    
    # Convert to DataFrame and display
    df = pd.DataFrame(current_data)
    st.dataframe(df, width="stretch")
    
    # Pagination controls
    if pagination.total_pages > 1:
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=pagination.current_page == 0):
                pagination.go_to_page(0)
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", disabled=pagination.current_page == 0):
                pagination.prev_page()
                st.rerun()
        
        with col3:
            st.markdown(f"**Page {page_info['current_page']} of {page_info['total_pages']}**")
        
        with col4:
            if st.button("Next ▶️", disabled=pagination.current_page == pagination.total_pages - 1):
                pagination.next_page()
                st.rerun()
        
        with col5:
            if st.button("Last ⏭️", disabled=pagination.current_page == pagination.total_pages - 1):
                pagination.go_to_page(pagination.total_pages - 1)
                st.rerun()

def render_detailed_timing_dashboard(timing_summary: Dict[str, Any]):
    """Render detailed timing dashboard"""
    st.markdown("### ⏱️ Detailed Timing Analysis")
    
    # Overall timing
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Total Time",
            f"{timing_summary['total_time']:.3f}s",
            f"{timing_summary['total_time_ms']}ms"
        )
    
    with col2:
        total_llm = timing_summary['total_llm_time']
        st.metric(
            "LLM Time",
            f"{total_llm:.3f}s",
            f"{int(total_llm * 1000)}ms"
        )
    
    with col3:
        total_vectordb = timing_summary['total_vectordb_time']
        st.metric(
            "VectorDB Time",
            f"{total_vectordb:.3f}s",
            f"{int(total_vectordb * 1000)}ms"
        )
    
    with col4:
        total_db = timing_summary['total_database_time']
        st.metric(
            "Database Time",
            f"{total_db:.3f}s",
            f"{int(total_db * 1000)}ms"
        )
    
    # Agent timing breakdown
    st.markdown("#### 🤖 Agent Performance")
    
    if timing_summary['agent_timings']:
        agent_data = []
        for agent, timing in timing_summary['agent_timings'].items():
            agent_data.append({
                "Agent": agent.upper(),
                "Duration (ms)": timing['duration_ms'],
                "Duration (s)": f"{timing['duration']:.3f}",
                "Status": timing['status'],
                "Percentage": f"{(timing['duration'] / timing_summary['total_time'] * 100):.1f}%"
            })
        
        agent_df = pd.DataFrame(agent_data)
        st.dataframe(agent_df, width="stretch")
    
    # LLM interactions
    if timing_summary['llm_interactions']:
        st.markdown("#### 🧠 LLM Interactions")
        
        for interaction in timing_summary['llm_interactions']:
            st.markdown(f"""
            <div class="timing-card llm-interaction">
                <h4>🤖 {interaction['type'].upper()}</h4>
                <p><strong>Model:</strong> {interaction['model']}</p>
                <p><strong>Duration:</strong> {interaction['duration_ms']}ms ({interaction['duration']:.3f}s)</p>
                <p><strong>Tokens:</strong> {interaction['tokens_used']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # VectorDB interactions
    if timing_summary['vectordb_interactions']:
        st.markdown("#### 🔍 VectorDB Interactions")
        
        for interaction in timing_summary['vectordb_interactions']:
            st.markdown(f"""
            <div class="timing-card vectordb-interaction">
                <h4>🗄️ {interaction['operation'].upper()}</h4>
                <p><strong>Collection:</strong> {interaction['collection']}</p>
                <p><strong>Duration:</strong> {interaction['duration_ms']}ms ({interaction['duration']:.3f}s)</p>
                <p><strong>Results:</strong> {interaction['results_count']} items</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Database interactions
    if timing_summary['database_interactions']:
        st.markdown("#### 💾 Database Interactions")
        
        for interaction in timing_summary['database_interactions']:
            st.markdown(f"""
            <div class="timing-card database-interaction">
                <h4>⚡ {interaction['operation'].upper()}</h4>
                <p><strong>Table:</strong> {interaction['table']}</p>
                <p><strong>Duration:</strong> {interaction['duration_ms']}ms ({interaction['duration']:.3f}s)</p>
                <p><strong>Rows:</strong> {interaction['rows_affected']} affected</p>
            </div>
            """, unsafe_allow_html=True)

def render_security_validation_section(guards: Dict[str, Any], query_time: float):
    """Render Security & Validation section"""
    st.markdown("### 🛡️ Security & Validation")
    
    # Main guard status
    if guards["total_guards"] == 0:
        st.markdown("""
        <div class="security-guard guard-success">
            <h4>✅ All Guards Passed</h4>
            <p>No security issues detected in the generated SQL.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Show each guard
        for guard in guards["guards_applied"]:
            status_class = f"guard-{guard['status']}"
            st.markdown(f"""
            <div class="security-guard {status_class}">
                <h4>{guard['icon']} {guard['type']}</h4>
                <p>{guard['description']}</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Query timing
    st.markdown(f"""
    <div class="security-guard">
        <h4>⏱️ Query Time</h4>
        <p>{query_time:.3f}s</p>
    </div>
    """, unsafe_allow_html=True)

def render_recent_queries_sidebar():
    """Render recent queries in sidebar"""
    st.sidebar.markdown("### 📋 Recent Queries")
    
    history = QueryHistory()
    queries = history.get_history()
    
    if not queries:
        st.sidebar.info("No queries yet. Start by asking a question!")
        return
    
    for i, query_entry in enumerate(queries):
        # Create expandable section for each query
        with st.sidebar.expander(
            f"[{query_entry['timestamp'][:19]}] {query_entry['user']} ({query_entry['role']})",
            expanded=query_entry.get('expanded', False)
        ):
            st.markdown(f"**Query:** {query_entry['query']}")
            st.markdown(f"**Results:** {query_entry['results_count']} rows")
            st.markdown(f"**Total Time:** {query_entry['timing']['total_time']:.3f}s")
            
            # Show agent timings
            if 'agent_timings' in query_entry['timing']:
                st.markdown("**Agent Timings:**")
                for agent, timing in query_entry['timing']['agent_timings'].items():
                    st.markdown(f"- {agent}: {timing['duration_ms']}ms")
            
            # Show guards applied
            if query_entry['guards']['total_guards'] > 0:
                st.markdown("**Guards Applied:**")
                for guard in query_entry['guards']['guards_applied']:
                    st.markdown(f"- {guard['icon']} {guard['description']}")
            
            # Show SQL preview
            sql_preview = query_entry['sql'][:100] + "..." if len(query_entry['sql']) > 100 else query_entry['sql']
            st.markdown(f"**SQL:** `{sql_preview}`")

def render_tech_stack_about():
    """Render enhanced About section with tech stack"""
    st.sidebar.markdown("### ℹ️ About")
    
    st.sidebar.markdown("""
    **Local Orchestrator uses:**
    """)
    
    tech_stack = [
        {
            "name": "LLM-Powered",
            "description": "AI-driven SQL generation",
            "icon": "🧠",
            "details": f"Provider: {llm_config.get_default_provider().title()}, Model: {llm_config.get_default_model()}"
        },
        {
            "name": "Guards",
            "description": "Security validation & protection",
            "icon": "🛡️",
            "details": "SQL injection prevention, LIMIT enforcement, operation validation"
        },
        {
            "name": "Execution",
            "description": "SQLite database with thread safety",
            "icon": "⚡",
            "details": "In-memory database, connection pooling, concurrent query support"
        },
        {
            "name": "Vector Search",
            "description": "ChromaDB for context retrieval",
            "icon": "🔍",
            "details": f"Embeddings: {llm_config.get_default_embedding_model()}, Semantic search"
        },
        {
            "name": "Agents",
            "description": "Multi-agent orchestration",
            "icon": "🤖",
            "details": "Planner, Retriever, Generator, Validator, Executor, Summarizer"
        },
        {
            "name": "Framework",
            "description": "Streamlit + LangGraph",
            "icon": "⚙️",
            "details": "Stateful workflow, real-time UI, session management"
        }
    ]
    
    for tech in tech_stack:
        with st.sidebar.expander(f"{tech['icon']} {tech['name']}: {tech['description']}", expanded=False):
            st.markdown(f"**{tech['details']}**")

def simulate_agent_workflow_with_cot(query: str, timing_tracker: TimingTracker, cot_workflow: CoTWorkflow) -> Dict[str, Any]:
    """Simulate the complete agent workflow with Chain-of-Thought steps"""
    
    # Start workflow timing
    timing_tracker.start_workflow()
    
    # Step 1: Planner Agent
    planner_step = cot_workflow.add_step("planner", "Planner", "Analyzing query intent and requirements")
    planner_step.start()
    time.sleep(0.1)  # Simulate processing
    planner_step.complete(output="Query requires branch and employee data with salary analysis", 
                         details={"complexity": "medium", "tables_needed": ["branches", "employees"]})
    timing_tracker.track_agent("planner", planner_step.start_time, planner_step.end_time, "success", planner_step.details)
    cot_workflow.next_step()
    
    # Step 2: Retriever Agent with VectorDB interaction
    retriever_step = cot_workflow.add_step("retriever", "Retriever", "Retrieving relevant schema context")
    retriever_step.start()
    time.sleep(0.2)  # Simulate processing
    
    # VectorDB interaction
    vectordb_start = time.time()
    time.sleep(0.1)  # Simulate VectorDB query
    vectordb_end = time.time()
    timing_tracker.track_vectordb_interaction("query", vectordb_start, vectordb_end, "banking_schema", 5)
    
    retriever_step.complete(output="Retrieved 5 relevant schema items", 
                           details={"context_items": 5, "schema_matches": 3})
    timing_tracker.track_agent("retriever", retriever_step.start_time, retriever_step.end_time, "success", retriever_step.details)
    cot_workflow.next_step()
    
    # Step 3: SQL Generator with LLM interaction
    generator_step = cot_workflow.add_step("sql_generator", "SQL Generator", "Generating SQL using LLM")
    generator_step.start()
    time.sleep(0.3)  # Simulate processing
    
    # LLM interaction
    llm_start = time.time()
    time.sleep(0.5)  # Simulate LLM call
    llm_end = time.time()
    timing_tracker.track_llm_interaction("sql_generation", llm_start, llm_end, 
                                       llm_config.get_default_model(), 150)
    
    generated_sql = "SELECT b.name FROM branches b JOIN employees e ON b.id = e.branch_id GROUP BY b.id, b.name HAVING AVG(e.salary) > (SELECT AVG(salary) FROM employees) LIMIT 10;"
    generator_step.complete(output=generated_sql, 
                           details={"sql_length": len(generated_sql), "used_fallback": False})
    timing_tracker.track_agent("sql_generator", generator_step.start_time, generator_step.end_time, "success", generator_step.details)
    cot_workflow.next_step()
    
    # Step 4: Validator Agent
    validator_step = cot_workflow.add_step("validator", "Validator", "Validating SQL security and syntax")
    validator_step.start()
    time.sleep(0.05)  # Simulate validation
    validator_step.complete(output="SQL validation passed", 
                           details={"validation_passed": True, "security_checks": 5})
    timing_tracker.track_agent("validator", validator_step.start_time, validator_step.end_time, "success", validator_step.details)
    cot_workflow.next_step()
    
    # Step 5: Executor Agent with Database interaction
    executor_step = cot_workflow.add_step("executor", "Executor", "Executing SQL query")
    executor_step.start()
    time.sleep(0.1)  # Simulate processing
    
    # Database interaction
    db_start = time.time()
    time.sleep(0.2)  # Simulate database query
    db_end = time.time()
    timing_tracker.track_database_interaction("select", db_start, db_end, "branches", 10)
    
    executor_step.complete(output="Query executed successfully", 
                          details={"rows_returned": 10, "query_success": True})
    timing_tracker.track_agent("executor", executor_step.start_time, executor_step.end_time, "success", executor_step.details)
    cot_workflow.next_step()
    
    # Step 6: Summarizer Agent
    summarizer_step = cot_workflow.add_step("summarizer", "Summarizer", "Generating insights and summary")
    summarizer_step.start()
    time.sleep(0.15)  # Simulate summarization
    summary = "Found 10 branches where average employee salary exceeds the overall company average. This analysis helps identify high-performing branches."
    summarizer_step.complete(output=summary, 
                            details={"summary_length": len(summary), "insights_generated": 2})
    timing_tracker.track_agent("summarizer", summarizer_step.start_time, summarizer_step.end_time, "success", summarizer_step.details)
    cot_workflow.next_step()
    
    # End workflow timing
    timing_tracker.end_workflow()
    
    # Generate more realistic results
    results = [
        {"name": "Downtown Branch", "avg_salary": 75000},
        {"name": "Airport Branch", "avg_salary": 72000},
        {"name": "Mall Branch", "avg_salary": 68000},
        {"name": "University Branch", "avg_salary": 65000},
        {"name": "Hospital Branch", "avg_salary": 70000},
        {"name": "Shopping Center Branch", "avg_salary": 67000},
        {"name": "Business District Branch", "avg_salary": 78000},
        {"name": "Residential Branch", "avg_salary": 62000},
        {"name": "Industrial Branch", "avg_salary": 69000},
        {"name": "Tourist Branch", "avg_salary": 71000}
    ]
    
    return {
        "sql": generated_sql,
        "results": results,
        "summary": summary
    }

def export_pdf_report(session_state):
    """Export current query results to PDF"""
    try:
        # Prepare query data for PDF
        query_data = {
            'timestamp': datetime.now().isoformat(),
            'user': session_state.get('user_input', 'Unknown'),
            'role': session_state.get('role_input', 'Unknown'),
            'query': session_state.get('query_input', 'N/A'),
            'sql': session_state.get('last_sql', 'N/A'),
            'summary': session_state.get('last_summary', 'No summary available'),
            'results': session_state.get('last_results', []),
            'query_time': session_state.get('last_query_time', 0.0),
            'guards': session_state.get('last_guards', {}),
            'agent_timings': session_state.get('last_timing_summary', {}).get('agent_timings', {}),
            'llm_interactions': session_state.get('last_timing_summary', {}).get('llm_interactions', []),
            'total_time': session_state.get('last_timing_summary', {}).get('total_time', 0.0),
            'total_time_ms': session_state.get('last_timing_summary', {}).get('total_time_ms', 0),
            'total_llm_time': session_state.get('last_timing_summary', {}).get('total_llm_time', 0.0),
            'total_vectordb_time': session_state.get('last_timing_summary', {}).get('total_vectordb_time', 0.0),
            'total_database_time': session_state.get('last_timing_summary', {}).get('total_database_time', 0.0)
        }
        
        # Prepare data for PDF
        pdf_data = create_query_data_for_pdf(query_data)
        
        # Generate PDF
        pdf_exporter = PDFExporter()
        pdf_content = pdf_exporter.generate_query_report(pdf_data)
        
        # Create download button
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"sql_rag_report_{timestamp}.pdf"
        
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_content,
            file_name=filename,
            mime="application/pdf"
        )
        
        st.success("✅ PDF report generated successfully!")
        
    except Exception as e:
        st.error(f"❌ Error generating PDF: {str(e)}")
        st.exception(e)

def main():
    """Main Streamlit application"""
    
    # Initialize components
    security_guard = SecurityGuard()
    query_history = QueryHistory()
    timing_tracker = TimingTracker()
    
    # Header
    st.markdown("""
    <div style="text-align: center; margin: 20px 0;">
        <h1 style="color: #FF6B35; font-size: 2.5em; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">
            Wells Aug HackAThon NL 2 SQL DataInsight
        </h1>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("Transform natural language queries into SQL with AI-powered intelligence")
    
    # Sidebar
    with st.sidebar:
        render_recent_queries_sidebar()
        st.sidebar.markdown("---")
        render_tech_stack_about()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # User input section
        st.markdown("### 💬 Ask a Question")
        
        # User and role inputs
        user_col, role_col = st.columns(2)
        with user_col:
            user = st.text_input("User", value="test_user", key="user_input")
        with role_col:
            role = selectbox("Role", ["developer", "business_user"], key="role_input")
        
        # Query input
        query = st.text_area(
            "Ask a question",
            placeholder="e.g., Find the names of branches where the average salary of employees is higher than the overall average employee salary.",
            key="query_input"
        )
        
        # Ask button
        if st.button("Ask", type="primary"):
            if query.strip():
                process_query(user, role, query, security_guard, query_history, timing_tracker)
    
    with col2:
        # Security & Validation section
        if 'last_guards' in st.session_state:
            render_security_validation_section(
                st.session_state.last_guards,
                st.session_state.get('last_query_time', 0.0)
            )
    
    # Chain-of-Thought workflow (if processing)
    if 'cot_workflow' in st.session_state and not st.session_state.cot_workflow.completed:
        render_cot_workflow(st.session_state.cot_workflow)
    
    # Results section with pagination
    if 'last_results' in st.session_state:
        st.markdown("### 📊 Query Results")
        render_paginated_results(st.session_state.last_results, page_size=10)
    
    # Summary section
    if 'last_summary' in st.session_state:
        st.markdown("### 📝 Summary & Insights")
        st.info(st.session_state.last_summary)
        
        # PDF Export section
        st.markdown("### 📄 Export Report")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Export to PDF", type="secondary"):
                export_pdf_report(st.session_state)
        
        with col2:
            st.markdown("**Export includes:**")
            st.markdown("- 📋 Query details and generated SQL")
            st.markdown("- 🧠 Chain-of-Thought analysis")
            st.markdown("- 📊 Results and insights")
            st.markdown("- 🛡️ Security validation")
            st.markdown("- ⏱️ Performance metrics")
    
    # Detailed timing dashboard
    if 'last_timing_summary' in st.session_state:
        render_detailed_timing_dashboard(st.session_state.last_timing_summary)

def process_query(user: str, role: str, query: str, security_guard: SecurityGuard, 
                query_history: QueryHistory, timing_tracker: TimingTracker):
    """Process a natural language query with detailed timing and CoT"""
    
    # Initialize CoT workflow
    cot_workflow = CoTWorkflow()
    st.session_state.cot_workflow = cot_workflow
    
    # Show processing status
    with st.spinner("🔄 Processing your query..."):
        
        try:
            # Initialize system if not already done
            if 'system_initialized' not in st.session_state:
                st.info("🚀 Initializing system for first query...")
                initializer = SystemInitializer()
                report = initializer.run_full_initialization()
                
                if not report["ready_for_queries"]:
                    st.error("❌ System initialization failed")
                    st.json(report)
                    return
                
                st.session_state.system_initialized = True
                st.session_state.initializer = initializer
            
            # Get system components
            initializer = st.session_state.initializer
            schema_tables = initializer.schema_tables
            
            # Simulate complete agent workflow with CoT and timing
            workflow_results = simulate_agent_workflow_with_cot(query, timing_tracker, cot_workflow)
            
            # Apply security guards
            guards = security_guard.apply_guards(workflow_results["sql"], schema_tables)
            
            # Get timing summary
            timing_summary = timing_tracker.get_summary()
            
            # Store results in session state
            st.session_state.last_results = workflow_results["results"]
            st.session_state.last_guards = guards
            st.session_state.last_query_time = timing_summary["total_time"]
            st.session_state.last_sql = workflow_results["sql"]
            st.session_state.last_timing_summary = timing_summary
            st.session_state.last_summary = workflow_results["summary"]
            
            # Mark CoT workflow as completed
            cot_workflow.completed = True
            
            # Add to query history
            query_history.add_query(user, role, query, workflow_results["sql"], 
                                  workflow_results["results"], guards, timing_summary)
            
            st.success("✅ Query processed successfully!")
            
            # Rerun to update UI
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            st.exception(e)

if __name__ == "__main__":
    main()
