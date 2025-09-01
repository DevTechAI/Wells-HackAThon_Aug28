#!/usr/bin/env python3
"""
LangGraph Agents for SQL RAG Agent
LLM-neutral agent nodes for LangGraph workflow
"""

import time
from datetime import datetime
from typing import Dict, Any, Optional
import logging

from langgraph.graph import StateGraph, END
from .langgraph_state import SQLRAGState, update_state_timing, finalize_state_timing, add_agent_flow_log, add_error_to_state
from .llm_config import llm_config
from .llm_embedder import EnhancedRetriever
from .llm_sql_generator import LLMSQLGenerator
from .planner import PlannerAgent
from .validator import ValidatorAgent
from .executor import ExecutorAgent
from .summarizer import SummarizerAgent

logger = logging.getLogger(__name__)

class LangGraphAgents:
    """LangGraph agent nodes for SQL RAG workflow"""
    
    def __init__(self, schema_tables: Dict[str, Any], db_path: str = "banking.db"):
        self.schema_tables = schema_tables
        self.db_path = db_path
        
        # Initialize LLM components
        self.llm_provider = llm_config.get_default_provider()
        self.llm_api_key = llm_config.get_api_key(self.llm_provider)
        
        # Initialize agents
        self.planner = PlannerAgent(schema_tables)
        self.retriever = EnhancedRetriever(
            provider=self.llm_provider,
            api_key=self.llm_api_key,
            model_name=llm_config.get_default_embedding_model()
        )
        self.sql_generator = LLMSQLGenerator(
            provider=self.llm_provider,
            api_key=self.llm_api_key,
            model_name=llm_config.get_default_model()
        )
        self.validator = ValidatorAgent(schema_tables)
        self.executor = ExecutorAgent(db_path)
        self.summarizer = SummarizerAgent()
        
        logger.info(f"🤖 LangGraph Agents initialized with {self.llm_provider} provider")
    
    def planner_node(self, state: SQLRAGState) -> SQLRAGState:
        """Planner agent node"""
        logger.info("📋 Planner Node: Starting query analysis")
        
        # Start timing
        state = update_state_timing(state, "planner", datetime.now())
        
        try:
            # Call existing planner
            plan = self.planner.analyze_query(state["query"])
            
            # Check for clarifications
            clarifications = plan.get("clarifications", [])
            if clarifications:
                state["needs_clarification"] = True
                state["clarification_questions"] = clarifications
                state["should_continue"] = False
                logger.info("⚠️ Planner Node: Clarifications needed")
            else:
                state["plan"] = plan
                state["should_continue"] = True
                logger.info("✅ Planner Node: Plan generated successfully")
            
            # End timing
            state = finalize_state_timing(state, "planner", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "planner",
                {"query": state["query"]},
                plan,
                status="success" if state["should_continue"] else "clarification_needed"
            )
            
        except Exception as e:
            state = add_error_to_state(state, "planner", str(e))
            logger.error(f"❌ Planner Node: Error - {e}")
        
        return state
    
    def retriever_node(self, state: SQLRAGState) -> SQLRAGState:
        """Retriever agent node"""
        logger.info("🔍 Retriever Node: Starting context retrieval")
        
        # Start timing
        state = update_state_timing(state, "retriever", datetime.now())
        
        try:
            # Call enhanced retriever
            context = self.retriever.retrieve_context_with_details(state["query"])
            state["context"] = context
            
            # End timing
            state = finalize_state_timing(state, "retriever", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "retriever",
                {"query": state["query"], "plan": state["plan"]},
                context,
                status="success"
            )
            
            logger.info("✅ Retriever Node: Context retrieved successfully")
            
        except Exception as e:
            state = add_error_to_state(state, "retriever", str(e))
            logger.error(f"❌ Retriever Node: Error - {e}")
        
        return state
    
    def sql_generator_node(self, state: SQLRAGState) -> SQLRAGState:
        """SQL Generator agent node"""
        logger.info("🔧 SQL Generator Node: Starting SQL generation")
        
        # Start timing
        state = update_state_timing(state, "sql_generator", datetime.now())
        
        try:
            # Prepare generation context
            gen_ctx = {
                "schema_context": state["context"].get("schema_context", []),
                "value_hints": state["context"].get("value_hints", []),
                "exemplars": state["context"].get("exemplars", []),
                "query_analysis": state["context"].get("query_analysis", {}),
                "schema_tables": self.schema_tables
            }
            
            # Call SQL generator
            sql = self.sql_generator.generate_sql(state["query"], gen_ctx)
            state["sql"] = sql
            
            # End timing
            state = finalize_state_timing(state, "sql_generator", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "sql_generator",
                {"query": state["query"], "context": gen_ctx},
                {"sql": sql},
                status="success"
            )
            
            logger.info("✅ SQL Generator Node: SQL generated successfully")
            
        except Exception as e:
            state = add_error_to_state(state, "sql_generator", str(e))
            logger.error(f"❌ SQL Generator Node: Error - {e}")
        
        return state
    
    def validator_node(self, state: SQLRAGState) -> SQLRAGState:
        """Validator agent node"""
        logger.info("✅ Validator Node: Starting SQL validation")
        
        # Start timing
        state = update_state_timing(state, "validator", datetime.now())
        
        try:
            # Call validator
            is_valid, reason, details = self.validator.is_safe_sql(state["sql"])
            validation_result = {"valid": is_valid, "reason": reason}
            state["validation_result"] = validation_result
            
            if not is_valid:
                state["errors"].append(f"Validation failed: {reason}")
                state["retry_count"] += 1
                logger.info(f"❌ Validator Node: SQL validation failed - {reason}")
            else:
                logger.info("✅ Validator Node: SQL validation passed")
            
            # End timing
            state = finalize_state_timing(state, "validator", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "validator",
                {"sql": state["sql"]},
                validation_result,
                status="success" if is_valid else "failed"
            )
            
        except Exception as e:
            state = add_error_to_state(state, "validator", str(e))
            logger.error(f"❌ Validator Node: Error - {e}")
        
        return state
    
    def executor_node(self, state: SQLRAGState) -> SQLRAGState:
        """Executor agent node"""
        logger.info("⚡ Executor Node: Starting SQL execution")
        
        # Start timing
        state = update_state_timing(state, "executor", datetime.now())
        
        try:
            # Call executor
            results = self.executor.run_query(state["sql"], limit=100)
            state["results"] = results
            
            # End timing
            state = finalize_state_timing(state, "executor", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "executor",
                {"sql": state["sql"]},
                {"results": results},
                status="success"
            )
            
            logger.info("✅ Executor Node: SQL executed successfully")
            
        except Exception as e:
            state = add_error_to_state(state, "executor", str(e))
            logger.error(f"❌ Executor Node: Error - {e}")
        
        return state
    
    def summarizer_node(self, state: SQLRAGState) -> SQLRAGState:
        """Summarizer agent node"""
        logger.info("📝 Summarizer Node: Starting result summarization")
        
        # Start timing
        state = update_state_timing(state, "summarizer", datetime.now())
        
        try:
            # Call summarizer
            summary = self.summarizer.summarize(state["query"], {
                "success": True,
                "results": state["results"]
            })
            state["summary"] = summary
            
            # End timing
            state = finalize_state_timing(state, "summarizer", datetime.now())
            
            # Log agent flow
            state = add_agent_flow_log(
                state, "summarizer",
                {"query": state["query"], "results": state["results"]},
                summary,
                status="success"
            )
            
            logger.info("✅ Summarizer Node: Results summarized successfully")
            
        except Exception as e:
            state = add_error_to_state(state, "summarizer", str(e))
            logger.error(f"❌ Summarizer Node: Error - {e}")
        
        return state
    
    def error_handler_node(self, state: SQLRAGState) -> SQLRAGState:
        """Error handler node"""
        logger.info("🛠️ Error Handler Node: Processing errors")
        
        # Start timing
        state = update_state_timing(state, "error_handler", datetime.now())
        
        # Handle different error scenarios
        if state["retry_count"] < 3 and state["current_agent"] == "validator":
            # Retry SQL generation with repair
            try:
                gen_ctx = {
                    "schema_context": state["context"].get("schema_context", []),
                    "value_hints": state["context"].get("value_hints", []),
                    "exemplars": state["context"].get("exemplars", []),
                    "query_analysis": state["context"].get("query_analysis", {}),
                    "schema_tables": self.schema_tables
                }
                
                hint = state["validation_result"].get("reason", "") if state["validation_result"] else ""
                repaired_sql = self.sql_generator.repair_sql(state["query"], gen_ctx, hint=hint)
                state["sql"] = repaired_sql
                state["should_continue"] = True
                logger.info("🔄 Error Handler Node: SQL repaired, retrying validation")
                
            except Exception as e:
                state = add_error_to_state(state, "error_handler", f"Repair error: {str(e)}")
                state["should_continue"] = False
        else:
            # Max retries reached or other error
            state["should_continue"] = False
            state["summary"] = {
                "summary": f"❌ **Query Failed**\n\n**Your Question:** {state['query']}\n\n**Error:** {'; '.join(state['errors'])}"
            }
            logger.info("❌ Error Handler Node: Max retries reached or unrecoverable error")
        
        # End timing
        state = finalize_state_timing(state, "error_handler", datetime.now())
        
        return state
