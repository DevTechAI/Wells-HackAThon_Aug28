#!/usr/bin/env python3
"""
Test Security Guard Behavior
"""

def test_security_guard():
    """Test the security guard behavior"""
    
    # Test cases
    test_cases = [
        {
            "name": "Safe SELECT query",
            "sql": "SELECT * FROM customers LIMIT 10",
            "expected_guards": 0
        },
        {
            "name": "Dangerous DELETE query",
            "sql": "DELETE FROM customers WHERE id = 1",
            "expected_guards": 1
        },
        {
            "name": "Dangerous DROP query",
            "sql": "DROP TABLE customers",
            "expected_guards": 1
        },
        {
            "name": "Dangerous TRUNCATE query",
            "sql": "TRUNCATE TABLE customers",
            "expected_guards": 1
        },
        {
            "name": "Suspicious UNION query",
            "sql": "SELECT * FROM customers UNION SELECT * FROM accounts",
            "expected_guards": 1
        }
    ]
    
    print("🔍 Testing Security Guard Behavior")
    print("=" * 50)
    
    for test_case in test_cases:
        print(f"\n📋 Test: {test_case['name']}")
        print(f"SQL: {test_case['sql']}")
        print(f"Expected Guards: {test_case['expected_guards']}")
        
        # Simulate the security guard logic
        guards_applied = {}
        total_guards = 0
        
        # Check for dangerous operations
        dangerous_ops = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE", "GRANT", "REVOKE", "EXEC", "EXECUTE", "SHUTDOWN", "KILL", "BACKUP", "RESTORE"]
        
        for op in dangerous_ops:
            if op in test_case['sql'].upper():
                guards_applied[f"{op}_DETECTED"] = f"⚠️ Dangerous {op} operation detected"
                total_guards += 1
        
        # Check for suspicious patterns
        suspicious_patterns = [
            ("UNION", "UNION SELECT"),
            ("OR_INJECTION", "OR 1=1"),
            ("OR_TRUE", "OR TRUE"),
            ("SCRIPT_TAG", "<script"),
            ("JAVASCRIPT", "javascript:"),
            ("ONLOAD", "onload="),
            ("ONERROR", "onerror=")
        ]
        
        for pattern_name, pattern in suspicious_patterns:
            if pattern.upper() in test_case['sql'].upper():
                guards_applied[f"{pattern_name}_DETECTED"] = f"⚠️ Suspicious {pattern_name} pattern detected"
                total_guards += 1
        
        print(f"Actual Guards: {total_guards}")
        print(f"Guards Applied: {guards_applied}")
        
        if total_guards == 0:
            print("✅ Result: No dangerous operations detected - query is safe")
        else:
            print(f"⚠️ Result: {total_guards} security guard(s) applied due to dangerous operations")
        
        print("-" * 30)

if __name__ == "__main__":
    test_security_guard()
