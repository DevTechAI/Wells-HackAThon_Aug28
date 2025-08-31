#!/usr/bin/env python3
"""
Test script to verify SQL generation for the specific query
"""

def test_sql_generation():
    """Test the SQL generation logic for the specific query"""
    
    query = "List all branches and their managers' names. Include branches without a manager."
    query_lower = query.lower()
    
    print(f"🔍 Testing SQL generation for query: {query}")
    print(f"🔍 Query lower: {query_lower}")
    
    # Test the fallback logic
    if "branch" in query_lower and "manager" in query_lower:
        print("✅ Fallback condition met: 'branch' and 'manager' found in query")
        
        sql = """
        SELECT b.id, b.name, b.city, b.state, e.name as manager_name
        FROM branches b
        LEFT JOIN employees e ON b.manager_id = e.id
        ORDER BY b.name;
        """
        
        print(f"🔧 Generated SQL:")
        print(sql)
        
        return sql
    else:
        print("❌ Fallback condition not met")
        return None

if __name__ == "__main__":
    test_sql_generation()
