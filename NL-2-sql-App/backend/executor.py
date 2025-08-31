import sqlite3
import threading
from backend.db_manager import get_db_manager

class ExecutorAgent:
    def __init__(self, db_path="banking.db", db_connection=None):
        self.db_path = db_path
        self.db_connection = db_connection
        self.db_manager = get_db_manager(db_path)
        self.thread_id = threading.get_ident()
        
        print(f"⚡ EXECUTOR AGENT: Initialized with thread-safe database manager")
        print(f"🗄️ EXECUTOR AGENT: Database path: {self.db_path}")
        print(f"🧵 EXECUTOR AGENT: Thread ID: {self.thread_id}")

    def run_query(self, sql: str, limit: int = 100):
        print(f"⚡ EXECUTOR AGENT: Starting SQL execution")
        print(f"🔧 EXECUTOR AGENT: SQL query: {sql}")
        print(f"📊 EXECUTOR AGENT: Row limit: {limit}")
        print(f"🧵 EXECUTOR AGENT: Current thread ID: {threading.get_ident()}")
        
        try:
            print(f"🔌 EXECUTOR AGENT: Getting thread-safe database connection...")
            
            # Use thread-safe database manager
            result = self.db_manager.execute_query(sql, limit)
            
            if result["success"]:
                results = result["results"]
                print(f"✅ EXECUTOR AGENT: Query executed successfully!")
                print(f"📊 EXECUTOR AGENT: Found {len(results)} rows")
                if results:
                    print(f"📋 EXECUTOR AGENT: Columns: {list(results[0].keys())}")

                if not results:
                    print(f"⚠️ EXECUTOR AGENT: No results found")
                    return {"success": True, "results": [], "message": "No results found"}

                print(f"✅ EXECUTOR AGENT: Returning results to orchestrator")
                return {"success": True, "results": results}
            else:
                print(f"❌ EXECUTOR AGENT: Query execution failed")
                print(f"🔍 EXECUTOR AGENT: Error details: {result.get('error', 'Unknown error')}")
                return {"success": False, "error": result.get('error', 'Unknown error')}

        except Exception as e:
            print(f"❌ EXECUTOR AGENT: Unexpected error occurred")
            print(f"🔍 EXECUTOR AGENT: Error details: {str(e)}")
            print(f"🔧 EXECUTOR AGENT: Failed SQL: {sql}")
            return {"success": False, "error": str(e)}
    
    def cleanup_connection(self):
        """
        Clean up the database connection for this thread.
        This should be called after query execution is complete.
        """
        thread_id = threading.get_ident()
        print(f"🧹 EXECUTOR AGENT: Cleaning up connection for thread {thread_id}")
        self.db_manager.release_connection(thread_id)
    
    def get_connection_stats(self):
        """
        Get database connection statistics.
        """
        return self.db_manager.get_stats()
