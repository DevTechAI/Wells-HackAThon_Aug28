#!/usr/bin/env python3
"""
Timing Tracker Module
Full implementation for performance timing tracking with database persistence
"""

import time
import json
import sqlite3
import threading
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import psutil
import os

logger = logging.getLogger(__name__)

class TimingTracker:
    """Performance timing tracker with database persistence and advanced analytics"""
    
    def __init__(self, db_path: str = "tests/timing_tracker.db"):
        self.db_path = db_path
        self.timings = {}
        self.start_times = {}
        self._lock = threading.Lock()  # Thread safety
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database for timing data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create timing_records table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS timing_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    duration REAL NOT NULL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    metadata TEXT,
                    session_id TEXT
                )
            ''')
            
            # Create performance_snapshots table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS performance_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    memory_usage REAL,
                    cpu_usage REAL,
                    disk_usage REAL,
                    active_connections INTEGER,
                    session_id TEXT
                )
            ''')
            
            # Create indexes
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_operation ON timing_records(operation)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON timing_records(timestamp)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_session ON timing_records(session_id)')
            
            conn.commit()
            conn.close()
            logger.info("✅ Timing tracker database initialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize timing tracker database: {e}")
            raise
    
    def start_timer(self, operation: str, session_id: Optional[str] = None):
        """Start timing an operation"""
        with self._lock:
            self.start_times[operation] = {
                'start_time': time.time(),
                'session_id': session_id,
                'memory_start': self._get_memory_usage(),
                'cpu_start': self._get_cpu_usage()
            }
    
    def end_timer(self, operation: str, metadata: Optional[Dict[str, Any]] = None) -> float:
        """End timing an operation and return duration"""
        with self._lock:
            if operation in self.start_times:
                start_data = self.start_times[operation]
                duration = time.time() - start_data['start_time']
                
                # Get end metrics
                memory_end = self._get_memory_usage()
                cpu_end = self._get_cpu_usage()
                
                # Store in memory
                self.timings[operation] = {
                    'duration': duration,
                    'memory_usage': memory_end - start_data['memory_start'],
                    'cpu_usage': cpu_end - start_data['cpu_start'],
                    'metadata': metadata,
                    'session_id': start_data['session_id']
                }
                
                # Store in database
                self._store_timing_record(
                    operation, duration, 
                    memory_end - start_data['memory_start'],
                    cpu_end - start_data['cpu_start'],
                    metadata, start_data['session_id']
                )
                
                del self.start_times[operation]
                return duration
            return 0.0
    
    def _store_timing_record(self, operation: str, duration: float, 
                           memory_usage: float, cpu_usage: float,
                           metadata: Optional[Dict[str, Any]], session_id: Optional[str]):
        """Store timing record in database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO timing_records 
                (timestamp, operation, duration, memory_usage, cpu_usage, metadata, session_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                operation,
                duration,
                memory_usage,
                cpu_usage,
                json.dumps(metadata) if metadata else None,
                session_id
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"❌ Failed to store timing record: {e}")
    
    def _get_memory_usage(self) -> float:
        """Get current memory usage in MB"""
        try:
            process = psutil.Process(os.getpid())
            return process.memory_info().rss / 1024 / 1024  # Convert to MB
        except Exception:
            return 0.0
    
    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage"""
        try:
            process = psutil.Process(os.getpid())
            return process.cpu_percent()
        except Exception:
            return 0.0
    
    def get_timing(self, operation: str) -> Optional[Dict[str, Any]]:
        """Get timing for an operation"""
        return self.timings.get(operation)
    
    def get_all_timings(self) -> Dict[str, Dict[str, Any]]:
        """Get all recorded timings"""
        return self.timings.copy()
    
    def get_operation_stats(self, operation: str, hours: int = 24) -> Dict[str, Any]:
        """Get statistics for a specific operation"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get records from last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT duration, memory_usage, cpu_usage 
                FROM timing_records 
                WHERE operation = ? AND timestamp > ?
            ''', (operation, cutoff_time))
            
            records = cursor.fetchall()
            conn.close()
            
            if not records:
                return {}
            
            durations = [r[0] for r in records]
            memory_usages = [r[1] for r in records if r[1] is not None]
            cpu_usages = [r[2] for r in records if r[2] is not None]
            
            return {
                'count': len(records),
                'avg_duration': sum(durations) / len(durations),
                'min_duration': min(durations),
                'max_duration': max(durations),
                'avg_memory_usage': sum(memory_usages) / len(memory_usages) if memory_usages else 0,
                'avg_cpu_usage': sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0,
                'total_duration': sum(durations)
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to get operation stats: {e}")
            return {}
    
    def get_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get records from last N hours
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            # Total operations
            cursor.execute('SELECT COUNT(*) FROM timing_records WHERE timestamp > ?', (cutoff_time,))
            total_operations = cursor.fetchone()[0]
            
            # Average duration
            cursor.execute('SELECT AVG(duration) FROM timing_records WHERE timestamp > ?', (cutoff_time,))
            avg_duration = cursor.fetchone()[0] or 0
            
            # Top operations by frequency
            cursor.execute('''
                SELECT operation, COUNT(*) as count, AVG(duration) as avg_duration
                FROM timing_records 
                WHERE timestamp > ?
                GROUP BY operation 
                ORDER BY count DESC
                LIMIT 10
            ''', (cutoff_time,))
            top_operations = []
            for row in cursor.fetchall():
                top_operations.append({
                    'operation': row[0],
                    'count': row[1],
                    'avg_duration': row[2]
                })
            
            # Memory usage trends
            cursor.execute('''
                SELECT AVG(memory_usage) as avg_memory
                FROM timing_records 
                WHERE timestamp > ? AND memory_usage IS NOT NULL
            ''', (cutoff_time,))
            avg_memory = cursor.fetchone()[0] or 0
            
            # CPU usage trends
            cursor.execute('''
                SELECT AVG(cpu_usage) as avg_cpu
                FROM timing_records 
                WHERE timestamp > ? AND cpu_usage IS NOT NULL
            ''', (cutoff_time,))
            avg_cpu = cursor.fetchone()[0] or 0
            
            conn.close()
            
            return {
                'period_hours': hours,
                'total_operations': total_operations,
                'avg_duration': avg_duration,
                'avg_memory_usage': avg_memory,
                'avg_cpu_usage': avg_cpu,
                'top_operations': top_operations,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Failed to generate performance report: {e}")
            return {}
    
    def take_performance_snapshot(self, session_id: Optional[str] = None):
        """Take a performance snapshot"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get system metrics
            memory_usage = self._get_memory_usage()
            cpu_usage = self._get_cpu_usage()
            
            # Get disk usage
            try:
                disk_usage = psutil.disk_usage('/').percent
            except Exception:
                disk_usage = 0.0
            
            # Get active connections (placeholder)
            active_connections = 0
            
            cursor.execute('''
                INSERT INTO performance_snapshots 
                (timestamp, memory_usage, cpu_usage, disk_usage, active_connections, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                memory_usage,
                cpu_usage,
                disk_usage,
                active_connections,
                session_id
            ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"✅ Performance snapshot taken: Memory={memory_usage:.2f}MB, CPU={cpu_usage:.2f}%")
            
        except Exception as e:
            logger.error(f"❌ Failed to take performance snapshot: {e}")
    
    def reset_timings(self):
        """Reset all timings"""
        with self._lock:
            self.timings = {}
            self.start_times = {}
    
    def clear_database(self):
        """Clear all timing data from database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM timing_records')
            cursor.execute('DELETE FROM performance_snapshots')
            
            conn.commit()
            conn.close()
            
            logger.info("✅ Timing database cleared")
            
        except Exception as e:
            logger.error(f"❌ Failed to clear timing database: {e}")
            raise
    
    def export_timing_data(self, format: str = "json", hours: int = 24) -> str:
        """Export timing data in specified format"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cutoff_time = (datetime.now() - timedelta(hours=hours)).isoformat()
            
            cursor.execute('''
                SELECT * FROM timing_records 
                WHERE timestamp > ?
                ORDER BY timestamp DESC
            ''', (cutoff_time,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Convert to list of dictionaries
            records = []
            for row in rows:
                records.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'operation': row[2],
                    'duration': row[3],
                    'memory_usage': row[4],
                    'cpu_usage': row[5],
                    'metadata': json.loads(row[6]) if row[6] else {},
                    'session_id': row[7]
                })
            
            if format.lower() == "json":
                return json.dumps(records, indent=2)
            elif format.lower() == "csv":
                import csv
                import io
                
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write header
                writer.writerow(['ID', 'Timestamp', 'Operation', 'Duration', 'Memory Usage', 'CPU Usage', 'Session ID'])
                
                # Write data
                for record in records:
                    writer.writerow([
                        record['id'],
                        record['timestamp'],
                        record['operation'],
                        record['duration'],
                        record['memory_usage'] or '',
                        record['cpu_usage'] or '',
                        record['session_id'] or ''
                    ])
                
                return output.getvalue()
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            logger.error(f"❌ Failed to export timing data: {e}")
            raise
