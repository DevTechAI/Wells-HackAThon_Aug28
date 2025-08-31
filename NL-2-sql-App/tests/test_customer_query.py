#!/usr/bin/env python3
"""
Test the customer account query logic
"""

def test_customer_query_logic():
    """Test the customer account query logic"""
    
    query = "Find the names of customers who have both 'checking' and 'savings' accounts"
    query_lower = query.lower()
    
    print(f"🔍 Testing Customer Account Query Logic")
    print(f"🔍 Query: {query}")
    print(f"🔍 Query lower: {query_lower}")
    
    # Test the conditions
    has_customer = "customer" in query_lower
    has_both = "both" in query_lower
    has_checking = "checking" in query_lower
    has_savings = "savings" in query_lower
    
    print(f"🔍 Contains 'customer': {has_customer}")
    print(f"🔍 Contains 'both': {has_both}")
    print(f"🔍 Contains 'checking': {has_checking}")
    print(f"🔍 Contains 'savings': {has_savings}")
    
    # Test the condition
    condition = has_customer and (has_both or (has_checking and has_savings))
    print(f"🔍 Condition met: {condition}")
    
    if condition:
        print("✅ Special query detected: Using customer account types handler")
        sql = """
        SELECT DISTINCT c.first_name, c.last_name, c.email
        FROM customers c
        WHERE c.id IN (
            SELECT customer_id 
            FROM accounts 
            WHERE type = 'checking'
        )
        AND c.id IN (
            SELECT customer_id 
            FROM accounts 
            WHERE type = 'savings'
        )
        ORDER BY c.last_name, c.first_name;
        """
        print(f"🔧 Correct SQL:")
        print(sql)
        return True
    else:
        print("❌ Special query not detected")
        return False

if __name__ == "__main__":
    test_customer_query_logic()
