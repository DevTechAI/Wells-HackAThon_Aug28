#!/usr/bin/env python3
"""
Quick OpenAI Test Script
Tests OpenAI integration using .env configuration
"""

import os
import sys

# Add backend to path
sys.path.append('./backend')

from llm_config import llm_config
from llm_embedder import LLMEmbedder
from llm_sql_generator import LLMSQLGenerator

def quick_test():
    """Quick test of OpenAI integration"""
    print("🧪 Quick OpenAI Test (with .env)")
    print("=" * 30)
    
    # Test configuration
    api_key = llm_config.get_api_key("openai")
    if not api_key:
        print("❌ OpenAI API key not found!")
        print("💡 Please set your OpenAI API key in .env file:")
        print("   OPENAI_API_KEY=your-api-key-here")
        return
    
    print("✅ OpenAI API key found in .env file")
    
    # Test embedder
    try:
        embedder = LLMEmbedder(
            provider="openai",
            api_key=api_key,
            model_name="text-embedding-ada-002"
        )
        
        test_text = "Find customers with both checking and savings accounts"
        embedding = embedder.generate_embedding(test_text)
        print(f"✅ Embedder test passed - {len(embedding)} dimensions")
        
    except Exception as e:
        print(f"❌ Embedder test failed: {e}")
        return
    
    # Test SQL generator
    try:
        sql_generator = LLMSQLGenerator(
            provider="openai",
            api_key=api_key,
            model_name="gpt-4"
        )
        
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
        print(f"✅ SQL Generator test passed")
        print(f"📝 Generated SQL: {sql}")
        
    except Exception as e:
        print(f"❌ SQL Generator test failed: {e}")
        return
    
    print("\n🎉 All tests passed! OpenAI integration is working.")

if __name__ == "__main__":
    quick_test()
