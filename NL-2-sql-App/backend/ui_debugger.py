#!/usr/bin/env python3
"""
UI Debugger Components for Agent Flow Visualization
"""

import streamlit as st
from typing import Dict, Any, List

def render_agent_flow_debugger(debug_report: Dict[str, Any]):
    """Render detailed agent flow debugger UI"""
    st.markdown("#### 🔍 Agent Flow Debugger")
    
    if not debug_report:
        st.info("No debug report available. Run a query to see agent details.")
        return
    
    # Session info
    session_info = debug_report.get("debug_session", {})
    st.markdown(f"**Session ID:** {session_info.get('session_id', 'N/A')}")
    st.markdown(f"**Query:** {session_info.get('query', 'N/A')}")
    st.markdown(f"**Total Time:** {session_info.get('total_timing', 0)}ms")
    
    # Agent summary
    agent_summary = debug_report.get("agent_summary", {})
    if agent_summary:
        st.markdown("#### 📊 Agent Summary")
        
        # Create a summary table
        summary_data = []
        for agent_name, agent_data in agent_summary.items():
            summary_data.append({
                "Agent": agent_name,
                "Calls": agent_data["total_calls"],
                "Success": agent_data["success_count"],
                "Errors": agent_data["error_count"],
                "Total Time (ms)": agent_data["total_timing_ms"]
            })
        
        st.table(summary_data)
    
    # Detailed agent logs
    agents = debug_report.get("debug_session", {}).get("agents", [])
    if agents:
        st.markdown("#### 🔍 Detailed Agent Logs")
        
        # Create tabs for each agent
        agent_names = list(set([agent["agent"] for agent in agents]))
        tabs = st.tabs([f"🤖 {name}" for name in agent_names])
        
        for i, agent_name in enumerate(agent_names):
            with tabs[i]:
                agent_logs = [agent for agent in agents if agent["agent"] == agent_name]
                
                for j, log in enumerate(agent_logs):
                    with st.expander(f"Step {j+1}: {log['step']} ({log['timing_ms']}ms)", expanded=True):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("**📥 Input:**")
                            st.json(log["input"])
                        
                        with col2:
                            st.markdown("**📤 Output:**")
                            st.json(log["output"])
                        
                        if log.get("error"):
                            st.error(f"**❌ Error:** {log['error']}")
                        
                        # Status indicator
                        status_color = "green" if log["status"] == "success" else "red"
                        st.markdown(f"**Status:** :{status_color}[{log['status'].upper()}]")
    
    # Timing breakdown
    timing_breakdown = debug_report.get("timing_breakdown", {})
    if timing_breakdown:
        st.markdown("#### ⏱️ Timing Breakdown")
        
        # Create a bar chart
        import plotly.express as px
        
        timing_data = {
            "Agent": list(timing_breakdown.keys()),
            "Time (ms)": list(timing_breakdown.values())
        }
        
        fig = px.bar(
            x=timing_data["Agent"],
            y=timing_data["Time (ms)"],
            title="Agent Execution Time",
            color=timing_data["Time (ms)"],
            color_continuous_scale="viridis"
        )
        fig.update_layout(xaxis_title="Agent", yaxis_title="Time (ms)")
        st.plotly_chart(fig, use_container_width=True)
    
    # Error summary
    error_summary = debug_report.get("error_summary", [])
    if error_summary:
        st.markdown("#### ❌ Error Summary")
        
        for error in error_summary:
            st.error(f"**{error['agent']} ({error['step']}):** {error['error']}")

def render_sql_details(sql: str, generated_sql: str):
    """Render SQL generation and execution details"""
    st.markdown("#### 🔧 SQL Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📝 Generated SQL:**")
        st.code(sql, language="sql")
        st.markdown(f"**Length:** {len(sql)} characters")
    
    with col2:
        st.markdown("**⚡ Executed SQL:**")
        st.code(generated_sql, language="sql")
        st.markdown(f"**Length:** {len(generated_sql)} characters")
    
    # Show differences if they exist
    if sql != generated_sql:
        st.warning("⚠️ **Note:** Generated SQL differs from executed SQL (possibly due to validation/repair)")

def render_planner_details(agent_flow: List[Dict[str, Any]]):
    """Render planner agent details"""
    st.markdown("#### 📋 Planner Details")
    
    # Find planner logs
    planner_logs = [log for log in agent_flow if log.get("agent") == "PLANNER"]
    
    if planner_logs:
        planner_log = planner_logs[0]  # Take the first one
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 Input:**")
            st.json(planner_log["input"])
        
        with col2:
            st.markdown("**📤 Output:**")
            st.json(planner_log["output"])
        
        # Show planning details
        output = planner_log["output"]
        
        st.markdown("**📊 Planning Analysis:**")
        st.markdown(f"**Tables Needed:** {', '.join(output.get('tables_needed', []))}")
        st.markdown(f"**Operations:** {', '.join(output.get('operations', []))}")
        st.markdown(f"**Complexity:** {output.get('complexity', 'unknown')}")
        st.markdown(f"**Estimated Tokens:** {output.get('estimated_tokens', 0)}")
        
        clarifications = output.get('clarifications', [])
        if clarifications:
            st.markdown("**❓ Clarifications Needed:**")
            for clarification in clarifications:
                st.info(f"• {clarification}")
    else:
        st.info("No planner details available")

def render_executor_details(agent_flow: List[Dict[str, Any]]):
    """Render executor agent details"""
    st.markdown("#### ⚡ Executor Details")
    
    # Find executor logs
    executor_logs = [log for log in agent_flow if log.get("agent") == "EXECUTOR"]
    
    if executor_logs:
        executor_log = executor_logs[0]  # Take the first one
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📥 Input:**")
            st.json(executor_log["input"])
        
        with col2:
            st.markdown("**📤 Output:**")
            st.json(executor_log["output"])
        
        # Show execution details
        output = executor_log["output"]
        
        st.markdown("**📊 Execution Results:**")
        st.markdown(f"**Success:** {'✅ Yes' if output.get('success', False) else '❌ No'}")
        st.markdown(f"**Results Count:** {len(output.get('results', []))}")
        st.markdown(f"**Execution Time:** {output.get('execution_time_ms', 0)}ms")
        
        if output.get('error'):
            st.error(f"**❌ Error:** {output['error']}")
    else:
        st.info("No executor details available")



