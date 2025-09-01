#!/usr/bin/env python3
"""
LLM Configuration Manager for SQL RAG Agent
Handles API keys and provider configuration via .env files
"""

import os
from typing import Dict, Any, Optional
import logging
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

class LLMConfig:
    """Configuration manager for LLM providers"""
    
    def __init__(self, env_file: str = ".env"):
        self.env_file = env_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from .env file and environment variables"""
        
        # Load .env file if it exists
        env_path = Path(self.env_file)
        if env_path.exists():
            load_dotenv(env_path)
            logger.info(f"✅ Loaded configuration from {self.env_file}")
        else:
            logger.warning(f"⚠️ {self.env_file} not found, using environment variables only")
        
        config = {
            # API Keys
            "openai_api_key": os.getenv("OPENAI_API_KEY"),
            "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY"),
            "google_api_key": os.getenv("GOOGLE_API_KEY"),
            
            # Provider Settings
            "default_provider": os.getenv("DEFAULT_LLM_PROVIDER", "openai"),
            "default_model": os.getenv("DEFAULT_LLM_MODEL", "gpt-4o-mini"),
            "default_embedding_model": os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-3-small"),
            
            # Application Settings
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "sql_row_limit": int(os.getenv("SQL_ROW_LIMIT", "100")),
            "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "45")),
            
            # Database Settings
            "db_path": os.getenv("DB_PATH", "banking.db"),
            "chroma_persist_dir": os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        }
        
        return config
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Get API key for specified provider"""
        key_map = {
            "openai": self.config["openai_api_key"],
            "anthropic": self.config["anthropic_api_key"],
            "google": self.config["google_api_key"]
        }
        return key_map.get(provider)
    
    def get_default_provider(self) -> str:
        """Get default LLM provider"""
        return self.config["default_provider"]
    
    def get_default_model(self) -> str:
        """Get default LLM model"""
        return self.config["default_model"]
    
    def get_default_embedding_model(self) -> str:
        """Get default embedding model"""
        return self.config["default_embedding_model"]
    
    def validate_config(self) -> Dict[str, bool]:
        """Validate configuration and return status"""
        status = {
            "openai": bool(self.config["openai_api_key"]),
            "anthropic": bool(self.config["anthropic_api_key"]),
            "google": bool(self.config["google_api_key"]),
            "default_provider": self.config["default_provider"] in ["openai", "anthropic", "google", "local"]
        }
        
        return status
    
    def print_config_status(self):
        """Print configuration status"""
        status = self.validate_config()
        
        print("🔧 LLM Configuration Status:")
        print(f"  Environment File: {self.env_file}")
        print(f"  OpenAI: {'✅' if status['openai'] else '❌'}")
        print(f"  Anthropic: {'✅' if status['anthropic'] else '❌'}")
        print(f"  Google: {'✅' if status['google'] else '❌'}")
        print(f"  Default Provider: {self.config['default_provider']}")
        print(f"  Default Model: {self.config['default_model']}")
        print(f"  Default Embedding Model: {self.config['default_embedding_model']}")
        
        if not status[self.config["default_provider"]]:
            print(f"⚠️ Warning: Default provider '{self.config['default_provider']}' is not configured!")
    
    def create_env_template(self, template_file: str = ".env.template"):
        """Create a template .env file"""
        template_content = """# LLM Configuration
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
"""
        
        try:
            with open(template_file, 'w') as f:
                f.write(template_content)
            logger.info(f"✅ Created {template_file} template")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to create {template_file}: {e}")
            return False

# Global config instance
llm_config = LLMConfig()
