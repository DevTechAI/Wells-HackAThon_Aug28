#!/usr/bin/env python3
"""
Simple .env Configuration Test
Tests if .env file loading works correctly
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.append('./backend')

def test_env_loading():
    """Test .env file loading"""
    print("🔧 Testing .env Configuration Loading")
    print("=" * 40)
    
    # Check if .env file exists
    env_file = Path(".env")
    if env_file.exists():
        print(f"✅ .env file found: {env_file}")
    else:
        print(f"❌ .env file not found: {env_file}")
        print("💡 Create .env file from env_template.txt")
        return False
    
    # Test loading configuration
    try:
        from llm_config import llm_config
        
        # Print configuration status
        llm_config.print_config_status()
        
        # Test API key retrieval
        openai_key = llm_config.get_api_key("openai")
        if openai_key:
            print(f"✅ OpenAI API key loaded: {openai_key[:10]}...")
        else:
            print("❌ OpenAI API key not found in .env")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration loading failed: {e}")
        return False

if __name__ == "__main__":
    test_env_loading()
