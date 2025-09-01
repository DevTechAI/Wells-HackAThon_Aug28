# backend/pipeline.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time

@dataclass
class PipelineConfig:
    max_retries: int = 2
    sql_row_limit: int = 200

@dataclass
class PipelineDiagnostics:
    retries: int = 0
    validator_fail_reasons: List[str] = field(default_factory=list)
    executor_errors: List[str] = field(default_factory=list)
    timings_ms: Dict[str, int] = field(default_factory=dict)
    generated_sql: Optional[str] = None
    final_sql: Optional[str] = None
    chosen_tables: List[str] = field(default_factory=list)

class NL2SQLPipeline:
    def __init__(self, planner, retriever, generator, validator, executor, summarizer,
                 schema_tables: Dict[str, List[str]], config: PipelineConfig = PipelineConfig()):
        self.planner = planner
        self.retriever = retriever
        self.generator = generator
        self.validator = validator
        self.executor = executor
        self.summarizer = summarizer
        self.schema_tables = schema_tables
        self.cfg = config

    def run(self, nl_query: str, clarified_values: Optional[Dict[str, Any]] = None, 
            user: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        print(f"\n{'='*60}")
        print(f"🚀 ORCHESTRATOR: Starting pipeline execution")
        print(f"📝 Query: {nl_query}")
        print(f"{'='*60}")
        
        diag = PipelineDiagnostics()
        start_all = time.time()
        
        # Store agent flow for UI display
        agent_flow = []
        
        # 1) Plan
        print(f"\n🔄 ORCHESTRATOR: Transferring control to PLANNER AGENT")
        print(f"📋 INPUT to PLANNER: query='{nl_query}'")
        t0 = time.time()
        plan = self.planner.analyze_query(nl_query)
        diag.timings_ms["planning"] = int((time.time() - t0) * 1000)
        diag.chosen_tables = plan.get("tables", [])
        
        # Log planner output
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
        
        print(f"✅ ORCHESTRATOR: PLANNER AGENT returned control")
        print(f"📊 PLANNER OUTPUT: tables={diag.chosen_tables}, capabilities={plan.get('capabilities', [])}")
        print(f"📊 PLANNER OUTPUT: clarifications={plan.get('clarifications', [])}")
        print(f"⏱️ PLANNER timing: {diag.timings_ms['planning']}ms")
        
        # If planner emitted clarifications and user didn't provide them -> return clarifications to UI
        clar = plan.get("clarifications", [])
        if clar and not clarified_values:
            print(f"⚠️ ORCHESTRATOR: PLANNER requested clarifications - stopping pipeline")
            print(f"❓ Clarifications needed: {clar}")
            return {"needs_clarification": True, "clarifications": clar, "diagnostics": diag.__dict__}

        # 2) Retrieve context
        print(f"\n🔄 ORCHESTRATOR: Transferring control to RETRIEVER AGENT")
        print(f"🔍 INPUT to RETRIEVER: query='{nl_query}', schema_tables={list(self.schema_tables.keys())}")
        t1 = time.time()
        ctx_bundle = self.retriever.retrieve(nl_query, self.schema_tables)
        diag.timings_ms["retrieval"] = int((time.time() - t1) * 1000)
        
        # Log retriever output with detailed ChromaDB and Ollama interactions
        retriever_output = {
            "agent": "RETRIEVER",
            "input": {
                "query": nl_query,
                "available_tables": list(self.schema_tables.keys())
            },
            "output": {
                "schema_context_count": len(ctx_bundle.get('schema_context', [])),
                "schema_context_preview": ctx_bundle.get('schema_context', [])[:3],  # First 3 items
                "value_hints_count": len(ctx_bundle.get('value_hints', {})),
                "exemplars_count": len(ctx_bundle.get('exemplars', [])),
                "retrieval_method": ctx_bundle.get('retrieval_method', 'unknown'),
                "chromadb_interactions": ctx_bundle.get('chromadb_interactions', {}),
                "ollama_interactions": ctx_bundle.get('ollama_interactions', {}),
                "vector_search_details": ctx_bundle.get('vector_search_details', {})
            },
            "timing_ms": diag.timings_ms["retrieval"]
        }
        agent_flow.append(retriever_output)
        
        print(f"✅ ORCHESTRATOR: RETRIEVER AGENT returned control")
        print(f"📚 RETRIEVER OUTPUT: Retrieved {len(ctx_bundle.get('schema_context', []))} schema items")
        print(f"📚 RETRIEVER OUTPUT: Method={ctx_bundle.get('retrieval_method', 'unknown')}")
        print(f"📚 RETRIEVER OUTPUT: Value hints={len(ctx_bundle.get('value_hints', {}))} items")
        print(f"📚 RETRIEVER OUTPUT: Exemplars={len(ctx_bundle.get('exemplars', []))} items")
        print(f"⏱️ RETRIEVER timing: {diag.timings_ms['retrieval']}ms")

        gen_ctx = {
            "schema_context": ctx_bundle.get("schema_context", []),
            "value_hints": ctx_bundle.get("value_hints", []),
            "exemplars": ctx_bundle.get("exemplars", []),
            "query_analysis": ctx_bundle.get("query_analysis", {}),
            "clarified_values": clarified_values or {}
        }

        # 3) Generate SQL
        print(f"\n🔄 ORCHESTRATOR: Transferring control to SQL GENERATOR AGENT")
        print(f"🧠 INPUT to SQL GENERATOR: query='{nl_query}'")
        print(f"🧠 INPUT to SQL GENERATOR: schema_context_count={len(gen_ctx.get('schema_context', []))}")
        print(f"🧠 INPUT to SQL GENERATOR: value_hints_count={len(gen_ctx.get('value_hints', []))}")
        print(f"🧠 INPUT to SQL GENERATOR: exemplars_count={len(gen_ctx.get('exemplars', []))}")
        print(f"🧠 INPUT to SQL GENERATOR: query_analysis_keys={list(gen_ctx.get('query_analysis', {}).keys())}")
        
        # Show some sample value hints
        value_hints = gen_ctx.get('value_hints', [])
        if value_hints:
            print(f"🎯 SAMPLE VALUE HINTS:")
            for i, hint in enumerate(value_hints[:3]):  # Show first 3
                if isinstance(hint, dict):
                    if 'table' in hint and 'column' in hint:
                        print(f"  {i+1}. {hint['table']}.{hint['column']}: {hint.get('values', [])[:3]}...")
                    elif 'type' in hint:
                        print(f"  {i+1}. {hint['type']}: {hint.get('value', 'N/A')}")
        t2 = time.time()
        sql = self.generator.generate(nl_query, {}, gen_ctx, self.schema_tables)
        diag.generated_sql = sql
        diag.timings_ms["generation"] = int((time.time() - t2) * 1000)
        
        # Log SQL generator output
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
        
        print(f"✅ ORCHESTRATOR: SQL GENERATOR AGENT returned control")
        print(f"🔧 SQL GENERATOR OUTPUT: SQL='{sql}'")
        print(f"🔧 SQL GENERATOR OUTPUT: SQL length={len(sql)} characters")
        print(f"🔧 SQL GENERATOR OUTPUT: Used special handler={sql_generator_output['output']['used_special_handler']}")
        print(f"🔧 SQL GENERATOR OUTPUT: Used fallback={sql_generator_output['output']['used_fallback']}")
        print(f"⏱️ SQL GENERATOR timing: {diag.timings_ms['generation']}ms")

        attempts = 0
        last_error = None
        while attempts <= self.cfg.max_retries:
            # 4) Validate
            print(f"\n🔄 ORCHESTRATOR: Transferring control to VALIDATOR AGENT (attempt {attempts + 1})")
            print(f"🔍 INPUT to VALIDATOR: sql='{sql[:100]}{'...' if len(sql) > 100 else ''}'")
            print(f"🔍 INPUT to VALIDATOR: schema_tables={list(self.schema_tables.keys())}")
            t3 = time.time()
            ok, reason = self.validator.is_safe(sql, self.schema_tables, user, ip_address)
            diag.timings_ms.setdefault("validation", 0)
            diag.timings_ms["validation"] += int((time.time() - t3) * 1000)
            
            # Get detailed validation report including security guard info
            validation_report = self.validator.get_validation_report(sql, user, ip_address)
            
            # Log validator output
            validator_output = {
                "agent": "VALIDATOR",
                "attempt": attempts + 1,
                "input": {
                    "sql": sql,
                    "schema_tables": list(self.schema_tables.keys()),
                    "user": user,
                    "ip_address": ip_address
                },
                "output": {
                    "is_safe": ok,
                    "reason": reason,
                    "validation_passed": ok,
                    "validation_details": validation_report.get("details", {}),
                    "security_events": validation_report.get("security_events", [])
                },
                "timing_ms": diag.timings_ms["validation"]
            }
            agent_flow.append(validator_output)

            if not ok:
                print(f"❌ ORCHESTRATOR: VALIDATOR AGENT rejected SQL")
                print(f"⚠️ VALIDATOR OUTPUT: Validation failed - {reason}")
                print(f"⏱️ VALIDATOR timing: {diag.timings_ms['validation']}ms")
                diag.validator_fail_reasons.append(reason or "unknown")
                attempts += 1
                diag.retries = attempts
                if attempts > self.cfg.max_retries:
                    print(f"❌ ORCHESTRATOR: Max retries ({self.cfg.max_retries}) reached - stopping")
                    break
                print(f"🔄 ORCHESTRATOR: Transferring control back to SQL GENERATOR AGENT for repair")
                print(f"🔧 Calling: generator.repair_sql(hint='{reason}')")
                # ask generator to repair (provide hint/reason)
                sql = self.generator.repair_sql(nl_query, gen_ctx, hint=reason)
                print(f"✅ ORCHESTRATOR: SQL GENERATOR AGENT returned repaired SQL")
                print(f"🔧 Repaired SQL: {sql}")
                continue

            print(f"✅ ORCHESTRATOR: VALIDATOR AGENT approved SQL")
            print(f"✅ VALIDATOR OUTPUT: Validation passed")
            print(f"⏱️ VALIDATOR timing: {diag.timings_ms['validation']}ms")

            # 5) Execute
            print(f"\n🔄 ORCHESTRATOR: Transferring control to EXECUTOR AGENT")
            print(f"⚡ INPUT to EXECUTOR: sql='{sql[:100]}{'...' if len(sql) > 100 else ''}'")
            print(f"⚡ INPUT to EXECUTOR: limit={self.cfg.sql_row_limit}")
            t4 = time.time()
            exec_result = self.executor.run_query(sql, limit=self.cfg.sql_row_limit)
            diag.timings_ms["execution"] = int((time.time() - t4) * 1000)
            
            # Log executor output
            executor_output = {
                "agent": "EXECUTOR",
                "input": {
                    "sql": sql,
                    "limit": self.cfg.sql_row_limit
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
                print(f"✅ ORCHESTRATOR: EXECUTOR AGENT returned control")
                print(f"📊 EXECUTOR OUTPUT: Execution successful! Found {len(exec_result.get('results', []))} rows")
                print(f"⏱️ EXECUTOR timing: {diag.timings_ms['execution']}ms")
                diag.final_sql = sql
                diag.retries = attempts
                
                # Clean up database connection after successful execution
                try:
                    self.executor.cleanup_connection()
                    print(f"🧹 ORCHESTRATOR: Database connection cleaned up after successful execution")
                except Exception as cleanup_error:
                    print(f"⚠️ ORCHESTRATOR: Error during connection cleanup: {cleanup_error}")
                
                # 6) Summarize
                print(f"\n🔄 ORCHESTRATOR: Transferring control to SUMMARIZER AGENT")
                print(f"📝 INPUT to SUMMARIZER: query='{nl_query}'")
                print(f"📝 INPUT to SUMMARIZER: results_count={len(exec_result.get('results', []))}")
                t5 = time.time()
                out = self.summarizer.summarize(nl_query, exec_result)
                diag.timings_ms["summarization"] = int((time.time() - t5) * 1000)
                
                # Log summarizer output
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
                
                print(f"✅ ORCHESTRATOR: SUMMARIZER AGENT returned control")
                print(f"📝 SUMMARIZER OUTPUT: Summary length={len(out.get('summary', ''))} characters")
                print(f"📝 SUMMARIZER OUTPUT: Has suggestions={summarizer_output['output']['has_suggestions']}")
                print(f"⏱️ SUMMARIZER timing: {diag.timings_ms['summarization']}ms")
                
                out["sql"] = sql
                out["diagnostics"] = diag.__dict__
                out["success"] = True
                out["generated_sql"] = diag.generated_sql
                out["agent_flow"] = agent_flow  # Add agent flow to output
                
                # Add planner suggestions if available
                if hasattr(self, 'planner') and hasattr(self.planner, 'analyze_query'):
                    print(f"🔄 ORCHESTRATOR: Getting follow-up suggestions from PLANNER AGENT")
                    plan = self.planner.analyze_query(nl_query)
                    if plan.get("follow_up_suggestions"):
                        out["suggestions"] = plan["follow_up_suggestions"]
                        print(f"💡 Generated {len(plan['follow_up_suggestions'])} follow-up suggestions")
                
                total_time = int((time.time() - start_all) * 1000)
                print(f"\n{'='*60}")
                print(f"🎉 ORCHESTRATOR: Pipeline completed successfully in {total_time}ms")
                print(f"📊 Final result: Success=True, SQL generated, Results found")
                print(f"{'='*60}")
                return out

            # If execution failed, try repair
            err = exec_result.get("error", "unknown")
            print(f"❌ ORCHESTRATOR: EXECUTOR AGENT failed")
            print(f"⚠️ Execution failed: {err}")
            diag.executor_errors.append(err)
            last_error = err
            attempts += 1
            diag.retries = attempts
            
            # Clean up database connection after failed execution
            try:
                self.executor.cleanup_connection()
                print(f"🧹 ORCHESTRATOR: Database connection cleaned up after failed execution")
            except Exception as cleanup_error:
                print(f"⚠️ ORCHESTRATOR: Error during connection cleanup: {cleanup_error}")
            
            if attempts > self.cfg.max_retries:
                print(f"❌ ORCHESTRATOR: Max retries ({self.cfg.max_retries}) reached - stopping")
                break
            print(f"🔄 ORCHESTRATOR: Transferring control back to SQL GENERATOR AGENT for repair")
            print(f"🔧 Calling: generator.repair_sql(hint='{err}')")
            sql = self.generator.repair_sql(nl_query, gen_ctx, hint=err)
            print(f"✅ ORCHESTRATOR: SQL GENERATOR AGENT returned repaired SQL")
            print(f"🔧 Repaired SQL: {sql}")

        # Failed after retries
        total_ms = int((time.time() - start_all) * 1000)
        diag.timings_ms["total"] = total_ms
        print(f"\n{'='*60}")
        print(f"❌ ORCHESTRATOR: Pipeline failed after {total_ms}ms")
        print(f"🔍 Last error: {last_error}")
        print(f"🔄 Total attempts: {attempts}")
        print(f"{'='*60}")
        return {
            "success": False,
            "error": last_error or "Could not produce safe SQL",
            "sql": sql,
            "diagnostics": diag.__dict__,
        }
