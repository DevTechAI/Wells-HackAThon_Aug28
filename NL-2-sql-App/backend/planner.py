# backend/planner.py
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

class PlannerAgent:
    """
    PlannerAgent analyzes a natural-language query and returns:
      - tables: list of likely relevant tables
      - steps: ordered actions for pipeline
      - capabilities: short tags (exists, group_by, date_filter, window, etc.)
      - clarifications: if any ambiguity detected (thresholds, date ranges)
      - conversation_state: optional lightweight context to carry across turns
    """
    DATE_WORDS = ["q1", "q2", "q3", "q4", "quarter", "year", "month", "week", "today", "yesterday", "last", "first quarter", "2024", "2025"]
    AGG_WORDS = ["average", "avg", "sum", "count", "total", "number of", "how many"]
    EXISTS_WORDS = ["both", "either", "and", "have both", "have both a", "have both an"]
    WINDOW_WORDS = ["consecutive", "consecutive days", "lag", "lead"]
    WEEKEND_WORDS = ["weekend", "saturday", "sunday"]
    THRESHOLD_WORDS = ["greater than", "less than", "above", "below", "minimum", "max", "at least", "more than"]

    def __init__(self, schema_map: Dict[str, List[str]], conversation_state: Optional[Dict[str, Any]] = None):
        """
        schema_map: {"customers": ["id","first_name",...], "accounts": [...], ...}
        conversation_state: optional prior context (last_tables, last_filters)
        """
        self.schema_map = schema_map
        self.conversation_state = conversation_state or {}

    def _detect_tables(self, text: str) -> List[str]:
        found = []
        tl = text.lower()
        for table in self.schema_map.keys():
            if table.lower() in tl:
                found.append(table)
        # heuristics: mention of "customer", "account", "transaction", "branch", "employee"
        if not found:
            if "customer" in tl: found.extend([t for t in self.schema_map if "customer" in t])
            if "account" in tl: found.extend([t for t in self.schema_map if "account" in t])
            if "transaction" in tl or "transactions" in tl: found.extend([t for t in self.schema_map if "transaction" in t])
            if "employee" in tl or "employees" in tl: found.extend([t for t in self.schema_map if "employee" in t])
            if "branch" in tl or "branches" in tl: found.extend([t for t in self.schema_map if "branch" in t])
        # unique preserving order
        return list(dict.fromkeys(found)) or list(self.schema_map.keys())

    def _detect_capabilities(self, text: str) -> List[str]:
        caps = set()
        tl = text.lower()
        if any(w in tl for w in self.AGG_WORDS): caps.add("aggregate")
        if any(w in tl for w in self.EXISTS_WORDS): caps.add("exists")
        if any(w in tl for w in self.WINDOW_WORDS): caps.add("window")
        if any(w in tl for w in self.WEEKEND_WORDS): caps.add("weekend")
        if any(w in tl for w in self.DATE_WORDS): caps.add("date_filter")
        if any(w in tl for w in self.THRESHOLD_WORDS): caps.add("threshold")
        # detect join hint
        if "manager" in tl or "handled by" in tl or "handled" in tl: caps.add("join_employees")
        return sorted(list(caps))

    def _detect_clarifications(self, text: str) -> List[Dict[str, Any]]:
        tl = text.lower()
        clar = []
        # threshold numeric missing
        if any(k in tl for k in ["high value", "high balance", "rich", "wealthy"]) and not re.search(r"\b\d{2,}\b", text):
            clar.append({"field": "min_balance", "prompt": "What minimum balance should count as 'high'?", "type": "number", "default": 20000})
        # ambiguous timeframe
        if "recent" in tl or "last" in tl and not re.search(r"\b(20\d{2}|202\d)\b", text):
            clar.append({"field": "date_range", "prompt": "What date range do you mean by 'recent'?", "type": "text", "default": "last 30 days"})
        # explicit q1 text -> convert to date_range default
        if "q1" in tl or "first quarter" in tl:
            clar.append({"field":"date_range","prompt":"Confirm date range for Q1", "type":"text","default":"2025-01-01..2025-03-31"})
        return clar

    def analyze_query(self, nl_query: str) -> Dict[str, Any]:
        """
        Main entrypoint. Returns structured plan dict.
        """
        if not nl_query or not nl_query.strip():
            return {"tables": list(self.schema_map.keys()), "steps": [{"action":"fetch_schema","tables": list(self.schema_map.keys())}], "capabilities": [], "clarifications": []}

        tables = self._detect_tables(nl_query)
        capabilities = self._detect_capabilities(nl_query)
        clarifications = self._detect_clarifications(nl_query)

        steps = [
            {"action":"fetch_schema","tables": tables},
            {"action":"retrieve_examples","tables": tables},
            {"action":"generate_sql"},
            {"action":"validate_sql"},
            {"action":"execute_sql"}
        ]

        plan = {
            "query": nl_query,
            "tables": tables,
            "steps": steps,
            "capabilities": capabilities,
            "clarifications": clarifications,
            "conversation_state": self.conversation_state
        }
        return plan
