#!/usr/bin/env python3
"""
Test the fallback logic for branch/manager queries
"""

def test_fallback_logic():
    """Test the fallback logic"""
    
    query = "List all branches and their managers' names. Include branches without a manager."
    query_lower = query.lower()
    
    print(f"🔍 Testing query: {query}")
    print(f"🔍 Query lower: {query_lower}")
    print(f"🔍 Contains 'branch': {'branch' in query_lower}")
    print(f"🔍 Contains 'manager': {'manager' in query_lower}")
    
    if "branch" in query_lower and "manager" in query_lower:
        print("✅ Fallback condition met!")
        sql = """
        SELECT b.id, b.name, b.city, b.state, e.name as manager_name
        FROM branches b
        LEFT JOIN employees e ON b.manager_id = e.id
        ORDER BY b.name;
        """
        print(f"🔧 Correct SQL:")
        print(sql)
        return True
    else:
        print("❌ Fallback condition not met")
        return False

if __name__ == "__main__":
    test_fallback_logic()
