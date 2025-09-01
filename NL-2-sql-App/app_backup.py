#!/usr/bin/env python3
"""
SQL RAG Agent - Main Application
Natural Language to SQL with RAG (Retrieval-Augmented Generation)
"""

import streamlit as st
import os
import sys
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add backend to path
sys.path.append('./backend')

from backend.system_initializer import run_system_initialization
from backend.pdf_exporter import PDFExporter
from backend.pipeline import NL2SQLPipeline, PipelineConfig
from backend.planner import PlannerAgent
from backend.retriever import RetrieverAgent
from backend.llm_sql_generator import LLMSQLGenerator
from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent
from backend.db_manager import get_db_manager
from backend.llm_config import llm_config
from backend.integration_test_runner import get_integration_test_results
from backend.query_history import QueryHistory
from backend.timing_tracker import TimingTracker
from backend.security_guard import SecurityGuard
from backend.ui_debugger import render_agent_flow_debugger, render_sql_details, render_planner_details, render_executor_details

# Page configuration
st.set_page_config(
    page_title="SQL RAG Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Updated CSS for bright cream/white theme
st.markdown("""
<style>
    /* Bright cream/white background - target all Streamlit elements */
    .main {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #000000 !important;  /* Black text */
    }
    
    /* Target Streamlit app container */
    .stApp {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #000000 !important;
    }
    
    /* Target Streamlit main content area */
    .main .block-container {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #000000 !important;
        padding-top: 1rem !important;
    }
    
    /* Target Streamlit sidebar */
    .css-1d391kg, .css-1lcbmhc {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
    
    /* Target all Streamlit text elements */
    .stMarkdown, .stText, .stWrite {
        color: #000000 !important;
    }
    
    /* Target Streamlit form labels for better visibility */
    .stTextArea label, .stTextInput label, .stSelectbox label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    /* Make tab names visible with dark lettering */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-bottom: 2px solid #d4d1cc !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f7f4 !important;
        color: #000000 !important;
        border: 1px solid #d4d1cc !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0 0 !important;
        margin-right: 4px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e8e6e3 !important;
        color: #000000 !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #000000 !important;
        border-bottom: 2px solid #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Input boxes with subtle styling */
    .stTextArea textarea, .stTextInput input {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #d4d4d4 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border-radius: 6px !important;
        caret-color: #000000 !important;  /* Make cursor visible */
        padding: 12px !important;
        font-size: 16px !important;
    }
    
    /* Focus state for input boxes */
    .stTextArea textarea:focus, .stTextInput input:focus {
        background-color: #ffffff !important;
        border-color: #4CAF50 !important;
        box-shadow: 0 4px 8px rgba(76, 175, 80, 0.15) !important;
        outline: none !important;
        caret-color: #000000 !important;  /* Ensure cursor is visible on focus */
    }
    
    /* Select box styling with white text for dropdown options */
    .stSelectbox select {
        background-color: #ffffff !important;
        color: #000000 !important;
        border: 2px solid #d4d4d4 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
        border-radius: 6px !important;
    }
    
    /* Dropdown options - white text on dark background */
    .stSelectbox select option {
        background-color: #2c3e50 !important;
        color: #ffffff !important;
        padding: 8px !important;
    }
    
    /* Dropdown options on hover */
    .stSelectbox select option:hover {
        background-color: #34495e !important;
        color: #ffffff !important;
    }
    
    /* Dropdown options when selected */
    .stSelectbox select option:checked {
        background-color: #3498db !important;
        color: #ffffff !important;
    }
    
    /* Dropdown list container */
    .stSelectbox [data-baseweb="select"] {
        background-color: #2c3e50 !important;
    }
    
    /* Dropdown list items */
    .stSelectbox [data-baseweb="select"] [role="option"] {
        background-color: #2c3e50 !important;
        color: #ffffff !important;
        padding: 8px 12px !important;
    }
    
    /* Dropdown list items on hover */
    .stSelectbox [data-baseweb="select"] [role="option"]:hover {
        background-color: #34495e !important;
        color: #ffffff !important;
    }
    
    /* Dropdown list items when selected */
    .stSelectbox [data-baseweb="select"] [role="option"][aria-selected="true"] {
        background-color: #3498db !important;
        color: #ffffff !important;
    }
    
    /* Dropdown popup container */
    .stSelectbox [data-baseweb="popup"] {
        background-color: #2c3e50 !important;
        border: 1px solid #34495e !important;
        border-radius: 6px !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }
    
    /* Streamlit metrics styling - white text */
    .stMetric {
        color: #ffffff !important;
    }
    
    .stMetric [data-testid="metric-container"] {
        color: #ffffff !important;
    }
    
    .stMetric [data-testid="metric-container"] label {
        color: #ffffff !important;
    }
    
    .stMetric [data-testid="metric-container"] div {
        color: #ffffff !important;
    }
    
    /* Streamlit metric labels and values */
    .stMetric [data-testid="metric-container"] [data-testid="metric-label"] {
        color: #ffffff !important;
    }
    
    .stMetric [data-testid="metric-container"] [data-testid="metric-value"] {
        color: #ffffff !important;
    }
    
    .stMetric [data-testid="metric-container"] [data-testid="metric-delta"] {
        color: #ffffff !important;
    }
    
    /* Selectbox label styling - white text */
    .stSelectbox label {
        color: #ffffff !important;
    }
    
    .stSelectbox [data-testid="stSelectbox"] label {
        color: #ffffff !important;
    }
    
    /* Enhanced selectbox styling for role selection dropdown options */
    .stSelectbox [data-baseweb="select"] [data-testid="stSelectbox"] {
        background-color: #2c3e50 !important;
    }
    
    /* Force white text for all selectbox dropdown options */
    .stSelectbox [data-baseweb="select"] [role="option"] {
        color: #ffffff !important;
        background-color: #2c3e50 !important;
    }
    
    .stSelectbox [data-baseweb="select"] [role="option"]:hover {
        background-color: #34495e !important;
        color: #ffffff !important;
    }
    
    .stSelectbox [data-baseweb="select"] [role="option"][aria-selected="true"] {
        background-color: #3498db !important;
        color: #ffffff !important;
    }
    
    /* Override any conflicting styles for dropdown options */
    .stSelectbox [data-baseweb="select"] [role="option"],
    .stSelectbox [data-baseweb="select"] [role="option"]:hover,
    .stSelectbox [data-baseweb="select"] [role="option"][aria-selected="true"] {
        color: #ffffff !important;
    }
    
    /* Specific styling for role selector dropdown */
    [data-testid="stSelectbox"] [role="option"] {
        background-color: #2c3e50 !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSelectbox"] [role="option"]:hover {
        background-color: #34495e !important;
        color: #ffffff !important;
    }
    
    [data-testid="stSelectbox"] [role="option"][aria-selected="true"] {
        background-color: #3498db !important;
        color: #ffffff !important;
    }
    
    /* Streamlit info, warning, success messages - ensure good visibility */
    .stAlert {
        color: #ffffff !important;
    }
    
    .stAlert [data-testid="stAlert"] {
        color: #ffffff !important;
    }
    
    /* Info messages */
    .stAlert [data-testid="stAlert"] [data-testid="stAlertContent"] {
        color: #ffffff !important;
    }
    
    /* Warning messages */
    .stAlert [data-testid="stAlert"] [data-testid="stAlertContent"] {
        color: #ffffff !important;
    }
    
    /* Success messages */
    .stAlert [data-testid="stAlert"] [data-testid="stAlertContent"] {
        color: #ffffff !important;
    }
    
    /* Tech stack and integration test results - white text */
    .stMarkdown {
        color: #ffffff !important;
    }
    
    .stMarkdown p {
        color: #ffffff !important;
    }
    
    .stMarkdown strong {
        color: #ffffff !important;
    }
    
    /* Process query button - narrower width */
    .stButton > button {
        background-color: #f8f9fa !important;  /* Whitish background */
        color: #000000 !important;  /* Black text */
        border: 2px solid #d4d1cc !important;  /* Light border */
        border-radius: 8px !important;
        padding: 12px 20px !important;
        font-size: 16px !important;
        font-weight: 600 !important;  /* Slightly less bold */
        transition: all 0.3s ease !important;
        width: 150px !important;  /* Narrower width */
        margin: 0 auto !important;
        display: block !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;  /* Subtle shadow */
    }
    
    .stButton > button:hover {
        background-color: #e8e6e3 !important;  /* Slightly darker on hover */
        color: #000000 !important;  /* Black text */
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    
    .stButton > button:active {
        background-color: #2c3e50 !important;  /* Dark background when clicked */
        color: #ffffff !important;  /* White text when clicked */
        transform: translateY(0) !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2) !important;
    }
    
    /* Card styling for bright theme */
    .security-guard, .recent-query, .tech-stack, .timing-card, .cot-step, .init-status {
        background-color: #ffffff !important;
        border: 1px solid #e0e0e0 !important;
        border-radius: 8px !important;
        padding: 12px !important;
        margin: 8px 0 !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05) !important;
    }
    
    /* Hover effects for cards */
    .recent-query:hover, .tech-stack:hover, .timing-card:hover {
        background-color: #f8f9fa !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1) !important;
    }
    
    /* Status colors for bright theme */
    .status-icon.passed { color: #27ae60; }
    .status-icon.failed { color: #e74c3c; }
    .status-icon.error { color: #f39c12; }
    .status-icon.pending { color: #95a5a6; }
    .status-icon.running { color: #3498db; }
    
    /* Security guard status colors */
    .security-guard.passed {
        border-left: 4px solid #27ae60 !important;
    }
    
    .security-guard.failed {
        border-left: 4px solid #e74c3c !important;
    }
    
    .security-guard.warning {
        border-left: 4px solid #f39c12 !important;
    }
    
    /* Developer View text styling - darker and bold */
    .developer-view-info {
        color: #000000 !important;  /* Black color */
        font-weight: bold !important;
        font-size: 18px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Business View text styling */
    .business-view-info {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    /* Dark text for info messages on light background */
    .info-message-dark {
        color: #000000 !important;  /* Black color for better visibility */
        font-weight: 600 !important;
        font-size: 16px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Dark text for test results and metrics */
    .test-results-dark {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Dark text for section headers */
    .section-header-dark {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 18px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Dark text for form labels */
    .form-label-dark {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Target Streamlit form labels specifically */
    .stTextArea label, .stTextInput label, .stSelectbox label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Dark text for sidebar elements */
    .sidebar .stMarkdown, .sidebar .stText, .sidebar .stWrite {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Dark text for sidebar headers */
    .sidebar h3, .sidebar h4, .sidebar h5 {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 16px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    /* Security Guard Results - black text for quoted content */
    .security-guard-sql {
        color: #000000 !important;
        font-weight: 600 !important;
        font-family: 'Courier New', monospace !important;
        background-color: #f8f9fa !important;
        padding: 8px 12px !important;
        border-radius: 4px !important;
        border: 1px solid #dee2e6 !important;
        margin: 4px 0 !important;
    }
    
    .security-guard-details {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    .security-guard-message {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background-color: #f8f9fa !important;
        padding: 6px 10px !important;
        border-radius: 4px !important;
        border-left: 3px solid #28a745 !important;
    }
    
    /* Query Processing Results - dark text */
    .query-result-item {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        margin: 4px 0 !important;
    }
    
    .query-result-sql {
        color: #000000 !important;
        font-weight: 600 !important;
        font-family: 'Courier New', monospace !important;
        background-color: #f8f9fa !important;
        padding: 6px 10px !important;
        border-radius: 4px !important;
        border: 1px solid #dee2e6 !important;
        margin: 4px 0 !important;
    }
    
    .query-result-time {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Streamlit write and text elements - ensure dark text */
    .stMarkdown p, .stText, .stWrite {
        color: #000000 !important;
    }
    
    /* Force dark text for all query-related content */
    div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
    }
    
    /* Dark text for sidebar expanders and query entries */
    .sidebar .streamlit-expanderHeader, .sidebar .streamlit-expanderContent {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Dark text for sidebar info messages */
    .sidebar .stAlert {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
    }
    
    /* Streamlit alert components - ensure black text */
    .stAlert {
        color: #000000 !important;
        background-color: #ffffff !important;
        border: 1px solid #d4d1cc !important;
    }
    
    /* Info messages */
    .stAlert[data-baseweb="notification"] {
        color: #000000 !important;
        background-color: #f0f8ff !important;
        border-color: #3498db !important;
    }
    
    /* Success messages */
    .stAlert[data-baseweb="notification"].success {
        color: #000000 !important;
        background-color: #f0f9ff !important;
        border-color: #27ae60 !important;
    }
    
    /* Error messages */
    .stAlert[data-baseweb="notification"].error {
        color: #000000 !important;
        background-color: #fef2f2 !important;
        border-color: #e74c3c !important;
    }
    
    /* Warning messages */
    .stAlert[data-baseweb="notification"].warning {
        color: #000000 !important;
        background-color: #fff7ed !important;
        border-color: #f39c12 !important;
    }
    
    /* Progress bar text */
    .stProgress > div > div > div > div {
        color: #000000 !important;
    }
    
    /* All Streamlit text elements with black color */
    .stMarkdown, .stText, .stWrite, .stAlert, .stProgress {
        color: #000000 !important;
    }
    
    /* Specific styling for progress messages */
    .stProgress + div {
        color: #000000 !important;
    }
    
    /* Ensure all text in containers is black */
    .stContainer, .stExpander, .stColumns {
        color: #000000 !important;
    }
    
    /* Target all text elements within the app */
    .stApp * {
        color: #000000 !important;
    }
    
    /* Specific styling for Streamlit progress and status messages */
    .stProgress {
        color: #000000 !important;
    }
    
    .stProgress > div {
        color: #000000 !important;
    }
    
    /* Streamlit status messages */
    .stAlert, .stAlert > div {
        color: #000000 !important;
    }
    
    /* Override Streamlit's default white text in alerts */
    .stAlert[data-baseweb="notification"] {
        color: #000000 !important;
    }
    
    .stAlert[data-baseweb="notification"] * {
        color: #000000 !important;
    }
    
    /* Ensure all text in the app is black */
    .stApp, .stApp * {
        color: #000000 !important;
    }
    
    /* Force black text for all elements */
    * {
        color: #000000 !important;
    }
    
    /* Target all sidebar content with dark text */
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stText,
    [data-testid="stSidebar"] .stWrite,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5 {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Dark text for sidebar expander headers */
    [data-testid="stSidebar"] .streamlit-expanderHeader {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 14px !important;
        background-color: #f8f7f4 !important;
        border: 1px solid #d4d1cc !important;
    }
    
    /* Dark text for sidebar expander content */
    [data-testid="stSidebar"] .streamlit-expanderContent {
        color: #000000 !important;
        font-weight: 500 !important;
        font-size: 13px !important;
    }
    
    /* Dark text for form labels and input labels */
    .form-label-dark {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.05) !important;
    }
    
    /* Target Streamlit text area and input labels */
    .stTextArea label, .stTextInput label, .stSelectbox label {
        color: #000000 !important;
        font-weight: 600 !important;
        font-size: 16px !important;
    }
    
    .cot-step.error {
        border-left-color: #e74c3c !important;
    }
    
    /* Pagination styling for bright theme */
    .pagination button {
        background-color: #3498db !important;
        color: white !important;
        border: none !important;
        padding: 8px 16px !important;
        border-radius: 4px !important;
        cursor: pointer !important;
    }
    
    .pagination button:disabled {
        background-color: #bdc3c7 !important;
        cursor: not-allowed !important;
    }
    
    /* Remove top margin to move elements up */
    .main .block-container {
        padding-top: 1rem !important;
    }
    
    /* Move title up more */
    .main h1 {
        margin-top: -60px !important;
    }
    
    /* Override any dark theme styles */
    [data-testid="stAppViewContainer"] {
        background-color: #faf8f3 !important;
    }
    
    [data-testid="stSidebar"] {
        background-color: #f5f5f0 !important;
    }
</style>
""", unsafe_allow_html=True)

class SecurityGuard:
    """Security validation for SQL queries"""
    
    def __init__(self):
        self.guards = {
            "LIMIT_INJECTION": False,
            "DANGEROUS_OPERATION": False,
            "INVALID_OPERATION": False,
            "TABLE_VALIDATION": False,
            "COMPLEXITY_CHECK": False
        }
    
    def apply_guards(self, sql_query: str) -> Dict[str, Any]:
        """Apply security guards to SQL query - only show when dangerous operations detected"""
        guards_applied = {}
        total_guards = 0
        
        # Check for dangerous operations (only these should trigger guards)
        dangerous_ops = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "SHUTDOWN", "KILL", "BACKUP", "RESTORE"]
        
        for op in dangerous_ops:
            if op in sql_query.upper():
                guards_applied[f"{op}_DETECTED"] = f"⚠️ Dangerous {op} operation detected"
                total_guards += 1
        
        # Check for suspicious patterns (warn but don't block)
        suspicious_patterns = [
            ("UNION", "UNION SELECT"),
            ("OR_INJECTION", "OR 1=1"),
            ("OR_TRUE", "OR TRUE"),
            ("SCRIPT_TAG", "<script"),
            ("JAVASCRIPT", "javascript:"),
            ("ONLOAD", "onload="),
            ("ONERROR", "onerror=")
        ]
        
        for pattern_name, pattern in suspicious_patterns:
            if pattern.upper() in sql_query.upper():
                guards_applied[f"{pattern_name}_DETECTED"] = f"⚠️ Suspicious {pattern_name} pattern detected"
                total_guards += 1
        
        # Only return guards if dangerous operations were detected
        if total_guards == 0:
            return {
                "sql": sql_query,
                "guards_applied": {},
                "total_guards": 0,
                "message": "No dangerous operations detected - query is safe"
            }
        else:
            return {
                "sql": sql_query,
                "guards_applied": guards_applied,
                "total_guards": total_guards,
                "message": f"⚠️ {total_guards} security guard(s) applied due to dangerous operations"
            }

class QueryHistory:
    """Manage recent queries in session state"""
    
    def __init__(self):
        # Ensure query_history is always a list in session state
        if "query_history" not in st.session_state:
            st.session_state.query_history = []
        elif not isinstance(st.session_state.query_history, list):
            # If it's not a list, reset it
            st.session_state.query_history = []
    
    def add_query(self, query: str, sql: str, results_count: int, timestamp: str):
        """Add a query to history"""
        # Ensure we're working with a list
        if not isinstance(st.session_state.query_history, list):
            st.session_state.query_history = []
        
        query_entry = {
            "query": query,
            "sql": sql,
            "results_count": results_count,
            "timestamp": timestamp
        }
        st.session_state.query_history.insert(0, query_entry)
        
        # Keep only last 10 queries
        if len(st.session_state.query_history) > 10:
            st.session_state.query_history = st.session_state.query_history[:10]
    
    def get_history(self) -> List[Dict[str, Any]]:
        """Get query history"""
        # Ensure we return a list
        if not isinstance(st.session_state.query_history, list):
            st.session_state.query_history = []
        return st.session_state.query_history

class TimingTracker:
    """Track timing information for queries"""
    
    def __init__(self):
        self.start_time = None
        self.agent_timings = {}
        self.llm_interactions = []
        self.vectordb_interactions = []
        self.database_interactions = []
    
    def start_tracking(self):
        """Start timing tracking"""
        self.start_time = time.time()
        self.agent_timings = {}
        self.llm_interactions = []
        self.vectordb_interactions = []
        self.database_interactions = []
    
    def track_agent(self, agent_name: str, duration: float):
        """Track agent timing"""
        self.agent_timings[agent_name] = duration
    
    def track_llm_interaction(self, operation: str, duration: float):
        """Track LLM interaction timing"""
        self.llm_interactions.append({
            "operation": operation,
            "duration": duration,
            "timestamp": time.time()
        })
    
    def track_vectordb_interaction(self, operation: str, duration: float):
        """Track VectorDB interaction timing"""
        self.vectordb_interactions.append({
            "operation": operation,
            "duration": duration,
            "timestamp": time.time()
        })
    
    def track_database_interaction(self, operation: str, duration: float):
        """Track database interaction timing"""
        self.database_interactions.append({
            "operation": operation,
            "duration": duration,
            "timestamp": time.time()
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get timing summary"""
        if not self.start_time:
            return {}
        
        total_time = time.time() - self.start_time
        total_llm_time = sum(interaction["duration"] for interaction in self.llm_interactions)
        total_vectordb_time = sum(interaction["duration"] for interaction in self.vectordb_interactions)
        total_database_time = sum(interaction["duration"] for interaction in self.database_interactions)
        
        return {
            "total_time": total_time,
            "total_time_ms": int(total_time * 1000),
            "agent_timings": self.agent_timings,
            "llm_interactions": self.llm_interactions,
            "vectordb_interactions": self.vectordb_interactions,
            "database_interactions": self.database_interactions,
            "total_llm_time": total_llm_time,
            "total_llm_time_ms": int(total_llm_time * 1000),
            "total_vectordb_time": total_vectordb_time,
            "total_vectordb_time_ms": int(total_vectordb_time * 1000),
            "total_database_time": total_database_time,
            "total_database_time_ms": int(total_database_time * 1000)
        }

class CoTStep:
    """Chain-of-Thought step"""
    
    def __init__(self, agent: str, action: str, details: str = "", status: str = "pending"):
        self.agent = agent
        self.action = action
        self.details = details
        self.status = status  # pending, running, completed, error
        self.timestamp = time.time()

class CoTWorkflow:
    """Manage Chain-of-Thought workflow"""
    
    def __init__(self):
        self.steps = []
        self.current_step = 0
    
    def add_step(self, agent: str, action: str, details: str = ""):
        """Add a CoT step"""
        step = CoTStep(agent, action, details)
        self.steps.append(step)
    
    def update_current_step(self, status: str, details: str = ""):
        """Update current step status"""
        if self.current_step < len(self.steps):
            self.steps[self.current_step].status = status
            if details:
                self.steps[self.current_step].details = details
            self.current_step += 1
    
    def update_step_status(self, step_index: int, status: str, details: str = ""):
        """Update specific step status by index"""
        if 0 <= step_index < len(self.steps):
            self.steps[step_index].status = status
            if details:
                self.steps[step_index].details = details
    
    def get_steps(self) -> List[CoTStep]:
        """Get all steps"""
        return self.steps

class PaginationManager:
    """Manage pagination for large result sets"""
    
    def __init__(self, results: List[Dict[str, Any]], items_per_page: int = 10):
        self.results = results
        self.items_per_page = items_per_page
        self.current_page = 0
        self.total_pages = (len(results) + items_per_page - 1) // items_per_page
    
    def get_current_page_data(self) -> List[Dict[str, Any]]:
        """Get data for current page"""
        start_idx = self.current_page * self.items_per_page
        end_idx = start_idx + self.items_per_page
        return self.results[start_idx:end_idx]
    
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

def render_security_validation_section(guards: Dict[str, Any]):
    """Render security validation section"""
    st.markdown("### 🛡️ Security & Validation")
    
    if not guards:
        st.info("No security guards applied")
        return
    
    for guard_name, guard_details in guards.get("guards_applied", {}).items():
        guard_class = "passed" if "Added" in guard_details or "Validated" in guard_details else "warning"
        st.markdown(f"""
        <div class="security-guard {guard_class}">
            <strong>{guard_name}:</strong> {guard_details}
        </div>
        """, unsafe_allow_html=True)

def render_recent_queries_sidebar():
    """Render recent queries in sidebar"""
    st.sidebar.markdown("### 📋 Recent Queries")
    
    # Get query history using QueryHistory class
    query_history = QueryHistory()
    history = query_history.get_history()
    
    if not history:
        st.sidebar.info("No recent queries")
        return
    
    for i, entry in enumerate(history):
        # Ensure entry is a dictionary with required keys
        if isinstance(entry, dict) and 'query' in entry:
            with st.sidebar.expander(f"Query {i+1}: {entry['query'][:30]}...", expanded=False):
                st.write(f"**Query:** {entry['query']}")
                st.write(f"**SQL:** `{entry.get('sql', 'N/A')}`")
                st.write(f"**Results:** {entry.get('results_count', 0)} records")
                st.write(f"**Time:** {entry.get('timestamp', 'N/A')}")
        else:
            st.sidebar.warning(f"Invalid query entry format: {type(entry)}")

def render_tech_stack_about():
    """Render tech stack information in sidebar"""
    st.sidebar.markdown("### 🛠️ Tech Stack")
    
    tech_stack = {
        "Frontend": "Streamlit",
        "Backend": "Python 3.9+",
        "Database": "SQLite (In-Memory)",
        "Vector DB": "ChromaDB",
        "LLM": "OpenAI GPT-4",
        "Embeddings": "OpenAI text-embedding-ada-002",
        "PDF Export": "ReportLab",
        "Testing": "Pytest + Custom Integration Tests"
    }
    
    for tech, description in tech_stack.items():
        st.sidebar.markdown(f'<div style="color: #000000; margin-bottom: 8px;"><span style="background-color: #f5f5dc; padding: 6px 12px; border-radius: 12px; font-weight: bold; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{tech}</span>: {description}</div>', unsafe_allow_html=True)

def render_tech_stack_with_tests():
    """Render tech stack with integration test results for Developer view"""
    st.markdown("#### 🛠️ Technology Stack & Integration Tests")
    
    # Run integration tests if not already cached
    if 'integration_test_results' not in st.session_state:
        with st.spinner("🧪 Running integration tests..."):
            st.session_state.integration_test_results = get_integration_test_results()
    
    test_results = st.session_state.integration_test_results
    
    # Tech Stack Overview
    st.markdown("##### 📋 Technology Stack")
    tech_stack = {
        "Frontend": "Streamlit",
        "Backend": "Python 3.9+",
        "Database": "SQLite (In-Memory)",
        "Vector DB": "ChromaDB",
        "LLM": "OpenAI GPT-4",
        "Embeddings": "OpenAI text-embedding-ada-002",
        "PDF Export": "ReportLab",
        "Testing": "Pytest + Custom Integration Tests"
    }
    
    for tech, description in tech_stack.items():
        st.markdown(f'<div style="color: #000000; margin-bottom: 8px;"><span style="background-color: #f5f5dc; padding: 6px 12px; border-radius: 12px; font-weight: bold; border: 1px solid #e0e0e0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">{tech}</span>: {description}</div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Integration Test Results
    st.markdown("##### 🧪 Integration Test Results")
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Tests", len(test_results['tests']))
    with col2:
        st.metric("Passed", test_results['passed_count'], delta=f"+{test_results['passed_count']}")
    with col3:
        st.metric("Failed", test_results['failed_count'], delta=f"-{test_results['failed_count']}")
    with col4:
        st.metric("Duration", f"{test_results['total_duration']:.2f}s")
    
    # Individual test results
    st.markdown("##### 📊 Test Details")
    
    for test_name, result in test_results['tests'].items():
        # Status icon and color
        if result['status'] == 'passed':
            status_icon = "✅"
            status_color = "#00FF00"
            border_color = "#00FF00"
        else:
            status_icon = "❌"
            status_color = "#FF0000"
            border_color = "#FF0000"
        
        # Test result card
        st.markdown(f"""
        <div style="
            border: 2px solid {border_color};
            border-radius: 8px;
            padding: 12px;
            margin: 8px 0;
            background-color: #1e1e1e;
            color: #ffffff;
        ">
            <div style="display: flex; align-items: center; margin-bottom: 8px;">
                <span style="font-size: 1.5em; margin-right: 8px;">{status_icon}</span>
                <strong style="color: {status_color};">{result['name']}</strong>
                <span style="margin-left: auto; font-size: 0.8em; color: #ffffff;">
                    {result['duration']:.2f}s
                </span>
            </div>
            <div style="color: #ffffff; font-size: 0.9em;">
                {result['details']}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Refresh button
    if st.button("🔄 Refresh Tests", type="secondary"):
        with st.spinner("🧪 Running integration tests..."):
            st.session_state.integration_test_results = get_integration_test_results()
        st.rerun()

def render_detailed_timing_dashboard(timing_summary: Dict[str, Any]):
    """Render detailed timing dashboard"""
    st.markdown("### ⏱️ Detailed Timing Dashboard")
    
    if not timing_summary:
        st.info("No timing data available")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Time", f"{timing_summary.get('total_time', 0):.3f}s")
    
    with col2:
        st.metric("LLM Time", f"{timing_summary.get('total_llm_time', 0):.3f}s")
    
    with col3:
        st.metric("VectorDB Time", f"{timing_summary.get('total_vectordb_time', 0):.3f}s")
    
    with col4:
        st.metric("Database Time", f"{timing_summary.get('total_database_time', 0):.3f}s")
    
    # Agent timings
    if timing_summary.get("agent_timings"):
        st.markdown("#### Agent Performance")
        agent_timings = timing_summary["agent_timings"]
        
        for agent, duration in agent_timings.items():
            st.markdown(f"""
            <div class="timing-card">
                <div class="timing-metric">
                    <span><strong>{agent}:</strong></span>
                    <span>{duration:.3f}s</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

def render_cot_workflow(cot_workflow: CoTWorkflow):
    """Render Chain-of-Thought workflow"""
    st.markdown("### 🧠 Chain-of-Thought Analysis")
    
    steps = cot_workflow.get_steps()
    
    if not steps:
        st.info("No CoT steps available")
        return
    
    for i, step in enumerate(steps):
        status_icon = {
            "pending": "⏳",
            "running": "🔄",
            "completed": "✅",
            "error": "❌"
        }.get(step.status, "❓")
        
        step_class = "completed" if step.status == "completed" else "error" if step.status == "error" else ""
        
        st.markdown(f"""
        <div class="cot-step {step_class}">
            <strong>{status_icon} {step.agent}:</strong> {step.action}
            {f'<br><em>{step.details}</em>' if step.details else ''}
        </div>
        """, unsafe_allow_html=True)

def render_paginated_results(results: List[Dict[str, Any]], pagination_manager: PaginationManager):
    """Render paginated results"""
    st.markdown("### 📊 Query Results")
    
    if not results:
        st.info("No results to display")
        return
    
    # Show current page data
    current_data = pagination_manager.get_current_page_data()
    
    if current_data:
        st.dataframe(current_data, width='stretch')
    
    # Pagination controls
    if pagination_manager.total_pages > 1:
        st.markdown("#### Pagination")
        
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        with col1:
            if st.button("⬅️ Previous", disabled=pagination_manager.current_page == 0):
                pagination_manager.prev_page()
                st.rerun()
        
        with col2:
            st.write(f"Page {pagination_manager.current_page + 1} of {pagination_manager.total_pages}")
        
        with col3:
            page_input = st.number_input("Go to page:", min_value=1, max_value=pagination_manager.total_pages, value=pagination_manager.current_page + 1)
            if st.button("Go"):
                pagination_manager.go_to_page(page_input - 1)
                st.rerun()
        
        with col4:
            if st.button("Next ➡️", disabled=pagination_manager.current_page == pagination_manager.total_pages - 1):
                pagination_manager.next_page()
                st.rerun()

def render_initialization_status(init_report: Dict[str, Any]):
    """Render initialization status"""
    st.markdown("### 🚀 System Initialization Status")
    
    if not init_report:
        st.info("No initialization data available")
        return
    
    # Overall status
    overall_status = init_report.get("overall_status", "unknown")
    status_icon = {
        "passed": "✅",
        "failed": "❌",
        "error": "⚠️",
        "partial": "⚠️",
        "pending": "⏳"
    }.get(overall_status, "❓")
    
    st.markdown(f"**Overall Status:** {status_icon} {overall_status.upper()}")
    
    # Component status
    components = init_report.get("components", {})
    
    for component_name, component_data in components.items():
        status = component_data.get("status", "unknown")
        message = component_data.get("message", "No message")
        duration = component_data.get("duration", 0)
        
        status_icon_class = status
        status_icon = {
            "passed": "✅",
            "failed": "❌",
            "error": "⚠️",
            "pending": "⏳",
            "running": "🔄"
        }.get(status, "❓")
        
        st.markdown(f"""
        <div class="init-component">
            <span><strong>{component_name.replace('_', ' ').title()}:</strong></span>
            <span class="status-icon {status_icon_class}">{status_icon} {message}</span>
        </div>
        """, unsafe_allow_html=True)
        
        if duration > 0:
            st.caption(f"Duration: {duration:.3f}s")
    
    # Summary
    summary = init_report.get("summary", {})
    if summary:
        st.markdown("#### Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Components", summary.get("total_components", 0))
        
        with col2:
            st.metric("Passed", summary.get("passed", 0))
        
        with col3:
            st.metric("Failed/Errors", summary.get("failed", 0) + summary.get("errors", 0))
    
    # Errors and warnings
    errors = init_report.get("errors", [])
    warnings = init_report.get("warnings", [])
    
    if errors:
        st.error("#### Errors")
        for error in errors:
            st.error(f"• {error}")
    
    if warnings:
        st.warning("#### Warnings")
        for warning in warnings:
            st.warning(f"• {warning}")

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
            'total_llm_time_ms': session_state.get('last_timing_summary', {}).get('total_llm_time_ms', 0),
            'total_vectordb_time': session_state.get('last_timing_summary', {}).get('total_vectordb_time', 0.0),
            'total_vectordb_time_ms': session_state.get('last_timing_summary', {}).get('total_vectordb_time_ms', 0),
            'total_database_time': session_state.get('last_timing_summary', {}).get('total_database_time', 0.0),
            'total_database_time_ms': session_state.get('last_timing_summary', {}).get('total_database_time_ms', 0)
        }

        # Generate PDF
        pdf_exporter = PDFExporter()
        pdf_content = pdf_exporter.generate_query_report(query_data)

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

def simulate_agent_workflow_with_cot(query: str, timing_tracker: TimingTracker, cot_workflow: CoTWorkflow, 
                                     user: Optional[str] = None, ip_address: Optional[str] = None) -> tuple:
    """Execute real agent workflow with Chain-of-Thought tracking"""
    timing_tracker.start_tracking()
    
    try:
        # Add CoT steps for real-time display
        cot_workflow.add_step("Planner", "Analyzing query intent and requirements")
        cot_workflow.add_step("Retriever", "Retrieving relevant schema context")
        cot_workflow.add_step("SQL Generator", "Generating SQL query")
        cot_workflow.add_step("Validator", "Validating SQL security and syntax")
        cot_workflow.add_step("Executor", "Executing query against database")
        cot_workflow.add_step("Summarizer", "Generating natural language summary")
        
        # Initialize agents
        db_path = os.getenv("DB_PATH", "banking.db")
        db_manager = get_db_manager(db_path)
        
        # Get schema tables from database
        schema_tables = {}
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema_tables[table] = columns
            
            db_manager.release_connection(conn)
        except Exception as e:
            st.error(f"❌ Error getting schema: {e}")
            schema_tables = {"customers": ["id", "name", "email"], "accounts": ["id", "customer_id", "type"]}
        
        # Initialize agents
        planner = PlannerAgent(schema_tables)
        retriever = RetrieverAgent()
        generator = LLMSQLGenerator()
        validator = ValidatorAgent()
        executor = ExecutorAgent(db_path, db_manager)
        summarizer = SummarizerAgent()
        
        # Configure pipeline
        config = PipelineConfig(max_retries=2, sql_row_limit=100)
        
        # Create pipeline
        pipeline = NL2SQLPipeline(
            planner=planner,
            retriever=retriever,
            generator=generator,
            validator=validator,
            executor=executor,
            summarizer=summarizer,
            schema_tables=schema_tables,
            config=config
        )
        
        # Execute pipeline with real-time CoT updates
        result = pipeline.run(query, user=user, ip_address=ip_address)
        
        # Update CoT steps based on actual execution
        steps = cot_workflow.get_steps()
        for i, step in enumerate(steps):
            if result.get("success", False):
                cot_workflow.update_step_status(i, "completed", f"Completed successfully")
            else:
                cot_workflow.update_step_status(i, "error", f"Failed: {result.get('error', 'Unknown error')}")
        
        if result.get("success", False):
            sql = result.get("sql", "")
            results = result.get("results", [])
            summary = result.get("summary", "Query executed successfully")
            
            # Extract timing information from diagnostics
            diagnostics = result.get("diagnostics", {})
            timings = diagnostics.get("timings_ms", {})
            
            # Update timing tracker with real timings
            for agent, timing_ms in timings.items():
                timing_tracker.track_agent(agent, timing_ms / 1000.0)
            
            return sql, results, summary, timing_tracker.get_summary()
        else:
            # Handle failure
            error_msg = result.get("error", "Unknown error")
            st.error(f"❌ Pipeline failed: {error_msg}")
            
            # Return fallback results
            sql = "SELECT * FROM customers LIMIT 10"
            results = [{"id": i, "name": f"Customer {i}", "email": f"customer{i}@example.com"} for i in range(1, 11)]
            summary = f"Query failed: {error_msg}. Showing sample data instead."
            
            return sql, results, summary, timing_tracker.get_summary()
            
    except Exception as e:
        st.error(f"❌ Error in workflow: {e}")
        
        # Return fallback results
        sql = "SELECT * FROM customers LIMIT 10"
        results = [{"id": i, "name": f"Customer {i}", "email": f"customer{i}@example.com"} for i in range(1, 11)]
        summary = f"Workflow error: {str(e)}. Showing sample data instead."
        
        return sql, results, summary, timing_tracker.get_summary()

def handle_query_submit(role_type):
    """Handle query submission when Enter is pressed"""
    if 'query_input' in st.session_state and st.session_state.query_input.strip():
        # Get user input based on role
        if role_type == "developer":
            user_input = st.session_state.get("user_input", "Developer")
            role_input = st.session_state.get("role_input", "Developer")
        else:
            user_input = st.session_state.get("user_input", "Business User")
            role_input = st.session_state.get("role_input", "Business User")
        
        # Process the query
        process_query(st.session_state.query_input, user_input, role_input)

def create_query_input_with_enter_support(label, placeholder, key, role_type):
    """Create a query input that processes on Enter key press"""
    
    # Add custom CSS and JavaScript for Enter key handling
    st.markdown(f"""
    <style>
    .query-input-container {{
        position: relative;
    }}
    </style>
    <script>
    // Function to handle Enter key for {key}
    function handleEnterKey_{key.replace('-', '_')}() {{
        const textarea = document.querySelector('textarea[data-testid="stTextArea"]');
        if (textarea) {{
            textarea.addEventListener('keydown', function(e) {{
                if (e.key === 'Enter' && !e.shiftKey) {{
                    e.preventDefault();
                    // Set session state to trigger processing
                    window.parent.postMessage({{
                        type: 'streamlit:setComponentValue',
                        key: '{key}_enter_pressed',
                        value: true
                    }}, '*');
                }}
            }});
        }}
    }}
    
    // Run the function
    handleEnterKey_{key.replace('-', '_')}();
    </script>
    """, unsafe_allow_html=True)
    
    # Create the text area
    query_input = st.text_area(
        label,
        placeholder=placeholder,
        height=100,
        key=key
    )
    
    # Check if Enter was pressed
    if st.session_state.get(f"{key}_enter_pressed", False):
        st.session_state[f"{key}_enter_pressed"] = False
        if query_input.strip():
            # Get user input based on role
            if role_type == "developer":
                user_input = st.session_state.get("user_input", "Developer")
                role_input = st.session_state.get("role_input", "Developer")
            else:
                user_input = st.session_state.get("user_input", "Business User")
                role_input = st.session_state.get("role_input", "Business User")
            
            # Process the query
            process_query(query_input, user_input, role_input)
            st.rerun()
    
    return query_input

def render_developer_ui(selected_role):
    """Render UI for Developer role"""
    st.markdown("### 👨‍💻 Developer View")
    
    # Tech Stack and Agent Flow tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "💬 Query", "🛠️ Tech Stack", "🤖 Agent Flow", "📊 Results", 
        "🛡️ Security", "🔍 Debug", "🤖 Agent Debug", "📄 Export"
    ])
    
    with tab1:
        st.markdown("#### 💬 Natural Language Query")
        
        # User inputs
        col1, col2 = st.columns(2)
        
        with col1:
            user_input = st.text_input("👤 Your Name:", value="John", placeholder="Enter your name", key="user_input")
        
        with col2:
            # Role is now handled in main content area
            st.markdown('<div style="color: #000000;">🎭 **Role:** Developer</div>', unsafe_allow_html=True)
            role_input = "Developer"
        
        # Query input with Enter key handling
        query_input = st.text_area(
            "🔍 Enter your question:",
            placeholder="e.g., Find all customers who have both checking and savings accounts",
            height=100,
            key="query_input_dev"
        )
        
        # Check if Enter was pressed (using session state)
        if st.session_state.get('enter_pressed', False):
            st.session_state.enter_pressed = False
            if query_input.strip():
                process_query(query_input, user_input, selected_role)
            else:
                st.warning("Please enter a query")
        
        # Process button with light color
        if st.button("🚀 Process Query", width="stretch", 
                    help="Click to process your query"):
            if query_input.strip():
                process_query(query_input, user_input, selected_role)
            else:
                st.warning("Please enter a query")
        
        # Handle Enter key press using session state - Improved detection
        if query_input and st.session_state.get('query_input_dev_previous', '') != query_input:
            st.session_state.query_input_dev_previous = query_input
            # Check if Enter was pressed (improved approach)
            if '\n' in query_input:
                # User pressed Enter, process the query
                clean_query = query_input.replace('\n', ' ').strip()
                if clean_query:
                    st.session_state.enter_pressed = True
                    st.session_state.pending_query = clean_query
                    st.rerun()
        
        # Process pending query from Enter key
        if st.session_state.get('enter_pressed', False) and st.session_state.get('pending_query'):
            query_to_process = st.session_state.pending_query
            st.session_state.enter_pressed = False
            st.session_state.pending_query = None
            process_query(query_to_process, user_input, selected_role)
    
    with tab2:
        st.markdown("#### 🛠️ Technology Stack")
        render_tech_stack_with_tests()
        
        # System Status
        if 'init_report' in st.session_state:
            st.markdown("#### 🚀 System Status")
            render_initialization_status(st.session_state.init_report)
    
    with tab3:
        st.markdown("#### 🤖 Agent-to-Agent Flow")
        
        if 'last_timing_summary' in st.session_state:
            # Agent timings
            st.markdown("##### ⏱️ Agent Performance")
            render_detailed_timing_dashboard(st.session_state.last_timing_summary)
            
            # Agent flow details
            if 'last_cot_workflow' in st.session_state:
                st.markdown("##### 🧠 Chain-of-Thought Steps")
                render_cot_workflow(st.session_state.last_cot_workflow)
        else:
            st.markdown('<div class="info-message-dark">No agent flow data available. Please run a query first.</div>', unsafe_allow_html=True)
    
    with tab4:
        st.markdown("#### 📊 Query Results")
        
        if 'last_results' in st.session_state:
            # Results count
            results_count = len(st.session_state.last_results)
            st.metric("Results", f"{results_count} records")
            
            # Pagination
            if results_count > 10:
                pagination_manager = PaginationManager(st.session_state.last_results)
                render_paginated_results(st.session_state.last_results, pagination_manager)
            else:
                st.dataframe(st.session_state.last_results, width='stretch')
        else:
            st.info("No results available. Please run a query first.")
    
    with tab5:
        st.markdown("#### 🛡️ Security Guard Results")
        
        if 'last_guards' in st.session_state:
            # Display security guard results
            guards = st.session_state.last_guards
            
            # Check if we have validation details from the pipeline
            if 'last_validation_details' in st.session_state:
                validation_details = st.session_state.last_validation_details
                security_events = st.session_state.get('last_security_events', [])
                render_security_guard_results(validation_details, security_events)
            else:
                # Fallback to basic guard information
                st.info("Security validation completed")
                if isinstance(guards, dict):
                    for key, value in guards.items():
                        if key == "sql":
                            # Style SQL with dark monospace text
                            st.markdown(f'<div class="security-guard-sql"><strong>{key}:</strong> {value}</div>', unsafe_allow_html=True)
                        elif key in ["guards_applied", "total_guards", "message"]:
                            # Style other guard details with dark text
                            st.markdown(f'<div class="security-guard-details"><strong>"{key}":</strong> {value}</div>', unsafe_allow_html=True)
                        else:
                            # Default styling for other keys
                            st.markdown(f'<div class="security-guard-details"><strong>{key}:</strong> {value}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="security-guard-details"><strong>Guards:</strong> {guards}</div>', unsafe_allow_html=True)
        else:
            st.info("No security guard data available. Please run a query first.")
    
    with tab6:
        st.markdown("#### 📄 Export Report")
        
        if 'last_results' in st.session_state:
            if st.button("📊 Export to PDF", type="secondary"):
                export_pdf_report(st.session_state)
        else:
            st.info("No data available for export. Please run a query first.")

    with tab7:
        st.markdown("#### 🔍 Agent Flow Debugger")
        
        if 'debug_report' in st.session_state:
            # Render the comprehensive debug report
            render_agent_flow_debugger(st.session_state.debug_report)
            
            # Show SQL details if available
            if 'last_sql' in st.session_state and 'last_generated_sql' in st.session_state:
                render_sql_details(st.session_state.last_sql, st.session_state.last_generated_sql)
            
            # Show planner details if available
            if 'last_agent_flow' in st.session_state:
                render_planner_details(st.session_state.last_agent_flow)
                render_executor_details(st.session_state.last_agent_flow)
        else:
            st.info("No debug report available. Run a query to see detailed agent flow information.")
            
            # Show sample debug structure
            st.markdown("**📋 Debug Information Available:**")
            st.markdown("""
            - **Agent Input/Output JSON** for each step
            - **SQL Generation Details** (generated vs executed)
            - **Planner Analysis** (tables, operations, complexity)
            - **Executor Results** (success, timing, errors)
            - **Timing Breakdown** by agent
            - **Error Summary** with detailed messages
            """)
    
    with tab8:
        st.markdown("#### 🤖 Agent Debugging Dashboard")
        
        if 'debug_report' in st.session_state:
            render_agent_debugging_tab()
        else:
            st.info("No agent debugging data available. Please run a query first.")
            
            # Show what will be available
            st.markdown("**📋 Agent Debugging Features:**")
            st.markdown("""
            - **Individual Agent Analysis** - Select any agent to see detailed input/output JSON
            - **Agent Performance Metrics** - Timing, status, and performance breakdown
            - **Error Diagnostics** - Detailed error messages and troubleshooting
            - **Agent Summary Table** - Overview of all agents' performance
            - **Real-time Debugging** - Live agent flow with JSON inspection
            """)

def render_business_user_ui(selected_role):
    """Render UI for Business User role"""
    st.markdown("### 👔 Business User View")
    
    # Application Health and Results tabs
    tab1, tab2, tab3 = st.tabs(["💬 Query", "📊 Results", "💬 Feedback"])
    
    with tab1:
        st.markdown("#### 💬 Natural Language Query")
        
        # User inputs
        col1, col2 = st.columns(2)
        
        with col1:
            user_input = st.text_input("👤 Your Name:", value="John", placeholder="Enter your name", key="user_input_business")
        
        with col2:
            # Role is now handled in main content area
            st.markdown("🎭 **Role:** Business User")
            role_input = "Business User"
        
        # Query input with Enter key handling
        query_input = st.text_area(
            "🔍 Enter your question:",
            placeholder="e.g., Find all customers who have both checking and savings accounts",
            height=100,
            key="query_input_business"
        )
        
        # Check if Enter was pressed (using session state)
        if st.session_state.get('enter_pressed', False):
            st.session_state.enter_pressed = False
            if query_input.strip():
                process_query(query_input, user_input, selected_role)
            else:
                st.warning("Please enter a query")
        
        # Process button with light color
        if st.button("🚀 Process Query", width="stretch", 
                    help="Click to process your query"):
            if query_input.strip():
                process_query(query_input, user_input, selected_role)
            else:
                st.warning("Please enter a query")
        
        # Handle Enter key press using session state - Improved detection
        if query_input and st.session_state.get('query_input_business_previous', '') != query_input:
            st.session_state.query_input_business_previous = query_input
            # Check if Enter was pressed (improved approach)
            if '\n' in query_input:
                # User pressed Enter, process the query
                clean_query = query_input.replace('\n', ' ').strip()
                if clean_query:
                    st.session_state.enter_pressed = True
                    st.session_state.pending_query = clean_query
                    st.rerun()
        
        # Process pending query from Enter key
        if st.session_state.get('enter_pressed', False) and st.session_state.get('pending_query'):
            query_to_process = st.session_state.pending_query
            st.session_state.enter_pressed = False
            st.session_state.pending_query = None
            process_query(query_to_process, user_input, selected_role)
    
    with tab2:
        st.markdown("#### 📊 Query Results")
        
        if 'last_results' in st.session_state:
            # Results count
            results_count = len(st.session_state.last_results)
            st.metric("Results", f"{results_count} records")
            
            # Results table
            st.dataframe(st.session_state.last_results, width='stretch')
            
            # Summary
            if 'last_summary' in st.session_state:
                st.markdown("#### 📝 Summary")
                st.write(st.session_state.last_summary)
        else:
            st.info("No results available. Please run a query first.")
    
    with tab3:
        st.markdown("#### 💬 Business User Feedback")
        
        # Application Health Status
        st.markdown("##### 🏥 Application Health")
        if 'init_report' in st.session_state:
            render_initialization_status(st.session_state.init_report)
        else:
            st.info("System status not available")
        
        # Feedback Box
        st.markdown("##### 📝 Your Feedback")
        feedback = st.text_area(
            "Please provide your feedback about the application:",
            placeholder="Share your thoughts about the query results, user experience, or any suggestions for improvement...",
            height=200,
            max_chars=1000,
            key="business_feedback"
        )
        
        if st.button("📤 Submit Feedback", type="secondary"):
            if feedback.strip():
                st.success("✅ Thank you for your feedback!")
                # Here you could save the feedback to a file or database
            else:
                st.warning("Please enter your feedback")

def verify_database_connections():
    """Verify SQLite and ChromaDB connections before processing queries"""
    connection_status = {
        'sqlite': {'status': False, 'message': '', 'details': ''},
        'chromadb': {'status': False, 'message': '', 'details': ''}
    }
    
    # Test SQLite connection
    try:
        db_path = os.getenv("DB_PATH", "banking.db")
        db_manager = get_db_manager(db_path)
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Test basic query
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 1")
        tables = cursor.fetchall()
        
        if tables:
            connection_status['sqlite']['status'] = True
            connection_status['sqlite']['message'] = f"✅ SQLite connected successfully to {db_path}"
            connection_status['sqlite']['details'] = f"Found {len(tables)} tables"
        else:
            connection_status['sqlite']['status'] = False
            connection_status['sqlite']['message'] = f"⚠️ SQLite connected but no tables found in {db_path}"
            connection_status['sqlite']['details'] = "Database may be empty"
        
        db_manager.release_connection(conn)
        
    except Exception as e:
        connection_status['sqlite']['status'] = False
        connection_status['sqlite']['message'] = f"❌ SQLite connection failed"
        connection_status['sqlite']['details'] = str(e)
    
    # Test ChromaDB connection
    try:
        from backend.llm_embedder import ChromaDBManager
        chroma_manager = ChromaDBManager()
        
        # Try to get or create a test collection
        collection = chroma_manager.get_or_create_collection("test_connection")
        
        # Test basic operation
        collection.add(
            documents=["test document"],
            metadatas=[{"source": "test"}],
            ids=["test_id"]
        )
        
        # Clean up test data
        collection.delete(ids=["test_id"])
        
        # Check for enhanced schema collections
        enhanced_collections = []
        expected_collections = [
            "database_schema"
        ]
        
        for collection_name in expected_collections:
            try:
                test_collection = chroma_manager.get_or_create_collection(collection_name)
                collection_count = test_collection.count()
                enhanced_collections.append(f"{collection_name}: {collection_count} items")
            except Exception as e:
                enhanced_collections.append(f"{collection_name}: Not available")
        
        # Note about skipped collections for essential schema focus
        enhanced_collections.append("sql_schema: Skipped (essential schema only)")
        enhanced_collections.append("sql_sample_data: Skipped (essential schema only)")
        enhanced_collections.append("entity_relationships: Skipped (essential schema only)")
        
        connection_status['chromadb']['status'] = True
        connection_status['chromadb']['message'] = "✅ ChromaDB connected successfully"
        connection_status['chromadb']['details'] = f"Vector database operational. Enhanced collections: {', '.join(enhanced_collections)}"
        
    except Exception as e:
        connection_status['chromadb']['status'] = False
        connection_status['chromadb']['message'] = "❌ ChromaDB connection failed"
        connection_status['chromadb']['details'] = str(e)
    
    return connection_status

def process_query(query: str, user_input: str, role_input: str):
    """Process a natural language query with comprehensive logging and step-by-step reasoning"""
    
    # Create a progress container
    progress_container = st.container()
    
    with progress_container:
        st.markdown("### 🔄 Query Processing Progress")
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Step 1: Verify database connections
        status_text.text("🔍 Step 1/7: Verifying database connections...")
        progress_bar.progress(14)
        
        # Log start of processing
        st.info(f"🚀 **Starting Query Processing** - User: {user_input}, Role: {role_input}")
        st.info(f"📝 **Query:** {query}")
        
        # Verify database connections
        st.info("🔍 **Verifying database connections**")
        connection_status = verify_database_connections()
        
        # Display connection status
        col1, col2 = st.columns(2)
        with col1:
            if connection_status['sqlite']['status']:
                st.success(connection_status['sqlite']['message'])
                st.info(f"📊 **SQLite Details:** {connection_status['sqlite']['details']}")
            else:
                st.error(connection_status['sqlite']['message'])
                st.error(f"🔧 **SQLite Error:** {connection_status['sqlite']['details']}")
        
        with col2:
            if connection_status['chromadb']['status']:
                st.success(connection_status['chromadb']['message'])
                st.info(f"📊 **ChromaDB Details:** {connection_status['chromadb']['details']}")
            else:
                st.error(connection_status['chromadb']['message'])
                st.error(f"🔧 **ChromaDB Error:** {connection_status['chromadb']['details']}")
        
        # Check if both connections are successful
        if not (connection_status['sqlite']['status'] and connection_status['chromadb']['status']):
            st.error("❌ **Critical Error:** One or more database connections failed. Cannot proceed with query processing.")
            status_text.text("❌ Step 1/7: Database connections failed")
            return
        
        st.success("✅ **All database connections verified successfully**")
        status_text.text("✅ Step 1/7: Database connections verified")
        
        # Step 2: System initialization
        status_text.text("🚀 Step 2/7: Initializing system...")
        progress_bar.progress(28)
        
    # Initialize components if not already done
    if 'system_initialized' not in st.session_state:
            status_text.text("⚠️ Step 2/7: System not initialized - Starting initialization...")
        with st.spinner("🚀 Initializing system..."):
                try:
            init_report = run_system_initialization()
            st.session_state.system_initialized = True
            st.session_state.init_report = init_report
                    st.success("✅ **System initialization completed**")
                    status_text.text("✅ Step 2/7: System initialization completed")
                except Exception as e:
                    st.error(f"❌ **System initialization failed:** {str(e)}")
                    status_text.text("❌ Step 2/7: System initialization failed")
                    return
        else:
            st.success("✅ **System already initialized**")
            status_text.text("✅ Step 2/7: System already initialized")
        
        # Step 3: Initialize timing tracker and CoT workflow
        status_text.text("⏱️ Step 3/7: Initializing timing tracker and CoT workflow...")
        progress_bar.progress(42)
        st.info("⏱️ **Initializing timing tracker and CoT workflow**")
    timing_tracker = TimingTracker()
    cot_workflow = CoTWorkflow()
        status_text.text("✅ Step 3/7: Timing tracker and CoT workflow initialized")
        
        # Step 4: Start agent workflow processing
        status_text.text("🔄 Step 4/7: Starting agent workflow processing...")
        progress_bar.progress(56)
        st.info("🔄 **Starting agent workflow processing**")
        
    with st.spinner("🔄 Processing.... please wait"):
            try:
                result = simulate_agent_workflow_with_cot(
                    query, timing_tracker, cot_workflow, user=user_input, ip_address="127.0.0.1"
                )
                st.success("✅ **Agent workflow completed successfully**")
                status_text.text("✅ Step 4/7: Agent workflow completed successfully")
                
                # Log result structure
                st.info(f"📋 **Result type:** {type(result)}")
                if isinstance(result, dict):
                    st.info(f"🔑 **Result keys:** {list(result.keys())}")
                elif isinstance(result, (list, tuple)):
                    st.info(f"📊 **Result length:** {len(result)}")
                
            except Exception as e:
                st.error(f"❌ **Agent workflow failed:** {str(e)}")
                st.exception(e)
                status_text.text("❌ Step 4/7: Agent workflow failed")
                return
            
            # Step 5: Extract results from pipeline
            status_text.text("📊 Step 5/7: Extracting results from pipeline...")
            progress_bar.progress(70)
            
            try:
                if len(result) >= 4:
                    sql, results, summary, timing_summary = result
                    st.success("✅ **Results extracted from tuple/list**")
                else:
                    # Handle case where pipeline returns a dict
                    sql = result.get("sql", "")
                    results = result.get("results", [])
                    summary = result.get("summary", "")
                    timing_summary = result.get("timing_summary", {})
                    st.success("✅ **Results extracted from dictionary**")
                
                # Log extracted data
                st.info(f"🔍 **Generated SQL:** {sql[:100]}{'...' if len(sql) > 100 else ''}")
                st.info(f"📊 **Results count:** {len(results)}")
                st.info(f"📝 **Summary:** {summary[:100]}{'...' if len(summary) > 100 else ''}")
                status_text.text("✅ Step 5/7: Results extracted successfully")
                
            except Exception as e:
                st.error(f"❌ **Result extraction failed:** {str(e)}")
                st.exception(e)
                status_text.text("❌ Step 5/7: Result extraction failed")
                return
        
        # Step 6: Apply security guards
        status_text.text("🛡️ Step 6/7: Applying security guards...")
        progress_bar.progress(85)
        st.info("🛡️ **Applying security guards**")
        try:
    security_guard = SecurityGuard()
    guard_result = security_guard.apply_guards(sql)
            st.success("✅ **Security guards applied**")
            st.info(f"🛡️ **Guard result:** {guard_result.get('message', 'No message')}")
            status_text.text("✅ Step 6/7: Security guards applied")
        except Exception as e:
            st.error(f"❌ **Security guard application failed:** {str(e)}")
            guard_result = {"sql": sql, "guards_applied": {}, "total_guards": 0}
            status_text.text("❌ Step 6/7: Security guard application failed")
        
        # Step 7: Store results and finalize
        status_text.text("💾 Step 7/7: Storing results and finalizing...")
        progress_bar.progress(100)
        
        # Store results in session state with logging
        st.info("💾 **Storing results in session state**")
        try:
    st.session_state.last_results = results
    st.session_state.last_guards = guard_result
    st.session_state.last_query_time = timing_summary.get('total_time', 0)
    st.session_state.last_sql = guard_result.get('sql', sql)
    st.session_state.last_timing_summary = timing_summary
    st.session_state.last_summary = summary
    st.session_state.last_cot_workflow = cot_workflow
            st.success("✅ **Results stored in session state**")
        except Exception as e:
            st.error(f"❌ **Session state storage failed:** {str(e)}")
        
        # Store debug information from pipeline
        st.info("🔍 **Storing debug information**")
        try:
            if hasattr(result, 'get') and isinstance(result, dict):
                st.session_state.debug_report = result.get("debug_report", {})
                st.session_state.last_agent_flow = result.get("agent_flow", [])
                st.session_state.last_generated_sql = result.get("generated_sql", sql)
                st.session_state.last_validation_details = result.get("validation_details", {})
                st.session_state.last_security_events = result.get("security_events", [])
                st.success("✅ **Debug information stored**")
    else:
                st.warning("⚠️ **No debug information available**")
        except Exception as e:
            st.error(f"❌ **Debug information storage failed:** {str(e)}")
    
        # Add to query history with logging
        st.info("📚 **Adding to query history**")
        try:
            query_history = QueryHistory()
    query_history.add_query(
        query=query,
        sql=guard_result.get('sql', sql),
        results_count=len(results),
        timestamp=datetime.now().strftime("%H:%M:%S")
    )
            st.success("✅ **Query added to history**")
        except Exception as e:
            st.error(f"❌ **Query history update failed:** {str(e)}")
        
        # Final success message
        status_text.text("🎉 All steps completed successfully!")
        st.success("🎉 **Query processing completed successfully!**")
        st.info(f"⏱️ **Total processing time:** {timing_summary.get('total_time', 0):.2f}s")
    
    # Trigger UI update
        st.info("🔄 **Triggering UI update**")
    st.rerun()

def render_security_guard_results(validation_details: Dict[str, Any], security_events: List[Dict[str, Any]]):
    """Render security guard results in the UI"""
    st.markdown("#### 🛡️ Security Guard Results")
    
    # Create columns for security information
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🔍 Validation Details**")
        
        # Validation step
        validation_step = validation_details.get("validation_step", "unknown")
        step_icon = "✅" if validation_step == "complete" else "⚠️"
        st.write(f"{step_icon} **Step:** {validation_step}")
        
        # Security action
        security_action = validation_details.get("security_action", "UNKNOWN")
        action_color = {
            "ALLOWED": "green",
            "BLOCKED": "red", 
            "FLAGGED": "orange",
            "UNKNOWN": "gray"
        }.get(security_action, "gray")
        
        st.markdown(f"**🛡️ Action:** :{action_color}[{security_action}]")
        
        # Syntax validation
        syntax_valid = validation_details.get("syntax_valid", False)
        st.write(f"{'✅' if syntax_valid else '❌'} **Syntax:** {'Valid' if syntax_valid else 'Invalid'}")
        
        # Schema validation
        schema_valid = validation_details.get("schema_valid", False)
        st.write(f"{'✅' if schema_valid else '❌'} **Schema:** {'Valid' if schema_valid else 'Invalid'}")
        
        # Performance warning
        performance_warning = validation_details.get("performance_warning")
        if performance_warning:
            st.warning(f"⚠️ **Performance:** {performance_warning}")
    
    with col2:
        st.markdown("**🚨 Recent Security Events**")
        
        if security_events:
            for i, event in enumerate(security_events[:5]):  # Show last 5 events
                event_type = event.get("event_type", "unknown")
                threat_level = event.get("threat_level", "LOW")
                action_taken = event.get("action_taken", "LOGGED")
                timestamp = event.get("timestamp", "unknown")
                
                # Color coding for threat levels
                threat_color = {
                    "HIGH": "red",
                    "MEDIUM": "orange", 
                    "LOW": "green"
                }.get(threat_level, "gray")
                
                st.markdown(f"""
                **Event {i+1}:**
                - **Type:** {event_type}
                - **Threat:** :{threat_color}[{threat_level}]
                - **Action:** {action_taken}
                - **Time:** {timestamp}
                """)
        else:
            st.info("No recent security events")

def render_agent_debugging_tab():
    """Render comprehensive agent debugging tab"""
    st.markdown("#### 🤖 Agent Debugging Dashboard")
    
    if 'debug_report' not in st.session_state:
        st.info("No agent debugging data available. Please run a query first.")
        return
    
    debug_report = st.session_state.debug_report
    
    # Agent selection
    agents = ["Planner", "Retriever", "SQL Generator", "Validator", "Executor", "Summarizer"]
    selected_agent = st.selectbox("Select Agent to Debug:", agents, key="agent_selector")
    
    if selected_agent in debug_report:
        agent_data = debug_report[selected_agent]
        
        # Agent overview
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Status", agent_data.get('status', 'Unknown'))
        with col2:
            st.metric("Timing (ms)", f"{agent_data.get('timing_ms', 0):.2f}")
        with col3:
            st.metric("Input Size", len(str(agent_data.get('input', {}))))
        
        # Input JSON
        st.markdown("##### 📥 Input JSON")
        input_data = agent_data.get('input', {})
        if input_data:
            st.json(input_data)
        else:
            st.info("No input data available")
        
        # Output JSON
        st.markdown("##### 📤 Output JSON")
        output_data = agent_data.get('output', {})
        if output_data:
            st.json(output_data)
        else:
            st.info("No output data available")
        
        # Error details
        if agent_data.get('error'):
            st.markdown("##### ❌ Error Details")
            st.error(agent_data['error'])
        
        # Timing breakdown
        if 'timing_breakdown' in agent_data:
            st.markdown("##### ⏱️ Timing Breakdown")
            timing_data = agent_data['timing_breakdown']
            for step, time_ms in timing_data.items():
                st.metric(step, f"{time_ms:.2f}ms")
    
    # All agents summary
    st.markdown("##### 📊 All Agents Summary")
    if debug_report:
        summary_data = []
        for agent_name, agent_data in debug_report.items():
            summary_data.append({
                "Agent": agent_name,
                "Status": agent_data.get('status', 'Unknown'),
                "Timing (ms)": f"{agent_data.get('timing_ms', 0):.2f}",
                "Input Size": len(str(agent_data.get('input', {}))),
                "Output Size": len(str(agent_data.get('output', {})))
            })
        
        st.dataframe(summary_data, width='stretch')

def render_agent_flow_debugger():
    """Render agent flow debugger with detailed JSON views"""
    st.markdown("#### 🔍 Agent Flow Debugger")
    
    if 'agent_flow' not in st.session_state:
        st.info("No agent flow data available. Please run a query first.")
        return
    
    agent_flow = st.session_state.agent_flow
    
    # Agent selection tabs
    agent_tabs = st.tabs([
        "🧠 Planner", "🔍 Retriever", "⚙️ SQL Generator", 
        "✅ Validator", "🚀 Executor", "📝 Summarizer"
    ])
    
    agents = ["planner", "retriever", "sql_generator", "validator", "executor", "summarizer"]
    
    for i, (tab, agent) in enumerate(zip(agent_tabs, agents)):
        with tab:
            if agent in agent_flow:
                agent_data = agent_flow[agent]
                
                # Agent status
                status = agent_data.get('status', 'Unknown')
                status_color = "green" if status == "success" else "red"
                st.markdown(f"**Status:** :{status_color}[{status.upper()}]")
                
                # Input JSON
                st.markdown("**📥 Input JSON:**")
                input_json = agent_data.get('input', {})
                if input_json:
                    st.json(input_json)
                else:
                    st.info("No input data")
                
                # Output JSON
                st.markdown("**📤 Output JSON:**")
                output_json = agent_data.get('output', {})
                if output_json:
                    st.json(output_json)
                else:
                    st.info("No output data")
                
                # Error if any
                if 'error' in agent_data:
                    st.error(f"**Error:** {agent_data['error']}")
                
                # Timing
                timing = agent_data.get('timing_ms', 0)
                st.metric("Execution Time", f"{timing:.2f}ms")
            else:
                st.info(f"No data available for {agent}")

def render_sql_details():
    """Render SQL generation details"""
    st.markdown("#### ⚙️ SQL Generation Details")
    
    if 'generated_sql' not in st.session_state:
        st.info("No SQL generation data available. Please run a query first.")
        return
    
    sql_data = st.session_state.generated_sql
    
    # SQL Query
    st.markdown("**🔍 Generated SQL Query:**")
    st.code(sql_data.get('sql', 'No SQL generated'), language='sql')
    
    # Generation details
    if 'details' in sql_data:
        st.markdown("**📋 Generation Details:**")
        st.json(sql_data['details'])
    
    # Validation results
    if 'validation' in sql_data:
        st.markdown("**✅ Validation Results:**")
        st.json(sql_data['validation'])

def render_planner_details():
    """Render planner agent details"""
    st.markdown("#### 🧠 Planner Agent Details")
    
    if 'agent_flow' not in st.session_state or 'planner' not in st.session_state.agent_flow:
        st.info("No planner data available. Please run a query first.")
        return
    
    planner_data = st.session_state.agent_flow['planner']
    
    # Planning strategy
    st.markdown("**🎯 Planning Strategy:**")
    strategy = planner_data.get('output', {}).get('strategy', 'No strategy available')
    st.write(strategy)
    
    # Steps breakdown
    if 'steps' in planner_data.get('output', {}):
        st.markdown("**📋 Planning Steps:**")
        steps = planner_data['output']['steps']
        for i, step in enumerate(steps, 1):
            st.markdown(f"**Step {i}:** {step}")

def render_executor_details():
    """Render executor agent details"""
    st.markdown("#### 🚀 Executor Agent Details")
    
    if 'agent_flow' not in st.session_state or 'executor' not in st.session_state.agent_flow:
        st.info("No executor data available. Please run a query first.")
        return
    
    executor_data = st.session_state.agent_flow['executor']
    
    # Execution results
    st.markdown("**📊 Execution Results:**")
    results = executor_data.get('output', {})
    if results:
        st.json(results)
    else:
        st.info("No execution results available")
    
    # Performance metrics
    timing = executor_data.get('timing_ms', 0)
    st.metric("Execution Time", f"{timing:.2f}ms")

def main():
    """Main application function"""
    # Force bright theme immediately
        st.markdown("""
    <style>
    /* FORCE BRIGHT THEME - OVERRIDE EVERYTHING */
    .stApp {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
    }
    .main {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
    }
    .main .block-container {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
        padding-top: 1rem !important;
    }
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
    .css-1d391kg, .css-1lcbmhc {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
    .stMarkdown, .stText, .stWrite {
        color: #2c3e50 !important;
    }
    
    /* Make tab names visible with dark lettering */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #ffffff !important;
        border-bottom: 2px solid #d4d1cc !important;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f7f4 !important;
        color: #2c3e50 !important;
        border: 1px solid #d4d1cc !important;
        border-bottom: none !important;
        border-radius: 8px 8px 0 0 !important;
        margin-right: 4px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #e8e6e3 !important;
        color: #1a252f !important;
    }
    
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
        border-bottom: 2px solid #ffffff !important;
        font-weight: bold !important;
    }
    
    /* Target header and navigation areas */
    .stApp > header {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
    }
    .stApp > div:first-child {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
    }
    .stApp > div:first-child > div:first-child {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
    }
    
    /* Target all possible header elements */
    header, .stApp header, .stApp > div:first-child, .stApp > div:first-child > div {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
    }
    
    /* Target navigation and menu areas */
    .stApp nav, .stApp .navigation, .stApp .menu {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
    }
    
    /* Target specific Streamlit elements that might be dark */
    .stApp > div, .stApp > div > div, .stApp > div > div > div {
        background: linear-gradient(135deg, #f5f5f0 0%, #e8e6e3 50%, #d4d1cc 100%) !important;  /* Creamy coffee gradient */
        color: #2c3e50 !important;
    }
    
    /* But allow specific elements to have their own colors */
    .stButton > button {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .stTextArea textarea, .stTextInput input, .stSelectbox select {
        background-color: #ffffff !important;
        color: #2c3e50 !important;
    }
    /* Ensure selectbox dropdown options have white text */
    .stSelectbox select option {
        background-color: #2c3e50 !important;
        color: #ffffff !important;
    }
    .stSelectbox [data-baseweb="select"] [role="option"] {
        background-color: #2c3e50 !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #e8e6e3 0%, #d4d1cc 100%) !important;  /* Sidebar gradient */
    }
    </style>
        """, unsafe_allow_html=True)
    
    # Initialize Enter key tracking
    if 'enter_pressed' not in st.session_state:
        st.session_state.enter_pressed = False
    if 'pending_query' not in st.session_state:
        st.session_state.pending_query = None
    
    # REMOVED: Dark mode toggle - no longer needed
    
    # Header with blood-red title moved up significantly
    st.markdown("""
    <div style="text-align: center; margin-top: -100px; margin-bottom: 10px;">
        <h1 style="color: #8B0000; font-size: 2.8em; font-weight: bold; margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(139,0,0,0.3);">
            WELLS - NL2SQL Data Insighter
            </h1>
        <p style="color: #000000; font-size: 1.0em; margin: 0; font-weight: 600;">
            Natural Language to SQL Query Processing with AI Agents
        </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Initialize ChromaDB with schema embeddings at startup using LangGraph agents
    if 'schema_initialized' not in st.session_state:
        st.session_state.schema_initialized = False
    
    if not st.session_state.schema_initialized:
        try:
            st.info("🔄 Initializing ChromaDB with database schema embeddings using LangGraph agents...")
            
            # Import enhanced schema initializer with LangGraph
            import sys
            import os
            sys.path.append('./backend')
            from schema_initializer import SQLFileProcessor, SchemaAnalyzer, LangGraphSchemaProcessor
            
            # Get OpenAI API key
            openai_api_key = os.getenv("OPENAI_API_KEY")
            if openai_api_key:
                # Initialize LangGraph-based schema processor
                st.info("📋 Step 1: Processing SQL schema files...")
                sql_processor = SQLFileProcessor(db_folder="./db")
                
                # Process schema.sql file
                schema_chunks = sql_processor.process_schema_file("schema.sql")
                st.success(f"✅ Processed schema.sql: {len(schema_chunks)} chunks")
                
                # Process sample_data.sql file
                sample_chunks = sql_processor.process_sample_data_file("sample_data.sql")
                st.success(f"✅ Processed sample_data.sql: {len(sample_chunks)} chunks")
                
                # Initialize LangGraph schema initializer
                st.info("🔄 Step 2: Initializing LangGraph schema agents...")
                langgraph_initializer = LangGraphSchemaProcessor(
                    openai_api_key=openai_api_key,
                    chromadb_persist_dir="./chroma_db"
                )
                
                # Run LangGraph pipeline to process schema and create embeddings
                st.info("🔄 Step 3: Running LangGraph pipeline for schema embeddings...")
                success = langgraph_initializer.run_schema_initialization_pipeline()
                
                if success:
                    st.success("✅ ChromaDB schema initialization with LangGraph completed!")
                    st.info("📊 Schema metadata, distinct values, and WHERE suggestions are now available")
                    
                    # Check PII scanning status
                    import os
                    pii_scanning_enabled = os.getenv("ENABLE_PII_SCANNING", "true").lower() == "true"
                    
                    if pii_scanning_enabled:
                        st.info("🔒 PII scanning is enabled - checking for sensitive data...")
                        
                        # Check for PII findings
                        pii_findings = langgraph_initializer.get_pii_findings()
                        pii_summary = langgraph_initializer.get_pii_summary()
                        
                        if pii_findings:
                            st.warning("⚠️ PII (Personally Identifiable Information) detected during schema processing!")
                            
                            # Display PII summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Total PII Findings", pii_summary['total_findings'])
                            with col2:
                                high_risk = pii_summary['risk_levels'].get('high', 0)
                                st.metric("High Risk Items", high_risk, delta=f"{high_risk} items")
    with col3:
                                medium_risk = pii_summary['risk_levels'].get('medium', 0)
                                st.metric("Medium Risk Items", medium_risk, delta=f"{medium_risk} items")
                            
                            # Show PII types detected
                            if pii_summary['pii_types']:
                                st.markdown("**🔍 PII Types Detected:**")
                                for pii_type, count in pii_summary['pii_types'].items():
                                    risk_level = "🔴 HIGH" if pii_type in ['ssn', 'credit_card'] else "🟡 MEDIUM" if pii_type in ['email', 'phone', 'date_of_birth'] else "🟢 LOW"
                                    st.markdown(f"- {risk_level} **{pii_type.title()}**: {count} instances")
                            
                            # Show contexts where PII was found
                            if pii_summary['contexts']:
                                st.markdown("**📍 PII Found In:**")
                                for context in pii_summary['contexts'][:5]:  # Show first 5
                                    st.markdown(f"- `{context}`")
                            
                            # Show recommendations
                            st.markdown("**🛡️ Security Recommendations:**")
                            st.markdown("- ✅ PII has been automatically sanitized before embedding")
                            st.markdown("- 🔒 High-risk PII (SSN, credit cards) has been removed")
                            st.markdown("- 📧 Medium-risk PII (emails, phones) has been masked")
                            st.markdown("- 📋 All PII detection events have been logged for audit")
                            
                            # Store PII findings in session state for later reference
                            st.session_state.pii_findings = pii_findings
                            st.session_state.pii_summary = pii_summary
                        else:
                            st.success("✅ No PII detected in schema data")
                    else:
                        st.info("⚡ PII scanning is disabled - initialization completed faster")
                        st.info("💡 To enable PII scanning, set ENABLE_PII_SCANNING=true in your .env file")
                    
                    st.session_state.schema_initialized = True
                else:
                    st.warning("⚠️ LangGraph schema initialization failed, continuing without enhanced schema embeddings")
            else:
                st.warning("⚠️ OpenAI API key not found, skipping LangGraph schema initialization")
                
        except Exception as e:
            st.warning(f"⚠️ LangGraph schema initialization error: {e}")
            logger.error(f"LangGraph schema initialization error22: {e}")
    
    # Initialize enhanced components in session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = QueryHistory()
    if 'timing_tracker' not in st.session_state:
        st.session_state.timing_tracker = TimingTracker()
    if 'security_guard' not in st.session_state:
        st.session_state.security_guard = SecurityGuard()
    
    # Sidebar - REMOVED duplicate role selection
    with st.sidebar:
        st.markdown("### 📋 Navigation")
        
        # Recent queries
        render_recent_queries_sidebar()
        
        # REMOVED: Role selector from sidebar (duplicate)
        # REMOVED: Role-specific info from sidebar
        
        # Show tech stack only for Developer role (will be determined by main UI)
        st.markdown("### 🛠️ Quick Tech Stack")
        render_tech_stack_about()
    
    # Main content area with role selection
        st.markdown("### 🎭 Role Selection")
        selected_role = st.selectbox(
            "Choose your role:",
        ["Developer", "Business User"],
        key="role_selector_main"
        )
    # Show role-specific info in main area
        if selected_role == "Developer":
        st.markdown('<div class="developer-view-info">👨‍💻 Developer View: Tech Stack, Agent Flow, Detailed Analysis</div>', unsafe_allow_html=True)
        elif selected_role == "Business User":
        st.markdown('<div class="business-view-info">👔 **Business View**: Simple Results, Health Status, Feedback</div>', unsafe_allow_html=True)
    
    # Render role-based UI
    if selected_role == "Developer":
        render_developer_ui(selected_role)
    elif selected_role == "Business User":
        render_business_user_ui(selected_role)

if __name__ == "__main__":
    main()
