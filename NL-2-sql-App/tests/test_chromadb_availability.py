#!/usr/bin/env python3
"""
ChromaDB Availability Test
Standalone script to check ChromaDB connection and functionality
"""

import os
import sys
import time
import traceback

def test_chromadb_availability():
    """Test ChromaDB availability and functionality"""
    print("🔍 Testing ChromaDB Availability...")
    print("=" * 50)
    
    # Test 1: Import check
    print("📦 Test 1: Checking ChromaDB import...")
    try:
        import chromadb
        print("✅ ChromaDB package imported successfully")
    except ImportError as e:
        print(f"❌ ChromaDB import failed: {e}")
        return False
    
    # Test 2: Client connection
    print("\n🔌 Test 2: Testing ChromaDB client connection...")
    try:
        persist_dir = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        print(f"📁 Using persist directory: {persist_dir}")
        
        client = chromadb.PersistentClient(path=persist_dir)
        print("✅ ChromaDB client connected successfully")
        
        # List existing collections
        existing_collections = client.list_collections()
        print(f"📋 Found {len(existing_collections)} existing collections:")
        for col in existing_collections:
            print(f"   - {col.name} (count: {col.count()})")
            
    except Exception as e:
        print(f"❌ ChromaDB client connection failed: {e}")
        print(f"🔍 Error details: {traceback.format_exc()}")
        return False
    
    # Test 3: Collection management
    print("\n🗂️ Test 3: Testing collection management...")
    try:
        collection_name = "availability_test_collection"
        
        # Check if collection exists
        existing_collections = client.list_collections()
        collection_exists = any(col.name == collection_name for col in existing_collections)
        
        if collection_exists:
            print(f"ℹ️ Collection '{collection_name}' already exists, using it")
            collection = client.get_collection(name=collection_name)
        else:
            print(f"➕ Creating new collection '{collection_name}'")
            collection = client.create_collection(
                name=collection_name,
                metadata={"description": "ChromaDB availability test collection"}
            )
        
        print("✅ Collection management test passed")
        
    except Exception as e:
        print(f"❌ Collection management test failed: {e}")
        return False
    
    # Test 4: Document operations
    print("\n📄 Test 4: Testing document operations...")
    try:
        # Add a test document
        collection.add(
            documents=["This is a test document for ChromaDB availability"],
            metadatas=[{"source": "availability_test", "timestamp": time.time()}],
            ids=["availability_test_id"]
        )
        print("✅ Document added successfully")
        
        # Query the document
        results = collection.query(
            query_texts=["test document"],
            n_results=1
        )
        
        if results and results['documents']:
            print("✅ Document query successful")
            print(f"📄 Retrieved document: {results['documents'][0][0][:50]}...")
        else:
            print("⚠️ Query returned no results")
            
    except Exception as e:
        print(f"❌ Document operations test failed: {e}")
        return False
    
    # Test 5: Collection cleanup (optional)
    print("\n🧹 Test 5: Testing collection cleanup...")
    try:
        # Only delete if we created it
        if not collection_exists:
            client.delete_collection(collection_name)
            print(f"🗑️ Test collection '{collection_name}' deleted successfully")
        else:
            print(f"ℹ️ Keeping existing collection '{collection_name}'")
        
        print("✅ Collection cleanup test passed")
        
    except Exception as e:
        print(f"⚠️ Collection cleanup test failed: {e}")
        # Don't fail the overall test for cleanup issues
    
    print("\n" + "=" * 50)
    print("🎉 ChromaDB Availability Test Completed Successfully!")
    print("✅ All ChromaDB functionality is working correctly")
    return True

def main():
    """Main function to run ChromaDB availability test"""
    success = test_chromadb_availability()
    
    if success:
        print("\n🚀 ChromaDB is ready for use!")
        sys.exit(0)
    else:
        print("\n💥 ChromaDB availability test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
