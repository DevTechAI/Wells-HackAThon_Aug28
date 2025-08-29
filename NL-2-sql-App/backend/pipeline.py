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

    def run(self, nl_query: str, clarified_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        diag = PipelineDiagnostics()
        start_all = time.time()

        # 1) Plan
        t0 = time.time()
        plan = self.planner.analyze_query(nl_query)
        diag.timings_ms["planning"] = int((time.time() - t0) * 1000)
        diag.chosen_tables = plan.get("tables", [])
        # If planner emitted clarifications and user didn't provide them -> return clarifications to UI
        clar = plan.get("clarifications", [])
        if clar and not clarified_values:
            return {"needs_clarification": True, "clarifications": clar, "diagnostics": diag.__dict__}

        # 2) Retrieve context
        t1 = time.time()
        ctx_bundle = self.retriever.fetch_schema_context(plan.get("tables", []))
        diag.timings_ms["retrieval"] = int((time.time() - t1) * 1000)

        gen_ctx = {
            "schema_context": ctx_bundle.get("schema_context", []),
            "value_hints": ctx_bundle.get("value_hints", {}),
            "exemplars": ctx_bundle.get("exemplars", []),
            "clarified_values": clarified_values or {}
        }

        # 3) Generate SQL
        t2 = time.time()
        sql = self.generator.generate_sql(nl_query, gen_ctx)
        diag.generated_sql = sql
        diag.timings_ms["generation"] = int((time.time() - t2) * 1000)

        attempts = 0
        last_error = None
        while attempts <= self.cfg.max_retries:
            # 4) Validate
            t3 = time.time()
            ok, reason = self.validator.is_safe(sql, self.schema_tables)
            diag.timings_ms.setdefault("validation", 0)
            diag.timings_ms["validation"] += int((time.time() - t3) * 1000)

            if not ok:
                diag.validator_fail_reasons.append(reason or "unknown")
                attempts += 1
                diag.retries = attempts
                if attempts > self.cfg.max_retries:
                    break
                # ask generator to repair (provide hint/reason)
                sql = self.generator.repair_sql(nl_query, gen_ctx, hint=reason)
                continue

            # 5) Execute
            t4 = time.time()
            exec_result = self.executor.run_query(sql, limit=self.cfg.sql_row_limit)
            diag.timings_ms["execution"] = int((time.time() - t4) * 1000)

            if exec_result.get("success"):
                diag.final_sql = sql
                diag.retries = attempts
                # 6) Summarize
                t5 = time.time()
                out = self.summarizer.summarize(nl_query, exec_result)
                diag.timings_ms["summarization"] = int((time.time() - t5) * 1000)
                out["sql"] = sql
                out["diagnostics"] = diag.__dict__
                out["success"] = True
                out["generated_sql"] = diag.generated_sql
                return out

            # If execution failed, try repair
            err = exec_result.get("error", "unknown")
            diag.executor_errors.append(err)
            last_error = err
            attempts += 1
            diag.retries = attempts
            if attempts > self.cfg.max_retries:
                break
            sql = self.generator.repair_sql(nl_query, gen_ctx, hint=err)

        # Failed after retries
        total_ms = int((time.time() - start_all) * 1000)
        diag.timings_ms["total"] = total_ms
        return {
            "success": False,
            "error": last_error or "Could not produce safe SQL",
            "sql": sql,
            "diagnostics": diag.__dict__,
        }
