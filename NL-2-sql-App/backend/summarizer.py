class SummarizerAgent:
    def __init__(self, max_preview=5):
        self.max_preview = max_preview

    def summarize(self, query: str, result: dict) -> dict:
        if not result.get("success", False):
            return {"summary": f"⚠️ Error: {result.get('error')}"}

        rows = result.get("results", [])
        if not rows:
            return {"summary": "No results found for your query."}

        # Single aggregate result
        if len(rows) == 1 and len(rows[0].keys()) == 1:
            key = list(rows[0].keys())[0]
            value = rows[0][key]
            return {"summary": f"The result for '{query}' is {value}."}

        # List of names or values
        if len(rows) <= self.max_preview and len(rows[0].keys()) <= 2:
            preview = ", ".join(
                [str(list(r.values())[0]) for r in rows[:self.max_preview]]
            )
            return {"summary": f"Top results for '{query}': {preview}", "table": rows}

        # Generic tabular result
        return {
            "summary": f"Here are the first {min(len(rows), self.max_preview)} results for '{query}':",
            "table": rows[: self.max_preview]
        }
