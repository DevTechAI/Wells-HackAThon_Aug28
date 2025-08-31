#!/usr/bin/env python3
"""
Test the SQL generator to see why fallback logic isn't working
"""

def test_sql_generator_logic():
    """Test the SQL generator logic"""
    
    # Simulate the conditions from the app
    user_query = "List all branches and their managers' names. Include branches without a manager."
    use_llm = True  # This is the default
    llm_available = True  # Simulate LLM being available
    
    print(f"🔍 Testing SQL Generator Logic")
    print(f"🔍 User Query: {user_query}")
    print(f"🔍 Use LLM: {use_llm}")
    print(f"🔍 LLM Available: {llm_available}")
    
    # Check the condition that determines if fallback is used
    fallback_condition = (llm_available is None) or (not use_llm)
    print(f"🔍 Fallback Condition: {fallback_condition}")
    print(f"🔍 Will use fallback: {fallback_condition}")
    
    if fallback_condition:
        print("✅ Fallback logic would be triggered")
        query_lower = user_query.lower()
        if "branch" in query_lower and "manager" in query_lower:
            print("✅ Branch/manager fallback would work")
            return True
        else:
            print("❌ Branch/manager fallback would NOT work")
            return False
    else:
        print("❌ Fallback logic would NOT be triggered - LLM would be used instead")
        return False

if __name__ == "__main__":
    test_sql_generator_logic()
