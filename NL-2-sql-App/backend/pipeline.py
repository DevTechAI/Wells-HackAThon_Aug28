# backend/pipeline.py
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import time
from .agent_debugger import EnhancedPipelineDebugger

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
        self.debugger = EnhancedPipelineDebugger()

    def run(self, nl_query: str, clarified_values: Optional[Dict[str, Any]] = None, 
            user: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        # Start debug session
        self.debugger.start_query_debug(nl_query)
        
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
        
        # Log planner with debugger
        self.debugger.log_planner(
            input_data={"query": nl_query},
            output_data=plan,
            timing_ms=diag.timings_ms["planning"]
        )
        
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

        # 2) Retrieve context with rich schema metadata
        print(f"\n🔄 ORCHESTRATOR: Transferring control to RETRIEVER AGENT")
        print(f"🔍 INPUT to RETRIEVER: query='{nl_query}', schema_tables={list(self.schema_tables.keys())}")
        t1 = time.time()
        
        # Use enhanced retriever with schema metadata
        ctx_bundle = self.retriever.retrieve_context_with_schema_metadata(
            query=nl_query, 
            tables=diag.chosen_tables,
            n_results=5
        )
        diag.timings_ms["retrieval"] = int((time.time() - t1) * 1000)
        
        # Log retriever with debugger
        self.debugger.log_retriever(
            input_data={
                "query": nl_query,
                "available_tables": list(self.schema_tables.keys()),
                "chosen_tables": diag.chosen_tables
            },
            output_data=ctx_bundle,
            timing_ms=diag.timings_ms["retrieval"]
        )
        
        print(f"✅ ORCHESTRATOR: RETRIEVER AGENT returned control")
        print(f"📚 RETRIEVER OUTPUT: Retrieved {len(ctx_bundle.get('schema_context', []))} schema items")
        print(f"📚 RETRIEVER OUTPUT: Schema metadata for {len(ctx_bundle.get('schema_metadata', {}))} tables")
        print(f"📚 RETRIEVER OUTPUT: Distinct values for {len(ctx_bundle.get('distinct_values', {}))} tables")
        print(f"📚 RETRIEVER OUTPUT: WHERE suggestions for {len(ctx_bundle.get('where_suggestions', {}))} tables")
        print(f"⏱️ RETRIEVER timing: {diag.timings_ms['retrieval']}ms")
        
        # 3) Enhanced planning with schema metadata
        print(f"\n🔄 ORCHESTRATOR: Transferring control to PLANNER AGENT (Enhanced)")
        print(f"📋 INPUT to PLANNER: query='{nl_query}', schema_context=rich_metadata")
        t2 = time.time()
        
        # Use enhanced planner with schema context
        enhanced_plan = self.planner.plan_with_schema_metadata(nl_query, ctx_bundle)
        diag.timings_ms["enhanced_planning"] = int((time.time() - t2) * 1000)
        
        # Log enhanced planner with debugger
        self.debugger.log_planner(
            input_data={
                "query": nl_query,
                "schema_context": ctx_bundle
            },
            output_data=enhanced_plan,
            timing_ms=diag.timings_ms["enhanced_planning"]
        )
        
        print(f"✅ ORCHESTRATOR: ENHANCED PLANNER AGENT returned control")
        print(f"📊 ENHANCED PLANNER OUTPUT: Table details for {len(enhanced_plan.get('table_details', {}))} tables")
        print(f"📊 ENHANCED PLANNER OUTPUT: Column mappings for {len(enhanced_plan.get('column_mappings', {}))} tables")
        print(f"📊 ENHANCED PLANNER OUTPUT: WHERE conditions: {len(enhanced_plan.get('where_conditions', []))}")
        print(f"📊 ENHANCED PLANNER OUTPUT: JOIN requirements: {len(enhanced_plan.get('join_requirements', []))}")
        print(f"📊 ENHANCED PLANNER OUTPUT: Value constraints for {len(enhanced_plan.get('value_constraints', {}))} tables")
        print(f"⏱️ ENHANCED PLANNER timing: {diag.timings_ms['enhanced_planning']}ms")

        gen_ctx = {
            "schema_context": ctx_bundle.get("schema_context", []),
            "value_hints": ctx_bundle.get("value_hints", []),
            "exemplars": ctx_bundle.get("exemplars", []),
            "query_analysis": ctx_bundle.get("query_analysis", {}),
            "clarified_values": clarified_values or {}
        }

        # 4) Generate SQL with enhanced schema context
        print(f"\n🔄 ORCHESTRATOR: Transferring control to SQL GENERATOR AGENT (Enhanced)")
        print(f"🧠 INPUT to SQL GENERATOR: query='{nl_query}'")
        print(f"🧠 INPUT to SQL GENERATOR: schema_metadata_count={len(ctx_bundle.get('schema_metadata', {}))}")
        print(f"🧠 INPUT to SQL GENERATOR: distinct_values_count={len(ctx_bundle.get('distinct_values', {}))}")
        print(f"🧠 INPUT to SQL GENERATOR: where_suggestions_count={len(ctx_bundle.get('where_suggestions', {}))}")
        print(f"🧠 INPUT to SQL GENERATOR: enhanced_plan_keys={list(enhanced_plan.keys())}")
        
        # Show sample distinct values and WHERE suggestions
        distinct_values = ctx_bundle.get('distinct_values', {})
        if distinct_values:
            print(f"🎯 SAMPLE DISTINCT VALUES:")
            for table_name, columns in list(distinct_values.items())[:2]:  # Show first 2 tables
                for column_name, values in list(columns.items())[:2]:  # Show first 2 columns
                    print(f"  {table_name}.{column_name}: {values[:3]}...")
        
        where_suggestions = ctx_bundle.get('where_suggestions', {})
        if where_suggestions:
            print(f"🎯 SAMPLE WHERE SUGGESTIONS:")
            for table_name, suggestions in list(where_suggestions.items())[:2]:  # Show first 2 tables
                print(f"  {table_name}: {suggestions[:2]}...")
        
        t3 = time.time()
        
        # Use enhanced SQL generator with schema context
        sql = self.generator.generate_sql_with_schema_context(nl_query, ctx_bundle, enhanced_plan)
        diag.generated_sql = sql
        diag.timings_ms["generation"] = int((time.time() - t3) * 1000)
        
        # Log enhanced SQL generator with debugger
        self.debugger.log_sql_generator(
            input_data={
                "query": nl_query,
                "schema_metadata_count": len(ctx_bundle.get('schema_metadata', {})),
                "distinct_values_count": len(ctx_bundle.get('distinct_values', {})),
                "where_suggestions_count": len(ctx_bundle.get('where_suggestions', {})),
                "enhanced_plan_keys": list(enhanced_plan.keys())
            },
            output_data={
                "generated_sql": sql,
                "used_schema_context": len(ctx_bundle.get('schema_metadata', {})) > 0,
                "used_distinct_values": len(ctx_bundle.get('distinct_values', {})) > 0,
                "used_where_suggestions": len(ctx_bundle.get('where_suggestions', {})) > 0
            },
            timing_ms=diag.timings_ms["generation"]
        )
        
        print(f"✅ ORCHESTRATOR: ENHANCED SQL GENERATOR AGENT returned control")
        print(f"🔧 ENHANCED SQL GENERATOR OUTPUT: SQL='{sql[:100]}{'...' if len(sql) > 100 else ''}'")
        print(f"🔧 ENHANCED SQL GENERATOR OUTPUT: SQL length={len(sql)} characters")
        print(f"🔧 ENHANCED SQL GENERATOR OUTPUT: Used schema context={len(ctx_bundle.get('schema_metadata', {})) > 0}")
        print(f"🔧 ENHANCED SQL GENERATOR OUTPUT: Used distinct values={len(ctx_bundle.get('distinct_values', {})) > 0}")
        print(f"🔧 ENHANCED SQL GENERATOR OUTPUT: Used WHERE suggestions={len(ctx_bundle.get('where_suggestions', {})) > 0}")
        print(f"⏱️ ENHANCED SQL GENERATOR timing: {diag.timings_ms['generation']}ms")

        attempts = 0
        last_error = None
        while attempts <= self.cfg.max_retries:
            # 5) Validate
            print(f"\n🔄 ORCHESTRATOR: Transferring control to VALIDATOR AGENT (attempt {attempts + 1})")
            print(f"🔍 INPUT to VALIDATOR: sql='{sql[:100]}{'...' if len(sql) > 100 else ''}'")
            print(f"🔍 INPUT to VALIDATOR: schema_tables={list(self.schema_tables.keys())}")
            t3 = time.time()
            ok, reason = self.validator.is_safe(sql, self.schema_tables, user, ip_address)
            diag.timings_ms.setdefault("validation", 0)
            diag.timings_ms["validation"] += int((time.time() - t3) * 1000)
            
            # Get detailed validation report including security guard info
            validation_report = self.validator.get_validation_report(sql, user, ip_address)
            
            # Log validator with debugger
            self.debugger.log_validator(
                input_data={
                    "sql": sql,
                    "schema_tables": list(self.schema_tables.keys()),
                    "user": user,
                    "ip_address": ip_address
                },
                output_data={
                    "is_safe": ok,
                    "reason": reason,
                    "validation_passed": ok,
                    "validation_details": validation_report.get("details", {}),
                    "security_events": validation_report.get("security_events", [])
                },
                timing_ms=diag.timings_ms["validation"],
                attempt=attempts + 1
            )

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
            
            # Log executor with debugger
            self.debugger.log_executor(
                input_data={
                    "sql": sql,
                    "limit": self.cfg.sql_row_limit
                },
                output_data={
                    "success": exec_result.get("success", False),
                    "results": exec_result.get("results", []),
                    "error": exec_result.get("error", None),
                    "execution_time_ms": diag.timings_ms["execution"]
                },
                timing_ms=diag.timings_ms["execution"]
            )

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
                
                # Log summarizer with debugger
                self.debugger.log_summarizer(
                    input_data={
                        "query": nl_query,
                        "results_count": len(exec_result.get('results', [])),
                        "execution_success": exec_result.get("success", False)
                    },
                    output_data=out,
                    timing_ms=diag.timings_ms["summarization"]
                )
                
                print(f"✅ ORCHESTRATOR: SUMMARIZER AGENT returned control")
                print(f"📝 SUMMARIZER OUTPUT: Summary length={len(out.get('summary', ''))} characters")
                print(f"📝 SUMMARIZER OUTPUT: Has suggestions={'suggestions' in out}")
                print(f"⏱️ SUMMARIZER timing: {diag.timings_ms['summarization']}ms")
                
                out["sql"] = sql
                out["diagnostics"] = diag.__dict__
                out["success"] = True
                out["generated_sql"] = diag.generated_sql
                out["agent_flow"] = agent_flow  # Add agent flow to output
                
                # Add debug report
                debug_report = self.debugger.get_debug_report()
                out["debug_report"] = debug_report
                
                # Print final debug summary
                self.debugger.print_final_summary()
                
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
