#!/usr/bin/env python3
"""
Ollama Initialization Module
Checks Ollama status, installs required models, and provides comprehensive logging
"""

import requests
import time
import logging
import os
from typing import Dict, List, Optional, Tuple
import subprocess
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OllamaInitializer:
    def __init__(self, base_url: str = "http://localhost:11434", model_name: str = "llama2", ollama_path: str = None):
        """
        Initialize Ollama manager
        
        Args:
            base_url: Ollama server URL
            model_name: Default model to use for embeddings
            ollama_path: Path to Ollama executable (auto-detected if None)
        """
        self.base_url = base_url
        self.model_name = model_name
        self.ollama_path = ollama_path or self._find_ollama_path()
        self.available_models = []
        self.server_status = False
        
        logger.info(f"🔧 Initializing Ollama manager")
        logger.info(f"🌐 Server URL: {base_url}")
        logger.info(f"🧠 Default model: {model_name}")
        logger.info(f"📁 Ollama path: {self.ollama_path}")
    
    def _find_ollama_path(self) -> str:
        """Find Ollama executable path"""
        try:
            import subprocess
            result = subprocess.run(['which', 'ollama'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip()
            else:
                # Common installation paths
                common_paths = [
                    "/opt/homebrew/bin/ollama",
                    "/usr/local/bin/ollama",
                    "/usr/bin/ollama"
                ]
                for path in common_paths:
                    if os.path.exists(path):
                        return path
                return "ollama"  # Fallback to PATH
        except Exception as e:
            logger.warning(f"⚠️ Could not find Ollama path: {e}")
            return "ollama"  # Fallback to PATH
        
    def check_server_status(self) -> bool:
        """Check if Ollama server is running"""
        try:
            logger.info(f"🔍 Checking Ollama server status...")
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            
            if response.status_code == 200:
                self.server_status = True
                logger.info(f"✅ Ollama server is running")
                return True
            else:
                logger.error(f"❌ Ollama server responded with status: {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error(f"❌ Cannot connect to Ollama server at {self.base_url}")
            logger.info("💡 Ollama server is not running")
            return False
        except Exception as e:
            logger.error(f"❌ Error checking Ollama server: {e}")
            return False
    
    def start_server(self) -> bool:
        """Start Ollama server if not running"""
        try:
            logger.info(f"🚀 Starting Ollama server...")
            logger.info(f"📁 Using Ollama path: {self.ollama_path}")
            
            # Check if server is already running
            if self.check_server_status():
                logger.info(f"✅ Ollama server is already running")
                return True
            
            # Start server in background
            import subprocess
            process = subprocess.Popen(
                [self.ollama_path, 'serve'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait a moment for server to start
            logger.info(f"⏳ Waiting for server to start...")
            time.sleep(3)
            
            # Check if server started successfully
            if self.check_server_status():
                logger.info(f"✅ Ollama server started successfully")
                return True
            else:
                logger.error(f"❌ Failed to start Ollama server")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error starting Ollama server: {e}")
            return False
    
    def ensure_server_running(self) -> bool:
        """Ensure Ollama server is running, start if needed"""
        logger.info(f"🔍 Ensuring Ollama server is running...")
        
        if self.check_server_status():
            logger.info(f"✅ Ollama server is already running")
            return True
        
        logger.info(f"🔄 Ollama server not running, attempting to start...")
        if self.start_server():
            logger.info(f"✅ Ollama server started successfully")
            return True
        else:
            logger.error(f"❌ Failed to start Ollama server")
            logger.info(f"💡 Manual start command: {self.ollama_path} serve")
            return False
    
    def get_available_models(self) -> List[str]:
        """Get list of available models"""
        try:
            logger.info(f"📋 Fetching available models...")
            response = requests.get(f"{self.base_url}/api/tags", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                models = [model['name'] for model in data.get('models', [])]
                self.available_models = models
                logger.info(f"✅ Found {len(models)} available models: {models}")
                return models
            else:
                logger.error(f"❌ Failed to fetch models: {response.status_code}")
                return []
                
        except Exception as e:
            logger.error(f"❌ Error fetching models: {e}")
            return []
    
    def check_model_availability(self, model_name: str = None) -> bool:
        """Check if a specific model is available"""
        model_to_check = model_name or self.model_name
        
        if not self.available_models:
            self.get_available_models()
        
        is_available = model_to_check in self.available_models
        if is_available:
            logger.info(f"✅ Model '{model_to_check}' is available")
        else:
            logger.warning(f"⚠️ Model '{model_to_check}' is not available")
            logger.info(f"📋 Available models: {self.available_models}")
        
        return is_available
    
    def pull_model(self, model_name: str = None) -> bool:
        """Pull a model from Ollama hub"""
        model_to_pull = model_name or self.model_name
        
        try:
            logger.info(f"📥 Pulling model '{model_to_pull}'...")
            logger.info(f"⏳ This may take several minutes depending on model size...")
            
            # Use subprocess to run ollama pull
            process = subprocess.Popen(
                [self.ollama_path, 'pull', model_to_pull],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Monitor the process
            start_time = time.time()
            while process.poll() is None:
                elapsed = time.time() - start_time
                if elapsed > 30:  # Log progress every 30 seconds
                    logger.info(f"⏳ Still pulling model '{model_to_pull}'... ({elapsed:.0f}s elapsed)")
                    start_time = time.time()
                time.sleep(5)
            
            # Check result
            if process.returncode == 0:
                logger.info(f"✅ Successfully pulled model '{model_to_pull}'")
                # Refresh available models
                self.get_available_models()
                return True
            else:
                stderr = process.stderr.read()
                logger.error(f"❌ Failed to pull model '{model_to_pull}': {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error pulling model '{model_to_pull}': {e}")
            return False
    
    def test_embedding_generation(self, model_name: str = None) -> Tuple[bool, Optional[List[float]]]:
        """Test embedding generation with a model"""
        model_to_test = model_name or self.model_name
        
        try:
            logger.info(f"🧠 Testing embedding generation with model '{model_to_test}'...")
            
            test_text = "This is a test for embedding generation"
            payload = {
                "model": model_to_test,
                "prompt": test_text
            }
            
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                embedding = result.get("embedding")
                if embedding:
                    logger.info(f"✅ Embedding test successful: {len(embedding)} dimensions")
                    return True, embedding
                else:
                    logger.error(f"❌ No embedding in response: {result}")
                    return False, None
            else:
                logger.error(f"❌ Embedding test failed: {response.status_code} - {response.text}")
                return False, None
                
        except Exception as e:
            logger.error(f"❌ Error testing embedding generation: {e}")
            return False, None
    
    def initialize_ollama(self) -> Dict[str, any]:
        """Complete Ollama initialization process"""
        logger.info(f"🚀 Starting Ollama initialization...")
        logger.info("=" * 60)
        
        initialization_result = {
            "server_running": False,
            "models_available": [],
            "default_model_ready": False,
            "embedding_test_passed": False,
            "recommendations": []
        }
        
        # Step 1: Ensure server is running
        logger.info(f"\n📋 Step 1: Ensuring Ollama server is running...")
        if self.ensure_server_running():
            initialization_result["server_running"] = True
        else:
            initialization_result["recommendations"].append(f"Start Ollama server manually: {self.ollama_path} serve")
            logger.error("❌ Ollama initialization failed - server not running")
            return initialization_result
        
        # Step 2: Get available models
        logger.info(f"\n📋 Step 2: Checking available models...")
        models = self.get_available_models()
        initialization_result["models_available"] = models
        
        # Step 3: Check default model
        logger.info(f"\n📋 Step 3: Checking default model availability...")
        if self.check_model_availability(self.model_name):
            initialization_result["default_model_ready"] = True
        else:
            logger.info(f"📥 Default model '{self.model_name}' not available, attempting to pull...")
            if self.pull_model(self.model_name):
                initialization_result["default_model_ready"] = True
            else:
                initialization_result["recommendations"].append(f"Pull model manually: ollama pull {self.model_name}")
        
        # Step 4: Test embedding generation
        logger.info(f"\n📋 Step 4: Testing embedding generation...")
        if initialization_result["default_model_ready"]:
            embedding_success, embedding = self.test_embedding_generation(self.model_name)
            initialization_result["embedding_test_passed"] = embedding_success
            if embedding_success:
                initialization_result["embedding_dimensions"] = len(embedding)
        else:
            initialization_result["recommendations"].append("Cannot test embeddings without model")
        
        # Summary
        logger.info(f"\n✅ Ollama initialization completed!")
        logger.info("=" * 60)
        logger.info(f"📊 Server running: {initialization_result['server_running']}")
        logger.info(f"📋 Models available: {len(initialization_result['models_available'])}")
        logger.info(f"🧠 Default model ready: {initialization_result['default_model_ready']}")
        logger.info(f"🔍 Embedding test passed: {initialization_result['embedding_test_passed']}")
        
        if initialization_result["recommendations"]:
            logger.info(f"💡 Recommendations:")
            for rec in initialization_result["recommendations"]:
                logger.info(f"   - {rec}")
        
        return initialization_result
    
    def get_status_summary(self) -> Dict[str, any]:
        """Get current Ollama status summary"""
        return {
            "server_url": self.base_url,
            "default_model": self.model_name,
            "server_running": self.server_status,
            "available_models": self.available_models,
            "default_model_available": self.model_name in self.available_models
        }

def initialize_ollama() -> Dict[str, any]:
    """Convenience function to initialize Ollama"""
    initializer = OllamaInitializer()
    return initializer.initialize_ollama()

if __name__ == "__main__":
    # Test the Ollama initialization
    try:
        result = initialize_ollama()
        print(f"\n🎉 Ollama initialization test completed!")
        print(f"📊 Result: {result}")
        
    except Exception as e:
        print(f"❌ Ollama initialization test failed: {e}")
        import traceback
        traceback.print_exc()
