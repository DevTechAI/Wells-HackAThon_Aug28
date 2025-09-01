"""LLM Provider Abstraction Layer"""
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
import logging
from openai import OpenAI
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_exponential

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        pass

class OpenAIProvider(LLMProvider):
    """OpenAI-specific implementation"""
    
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.client = OpenAI(api_key=self.api_key)
        logger.info(f"Initialized OpenAI provider with model: {self.model}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_text(self, prompt: str, **kwargs) -> str:
        """Generate text using OpenAI's chat completion"""
        try:
            temperature = kwargs.get('temperature', 0.1)
            max_tokens = kwargs.get('max_tokens', 1024)
            
            logger.info(f"Generating text with {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI text generation failed: {str(e)}")
            raise
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI's embedding model"""
        try:
            logger.info(f"Generating embeddings with {self.embedding_model}")
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=texts
            )
            return [data.embedding for data in response.data]
            
        except Exception as e:
            logger.error(f"OpenAI embedding generation failed: {str(e)}")
            raise

class LLMFactory:
    """Factory for creating LLM providers"""
    
    @staticmethod
    def create_provider(provider_type: str = "openai") -> LLMProvider:
        """Create and return an LLM provider instance"""
        if provider_type.lower() == "openai":
            return OpenAIProvider()
        else:
            raise ValueError(f"Unsupported LLM provider: {provider_type}")

# Global LLM provider instance
_llm_provider: Optional[LLMProvider] = None

def get_llm_provider() -> LLMProvider:
    """Get or create the global LLM provider instance"""
    global _llm_provider
    if _llm_provider is None:
        provider_type = os.getenv("LLM_PROVIDER", "openai")
        _llm_provider = LLMFactory.create_provider(provider_type)
    return _llm_provider
