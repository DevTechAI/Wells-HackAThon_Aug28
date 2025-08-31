#!/usr/bin/env python3
"""
LangGraph State Management for SQL RAG Agent
LLM-neutral state structure and management
"""

from typing import TypedDict, List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class AgentTiming:
    """Timing information for agent execution"""
    start_time: datetime
    end_time: Optional[datetime] = None
    
    @property
    def duration_ms(self) -> int:
        """Calculate duration in milliseconds"""
        if self.end_time:
            return int((self.end_time - self.start_time).total_seconds() * 1000)
        return 0

class SQLRAGState(TypedDict):
    """
    Complete state structure for LangGraph SQL RAG workflow
    LLM-neutral design for any LLM provider
    """
    
    # Core data
    query: str
    clarified_values: Optional[Dict[str, Any]]
    
    # Agent outputs
    plan: Optional[Dict[str, Any]]
    context: Optional[List[Dict[str, Any]]]
    sql: Optional[str]
    validation_result: Optional[Dict[str, Any]]
    results: Optional[List[Dict[str, Any]]]
    summary: Optional[Dict[str, Any]]
    
    # Error handling
    errors: List[str]
    retry_count: int
    current_agent: str
    
    # Timing and diagnostics
    timings: Dict[str, AgentTiming]
    agent_flow: List[Dict[str, Any]]
    
    # Pipeline control
    should_continue: bool
    needs_clarification: bool
    clarification_questions: List[Dict[str, Any]]
    
    # LLM configuration (provider-agnostic)
    llm_config: Optional[Dict[str, Any]]

def create_initial_state(query: str, clarified_values: Optional[Dict[str, Any]] = None) -> SQLRAGState:
    """Create initial state for LangGraph workflow"""
    return SQLRAGState(
        query=query,
        clarified_values=clarified_values,
        plan=None,
        context=None,
        sql=None,
        validation_result=None,
        results=None,
        summary=None,
        errors=[],
        retry_count=0,
        current_agent="",
        timings={},
        agent_flow=[],
        should_continue=True,
        needs_clarification=False,
        clarification_questions=[],
        llm_config=None
    )

def update_state_timing(state: SQLRAGState, agent_name: str, start_time: datetime) -> SQLRAGState:
    """Update state with agent timing information"""
    state["timings"][agent_name] = AgentTiming(start_time=start_time)
    state["current_agent"] = agent_name
    return state

def finalize_state_timing(state: SQLRAGState, agent_name: str, end_time: datetime) -> SQLRAGState:
    """Finalize timing for an agent"""
    if agent_name in state["timings"]:
        state["timings"][agent_name].end_time = end_time
    return state

def add_agent_flow_log(state: SQLRAGState, agent_name: str, input_data: Dict[str, Any], 
                      output_data: Dict[str, Any], status: str = "success", error: Optional[str] = None) -> SQLRAGState:
    """Add agent flow log entry"""
    log_entry = {
        "agent": agent_name.upper(),
        "input": input_data,
        "output": output_data,
        "timing_ms": state["timings"].get(agent_name, AgentTiming(datetime.now())).duration_ms,
        "status": status
    }
    
    if error:
        log_entry["error"] = error
    
    state["agent_flow"].append(log_entry)
    return state

def add_error_to_state(state: SQLRAGState, agent_name: str, error_message: str) -> SQLRAGState:
    """Add error to state and update flow"""
    state["errors"].append(f"{agent_name} error: {error_message}")
    state["should_continue"] = False
    
    # Add error to agent flow
    add_agent_flow_log(
        state, 
        agent_name, 
        {"query": state["query"]}, 
        {}, 
        status="error", 
        error=error_message
    )
    
    return state
