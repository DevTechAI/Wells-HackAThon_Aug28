#!/usr/bin/env python3
"""
Query History Module
Full implementation for query history tracking with database persistence
"""

import os
import json
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class QueryHistory:
    """Query history tracker with database persistence and advanced features"""
    
    def __init__(self, db_path: str = "query_history.db"):
        self.db_path = db_path
        self.max_history = 1000  # Increased for database storage
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for query history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create query_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS query_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    query TEXT NOT NULL,
                    user TEXT NOT NULL,
                    role TEXT NOT NULL,
                    sql_generated TEXT,
                    result_summary TEXT,
                    execution_time REAL,
                    success BOOLEAN,
                    error_message TEXT,
                    metadata TEXT
                )
            ''')
            
            # Create indexes for better performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON query_history(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_user ON query_history(user)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_success ON query_history(success)')
            
            conn.commit()
            conn.close()
            logger.info("✅ Query history database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize query history database: {e}")
            raise
    
    def add_query(self, query: str, user: str, role: str, 
                  sql_generated: Optional[str] = None,
                  result_summary: Optional[str] = None,
                  execution_time: Optional[float] = None,
                  success: bool = True,
                  error_message: Optional[str] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> int:
        """Add a query to history with full details"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO query_history 
                (timestamp, query, user, role, sql_generated, result_summary, 
                 execution_time, success, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                query,
                user,
                role,
                sql_generated,
                result_summary,
                execution_time,
                success,
                error_message,
                json.dumps(metadata) if metadata else None
            ))
            
            query_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Query added to history (ID: {query_id})")
            return query_id
            
        except Exception as e:
            logger.error(f"❌ Failed to add query to history: {e}")
            raise
    
    def get_recent_queries(self, limit: int = 10, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recent queries with optional user filter"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user:
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE user = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user, limit))
            else:
                cursor.execute('''
                    SELECT * FROM query_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            queries = []
            for row in rows:
                queries.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'query': row[2],
                    'user': row[3],
                    'role': row[4],
                    'sql_generated': row[5],
                    'result_summary': row[6],
                    'execution_time': row[7],
                    'success': bool(row[8]),
                    'error_message': row[9],
                    'metadata': json.loads(row[10]) if row[10] else {}
                })
            
            return queries
            
        except Exception as e:
            logger.error(f"❌ Failed to get recent queries: {e}")
            return []
    
    def search_queries(self, search_term: str, user: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search queries by content"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            search_pattern = f"%{search_term}%"
            
            if user:
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE user = ? AND (query LIKE ? OR sql_generated LIKE ? OR result_summary LIKE ?)
                    ORDER BY timestamp DESC
                ''', (user, search_pattern, search_pattern, search_pattern))
            else:
                cursor.execute('''
                    SELECT * FROM query_history 
                    WHERE query LIKE ? OR sql_generated LIKE ? OR result_summary LIKE ?
                    ORDER BY timestamp DESC
                ''', (search_pattern, search_pattern, search_pattern))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            queries = []
            for row in rows:
                queries.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'query': row[2],
                    'user': row[3],
                    'role': row[4],
                    'sql_generated': row[5],
                    'result_summary': row[6],
                    'execution_time': row[7],
                    'success': bool(row[8]),
                    'error_message': row[9],
                    'metadata': json.loads(row[10]) if row[10] else {}
                })
            
            return queries
            
        except Exception as e:
            logger.error(f"❌ Failed to search queries: {e}")
            return []
    
    def get_user_stats(self, user: str) -> Dict[str, Any]:
        """Get statistics for a specific user"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute('SELECT COUNT(*) FROM query_history WHERE user = ?', (user,))
            total_queries = cursor.fetchone()[0]
            
            # Successful queries
            cursor.execute('SELECT COUNT(*) FROM query_history WHERE user = ? AND success = 1', (user,))
            successful_queries = cursor.fetchone()[0]
            
            # Average execution time
            cursor.execute('SELECT AVG(execution_time) FROM query_history WHERE user = ? AND execution_time IS NOT NULL', (user,))
            avg_execution_time = cursor.fetchone()[0] or 0
            
            # Most common roles
            cursor.execute('''
                SELECT role, COUNT(*) as count 
                FROM query_history 
                WHERE user = ? 
                GROUP BY role 
                ORDER BY count DESC
            ''', (user,))
            role_stats = dict(cursor.fetchall())
            
            conn.close()
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                'avg_execution_time': avg_execution_time,
                'role_distribution': role_stats
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get user stats: {e}")
            return {}
    
    def clear_history(self, user: Optional[str] = None):
        """Clear query history for user or all users"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            if user:
                cursor.execute('DELETE FROM query_history WHERE user = ?', (user,))
                logger.info(f"✅ Cleared query history for user: {user}")
            else:
                cursor.execute('DELETE FROM query_history')
                logger.info("✅ Cleared all query history")
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to clear query history: {e}")
            raise
    
    def export_history(self, format: str = "json", user: Optional[str] = None) -> str:
        """Export history in specified format"""
        try:
            queries = self.get_recent_queries(limit=1000, user=user)
            
            if format.lower() == "json":
                return json.dumps(queries, indent=2)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['ID', 'Timestamp', 'Query', 'User', 'Role', 'SQL Generated', 
                               'Result Summary', 'Execution Time', 'Success', 'Error Message'])
                
                # Write data
                for query in queries:
                    writer.writerow([
                        query['id'],
                        query['timestamp'],
                        query['query'],
                        query['user'],
                        query['role'],
                        query['sql_generated'] or '',
                        query['result_summary'] or '',
                        query['execution_time'] or '',
                        query['success'],
                        query['error_message'] or ''
                    ])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export query history: {e}")
            raise
    
    def get_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total queries
            cursor.execute('SELECT COUNT(*) FROM query_history')
            total_queries = cursor.fetchone()[0]
            
            # Success rate
            cursor.execute('SELECT COUNT(*) FROM query_history WHERE success = 1')
            successful_queries = cursor.fetchone()[0]
            
            # Average execution time
            cursor.execute('SELECT AVG(execution_time) FROM query_history WHERE execution_time IS NOT NULL')
            avg_execution_time = cursor.fetchone()[0] or 0
            
            # Top users
            cursor.execute('''
                SELECT user, COUNT(*) as count 
                FROM query_history 
                GROUP BY user 
                ORDER BY count DESC 
                LIMIT 10
            ''')
            top_users = dict(cursor.fetchall())
            
            # Queries by role
            cursor.execute('''
                SELECT role, COUNT(*) as count 
                FROM query_history 
                GROUP BY role 
                ORDER BY count DESC
            ''')
            role_distribution = dict(cursor.fetchall())
            
            # Recent activity (last 7 days)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            cursor.execute('SELECT COUNT(*) FROM query_history WHERE timestamp > ?', (week_ago,))
            recent_activity = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_queries': total_queries,
                'successful_queries': successful_queries,
                'success_rate': (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                'avg_execution_time': avg_execution_time,
                'top_users': top_users,
                'role_distribution': role_distribution,
                'recent_activity_7_days': recent_activity
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get analytics: {e}")
            return {}
