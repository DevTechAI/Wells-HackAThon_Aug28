# 🔧 LLM Configuration Guide

## 📋 Overview

This SQL RAG Agent uses a `.env` file for configuration, making it easy to manage API keys and settings across different environments.

## 🚀 Quick Setup

### Step 1: Create .env File
```bash
# Run the setup script
python setup_env.py
```

### Step 2: Add Your API Keys
Edit the `.env` file and replace the placeholder values with your actual API keys:

```env
# API Keys (replace with your actual keys)
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-anthropic-key-here
GOOGLE_API_KEY=your-actual-google-key-here
```

### Step 3: Test Configuration
```bash
# Quick test
python quick_openai_test.py

# Full test suite
python test_openai_integration.py
```

## 🔑 API Key Setup

### OpenAI API Key
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create a new API key
3. Add it to your `.env` file:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   ```

### Anthropic API Key
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Create a new API key
3. Add it to your `.env` file:
   ```env
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   ```

### Google API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add it to your `.env` file:
   ```env
   GOOGLE_API_KEY=your-key-here
   ```

## ⚙️ Configuration Options

### LLM Provider Settings
```env
# Choose your default LLM provider
DEFAULT_LLM_PROVIDER=openai  # Options: openai, anthropic, google, local

# Model settings
DEFAULT_LLM_MODEL=gpt-4  # OpenAI: gpt-4, gpt-3.5-turbo
DEFAULT_EMBEDDING_MODEL=text-embedding-ada-002  # OpenAI: text-embedding-ada-002
```

### Application Settings
```env
# Retry and timeout settings
MAX_RETRIES=3
TIMEOUT_SECONDS=45

# Database settings
SQL_ROW_LIMIT=100
DB_PATH=banking.db
CHROMA_PERSIST_DIR=./chroma_db
```

## 🔄 Switching LLM Providers

To switch between different LLM providers, simply change the `DEFAULT_LLM_PROVIDER` in your `.env` file:

```env
# For OpenAI
DEFAULT_LLM_PROVIDER=openai

# For Anthropic
DEFAULT_LLM_PROVIDER=anthropic

# For Google
DEFAULT_LLM_PROVIDER=google

# For Local models
DEFAULT_LLM_PROVIDER=local
```

## 🛡️ Security Best Practices

1. **Never commit your `.env` file** to version control
2. **Use different API keys** for development and production
3. **Rotate your API keys** regularly
4. **Set appropriate rate limits** in your LLM provider dashboard

## 🧪 Testing Configuration

### Validate Configuration
```bash
python setup_env.py
```

### Test Specific Provider
```bash
# Test OpenAI
python quick_openai_test.py

# Test full integration
python test_openai_integration.py
```

## 📊 Configuration Status

The system will show you the status of your configuration:

```
🔧 LLM Configuration Status:
  Environment File: .env
  OpenAI: ✅
  Anthropic: ❌
  Google: ❌
  Default Provider: openai
  Default Model: gpt-4
  Default Embedding Model: text-embedding-ada-002
```

## 🚨 Troubleshooting

### API Key Not Found
- Check that your `.env` file exists
- Verify the API key variable name is correct
- Ensure there are no extra spaces in the `.env` file

### Authentication Errors
- Verify your API key is valid
- Check your account has sufficient credits
- Ensure the API key has the correct permissions

### Model Not Found
- Verify the model name is correct for your provider
- Check that your account has access to the specified model
- Try using a different model name

## 📁 File Structure

```
NL-2-sql-App/
├── .env                    # Your configuration file (create this)
├── env_template.txt        # Template for .env file
├── setup_env.py           # Setup script
├── quick_openai_test.py   # Quick test script
├── test_openai_integration.py  # Full test suite
└── backend/
    ├── llm_config.py       # Configuration manager
    ├── llm_embedder.py     # LLM-neutral embedder
    └── llm_sql_generator.py # LLM-neutral SQL generator
```
