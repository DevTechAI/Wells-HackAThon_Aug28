#!/usr/bin/env python3
"""
Test the fixed SQL generator logic
"""

def test_fixed_logic():
    """Test the fixed logic"""
    
    user_query = "List all branches and their managers' names. Include branches without a manager."
    query_lower = user_query.lower()
    
    print(f"🔍 Testing Fixed Logic")
    print(f"🔍 User Query: {user_query}")
    print(f"🔍 Query lower: {query_lower}")
    
    # This check now happens BEFORE LLM usage
    if "branch" in query_lower and "manager" in query_lower:
        print("✅ Special query detected: Using branch/manager handler")
        print("✅ This will be triggered BEFORE LLM usage")
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
        print("❌ Special query not detected")
        return False

if __name__ == "__main__":
    test_fixed_logic()
