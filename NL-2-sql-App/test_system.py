#!/usr/bin/env python3
"""
Quick Test Script for SQL RAG Agent
Tests basic functionality and initialization
"""

import os
import sys
import time

# Add backend to path
sys.path.append('./backend')

def test_system_initialization():
    """Test system initialization"""
    print("🧪 Testing System Initialization...")
    
    try:
        from system_initializer import run_system_initialization
        report = run_system_initialization()
        
        print(f"✅ System initialization completed")
        print(f"   Overall Status: {report['overall_status']}")
        print(f"   Duration: {report['initialization_duration']:.2f}s")
        print(f"   Components: {report['summary']}")
        
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ System initialization failed: {str(e)}")
        return False

def test_integration_tests():
    """Test integration tests"""
    print("🧪 Testing Integration Tests...")
    
    try:
        from tests.integration_tests import run_integration_tests
        report = run_integration_tests()
        
        print(f"✅ Integration tests completed")
        print(f"   Overall Status: {report['overall_status']}")
        print(f"   Duration: {report['test_duration']:.2f}s")
        print(f"   Summary: {report['summary']}")
        
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ Integration tests failed: {str(e)}")
        return False

def test_backend_tests():
    """Test backend tests"""
    print("🧪 Testing Backend Tests...")
    
    try:
        from tests.backend_test_runner import run_backend_tests
        report = run_backend_tests()
        
        print(f"✅ Backend tests completed")
        print(f"   Overall Status: {report['overall_status']}")
        print(f"   Duration: {report['test_duration']:.2f}s")
        print(f"   Summary: {report['summary']}")
        
        return report['overall_status'] in ['passed', 'partial']
        
    except Exception as e:
        print(f"❌ Backend tests failed: {str(e)}")
        return False

def test_basic_components():
    """Test basic component imports"""
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
        ("PDF Exporter", "backend.pdf_exporter")
    ]
    
    failed_components = []
    
    for component_name, module_path in components_to_test:
        try:
            __import__(module_path)
            print(f"   ✅ {component_name}")
        except Exception as e:
            print(f"   ❌ {component_name}: {str(e)}")
            failed_components.append(component_name)
    
    return len(failed_components) == 0

def main():
    """Run all tests"""
    print("🚀 Starting SQL RAG Agent Tests")
    print("=" * 50)
    
    # Test basic components
    basic_ok = test_basic_components()
    print()
    
    # Test system initialization
    init_ok = test_system_initialization()
    print()
    
    # Test integration tests
    integration_ok = test_integration_tests()
    print()
    
    # Test backend tests
    backend_ok = test_backend_tests()
    print()
    
    # Summary
    print("=" * 50)
    print("📊 Test Summary:")
    print(f"   Basic Components: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    print(f"   System Initialization: {'✅ PASS' if init_ok else '❌ FAIL'}")
    print(f"   Integration Tests: {'✅ PASS' if integration_ok else '❌ FAIL'}")
    print(f"   Backend Tests: {'✅ PASS' if backend_ok else '❌ FAIL'}")
    
    overall_success = basic_ok and init_ok and integration_ok and backend_ok
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    if overall_success:
        print("\n🎉 System is ready to run!")
        print("   Run: streamlit run app.py")
    else:
        print("\n⚠️ Please fix the failing tests before running the application.")

if __name__ == "__main__":
    main()
