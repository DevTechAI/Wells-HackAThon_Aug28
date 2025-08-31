#!/usr/bin/env python3
"""
Environment Setup Script for SQL RAG Agent
Creates .env file from template and validates configuration
"""

import os
import sys
from pathlib import Path

def create_env_file():
    """Create .env file from template"""
    template_file = "env_template.txt"
    env_file = ".env"
    
    if not Path(template_file).exists():
        print(f"❌ Template file {template_file} not found!")
        return False
    
    if Path(env_file).exists():
        print(f"⚠️ {env_file} already exists. Skipping creation.")
        return True
    
    try:
        # Read template
        with open(template_file, 'r') as f:
            template_content = f.read()
        
        # Write .env file
        with open(env_file, 'w') as f:
            f.write(template_content)
        
        print(f"✅ Created {env_file} from template")
        print(f"💡 Please edit {env_file} and add your API keys")
        return True
        
    except Exception as e:
        print(f"❌ Failed to create {env_file}: {e}")
        return False

def validate_env_file():
    """Validate .env file configuration"""
    env_file = ".env"
    
    if not Path(env_file).exists():
        print(f"❌ {env_file} not found!")
        return False
    
    try:
        # Add backend to path
        sys.path.append('./backend')
        
        from llm_config import llm_config
        
        # Print configuration status
        llm_config.print_config_status()
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to validate configuration: {e}")
        return False

def main():
    """Main setup function"""
    print("🔧 Environment Setup for SQL RAG Agent")
    print("=" * 40)
    
    # Create .env file
    if create_env_file():
        print("\n📝 Next steps:")
        print("1. Edit .env file and add your API keys")
        print("2. Run this script again to validate configuration")
        print("3. Test with: python test_openai_integration.py")
    else:
        print("\n❌ Setup failed!")
        return
    
    print("\n" + "=" * 40)
    print("🔍 Validating Configuration...")
    
    # Validate configuration
    if validate_env_file():
        print("\n✅ Configuration validation complete!")
    else:
        print("\n⚠️ Configuration validation failed. Please check your .env file.")

if __name__ == "__main__":
    main()
