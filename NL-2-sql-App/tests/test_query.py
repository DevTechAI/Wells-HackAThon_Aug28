#!/usr/bin/env python3
"""
Test script to verify database connection and query execution
"""

import sqlite3
import os

def test_database_connection():
    """Test the database connection and the specific query"""
    
    db_path = "banking.db"
    print(f"🔍 Testing database connection to: {db_path}")
    print(f"📁 Current directory: {os.getcwd()}")
    print(f"📁 Database exists: {os.path.exists(db_path)}")
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        print("✅ Database connected successfully!")
        
        # Test the exact query for "List all branches and their managers' names"
        query = """
        SELECT b.id, b.name, b.city, b.state, e.name as manager_name 
        FROM branches b 
        LEFT JOIN employees e ON b.manager_id = e.id 
        ORDER BY b.name
        LIMIT 10
        """
        
        print(f"🔍 Executing query: {query}")
        cursor.execute(query)
        results = cursor.fetchall()
        
        print(f"✅ Query executed successfully!")
        print(f"📊 Found {len(results)} rows")
        
        if results:
            print("\n📋 Sample results:")
            for i, row in enumerate(results[:5]):
                print(f"  {i+1}. Branch: {row[1]} | City: {row[2]} | Manager: {row[4] or 'No Manager'}")
        
        conn.close()
        print("✅ Database connection closed")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_database_connection()
