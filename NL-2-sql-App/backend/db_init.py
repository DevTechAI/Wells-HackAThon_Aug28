#!/usr/bin/env python3
"""
Database Initialization Module
Creates an in-memory SQLite database and loads schema and data files
"""

import sqlite3
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
import time

class DatabaseInitializer:
    def __init__(self):
        self.db_path = ":memory:"  # In-memory database
        self.conn = None
        self.cursor = None
        self.schema_file = "db/schema.sql"
        self.data_file = "db/sample_data.sql"
        self.table_stats = {}
        self.schema_info = {}
        self.column_values = {}
        
    def initialize_database(self) -> sqlite3.Connection:
        """Initialize the in-memory database with schema and data"""
        print("🚀 Starting Database Initialization...")
        print("=" * 60)
        
        try:
            # Create in-memory database connection
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            print("✅ In-memory SQLite database created successfully")
            
            # Step 1: Load Schema
            print("\n📋 Step 1: Loading Database Schema...")
            self._load_schema()
            
            # Step 2: Load Data
            print("\n📊 Step 2: Loading Database Data...")
            self._load_data()
            
            # Step 3: Generate Statistics
            print("\n📈 Step 3: Generating Database Statistics...")
            self._generate_statistics()
            
            # Step 4: Extract Schema Information
            print("\n🔍 Step 4: Extracting Schema Information...")
            self._extract_schema_info()
            
            # Step 5: Extract Column Values
            print("\n📝 Step 5: Extracting Column Values...")
            self._extract_column_values()
            
            print("\n✅ Database initialization completed successfully!")
            print("=" * 60)
            
            return self.conn
            
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            if self.conn:
                self.conn.close()
            raise
    
    def _load_schema(self):
        """Load the database schema"""
        try:
            schema_path = Path(self.schema_file)
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema file not found: {schema_path}")
            
            print(f"📁 Loading schema from: {schema_path}")
            
            with open(schema_path, 'r') as f:
                schema_sql = f.read()
            
            # Execute schema SQL
            self.cursor.executescript(schema_sql)
            self.conn.commit()
            
            # Get list of created tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            print(f"✅ Schema loaded successfully")
            print(f"📋 Tables created: {', '.join(tables)}")
            
        except Exception as e:
            print(f"❌ Schema loading failed: {e}")
            raise
    
    def _load_data(self):
        """Load the database data"""
        try:
            data_path = Path(self.data_file)
            if not data_path.exists():
                raise FileNotFoundError(f"Data file not found: {data_path}")
            
            print(f"📁 Loading data from: {data_path}")
            print(f"📊 File size: {data_path.stat().st_size / (1024*1024):.2f} MB")
            
            start_time = time.time()
            
            with open(data_path, 'r') as f:
                data_sql = f.read()
            
            # Execute data SQL
            self.cursor.executescript(data_sql)
            self.conn.commit()
            
            load_time = time.time() - start_time
            print(f"✅ Data loaded successfully in {load_time:.2f} seconds")
            
        except Exception as e:
            print(f"❌ Data loading failed: {e}")
            raise
    
    def _generate_statistics(self):
        """Generate statistics for all tables"""
        try:
            print("📊 Generating table statistics...")
            
            # Get all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in self.cursor.fetchall()]
            
            for table in tables:
                # Count rows in table
                self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = self.cursor.fetchone()[0]
                
                # Get table schema info
                self.cursor.execute(f"PRAGMA table_info({table})")
                columns = self.cursor.fetchall()
                column_count = len(columns)
                
                self.table_stats[table] = {
                    'rows': row_count,
                    'columns': column_count,
                    'columns_info': columns
                }
                
                print(f"📋 {table}: {row_count:,} rows, {column_count} columns")
            
            print(f"✅ Statistics generated for {len(tables)} tables")
            
        except Exception as e:
            print(f"❌ Statistics generation failed: {e}")
            raise
    
    def _extract_schema_info(self):
        """Extract detailed schema information"""
        try:
            print("🔍 Extracting detailed schema information...")
            
            for table_name in self.table_stats.keys():
                # Get table schema
                self.cursor.execute(f"PRAGMA table_info({table_name})")
                columns = self.cursor.fetchall()
                
                # Get CREATE TABLE statement
                self.cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                create_sql = self.cursor.fetchone()[0]
                
                # Get foreign key information
                self.cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                foreign_keys = self.cursor.fetchall()
                
                # Get indexes
                self.cursor.execute(f"PRAGMA index_list({table_name})")
                indexes = self.cursor.fetchall()
                
                self.schema_info[table_name] = {
                    'columns': columns,
                    'create_sql': create_sql,
                    'foreign_keys': foreign_keys,
                    'indexes': indexes,
                    'primary_keys': [col[1] for col in columns if col[5] == 1],
                    'column_types': {col[1]: col[2] for col in columns},
                    'nullable_columns': [col[1] for col in columns if col[3] == 0],
                    'not_null_columns': [col[1] for col in columns if col[3] == 1]
                }
                
                print(f"📋 {table_name}: {len(columns)} columns, {len(foreign_keys)} foreign keys")
            
            print(f"✅ Schema information extracted for {len(self.schema_info)} tables")
            
        except Exception as e:
            print(f"❌ Schema information extraction failed: {e}")
            raise
    
    def _extract_column_values(self):
        """Extract unique values for important columns"""
        try:
            print("📝 Extracting column values...")
            
            # Define important columns to extract values from
            important_columns = {
                'accounts': ['type', 'status'],
                'branches': ['city', 'state'],
                'employees': ['position'],
                'customers': ['gender'],
                'transactions': ['type', 'status']
            }
            
            for table_name, columns in important_columns.items():
                if table_name not in self.column_values:
                    self.column_values[table_name] = {}
                
                for column in columns:
                    try:
                        # Check if column exists
                        self.cursor.execute(f"PRAGMA table_info({table_name})")
                        table_columns = [col[1] for col in self.cursor.fetchall()]
                        
                        if column in table_columns:
                            # Get unique values
                            self.cursor.execute(f"SELECT DISTINCT {column} FROM {table_name} WHERE {column} IS NOT NULL ORDER BY {column}")
                            values = [row[0] for row in self.cursor.fetchall()]
                            
                            # Get value counts
                            self.cursor.execute(f"SELECT {column}, COUNT(*) FROM {table_name} WHERE {column} IS NOT NULL GROUP BY {column} ORDER BY COUNT(*) DESC")
                            value_counts = {row[0]: row[1] for row in self.cursor.fetchall()}
                            
                            self.column_values[table_name][column] = {
                                'unique_values': values,
                                'value_counts': value_counts,
                                'total_unique': len(values)
                            }
                            
                            print(f"📝 {table_name}.{column}: {len(values)} unique values")
                        else:
                            print(f"⚠️ Column {table_name}.{column} not found")
                            
                    except Exception as e:
                        print(f"⚠️ Error extracting values for {table_name}.{column}: {e}")
                        continue
            
            # Extract sample data for better context
            print("📊 Extracting sample data...")
            for table_name in self.table_stats.keys():
                try:
                    self.cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
                    sample_rows = self.cursor.fetchall()
                    
                    if table_name not in self.column_values:
                        self.column_values[table_name] = {}
                    
                    self.column_values[table_name]['sample_data'] = sample_rows
                    print(f"📊 {table_name}: {len(sample_rows)} sample rows")
                    
                except Exception as e:
                    print(f"⚠️ Error extracting sample data for {table_name}: {e}")
                    continue
            
            print(f"✅ Column values extracted for {len(self.column_values)} tables")
            
        except Exception as e:
            print(f"❌ Column values extraction failed: {e}")
            raise
    
    def get_table_statistics(self) -> Dict:
        """Get the table statistics"""
        return self.table_stats
    
    def get_schema_info(self) -> Dict:
        """Get the detailed schema information"""
        return self.schema_info
    
    def get_column_values(self) -> Dict:
        """Get the column values dictionary"""
        return self.column_values
    
    def get_database_summary(self) -> Dict:
        """Get a comprehensive summary of the database"""
        total_rows = sum(stats['rows'] for stats in self.table_stats.values())
        total_tables = len(self.table_stats)
        
        return {
            'total_tables': total_tables,
            'total_rows': total_rows,
            'tables': self.table_stats,
            'schema_info': self.schema_info,
            'column_values': self.column_values
        }
    
    def close(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            print("🔒 Database connection closed")

def initialize_database() -> Tuple[sqlite3.Connection, Dict]:
    """Convenience function to initialize database and return connection and stats"""
    initializer = DatabaseInitializer()
    conn = initializer.initialize_database()
    stats = initializer.get_database_summary()
    return conn, stats

if __name__ == "__main__":
    # Test the database initialization
    try:
        conn, stats = initialize_database()
        print("\n🎉 Database initialization test completed!")
        print(f"📊 Total tables: {stats['total_tables']}")
        print(f"📊 Total rows: {stats['total_rows']:,}")
        
        # Test a simple query
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM customers")
        customer_count = cursor.fetchone()[0]
        print(f"👥 Customers in database: {customer_count:,}")
        
        # Show some column values
        print("\n📝 Sample Column Values:")
        for table_name, columns in stats['column_values'].items():
            print(f"📋 {table_name}:")
            for col_name, col_data in columns.items():
                if col_name != 'sample_data':
                    print(f"  - {col_name}: {col_data['unique_values'][:5]}...")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        sys.exit(1)
