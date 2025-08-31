#!/usr/bin/env python3
"""
OpenAI LLM Integration Test Script
Tests OpenAI API integration for SQL RAG Agent using .env configuration
"""

import os
import sys
import time
from typing import Dict, Any

# Add backend to path
sys.path.append('./backend')

from llm_config import llm_config
from llm_embedder import LLMEmbedder, EnhancedRetriever
from llm_sql_generator import LLMSQLGenerator

def test_openai_configuration():
    """Test OpenAI configuration from .env file"""
    print("🔧 Testing OpenAI Configuration...")
    
    # Check if OpenAI API key is set
    api_key = llm_config.get_api_key("openai")
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("💡 Please set your OpenAI API key in .env file:")
        print("   OPENAI_API_KEY=your-api-key-here")
        return False
    
    print("✅ OpenAI API key found in .env file")
    return True

def test_openai_embedder():
    """Test OpenAI embedder"""
    print("\n🧠 Testing OpenAI Embedder...")
    
    try:
        # Initialize embedder
        embedder = LLMEmbedder(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_embedding_model()
        )
        
        # Test embedding generation
        test_text = "Find customers with both checking and savings accounts"
        embedding = embedder.generate_embedding(test_text)
        
        print(f"✅ OpenAI Embedder: Generated embedding with {len(embedding)} dimensions")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Embedder test failed: {e}")
        return False

def test_openai_sql_generator():
    """Test OpenAI SQL generator"""
    print("\n🔧 Testing OpenAI SQL Generator...")
    
    try:
        # Initialize SQL generator
        sql_generator = LLMSQLGenerator(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_model()
        )
        
        # Test SQL generation
        test_query = "Find customers with both checking and savings accounts"
        test_context = {
            "schema_context": [
                {"content": "CREATE TABLE customers (id INTEGER PRIMARY KEY, first_name TEXT, last_name TEXT);"},
                {"content": "CREATE TABLE accounts (id INTEGER PRIMARY KEY, customer_id INTEGER, type TEXT, balance REAL);"}
            ],
            "value_hints": ["checking", "savings"],
            "exemplars": ["SELECT * FROM customers WHERE id IN (SELECT customer_id FROM accounts WHERE type = 'checking');"],
            "query_analysis": {"required_tables": ["customers", "accounts"], "operations": []},
            "schema_tables": {"customers": ["id", "first_name", "last_name"], "accounts": ["id", "customer_id", "type", "balance"]}
        }
        
        sql = sql_generator.generate_sql(test_query, test_context)
        
        print(f"✅ OpenAI SQL Generator: Generated SQL successfully")
        print(f"📝 Generated SQL: {sql}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI SQL Generator test failed: {e}")
        return False

def test_openai_enhanced_retriever():
    """Test OpenAI enhanced retriever"""
    print("\n🔍 Testing OpenAI Enhanced Retriever...")
    
    try:
        # Initialize enhanced retriever
        retriever = EnhancedRetriever(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_embedding_model()
        )
        
        # Test context retrieval
        test_query = "Find customers with both checking and savings accounts"
        context = retriever.retrieve_context_with_details(test_query)
        
        print(f"✅ OpenAI Enhanced Retriever: Retrieved context successfully")
        print(f"📊 Context items: {len(context.get('schema_context', []))}")
        print(f"🎯 Query analysis: {context.get('query_analysis', {})}")
        return True
        
    except Exception as e:
        print(f"❌ OpenAI Enhanced Retriever test failed: {e}")
        return False

def test_openai_complete_workflow():
    """Test complete OpenAI workflow"""
    print("\n🚀 Testing Complete OpenAI Workflow...")
    
    try:
        # Initialize components
        embedder = LLMEmbedder(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_embedding_model()
        )
        
        sql_generator = LLMSQLGenerator(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_model()
        )
        
        retriever = EnhancedRetriever(
            provider="openai",
            api_key=llm_config.get_api_key("openai"),
            model_name=llm_config.get_default_embedding_model()
        )
        
        # Test complete workflow
        test_query = "Find customers with both checking and savings accounts"
        
        print(f"📝 Query: {test_query}")
        
        # Step 1: Retrieve context
        print("🔍 Step 1: Retrieving context...")
        context = retriever.retrieve_context_with_details(test_query)
        
        # Step 2: Generate SQL
        print("🔧 Step 2: Generating SQL...")
        sql = sql_generator.generate_sql(test_query, context)
        
        print(f"✅ Complete workflow successful!")
        print(f"📝 Generated SQL: {sql}")
        return True
        
    except Exception as e:
        print(f"❌ Complete workflow test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 OpenAI LLM Integration Test Suite (with .env)")
    print("=" * 50)
    
    # Print configuration status
    llm_config.print_config_status()
    print()
    
    # Run tests
    tests = [
        ("Configuration", test_openai_configuration),
        ("Embedder", test_openai_embedder),
        ("SQL Generator", test_openai_sql_generator),
        ("Enhanced Retriever", test_openai_enhanced_retriever),
        ("Complete Workflow", test_openai_complete_workflow)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test crashed: {e}")
            results.append((test_name, False))
    
    # Print results
    print("\n" + "=" * 50)
    print("📊 Test Results:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! OpenAI integration is ready.")
    else:
        print("⚠️ Some tests failed. Please check your .env configuration and try again.")

if __name__ == "__main__":
    main()
