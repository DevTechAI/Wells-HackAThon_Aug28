import sqlite3

class ExecutorAgent:
    def __init__(self, db_path="banking.db"):
        self.db_path = db_path

    def run_query(self, sql: str, limit: int = 100):
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # results as dict-like
            cursor = conn.cursor()

            cursor.execute(sql)
            rows = cursor.fetchmany(limit)  # avoid huge dumps

            # Convert to list of dicts
            results = [dict(row) for row in rows]

            conn.close()

            if not results:
                return {"success": True, "results": [], "message": "No results found"}

            return {"success": True, "results": results}

        except sqlite3.Error as e:
            return {"success": False, "error": str(e)}
