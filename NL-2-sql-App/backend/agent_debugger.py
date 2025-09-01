#!/usr/bin/env python3
"""
Agent Debugger - Comprehensive debugging system for agent workflow
Captures detailed input/output JSON for each agent to help with troubleshooting
"""

import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AgentDebugger:
    """Comprehensive debugging system for agent workflow"""
    
    def __init__(self):
        self.debug_session = {
            "session_id": f"debug_{int(time.time())}",
            "start_time": datetime.now().isoformat(),
            "agents": [],
            "total_timing": 0,
            "errors": [],
            "warnings": []
        }
    
    def log_agent_step(self, agent_name: str, step_name: str, 
                       input_data: Dict[str, Any], output_data: Dict[str, Any],
                       timing_ms: int, status: str = "success", error: Optional[str] = None):
        """Log a single agent step with detailed input/output"""
        
        agent_log = {
            "agent": agent_name,
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "timing_ms": timing_ms,
            "status": status,
            "input": self._sanitize_data(input_data),
            "output": self._sanitize_data(output_data),
            "error": error
        }
        
        self.debug_session["agents"].append(agent_log)
        
        # Log to console for immediate feedback
        self._print_agent_log(agent_log)
    
    def _sanitize_data(self, data: Any) -> Any:
        """Sanitize data for JSON serialization"""
        if isinstance(data, dict):
            return {k: self._sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._sanitize_data(item) for item in data]
        elif hasattr(data, '__dict__'):
            return str(data)
        else:
            return data
    
    def _print_agent_log(self, agent_log: Dict[str, Any]):
        """Print agent log in a formatted way"""
        print(f"\n{'='*80}")
        print(f"🔍 AGENT DEBUG: {agent_log['agent']} - {agent_log['step']}")
        print(f"⏱️ Timing: {agent_log['timing_ms']}ms | Status: {agent_log['status']}")
        print(f"{'='*80}")
        
        # Print input
        print(f"📥 INPUT:")
        print(json.dumps(agent_log['input'], indent=2, default=str))
        
        # Print output
        print(f"📤 OUTPUT:")
        print(json.dumps(agent_log['output'], indent=2, default=str))
        
        if agent_log.get('error'):
            print(f"❌ ERROR: {agent_log['error']}")
        
        print(f"{'='*80}\n")
    
    def get_debug_report(self) -> Dict[str, Any]:
        """Get comprehensive debug report"""
        self.debug_session["end_time"] = datetime.now().isoformat()
        self.debug_session["total_timing"] = sum(agent["timing_ms"] for agent in self.debug_session["agents"])
        
        return {
            "debug_session": self.debug_session,
            "agent_summary": self._generate_agent_summary(),
            "timing_breakdown": self._generate_timing_breakdown(),
            "error_summary": self._generate_error_summary()
        }
    
    def _generate_agent_summary(self) -> Dict[str, Any]:
        """Generate summary of all agents"""
        summary = {}
        for agent_log in self.debug_session["agents"]:
            agent_name = agent_log["agent"]
            if agent_name not in summary:
                summary[agent_name] = {
                    "total_calls": 0,
                    "total_timing_ms": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "steps": []
                }
            
            summary[agent_name]["total_calls"] += 1
            summary[agent_name]["total_timing_ms"] += agent_log["timing_ms"]
            summary[agent_name]["steps"].append({
                "step": agent_log["step"],
                "status": agent_log["status"],
                "timing_ms": agent_log["timing_ms"]
            })
            
            if agent_log["status"] == "success":
                summary[agent_name]["success_count"] += 1
            else:
                summary[agent_name]["error_count"] += 1
        
        return summary
    
    def _generate_timing_breakdown(self) -> Dict[str, Any]:
        """Generate timing breakdown by agent"""
        timing = {}
        for agent_log in self.debug_session["agents"]:
            agent_name = agent_log["agent"]
            if agent_name not in timing:
                timing[agent_name] = 0
            timing[agent_name] += agent_log["timing_ms"]
        
        # Sort by timing
        timing = dict(sorted(timing.items(), key=lambda x: x[1], reverse=True))
        return timing
    
    def _generate_error_summary(self) -> List[Dict[str, Any]]:
        """Generate error summary"""
        errors = []
        for agent_log in self.debug_session["agents"]:
            if agent_log.get("error"):
                errors.append({
                    "agent": agent_log["agent"],
                    "step": agent_log["step"],
                    "error": agent_log["error"],
                    "timestamp": agent_log["timestamp"]
                })
        return errors

class EnhancedPipelineDebugger:
    """Enhanced pipeline debugger with specific agent tracking"""
    
    def __init__(self):
        self.debugger = AgentDebugger()
        self.current_query = None
    
    def start_query_debug(self, query: str):
        """Start debugging for a new query"""
        self.current_query = query
        self.debugger = AgentDebugger()
        self.debugger.debug_session["query"] = query
        print(f"\n🚀 DEBUG SESSION STARTED")
        print(f"📝 Query: {query}")
        print(f"🆔 Session ID: {self.debugger.debug_session['session_id']}")
    
    def log_planner(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int):
        """Log planner agent details"""
        self.debugger.log_agent_step(
            agent_name="PLANNER",
            step_name="query_analysis",
            input_data={
                "query": input_data.get("query", ""),
                "query_length": len(input_data.get("query", ""))
            },
            output_data={
                "tables_needed": output_data.get("tables", []),
                "operations": output_data.get("operations", []),
                "complexity": output_data.get("complexity", "unknown"),
                "clarifications": output_data.get("clarifications", []),
                "estimated_tokens": output_data.get("estimated_tokens", 0)
            },
            timing_ms=timing_ms
        )
    
    def log_retriever(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int):
        """Log retriever agent details"""
        self.debugger.log_agent_step(
            agent_name="RETRIEVER",
            step_name="context_retrieval",
            input_data={
                "query": input_data.get("query", ""),
                "available_tables": input_data.get("available_tables", [])
            },
            output_data={
                "schema_context_count": len(output_data.get("schema_context", [])),
                "value_hints_count": len(output_data.get("value_hints", {})),
                "exemplars_count": len(output_data.get("exemplars", [])),
                "retrieval_method": output_data.get("retrieval_method", "unknown"),
                "chromadb_interactions": output_data.get("chromadb_interactions", {})
            },
            timing_ms=timing_ms
        )
    
    def log_sql_generator(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int):
        """Log SQL generator agent details"""
        self.debugger.log_agent_step(
            agent_name="SQL_GENERATOR",
            step_name="sql_generation",
            input_data={
                "query": input_data.get("query", ""),
                "schema_context_count": input_data.get("schema_context_count", 0),
                "value_hints_count": input_data.get("value_hints_count", 0),
                "exemplars_count": input_data.get("exemplars_count", 0)
            },
            output_data={
                "generated_sql": output_data.get("generated_sql", ""),
                "sql_length": len(output_data.get("generated_sql", "")),
                "used_special_handler": output_data.get("used_special_handler", False),
                "used_fallback": output_data.get("used_fallback", False)
            },
            timing_ms=timing_ms
        )
    
    def log_validator(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int, attempt: int = 1):
        """Log validator agent details"""
        self.debugger.log_agent_step(
            agent_name="VALIDATOR",
            step_name=f"sql_validation_attempt_{attempt}",
            input_data={
                "sql": input_data.get("sql", ""),
                "schema_tables": input_data.get("schema_tables", []),
                "user": input_data.get("user", "unknown"),
                "ip_address": input_data.get("ip_address", "unknown")
            },
            output_data={
                "is_safe": output_data.get("is_safe", False),
                "reason": output_data.get("reason", ""),
                "validation_passed": output_data.get("validation_passed", False),
                "security_events": output_data.get("security_events", [])
            },
            timing_ms=timing_ms,
            status="success" if output_data.get("is_safe", False) else "failed"
        )
    
    def log_executor(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int):
        """Log executor agent details"""
        self.debugger.log_agent_step(
            agent_name="EXECUTOR",
            step_name="sql_execution",
            input_data={
                "sql": input_data.get("sql", ""),
                "limit": input_data.get("limit", 100)
            },
            output_data={
                "success": output_data.get("success", False),
                "results_count": len(output_data.get("results", [])),
                "error": output_data.get("error", None),
                "execution_time_ms": output_data.get("execution_time_ms", 0)
            },
            timing_ms=timing_ms,
            status="success" if output_data.get("success", False) else "failed",
            error=output_data.get("error")
        )
    
    def log_summarizer(self, input_data: Dict[str, Any], output_data: Dict[str, Any], timing_ms: int):
        """Log summarizer agent details"""
        self.debugger.log_agent_step(
            agent_name="SUMMARIZER",
            step_name="result_summarization",
            input_data={
                "query": input_data.get("query", ""),
                "results_count": input_data.get("results_count", 0),
                "execution_success": input_data.get("execution_success", False)
            },
            output_data={
                "summary": output_data.get("summary", ""),
                "summary_length": len(output_data.get("summary", "")),
                "has_suggestions": "suggestions" in output_data,
                "suggestions_count": len(output_data.get("suggestions", []))
            },
            timing_ms=timing_ms
        )
    
    def get_debug_report(self) -> Dict[str, Any]:
        """Get comprehensive debug report"""
        return self.debugger.get_debug_report()
    
    def print_final_summary(self):
        """Print final debug summary"""
        report = self.get_debug_report()
        
        print(f"\n{'='*80}")
        print(f"🎯 FINAL DEBUG SUMMARY")
        print(f"{'='*80}")
        print(f"📝 Query: {self.current_query}")
        print(f"⏱️ Total Time: {report['debug_session']['total_timing']}ms")
        print(f"🤖 Agents Executed: {len(report['debug_session']['agents'])}")
        
        # Agent summary
        print(f"\n📊 AGENT SUMMARY:")
        for agent_name, agent_data in report['agent_summary'].items():
            print(f"  {agent_name}:")
            print(f"    Calls: {agent_data['total_calls']}")
            print(f"    Success: {agent_data['success_count']}")
            print(f"    Errors: {agent_data['error_count']}")
            print(f"    Total Time: {agent_data['total_timing_ms']}ms")
        
        # Timing breakdown
        print(f"\n⏱️ TIMING BREAKDOWN:")
        for agent_name, timing in report['timing_breakdown'].items():
            print(f"  {agent_name}: {timing}ms")
        
        # Error summary
        if report['error_summary']:
            print(f"\n❌ ERROR SUMMARY:")
            for error in report['error_summary']:
                print(f"  {error['agent']} ({error['step']}): {error['error']}")
        
        print(f"{'='*80}")
        
        return report
