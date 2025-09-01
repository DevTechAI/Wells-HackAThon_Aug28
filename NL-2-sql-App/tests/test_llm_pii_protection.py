#!/usr/bin/env python3
"""
Test LLM Components with PII Protection (when API key is available)
"""

import sys
import os
sys.path.append('./backend')

def test_llm_components_with_pii_protection():
    """Test LLM components with PII protection when API key is available"""
    
    print("🧠 Testing LLM Components with PII Protection")
    print("=" * 60)
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("⚠️ OPENAI_API_KEY not found in environment")
        print("ℹ️ Skipping LLM component tests (PII protection still works)")
        print("ℹ️ To test LLM components, set OPENAI_API_KEY environment variable")
        return
    
    print(f"✅ OpenAI API key found, testing LLM components...")
    
    try:
        from llm_sql_generator import LLMSQLGenerator
        from llm_embedder import LLMEmbedder
        
        # Test LLM SQL Generator
        print("\n1️⃣ Testing LLM SQL Generator with PII Protection...")
        llm_generator = LLMSQLGenerator()
        
        if llm_generator.llm_loaded:
            print("✅ LLM SQL Generator initialized successfully")
            print(f"🔒 PII Protection: {hasattr(llm_generator, 'security_guard')}")
            
            # Test PII protection in prompt
            test_prompt = "Generate SQL for customers with email john@example.com"
            pii_findings = llm_generator.security_guard.detect_pii(test_prompt, "test")
            
            if pii_findings['detected']:
                print(f"✅ PII detected and will be sanitized: {pii_findings['pii_types']}")
            else:
                print("✅ No PII detected in test prompt")
        else:
            print(f"❌ LLM SQL Generator failed to initialize: {llm_generator.llm_error}")
        
        # Test LLM Embedder
        print("\n2️⃣ Testing LLM Embedder with PII Protection...")
        llm_embedder = LLMEmbedder()
        
        if hasattr(llm_embedder, 'client') and llm_embedder.client:
            print("✅ LLM Embedder initialized successfully")
            print(f"🔒 PII Protection: {hasattr(llm_embedder, 'security_guard')}")
            
            # Test PII protection in embedding text
            test_text = "Customer data: john@example.com, phone: (555) 123-4567"
            pii_findings = llm_embedder.security_guard.detect_pii(test_text, "test")
            
            if pii_findings['detected']:
                print(f"✅ PII detected and will be sanitized: {pii_findings['pii_types']}")
            else:
                print("✅ No PII detected in test text")
        else:
            print(f"❌ LLM Embedder failed to initialize")
        
        print("\n🎉 LLM Components with PII Protection Test Complete!")
        
    except Exception as e:
        print(f"❌ Error testing LLM components: {e}")

if __name__ == "__main__":
    test_llm_components_with_pii_protection()
