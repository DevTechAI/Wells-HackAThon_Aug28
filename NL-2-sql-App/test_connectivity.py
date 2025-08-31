#!/usr/bin/env python3
"""
Test the connectivity status function
"""

import os
import sqlite3

def test_connectivity():
    """Test connectivity status"""
    
    DB_PATH = "banking.db"
    CHROMA_PATH = "./chroma_db"
    LLAMA_MODEL_PATH = "./models/llama-2-7b-chat.Q4_K_M.gguf"
    
    print("🔍 Testing System Connectivity")
    print("=" * 50)
    
    # Test SQL Database
    print("💾 Testing SQL Database...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM branches")
        result = cursor.fetchone()
        conn.close()
        print(f"✅ SQL DB Connected: {result[0]} branches")
    except Exception as e:
        print(f"❌ SQL DB Error: {e}")
    
    # Test LLM Model
    print("🧠 Testing LLM Model...")
    try:
        if os.path.exists(LLAMA_MODEL_PATH):
            size = os.path.getsize(LLAMA_MODEL_PATH) / (1024*1024*1024)
            print(f"✅ LLM Model Found: {size:.2f} GB")
        else:
            print(f"❌ LLM Model Not Found: {LLAMA_MODEL_PATH}")
    except Exception as e:
        print(f"❌ LLM Error: {e}")
    
    # Test ChromaDB
    print("🔍 Testing ChromaDB...")
    try:
        import chromadb
        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collections = client.list_collections()
        print(f"✅ ChromaDB Connected: {len(collections)} collections")
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")

if __name__ == "__main__":
    test_connectivity()
