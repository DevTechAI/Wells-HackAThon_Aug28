#!/bin/bash
# OpenAI API Key Setup Script
# Replace 'your-openai-api-key-here' with your actual OpenAI API key

echo "🔑 Setting up OpenAI API Key..."
export OPENAI_API_KEY='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'

echo "✅ OpenAI API Key set successfully!"
echo "💡 To make this permanent, add the export command to your ~/.zshrc or ~/.bashrc file"
echo ""
echo "🔧 Current configuration:"
echo "  OPENAI_API_KEY: $OPENAI_API_KEY"
echo "  DEFAULT_LLM_PROVIDER: openai"
echo "  DEFAULT_LLM_MODEL: gpt-4"
echo "  DEFAULT_EMBEDDING_MODEL: text-embedding-ada-002"
echo ""
echo "🧪 To test the integration, run:"
echo "  python test_openai_integration.py"
