"""Agent-specific tab interface components"""
import streamlit as st
import json
from typing import Dict, Any
import pandas as pd

def format_json(data: Any) -> str:
    """Format JSON data for display"""
    if isinstance(data, str):
        try:
            return json.dumps(json.loads(data), indent=2)
        except:
            return data
    return json.dumps(data, indent=2)

def render_agent_io(input_data: Any, output_data: Any):
    """Render agent input/output in two columns"""
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📥 Input")
        st.code(format_json(input_data), language="json")
        
    with col2:
        st.markdown("### 📤 Output")
        st.code(format_json(output_data), language="json")

def render_agent_status(status: str):
    """Render agent status with appropriate icon"""
    status_icons = {
        'started': '🟡',
        'completed': '🟢',
        'failed': '🔴',
        'pending': '⚪'
    }
    icon = status_icons.get(status.lower(), '⚪')
    st.markdown(f"### Status: {icon} {status}")

def render_planner_tab(agent_data: Dict[str, Any]):
    """Render Planner Agent tab"""
    st.markdown("## 🎯 Planner Agent")
    
    if 'PlannerAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['PlannerAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'query': state.get('input_args', [])[0] if state.get('input_args') else None,
            'constraints': state.get('input_kwargs', {}).get('constraints', {})
        }
        output_data = state.get('output', {})
        render_agent_io(input_data, output_data)
    else:
        st.info("No planner data available yet. Run a query to see the planner in action.")

def render_retriever_tab(agent_data: Dict[str, Any]):
    """Render Retriever Agent tab"""
    st.markdown("## 🔍 Retriever Agent")
    
    if 'RetrieverAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['RetrieverAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'query': state.get('input_args', [])[0] if state.get('input_args') else None,
            'context_type': state.get('input_kwargs', {}).get('context_type', 'unknown')
        }
        output_data = state.get('output', {})
        render_agent_io(input_data, output_data)
    else:
        st.info("No retriever data available yet. Run a query to see the retriever in action.")

def render_generator_tab(agent_data: Dict[str, Any]):
    """Render SQL Generator Agent tab"""
    st.markdown("## 💻 SQL Generator Agent")
    
    if 'SQLGeneratorAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['SQLGeneratorAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'query': state.get('input_args', [])[0] if state.get('input_args') else None,
            'context': state.get('input_kwargs', {}).get('retrieval_context', {}),
            'constraints': state.get('input_kwargs', {}).get('constraints', {})
        }
        output_data = {
            'generated_sql': state.get('output', 'No SQL generated yet')
        }
        render_agent_io(input_data, output_data)
    else:
        st.info("No generator data available yet. Run a query to see the SQL generation in action.")

def render_validator_tab(agent_data: Dict[str, Any]):
    """Render Validator Agent tab"""
    st.markdown("## ✅ Validator Agent")
    
    if 'ValidatorAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['ValidatorAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'sql': state.get('input_args', [])[0] if state.get('input_args') else None,
            'validation_type': state.get('input_kwargs', {}).get('validation_type', 'standard')
        }
        output_data = {
            'validation_result': state.get('output', {}),
            'errors': state.get('error', 'No errors')
        }
        render_agent_io(input_data, output_data)
    else:
        st.info("No validator data available yet. Run a query to see the validation in action.")

def render_executor_tab(agent_data: Dict[str, Any]):
    """Render Executor Agent tab"""
    st.markdown("## ⚡ Executor Agent")
    
    if 'ExecutorAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['ExecutorAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'sql': state.get('input_args', [])[0] if state.get('input_args') else None,
            'execution_options': state.get('input_kwargs', {})
        }
        output_data = {
            'results': state.get('output', {}),
            'execution_time': state.get('execution_time', 'unknown')
        }
        render_agent_io(input_data, output_data)
    else:
        st.info("No executor data available yet. Run a query to see the execution in action.")

def render_summarizer_tab(agent_data: Dict[str, Any]):
    """Render Summarizer Agent tab"""
    st.markdown("## 📝 Summarizer Agent")
    
    if 'SummarizerAgent' in agent_data['agent_states']:
        state = agent_data['agent_states']['SummarizerAgent']
        render_agent_status(state.get('status', 'unknown'))
        
        # Show input/output
        input_data = {
            'results': state.get('input_args', [])[0] if state.get('input_args') else None,
            'format': state.get('input_kwargs', {}).get('format', 'text')
        }
        output_data = {
            'summary': state.get('output', 'No summary generated yet')
        }
        render_agent_io(input_data, output_data)
    else:
        st.info("No summarizer data available yet. Run a query to see the summarization in action.")

def render_agent_tabs(agent_data: Dict[str, Any]):
    """Render all agent tabs"""
    # Create tabs for each agent
    planner_tab, retriever_tab, generator_tab, validator_tab, executor_tab, summarizer_tab = st.tabs([
        "🎯 Planner",
        "🔍 Retriever",
        "💻 Generator",
        "✅ Validator",
        "⚡ Executor",
        "📝 Summarizer"
    ])
    
    # Render each agent's tab
    with planner_tab:
        render_planner_tab(agent_data)
    
    with retriever_tab:
        render_retriever_tab(agent_data)
    
    with generator_tab:
        render_generator_tab(agent_data)
    
    with validator_tab:
        render_validator_tab(agent_data)
    
    with executor_tab:
        render_executor_tab(agent_data)
    
    with summarizer_tab:
        render_summarizer_tab(agent_data)
