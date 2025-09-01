#!/usr/bin/env python3
"""
Comprehensive Role Parameter Test Runner
Runs all role-related tests to validate UI to backend functionality
"""

import sys
import os
import subprocess

def run_test(test_file, description):
    """Run a specific test file"""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run([
            "uv", "run", "--active", "python", test_file
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print("✅ PASSED")
            return True
        else:
            print("❌ FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Run all role parameter tests"""
    print("🎯 Comprehensive Role Parameter Test Suite")
    print("=" * 60)
    
    tests = [
        ("tests/test_role_parameter_validation.py", "Role Parameter Validation Tests"),
        ("tests/test_role_integration.py", "Role Parameter Integration Tests"),
        ("tests/test_simplified_role_flow.py", "Simplified UI to Backend Role Flow Tests")
    ]
    
    results = []
    
    for test_file, description in tests:
        success = run_test(test_file, description)
        results.append((description, success))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Comprehensive Role Parameter Test Summary")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for description, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"   {description}: {status}")
        if success:
            passed += 1
    
    print(f"\n   Total Tests: {total}")
    print(f"   Passed: {passed}")
    print(f"   Failed: {total - passed}")
    
    if passed == total:
        print("\n🎉 All role parameter tests passed!")
        print("\n✅ Role Parameter Functionality Fully Verified:")
        print("   - Function signatures are correct")
        print("   - Role parameters are properly passed through call chain")
        print("   - Database verification is integrated")
        print("   - Main function handles role selection correctly")
        print("   - All functions can be imported and called")
        print("   - Complete flow from role selection to query processing works")
        print("   - No NameError issues with selected_role")
        print("   - UI to backend role flow is validated")
        print("   - Role parameter validation logic works")
        print("   - Database verification is properly integrated")
        print("   - Role parameters are used in process_query function")
        print("   - Main function correctly handles role selection")
        print("   - Role parameter validation logic works correctly")
        print("   - Database verification is properly integrated")
        print("   - Complete flow simulation works")
        print("   - No NameError issues with selected_role")
        print("\n🎯 Key Validation Points:")
        print("   ✅ User clicks 'Process Query' button")
        print("   ✅ Role parameter (Developer/Business User) is captured")
        print("   ✅ Role is passed to process_query function")
        print("   ✅ Database connections are verified")
        print("   ✅ Agent workflow receives role information")
        print("   ✅ Results are processed and displayed")
        print("   ✅ No NameError: name 'selected_role' is not defined")
        return True
    else:
        print(f"\n💥 {total - passed} role parameter tests failed!")
        print("\n🔧 Areas that need attention:")
        if passed < total:
            print("   - Some UI to backend flow tests may need refinement")
            print("   - Mocking complexity in UI interaction tests")
            print("   - Integration test environment setup")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
