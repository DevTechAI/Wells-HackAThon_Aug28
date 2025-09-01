#!/usr/bin/env python3
"""
Test SecurityGuard functionality
Demonstrates the enhanced security features
"""

import sys
import os
sys.path.append('./backend')

from backend.security_guard import SecurityGuard
from backend.validator import ValidatorAgent

def test_security_guard():
    """Test SecurityGuard functionality"""
    print("🛡️ Testing SecurityGuard Functionality")
    print("=" * 50)
    
    # Initialize SecurityGuard
    security_guard = SecurityGuard()
    print("✅ SecurityGuard initialized")
    
    # Test 1: Safe SQL
    print("\n🔍 Test 1: Safe SQL Query")
    safe_sql = "SELECT * FROM customers LIMIT 10"
    is_safe, message, action = security_guard.validate_sql(safe_sql, user="test_user", ip_address="127.0.0.1")
    print(f"SQL: {safe_sql}")
    print(f"Result: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    print(f"Message: {message}")
    print(f"Action: {action}")
    
    # Test 2: Dangerous SQL
    print("\n🔍 Test 2: Dangerous SQL Query")
    dangerous_sql = "DROP TABLE customers"
    is_safe, message, action = security_guard.validate_sql(dangerous_sql, user="test_user", ip_address="127.0.0.1")
    print(f"SQL: {dangerous_sql}")
    print(f"Result: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    print(f"Message: {message}")
    print(f"Action: {action}")
    
    # Test 3: Suspicious SQL
    print("\n🔍 Test 3: Suspicious SQL Query")
    suspicious_sql = "SELECT * FROM customers WHERE id = 1 OR 1=1"
    is_safe, message, action = security_guard.validate_sql(suspicious_sql, user="test_user", ip_address="127.0.0.1")
    print(f"SQL: {suspicious_sql}")
    print(f"Result: {'✅ SAFE' if is_safe else '❌ BLOCKED'}")
    print(f"Message: {message}")
    print(f"Action: {action}")
    
    # Test 4: Rate Limiting
    print("\n🔍 Test 4: Rate Limiting")
    ip_address = "192.168.1.100"
    for i in range(5):
        allowed = security_guard.check_rate_limit(ip_address, max_requests=3, window_minutes=1)
        print(f"Request {i+1}: {'✅ ALLOWED' if allowed else '❌ BLOCKED'}")
    
    # Test 5: Security Report
    print("\n🔍 Test 5: Security Report")
    report = security_guard.get_security_report(hours=1)
    print(f"Total Events: {report.get('total_events', 0)}")
    print(f"Events by Type: {report.get('events_by_type', {})}")
    print(f"Events by Threat: {report.get('events_by_threat', {})}")
    
    # Test 6: Validator Integration
    print("\n🔍 Test 6: Validator Integration")
    schema_tables = {"customers": ["id", "name", "email"]}
    validator = ValidatorAgent(schema_tables, security_guard)
    
    # Test safe query
    is_safe, message, details = validator.is_safe_sql(safe_sql, user="test_user", ip_address="127.0.0.1")
    print(f"Validator Test - Safe SQL: {'✅ PASSED' if is_safe else '❌ FAILED'}")
    print(f"Details: {details}")
    
    # Test dangerous query
    is_safe, message, details = validator.is_safe_sql(dangerous_sql, user="test_user", ip_address="127.0.0.1")
    print(f"Validator Test - Dangerous SQL: {'✅ BLOCKED' if not is_safe else '❌ ALLOWED'}")
    print(f"Details: {details}")
    
    print("\n" + "=" * 50)
    print("🎉 SecurityGuard Test Complete!")

if __name__ == "__main__":
    test_security_guard()
