#!/usr/bin/env python3
"""
Health Dashboard Component for Streamlit
Displays health check boxes and status indicators for all system components
"""

import streamlit as st
import time
from typing import Dict, Any
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from health_checker import HealthChecker, HealthStatus

def render_health_status(status: str) -> str:
    """Convert health status to emoji and color"""
    status_map = {
        "healthy": "✅",
        "warning": "⚠️", 
        "error": "❌",
        "unknown": "❓"
    }
    return status_map.get(status, "❓")

def get_status_color(status: str) -> str:
    """Get color for status"""
    color_map = {
        "healthy": "green",
        "warning": "orange",
        "error": "red", 
        "unknown": "gray"
    }
    return color_map.get(status, "gray")

def create_health_dashboard(db_connection=None) -> Dict[str, Any]:
    """
    Create and display health dashboard
    
    Args:
        db_connection: SQLite database connection
        
    Returns:
        Dictionary with health check results
    """
    
    # Create health checker
    checker = HealthChecker(db_connection=db_connection)
    
    # Run health checks
    with st.spinner("🔍 Running health checks..."):
        health_results = checker.run_full_health_check()
    
    # Display overall status
    overall_status = checker.get_overall_status().value
    overall_emoji = render_health_status(overall_status)
    overall_color = get_status_color(overall_status)
    
    st.markdown("---")
    st.subheader(f"{overall_emoji} **System Health Dashboard**")
    
    # Overall status metric
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "Overall Status", 
            f"{overall_emoji} {overall_status.title()}",
            delta=None
        )
    
    with col2:
        healthy_count = sum(1 for h in health_results.values() if h.status == HealthStatus.HEALTHY)
        st.metric("Healthy Components", healthy_count)
    
    with col3:
        error_count = sum(1 for h in health_results.values() if h.status == HealthStatus.ERROR)
        st.metric("Issues Found", error_count, delta=None)
    
    # Component health boxes
    st.markdown("### 📋 **Component Status**")
    
    # Create columns for health boxes
    cols = st.columns(len(health_results))
    
    for i, (component_name, health) in enumerate(health_results.items()):
        with cols[i]:
            # Health box
            status_emoji = render_health_status(health.status.value)
            status_color = get_status_color(health.status.value)
            
            # Create expandable box
            with st.expander(f"{status_emoji} {component_name.title()}", expanded=False):
                
                # Status indicator
                st.markdown(f"**Status:** {status_emoji} {health.status.value.title()}")
                
                # Message
                st.markdown(f"**Message:** {health.message}")
                
                # Details
                if health.details:
                    st.markdown("**Details:**")
                    for key, value in health.details.items():
                        if isinstance(value, list):
                            st.write(f"  - {key}: {', '.join(map(str, value))}")
                        elif isinstance(value, dict):
                            st.write(f"  - {key}:")
                            for k, v in value.items():
                                st.write(f"    - {k}: {v}")
                        else:
                            st.write(f"  - {key}: {value}")
                
                # Last check time
                if health.last_check:
                    st.markdown(f"**Last Check:** {time.strftime('%H:%M:%S', time.localtime(health.last_check))}")
    
    # Detailed status information
    with st.expander("📊 **Detailed System Information**", expanded=False):
        
        # SQLite Information
        if "sqlite" in health_results:
            sqlite_health = health_results["sqlite"]
            st.markdown("**🗄️ SQLite Database:**")
            if sqlite_health.status == HealthStatus.HEALTHY:
                details = sqlite_health.details
                st.write(f"- Type: {details.get('connection_type', 'Unknown')}")
                st.write(f"- Tables: {len(details.get('tables', []))}")
                st.write(f"- Total Rows: {details.get('total_rows', 0):,}")
                if 'table_stats' in details:
                    st.write("- Table Statistics:")
                    for table, count in details['table_stats'].items():
                        st.write(f"  - {table}: {count:,} rows")
            else:
                st.error(f"Database Error: {sqlite_health.message}")
        
        # Ollama Information
        if "ollama" in health_results:
            ollama_health = health_results["ollama"]
            st.markdown("**🧠 Ollama Server:**")
            if ollama_health.status == HealthStatus.HEALTHY:
                details = ollama_health.details
                st.write(f"- URL: {details.get('server_url', 'Unknown')}")
                st.write(f"- Models: {len(details.get('models', []))}")
                st.write(f"- Embedding Dimensions: {details.get('embedding_dimensions', 0)}")
                if 'models' in details:
                    st.write(f"- Available Models: {', '.join(details['models'])}")
            else:
                st.error(f"Ollama Error: {ollama_health.message}")
        
        # ChromaDB Information
        if "chromadb" in health_results:
            chromadb_health = health_results["chromadb"]
            st.markdown("**🗄️ ChromaDB:**")
            if chromadb_health.status in [HealthStatus.HEALTHY, HealthStatus.WARNING]:
                details = chromadb_health.details
                st.write(f"- Path: {details.get('path', 'Unknown')}")
                st.write(f"- Collections: {len(details.get('collections', []))}")
                if 'collections' in details and details['collections']:
                    st.write(f"- Collection Names: {', '.join(details['collections'])}")
            else:
                st.error(f"ChromaDB Error: {chromadb_health.message}")
    
    # Recommendations
    recommendations = []
    for health in health_results.values():
        if health.status == HealthStatus.ERROR:
            if "sqlite" in health.name.lower():
                recommendations.append("Initialize the database connection")
            elif "ollama" in health.name.lower():
                recommendations.append("Start Ollama server: brew services start ollama")
            elif "chromadb" in health.name.lower():
                recommendations.append("Initialize ChromaDB collections")
        elif health.status == HealthStatus.WARNING:
            if "missing tables" in health.message.lower():
                recommendations.append("Load database schema and data")
            elif "missing model" in health.message.lower():
                recommendations.append("Pull required Ollama model")
    
    if recommendations:
        st.markdown("### 💡 **Recommendations**")
        for rec in recommendations:
            st.info(f"• {rec}")
    
    return health_results

def create_mini_health_status(db_connection=None) -> Dict[str, Any]:
    """
    Create a mini health status indicator for sidebar
    
    Args:
        db_connection: SQLite database connection
        
    Returns:
        Dictionary with health check results
    """
    
    # Create health checker
    checker = HealthChecker(db_connection=db_connection)
    
    # Run health checks
    health_results = checker.run_full_health_check()
    
    # Display mini status in sidebar
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 **System Health**")
    
    # Overall status
    overall_status = checker.get_overall_status().value
    overall_emoji = render_health_status(overall_status)
    
    st.sidebar.markdown(f"**Overall:** {overall_emoji} {overall_status.title()}")
    
    # Component status
    for component_name, health in health_results.items():
        status_emoji = render_health_status(health.status.value)
        st.sidebar.markdown(f"**{component_name.title()}:** {status_emoji}")
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Health Check"):
        st.rerun()
    
    return health_results

if __name__ == "__main__":
    # Test the health dashboard
    st.title("Health Dashboard Test")
    create_health_dashboard()
