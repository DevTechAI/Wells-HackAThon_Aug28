#!/usr/bin/env python3
"""
Test script to diagnose LLM loading issues
"""

import os
import time
import threading

def test_llama_import():
    """Test if llama-cpp-python is properly installed"""
    print("🔍 Testing llama-cpp-python import...")
    try:
        from llama_cpp import Llama
        print("✅ llama-cpp-python imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Failed to import llama-cpp-python: {e}")
        return False

def test_model_file():
    """Test if the model file exists and is accessible"""
    model_path = "./models/llama-2-7b-chat.Q4_K_M.gguf"
    print(f"🔍 Testing model file: {model_path}")
    
    if os.path.exists(model_path):
        size = os.path.getsize(model_path)
        print(f"✅ Model file exists")
        print(f"📊 File size: {size / (1024*1024*1024):.2f} GB")
        return True
    else:
        print(f"❌ Model file not found: {model_path}")
        return False

def test_llm_loading():
    """Test LLM loading with timeout"""
    if not test_llama_import() or not test_model_file():
        return False
    
    model_path = "./models/llama-2-7b-chat.Q4_K_M.gguf"
    print(f"🚀 Attempting to load LLM model...")
    
    try:
        from llama_cpp import Llama
        
        # Test with a simple call first
        print(f"🧠 Loading model with basic parameters...")
        llm = Llama(
            model_path=model_path,
            n_ctx=512,  # Smaller context for testing
            n_threads=2,  # Fewer threads for testing
            temperature=0.1,
        )
        print(f"✅ LLM model loaded successfully!")
        
        # Test a simple generation
        print(f"🧠 Testing simple generation...")
        start_time = time.time()
        
        # Use threading to add timeout
        result = {"done": False, "output": None, "error": None}
        
        def generate():
            try:
                result["output"] = llm(
                    "Hello, how are you?",
                    max_tokens=10,
                    temperature=0.1,
                    stop=["\n"],
                    echo=False
                )
                result["done"] = True
            except Exception as e:
                result["error"] = e
                result["done"] = True
        
        thread = threading.Thread(target=generate)
        thread.start()
        thread.join(timeout=30)  # 30 second timeout
        
        if result["done"]:
            if result["error"]:
                print(f"❌ Generation failed: {result['error']}")
                return False
            else:
                elapsed = time.time() - start_time
                print(f"✅ Generation successful in {elapsed:.2f} seconds")
                print(f"📝 Output: {result['output']}")
                return True
        else:
            print(f"❌ Generation timed out after 30 seconds")
            return False
            
    except Exception as e:
        print(f"❌ Failed to load LLM: {e}")
        return False

if __name__ == "__main__":
    print("🔬 LLM Loading Diagnostic Test")
    print("=" * 50)
    
    success = test_llm_loading()
    
    if success:
        print("\n✅ LLM is working correctly!")
    else:
        print("\n❌ LLM has issues. Check the errors above.")
