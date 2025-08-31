#!/usr/bin/env python3
"""
Test ChromaDB to see what schema information is available
"""

import chromadb

def test_chromadb():
    """Test ChromaDB contents"""
    
    print("🔍 Testing ChromaDB Contents")
    print("=" * 50)
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        print(f"📚 Collections found: {len(collections)}")
        
        for collection in collections:
            print(f"📋 Collection: {collection.name}")
            print(f"📊 Count: {collection.count()}")
            
            if collection.count() > 0:
                # Get some sample documents
                results = collection.get(limit=3)
                print("📄 Sample documents:")
                for i, doc in enumerate(results['documents']):
                    print(f"  {i+1}. {doc[:200]}{'...' if len(doc) > 200 else ''}")
            else:
                print("❌ No documents found in collection")
        
        # Test the retriever logic
        print("\n🔍 Testing Retriever Logic")
        print("=" * 30)
        
        collection = client.get_or_create_collection("bank_schema")
        
        # Test querying for different tables
        test_tables = ["accounts", "branches", "employees", "transactions"]
        
        for table in test_tables:
            print(f"\n🔍 Querying for '{table}':")
            try:
                results = collection.query(
                    query_texts=[table],
                    n_results=1
                )
                if results and results["documents"] and len(results["documents"]) > 0 and len(results["documents"][0]) > 0:
                    print(f"✅ Found: {results['documents'][0][0][:200]}{'...' if len(results['documents'][0][0]) > 200 else ''}")
                else:
                    print(f"❌ No results found for '{table}'")
            except Exception as e:
                print(f"❌ Error querying '{table}': {e}")
        
    except Exception as e:
        print(f"❌ ChromaDB Error: {e}")

if __name__ == "__main__":
    test_chromadb()
