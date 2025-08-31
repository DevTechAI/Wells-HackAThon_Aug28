#!/usr/bin/env python3
"""
Thread-Safe Database Connection Manager
Handles SQLite threading issues by creating fresh connections per thread
"""

import sqlite3
import threading
import time
from typing import Optional, Dict, Any
import queue

class ThreadSafeDBManager:
    """
    Thread-safe database connection manager that creates fresh connections per thread
    to avoid SQLite threading issues.
    """
    
    def __init__(self, db_path: str, max_connections: int = 10):
        self.db_path = db_path
        self.max_connections = max_connections
        self._lock = threading.Lock()
        self._connections = {}  # thread_id -> connection
        self._connection_pool = queue.Queue(maxsize=max_connections)
        self._active_connections = 0
        
        print(f"🗄️ DB MANAGER: Initialized for database: {db_path}")
        print(f"🔒 DB MANAGER: Max connections: {max_connections}")
    
    def get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection for the current thread.
        Creates a new connection if one doesn't exist for this thread.
        """
        thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id in self._connections:
                conn = self._connections[thread_id]
                # Test if connection is still valid
                try:
                    conn.execute("SELECT 1")
                    print(f"🔗 DB MANAGER: Reusing existing connection for thread {thread_id}")
                    return conn
                except sqlite3.Error:
                    print(f"⚠️ DB MANAGER: Connection for thread {thread_id} is invalid, creating new one")
                    # Remove invalid connection
                    try:
                        conn.close()
                    except:
                        pass
                    del self._connections[thread_id]
                    self._active_connections -= 1
            
            # Create new connection
            print(f"🆕 DB MANAGER: Creating new connection for thread {thread_id}")
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            
            # Set connection properties for better performance
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("PRAGMA synchronous = NORMAL")
            conn.execute("PRAGMA cache_size = 10000")
            conn.execute("PRAGMA temp_store = MEMORY")
            
            self._connections[thread_id] = conn
            self._active_connections += 1
            
            print(f"✅ DB MANAGER: Connection created successfully for thread {thread_id}")
            print(f"📊 DB MANAGER: Active connections: {self._active_connections}")
            
            return conn
    
    def release_connection(self, thread_id: Optional[int] = None):
        """
        Release a database connection for a specific thread or current thread.
        """
        if thread_id is None:
            thread_id = threading.get_ident()
        
        with self._lock:
            if thread_id in self._connections:
                conn = self._connections[thread_id]
                try:
                    conn.close()
                    print(f"🔌 DB MANAGER: Closed connection for thread {thread_id}")
                except Exception as e:
                    print(f"⚠️ DB MANAGER: Error closing connection for thread {thread_id}: {e}")
                
                del self._connections[thread_id]
                self._active_connections -= 1
                print(f"📊 DB MANAGER: Active connections: {self._active_connections}")
    
    def execute_query(self, sql: str, limit: int = 100) -> Dict[str, Any]:
        """
        Execute a SQL query with proper connection management.
        """
        thread_id = threading.get_ident()
        conn = None
        
        try:
            print(f"🔍 DB MANAGER: Executing query for thread {thread_id}")
            conn = self.get_connection()
            cursor = conn.cursor()
            
            print(f"🚀 DB MANAGER: Executing SQL: {sql[:100]}...")
            cursor.execute(sql)
            
            print(f"📥 DB MANAGER: Fetching results (limit: {limit})")
            rows = cursor.fetchmany(limit)
            
            # Convert to list of dicts
            results = [dict(row) for row in rows]
            
            print(f"✅ DB MANAGER: Query executed successfully")
            print(f"📊 DB MANAGER: Found {len(results)} rows")
            
            return {
                "success": True,
                "results": results,
                "thread_id": thread_id
            }
            
        except sqlite3.Error as e:
            print(f"❌ DB MANAGER: SQL Error for thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }
        except Exception as e:
            print(f"❌ DB MANAGER: Unexpected error for thread {thread_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "thread_id": thread_id
            }
        finally:
            # Don't close the connection here - let it be reused
            # The connection will be closed when the thread ends or when explicitly released
            pass
    
    def cleanup_thread_connections(self):
        """
        Clean up connections for threads that are no longer active.
        """
        with self._lock:
            active_threads = set(threading.enumerate())
            threads_to_remove = []
            
            for thread_id in self._connections.keys():
                # Check if thread is still active
                thread_still_active = any(t.ident == thread_id for t in active_threads)
                if not thread_still_active:
                    threads_to_remove.append(thread_id)
            
            for thread_id in threads_to_remove:
                self.release_connection(thread_id)
                print(f"🧹 DB MANAGER: Cleaned up connection for inactive thread {thread_id}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get database manager statistics.
        """
        with self._lock:
            return {
                "active_connections": self._active_connections,
                "max_connections": self.max_connections,
                "db_path": self.db_path,
                "thread_connections": len(self._connections)
            }
    
    def close_all_connections(self):
        """
        Close all database connections.
        """
        with self._lock:
            for thread_id in list(self._connections.keys()):
                self.release_connection(thread_id)
            print(f"🔌 DB MANAGER: All connections closed")
    
    def __del__(self):
        """
        Cleanup when the manager is destroyed.
        """
        try:
            self.close_all_connections()
        except:
            pass

# Global database manager instance
_db_manager = None

def get_db_manager(db_path: str) -> ThreadSafeDBManager:
    """
    Get or create the global database manager instance.
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = ThreadSafeDBManager(db_path)
    return _db_manager

def cleanup_db_manager():
    """
    Clean up the global database manager.
    """
    global _db_manager
    if _db_manager:
        _db_manager.close_all_connections()
        _db_manager = None
