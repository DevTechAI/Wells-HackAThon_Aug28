#!/usr/bin/env python3
"""
Test script for Integration Test Runner
"""

import os
import sys
sys.path.append('./backend')

def test_integration_runner():
    """Test the integration test runner"""
    print("🧪 Testing Integration Test Runner")
    print("=" * 50)
    
    try:
        from backend.integration_test_runner import get_integration_test_results
        
        # Set environment variables for testing
        os.environ["DB_PATH"] = "banking.db"
        os.environ["CHROMA_PERSIST_DIR"] = "./chroma_db"
        
        # Run integration tests
        print("Running integration tests...")
        results = get_integration_test_results()
        
        # Display results
        print(f"\n📊 Test Summary:")
        print(f"Total Tests: {len(results['tests'])}")
        print(f"Passed: {results['passed_count']}")
        print(f"Failed: {results['failed_count']}")
        print(f"Duration: {results['total_duration']:.2f}s")
        
        print(f"\n📋 Individual Test Results:")
        for test_name, result in results['tests'].items():
            status_icon = "✅" if result['status'] == 'passed' else "❌"
            print(f"{status_icon} {test_name}: {result['details']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration_runner()
    if success:
        print("\n🎉 Integration test runner is working!")
    else:
        print("\n💥 Integration test runner has issues!")
        sys.exit(1)
