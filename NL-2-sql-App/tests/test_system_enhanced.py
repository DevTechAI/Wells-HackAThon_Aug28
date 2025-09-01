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

def test_basic_components():
    """Test basic component imports with detailed results"""
    print("🧪 Testing Basic Component Imports...")
    
    components_to_test = [
        ("LLM Config", "backend.llm_config"),
        ("Database Manager", "backend.db_manager"),
        ("Embedder", "backend.llm_embedder"),
        ("SQL Generator", "backend.llm_sql_generator"),
        ("Planner Agent", "backend.planner"),
        ("Validator Agent", "backend.validator"),
        ("Executor Agent", "backend.executor"),
        ("Summarizer Agent", "backend.summarizer"),
        ("PDF Exporter", "backend.pdf_exporter"),
        ("Query History", "backend.query_history"),
        ("Timing Tracker", "backend.timing_tracker"),
        ("Security Guard", "backend.security_guard")
    ]
    
    results = []
    
    for component_name, module_path in components_to_test:
        start_time = time.time()
        try:
            __import__(module_path)
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
    
    # Run all tests
    test_functions = [
        ("Basic Components", test_basic_components),
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
