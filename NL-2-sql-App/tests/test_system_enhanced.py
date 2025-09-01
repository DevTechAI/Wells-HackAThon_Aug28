#!/usr/bin/env python3
"""
Enhanced Test Script for SQL RAG Agent
Tests basic functionality and initialization with detailed table results
"""

import os
import sys
import time
from typing import Dict, List, Any
from tabulate import tabulate

# Add backend and tests to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.dirname(__file__))

def print_test_table(title: str, results: List[Dict[str, Any]]):
    """Print test results in a formatted table"""
    print(f"\n{'='*60}")
    print(f"📊 {title}")
    print(f"{'='*60}")
    
    # Prepare table data
    table_data = []
    for result in results:
        status_icon = "✅" if result['status'] == 'passed' else "❌" if result['status'] == 'failed' else "⚠️"
        table_data.append([
            status_icon,
            result['name'],
            result['status'].upper(),
            f"{result.get('duration', 0):.2f}s",
            result.get('details', '')[:50] + "..." if len(result.get('details', '')) > 50 else result.get('details', '')
        ])
    
    headers = ["Status", "Test Name", "Result", "Duration", "Details"]
    print(tabulate(table_data, headers=headers, tablefmt="grid"))
    
    # Summary
    passed = sum(1 for r in results if r['status'] == 'passed')
    failed = sum(1 for r in results if r['status'] == 'failed')
    errors = sum(1 for r in results if r['status'] == 'error')
    total = len(results)
    
    print(f"\n📈 Summary: {passed} ✅ PASSED | {failed} ❌ FAILED | {errors} ⚠️ ERRORS | {total} TOTAL")

def test_system_initialization():
    """Test system initialization with detailed results"""
    print("🧪 Testing System Initialization...")
    
    try:
        from backend.system_initializer import run_system_initialization
        report = run_system_initialization()
        
        # Extract detailed results
        results = []
        if 'components' in report:
            for component_name, component_data in report['components'].items():
                results.append({
                    'name': f"System: {component_name}",
                    'status': component_data.get('status', 'error'),
                    'duration': component_data.get('duration', 0),
                    'details': component_data.get('message', '')
                })
        
        print_test_table("System Initialization Results", results)
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ System initialization failed: {str(e)}")
        return False

def test_integration_tests():
    """Test integration tests with detailed results"""
    print("🧪 Testing Integration Tests...")
    
    try:
        from tests.integration_tests import run_integration_tests
        report = run_integration_tests()
        
        # Extract detailed results
        results = []
        if 'test_results' in report:
            for test_name, test_data in report['test_results'].items():
                results.append({
                    'name': f"Integration: {test_name}",
                    'status': test_data.get('status', 'error'),
                    'duration': test_data.get('duration', 0),
                    'details': test_data.get('message', '')
                })
        
        print_test_table("Integration Test Results", results)
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ Integration tests failed: {str(e)}")
        return False

def test_backend_tests():
    """Test backend tests with detailed results"""
    print("🧪 Testing Backend Tests...")
    
    try:
        from tests.backend_test_runner import run_backend_tests
        report = run_backend_tests()
        
        # Extract detailed results
        results = []
        if 'test_results' in report:
            for test_name, test_data in report['test_results'].items():
                results.append({
                    'name': f"Backend: {test_name}",
                    'status': test_data.get('status', 'error'),
                    'duration': test_data.get('duration', 0),
                    'details': test_data.get('message', '')
                })
        
        print_test_table("Backend Test Results", results)
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ Backend tests failed: {str(e)}")
        return False

def test_security_guard():
    """Test SecurityGuard functionality specifically"""
    print("🧪 Testing SecurityGuard Functionality...")
    
    try:
        from backend.security_guard import SecurityGuard
        from backend.validator import ValidatorAgent
        
        results = []
        
        # Initialize SecurityGuard
        start_time = time.time()
        security_guard = SecurityGuard()
        duration = time.time() - start_time
        results.append({
            'name': 'SecurityGuard: Initialization',
            'status': 'passed',
            'duration': duration,
            'details': 'SecurityGuard initialized successfully'
        })
        
        # Test safe SQL
        start_time = time.time()
        safe_sql = "SELECT * FROM customers LIMIT 10"
        is_safe, message, action = security_guard.validate_sql(safe_sql, user="test_user", ip_address="127.0.0.1")
        duration = time.time() - start_time
        results.append({
            'name': 'SecurityGuard: Safe SQL',
            'status': 'passed' if is_safe else 'failed',
            'duration': duration,
            'details': f"Safe SQL validation: {message}"
        })
        
        # Test dangerous SQL
        start_time = time.time()
        dangerous_sql = "DROP TABLE customers"
        is_safe, message, action = security_guard.validate_sql(dangerous_sql, user="test_user", ip_address="127.0.0.1")
        duration = time.time() - start_time
        results.append({
            'name': 'SecurityGuard: Dangerous SQL',
            'status': 'passed' if not is_safe else 'failed',
            'duration': duration,
            'details': f"Dangerous SQL blocked: {message}"
        })
        
        # Test Validator integration
        start_time = time.time()
        schema_tables = {"customers": ["id", "name", "email"]}
        validator = ValidatorAgent(schema_tables, security_guard)
        is_safe, message, details = validator.is_safe_sql(safe_sql, user="test_user", ip_address="127.0.0.1")
        duration = time.time() - start_time
        results.append({
            'name': 'SecurityGuard: Validator Integration',
            'status': 'passed' if is_safe else 'failed',
            'duration': duration,
            'details': f"Validator integration: {message}"
        })
        
        print_test_table("SecurityGuard Test Results", results)
        return all(r['status'] == 'passed' for r in results)
        
    except Exception as e:
        print(f"❌ SecurityGuard test failed: {str(e)}")
        return False

def test_query_history():
    """Test QueryHistory functionality"""
    print("🧪 Testing QueryHistory Functionality...")
    
    try:
        from backend.query_history import QueryHistory
        
        results = []
        
        # Initialize QueryHistory
        start_time = time.time()
        query_history = QueryHistory()
        duration = time.time() - start_time
        results.append({
            'name': 'QueryHistory: Initialization',
            'status': 'passed',
            'duration': duration,
            'details': 'QueryHistory initialized successfully'
        })
        
        # Test adding query
        start_time = time.time()
        query_history.add_query(
            query="SELECT * FROM customers",
            sql="SELECT * FROM customers LIMIT 10",
            user="test_user",
            role="developer",
            status="success",
            execution_time=0.5,
            tokens_used=150
        )
        duration = time.time() - start_time
        results.append({
            'name': 'QueryHistory: Add Query',
            'status': 'passed',
            'duration': duration,
            'details': 'Query added successfully'
        })
        
        # Test getting recent queries
        start_time = time.time()
        recent_queries = query_history.get_recent_queries(limit=5)
        duration = time.time() - start_time
        results.append({
            'name': 'QueryHistory: Get Recent Queries',
            'status': 'passed' if len(recent_queries) > 0 else 'failed',
            'duration': duration,
            'details': f"Retrieved {len(recent_queries)} recent queries"
        })
        
        print_test_table("QueryHistory Test Results", results)
        return all(r['status'] == 'passed' for r in results)
        
    except Exception as e:
        print(f"❌ QueryHistory test failed: {str(e)}")
        return False

def test_timing_tracker():
    """Test TimingTracker functionality"""
    print("🧪 Testing TimingTracker Functionality...")
    
    try:
        from backend.timing_tracker import TimingTracker
        
        results = []
        
        # Initialize TimingTracker
        start_time = time.time()
        timing_tracker = TimingTracker()
        duration = time.time() - start_time
        results.append({
            'name': 'TimingTracker: Initialization',
            'status': 'passed',
            'duration': duration,
            'details': 'TimingTracker initialized successfully'
        })
        
        # Test timing operations
        start_time = time.time()
        timer_id = timing_tracker.start_timer("test_operation")
        time.sleep(0.1)  # Simulate some work
        timing_tracker.end_timer(timer_id)
        duration = time.time() - start_time
        results.append({
            'name': 'TimingTracker: Timer Operations',
            'status': 'passed',
            'duration': duration,
            'details': 'Timer start/end operations successful'
        })
        
        # Test performance snapshot
        start_time = time.time()
        snapshot = timing_tracker.take_performance_snapshot()
        duration = time.time() - start_time
        results.append({
            'name': 'TimingTracker: Performance Snapshot',
            'status': 'passed' if snapshot else 'failed',
            'duration': duration,
            'details': 'Performance snapshot captured'
        })
        
        print_test_table("TimingTracker Test Results", results)
        return all(r['status'] == 'passed' for r in results)
        
    except Exception as e:
        print(f"❌ TimingTracker test failed: {str(e)}")
        return False

def test_basic_components():
    """Test basic component imports"""
    print("🧪 Testing Basic Component Imports...")
    
    components = [
        'backend.llm_config',
        'backend.llm_embedder',
        'backend.llm_sql_generator',
        'backend.planner',
        'backend.retriever',
        'backend.validator',
        'backend.executor',
        'backend.summarizer',
        'backend.query_history',
        'backend.timing_tracker',
        'backend.security_guard',
        'backend.pipeline',
        'backend.system_initializer'
    ]
    
    results = []
    for component_name in components:
        start_time = time.time()
        try:
            __import__(component_name)
            duration = time.time() - start_time
            results.append({
                'name': f"Import: {component_name}",
                'status': 'passed',
                'duration': duration,
                'details': 'Module imported successfully'
            })
        except Exception as e:
            duration = time.time() - start_time
            results.append({
                'name': f"Import: {component_name}",
                'status': 'failed',
                'duration': duration,
                'details': str(e)
            })
    
    print_test_table("Component Import Results", results)
    return all(r['status'] == 'passed' for r in results)

def test_openai_integration():
    """Test OpenAI integration with detailed results"""
    print("🧪 Testing OpenAI Integration...")
    
    try:
        from tests.test_openai_integration import (
            test_openai_configuration,
            test_openai_embedder,
            test_openai_sql_generator,
            test_openai_enhanced_retriever,
            test_openai_complete_workflow
        )
        
        tests = [
            ("Configuration", test_openai_configuration),
            ("Embedder", test_openai_embedder),
            ("SQL Generator", test_openai_sql_generator),
            ("Enhanced Retriever", test_openai_enhanced_retriever),
            ("Complete Workflow", test_openai_complete_workflow)
        ]
        
        results = []
        for test_name, test_func in tests:
            start_time = time.time()
            try:
                result = test_func()
                duration = time.time() - start_time
                results.append({
                    'name': f"OpenAI: {test_name}",
                    'status': 'passed' if result else 'failed',
                    'duration': duration,
                    'details': 'Test completed successfully' if result else 'Test failed'
                })
            except Exception as e:
                duration = time.time() - start_time
                results.append({
                    'name': f"OpenAI: {test_name}",
                    'status': 'error',
                    'duration': duration,
                    'details': str(e)
                })
        
        print_test_table("OpenAI Integration Results", results)
        return all(r['status'] == 'passed' for r in results)
        
    except Exception as e:
        print(f"❌ OpenAI integration test failed: {str(e)}")
        return False

def main():
    """Main test function with comprehensive results"""
    print("🧪 Enhanced SQL RAG Agent Test Suite")
    print("=" * 60)
    
    start_time = time.time()
    
    # Run all tests with enhanced coverage
    test_functions = [
        ("Basic Components", test_basic_components),
        ("SecurityGuard", test_security_guard),
        ("QueryHistory", test_query_history),
        ("TimingTracker", test_timing_tracker),
        ("OpenAI Integration", test_openai_integration),
        ("System Initialization", test_system_initialization),
        ("Integration Tests", test_integration_tests),
        ("Backend Tests", test_backend_tests)
    ]
    
    overall_results = []
    for test_name, test_func in test_functions:
        try:
            result = test_func()
            overall_results.append({
                'name': test_name,
                'status': 'passed' if result else 'failed',
                'duration': 0,
                'details': 'All tests passed' if result else 'Some tests failed'
            })
        except Exception as e:
            overall_results.append({
                'name': test_name,
                'status': 'error',
                'duration': 0,
                'details': str(e)
            })
    
    total_duration = time.time() - start_time
    
    # Print overall summary
    print(f"\n{'='*60}")
    print(f"📊 OVERALL TEST SUMMARY")
    print(f"{'='*60}")
    
    print_test_table("Overall Test Results", overall_results)
    
    passed = sum(1 for r in overall_results if r['status'] == 'passed')
    failed = sum(1 for r in overall_results if r['status'] == 'failed')
    errors = sum(1 for r in overall_results if r['status'] == 'error')
    total = len(overall_results)
    
    print(f"\n🎯 FINAL RESULT:")
    if passed == total:
        print("🎉 ALL TESTS PASSED! System is ready to use.")
    elif failed == 0 and errors > 0:
        print("⚠️ SOME ERRORS DETECTED. Check error details above.")
    else:
        print("❌ SOME TESTS FAILED. Review failed tests above.")
    
    print(f"⏱️ Total Duration: {total_duration:.2f}s")

if __name__ == "__main__":
    main()
