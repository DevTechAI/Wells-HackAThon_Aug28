#!/usr/bin/env python3
"""
PII Scanning Toggle Utility
Helps users enable/disable PII scanning for faster initialization
"""

import os
import sys

def toggle_pii_scanning():
    """Toggle PII scanning on/off"""
    current_setting = os.getenv("ENABLE_PII_SCANNING", "true").lower()
    
    print("🔒 PII Scanning Toggle Utility")
    print("=" * 40)
    print(f"Current setting: ENABLE_PII_SCANNING={current_setting}")
    print()
    
    if current_setting == "true":
        print("PII scanning is currently ENABLED")
        print("This provides security but slows down initialization")
        print()
        choice = input("Do you want to DISABLE PII scanning for faster startup? (y/n): ").lower()
        
        if choice == 'y':
            # Create or update .env file
            env_content = """# LLM Configuration
# Copy this file to .env and fill in your API keys

# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Provider Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002

# Application Settings
MAX_RETRIES=3
SQL_ROW_LIMIT=100
TIMEOUT_SECONDS=45

# Database Settings
DB_PATH=banking.db
CHROMA_PERSIST_DIR=./chroma_db

# PII Protection Settings
ENABLE_PII_SCANNING=false
"""
            
            try:
                with open('.env', 'w') as f:
                    f.write(env_content)
                print("✅ PII scanning DISABLED")
                print("💡 Your app will start faster but won't scan for sensitive data")
                print("⚠️  Remember to re-enable PII scanning in production environments")
            except Exception as e:
                print(f"❌ Error updating .env file: {e}")
        else:
            print("PII scanning remains ENABLED")
    else:
        print("PII scanning is currently DISABLED")
        print("This allows faster startup but doesn't protect sensitive data")
        print()
        choice = input("Do you want to ENABLE PII scanning for security? (y/n): ").lower()
        
        if choice == 'y':
            # Create or update .env file
            env_content = """# LLM Configuration
# Copy this file to .env and fill in your API keys

# API Keys (replace with your actual keys)
OPENAI_API_KEY=your_openai_api_key_here
ANTHROPIC_API_KEY=your_anthropic_api_key_here
GOOGLE_API_KEY=your_google_api_key_here

# LLM Provider Settings
DEFAULT_LLM_PROVIDER=openai
DEFAULT_LLM_MODEL=gpt-4
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002

# Application Settings
MAX_RETRIES=3
SQL_ROW_LIMIT=100
TIMEOUT_SECONDS=45

# Database Settings
DB_PATH=banking.db
CHROMA_PERSIST_DIR=./chroma_db

# PII Protection Settings
ENABLE_PII_SCANNING=true
"""
            
            try:
                with open('.env', 'w') as f:
                    f.write(env_content)
                print("✅ PII scanning ENABLED")
                print("🛡️  Your app will now scan for and protect sensitive data")
                print("⏱️  Initialization may take longer but provides better security")
            except Exception as e:
                print(f"❌ Error updating .env file: {e}")
        else:
            print("PII scanning remains DISABLED")

def show_status():
    """Show current PII scanning status"""
    current_setting = os.getenv("ENABLE_PII_SCANNING", "true").lower()
    
    print("🔒 PII Scanning Status")
    print("=" * 25)
    print(f"ENABLE_PII_SCANNING={current_setting}")
    print()
    
    if current_setting == "true":
        print("✅ PII scanning is ENABLED")
        print("🛡️  The app will scan for and protect sensitive data")
        print("⏱️  Initialization may take longer")
    else:
        print("⚡ PII scanning is DISABLED")
        print("🚀 The app will start faster")
        print("⚠️  No sensitive data protection")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        show_status()
    else:
        toggle_pii_scanning()
