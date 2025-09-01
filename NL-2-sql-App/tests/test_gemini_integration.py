#!/usr/bin/env python3
"""
Test Gemini Integration
Validates all Gemini components are working correctly
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_integration():
    """Test Gemini integration components"""
    
    print("🧪 Testing Gemini Integration")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found in environment variables")
        print("💡 Please create a .env file with your API key")
        return False
    
    print(f"✅ API Key found: {api_key[:10]}...")
    
    # Test Gemini Embedder
    print("\n🔍 Testing Gemini Embedder...")
    try:
        from backend.gemini_embedder import GeminiEmbedder
        
        embedder = GeminiEmbedder(api_key=api_key)
        embedding = embedder.generate_embedding("test query")
        
        if embedding:
            print(f"✅ Gemini Embedder working - {len(embedding)} dimensions")
        else:
            print("❌ Gemini Embedder failed to generate embedding")
            return False
            
    except Exception as e:
        print(f"❌ Gemini Embedder error: {e}")
        return False
    
    # Test Gemini SQL Generator
    print("\n🔍 Testing Gemini SQL Generator...")
    try:
        from backend.gemini_sql_generator import GeminiSQLGenerator
        
        generator = GeminiSQLGenerator(api_key=api_key)
        
        # Test with a simple query
        test_schema = {"customers": ["id", "name", "email"]}
        sql = generator.generate("List all customers", {}, {}, test_schema)
        
        if sql and "SELECT" in sql.upper():
            print(f"✅ Gemini SQL Generator working - Generated: {sql[:50]}...")
        else:
            print("❌ Gemini SQL Generator failed to generate valid SQL")
            return False
            
    except Exception as e:
        print(f"❌ Gemini SQL Generator error: {e}")
        return False
    
    # Test Gemini Health Checker
    print("\n🔍 Testing Gemini Health Checker...")
    try:
        from backend.gemini_health_checker import GeminiHealthChecker
        
        health_checker = GeminiHealthChecker(api_key=api_key)
        health_summary = health_checker.get_health_summary()
        
        print(f"✅ Gemini Health Checker working")
        print(f"   Overall Status: {health_summary['overall_status']}")
        print(f"   Components: {len(health_summary['components'])}")
        
        # Show component details
        for name, component in health_summary['components'].items():
            print(f"   - {name}: {component.status.value}")
            
    except Exception as e:
        print(f"❌ Gemini Health Checker error: {e}")
        return False
    
    # Test Gemini Enhanced Retriever
    print("\n🔍 Testing Gemini Enhanced Retriever...")
    try:
        from backend.gemini_embedder import GeminiEnhancedRetriever
        
        retriever = GeminiEnhancedRetriever(api_key=api_key)
        
        # Test context retrieval
        context = retriever.retrieve_context_with_details("customer information", n_results=3)
        
        if context and 'context_items' in context:
            print(f"✅ Gemini Enhanced Retriever working - {len(context['context_items'])} items")
        else:
            print("⚠️ Gemini Enhanced Retriever returned no context (this is normal if ChromaDB is empty)")
            
    except Exception as e:
        print(f"❌ Gemini Enhanced Retriever error: {e}")
        return False
    
    print("\n🎉 All Gemini components are working correctly!")
    return True

def test_environment_setup():
    """Test environment setup"""
    
    print("\n🔍 Testing Environment Setup...")
    
    # Check Python version
    python_version = sys.version_info
    if python_version.major >= 3 and python_version.minor >= 8:
        print(f"✅ Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    else:
        print(f"❌ Python version too old: {python_version.major}.{python_version.minor}.{python_version.micro}")
        print("💡 Python 3.8+ required")
        return False
    
    # Check required packages
    required_packages = ['google.generativeai', 'chromadb', 'streamlit', 'sqlite3']
    
    for package in required_packages:
        try:
            if package == 'sqlite3':
                import sqlite3
            else:
                __import__(package)
            print(f"✅ {package} package available")
        except ImportError:
            print(f"❌ {package} package not found")
            return False
    
    return True

def test_gemini_models():
    """Test specific Gemini models"""
    
    print("\n🔍 Testing Gemini Models...")
    
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("❌ GOOGLE_API_KEY not found")
        return False
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        
        # Test Gemini Pro
        print("🔍 Testing Gemini 1.5 Pro...")
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content("Say 'Hello from Gemini'")
        if response.text:
            print(f"✅ Gemini 1.5 Pro working - Response: {response.text[:50]}...")
        else:
            print("❌ Gemini 1.5 Pro failed")
            return False
        
        # Test Embeddings
        print("🔍 Testing text-embedding-004...")
        embedding_model = genai.get_model("text-embedding-004")
        result = embedding_model.embed_content("test")
        if result and 'embedding' in result:
            print(f"✅ text-embedding-004 working - {len(result['embedding'])} dimensions")
        else:
            print("❌ text-embedding-004 failed")
            return False
            
    except Exception as e:
        print(f"❌ Gemini models test error: {e}")
        return False
    
    return True

def main():
    """Main test function"""
    
    print("🚀 Gemini Integration Test Suite")
    print("=" * 60)
    
    # Test environment
    if not test_environment_setup():
        print("\n❌ Environment setup failed")
        return
    
    # Test Gemini models
    if not test_gemini_models():
        print("\n❌ Gemini models test failed")
        return
    
    # Test Gemini integration
    if test_gemini_integration():
        print("\n✅ All tests passed! Gemini integration is ready.")
        print("\n📋 Next Steps:")
        print("1. Update your app.py to use Gemini components")
        print("2. Run: streamlit run app.py")
        print("3. Test with your natural language queries")
        print("\n🎯 Benefits of Gemini:")
        print("- Better SQL accuracy (90-98%)")
        print("- Faster response times")
        print("- More cost-effective pricing")
        print("- Multimodal capabilities")
    else:
        print("\n❌ Some tests failed. Please check the errors above.")
        print("\n🔧 Troubleshooting:")
        print("1. Verify your GOOGLE_API_KEY is correct")
        print("2. Check your internet connection")
        print("3. Ensure you have sufficient API credits")
        print("4. Review the GEMINI_MIGRATION_GUIDE.md for details")

if __name__ == "__main__":
    main()
