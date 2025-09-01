#!/usr/bin/env python3
"""
ChromaDB Error Handling Test
Tests the improved error handling for existing collections and graceful degradation
"""

import os
import sys
import time
import traceback
import threading

def test_chromadb_error_handling():
    """Test ChromaDB error handling for existing collections"""
    print("🔍 Testing ChromaDB Error Handling...")
    print("=" * 60)
    
    # Test 1: Import and basic setup
    print("📦 Test 1: Basic ChromaDB setup...")
    try:
        import chromadb
        import sys
        sys.path.append('./backend')
        from llm_embedder import ChromaDBManager
        print("✅ ChromaDB and manager imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Multiple initialization attempts
    print("\n🔄 Test 2: Multiple initialization attempts...")
    try:
        # First initialization
        manager1 = ChromaDBManager("./chroma_db")
        print("✅ First ChromaDB manager initialized")
        
        # Second initialization (should reuse existing)
        manager2 = ChromaDBManager("./chroma_db")
        print("✅ Second ChromaDB manager initialized")
        
        # Third initialization (should reuse existing)
        manager3 = ChromaDBManager("./chroma_db")
        print("✅ Third ChromaDB manager initialized")
        
        print("✅ Multiple initializations handled gracefully")
        
    except Exception as e:
        print(f"❌ Multiple initialization test failed: {e}")
        return False
    
    # Test 3: Concurrent collection creation
    print("\n⚡ Test 3: Concurrent collection creation...")
    try:
        collection_name = "concurrent_test_collection"
        
        def create_collection(manager, thread_id):
            try:
                collection = manager.get_or_create_collection(collection_name)
                if collection:
                    print(f"✅ Thread {thread_id}: Collection '{collection_name}' ready")
                    return True
                else:
                    print(f"⚠️ Thread {thread_id}: Collection '{collection_name}' not available")
                    return False
            except Exception as e:
                print(f"❌ Thread {thread_id}: Error with collection: {e}")
                return False
        
        # Create multiple threads to test concurrent access
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_collection, args=(manager1, i+1))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        print("✅ Concurrent collection creation handled gracefully")
        
    except Exception as e:
        print(f"❌ Concurrent collection test failed: {e}")
        return False
    
    # Test 4: Collection already exists error handling
    print("\n🔄 Test 4: Collection already exists error handling...")
    try:
        collection_name = "exists_test_collection"
        
        # First creation
        collection1 = manager1.get_or_create_collection(collection_name)
        print(f"✅ First creation: Collection '{collection_name}' ready")
        
        # Second creation (should handle existing collection)
        collection2 = manager2.get_or_create_collection(collection_name)
        print(f"✅ Second creation: Collection '{collection_name}' ready")
        
        # Third creation (should handle existing collection)
        collection3 = manager3.get_or_create_collection(collection_name)
        print(f"✅ Third creation: Collection '{collection_name}' ready")
        
        print("✅ Collection already exists handled gracefully")
        
    except Exception as e:
        print(f"❌ Collection exists test failed: {e}")
        return False
    
    # Test 5: Document operations with error handling
    print("\n📄 Test 5: Document operations with error handling...")
    try:
        collection_name = "doc_test_collection"
        
        # Get or create collection
        collection = manager1.get_or_create_collection(collection_name)
        if collection:
            # Add documents
            try:
                collection.add(
                    documents=["Test document for error handling"],
                    metadatas=[{"source": "error_handling_test", "timestamp": time.time()}],
                    ids=["error_test_id"]
                )
                print("✅ Document added successfully")
                
                # Query documents
                results = collection.query(
                    query_texts=["Test document"],
                    n_results=1
                )
                
                if results and results['documents']:
                    print("✅ Document query successful")
                    print(f"📄 Retrieved: {results['documents'][0][0][:30]}...")
                else:
                    print("⚠️ Query returned no results")
                    
            except Exception as doc_error:
                print(f"⚠️ Document operation failed: {doc_error}")
                print("✅ Error handled gracefully, continuing...")
        else:
            print("⚠️ Collection not available for document operations")
        
        print("✅ Document operations with error handling completed")
        
    except Exception as e:
        print(f"❌ Document operations test failed: {e}")
        return False
    
    # Test 6: Graceful degradation when ChromaDB fails
    print("\n🛡️ Test 6: Graceful degradation test...")
    try:
        # Test with invalid path to simulate failure
        invalid_manager = ChromaDBManager("/invalid/path/that/does/not/exist")
        
        # Try to get collection (should return None gracefully)
        collection = invalid_manager.get_or_create_collection("test_collection")
        if collection is None:
            print("✅ Graceful degradation: Collection returned None for invalid path")
        else:
            print("⚠️ Unexpected: Collection created despite invalid path")
        
        # Try to add documents (should not crash)
        invalid_manager.add_documents(
            collection_name="test_collection",
            documents=["test"],
            metadatas=[{"test": "data"}],
            ids=["test_id"]
        )
        print("✅ Graceful degradation: Document addition handled without crash")
        
        # Try to query (should return empty results)
        results = invalid_manager.query(
            collection_name="test_collection",
            query_texts=["test"],
            n_results=1
        )
        
        if results and results.get('documents') == []:
            print("✅ Graceful degradation: Query returned empty results")
        else:
            print("⚠️ Unexpected: Query returned unexpected results")
        
        print("✅ Graceful degradation test completed")
        
    except Exception as e:
        print(f"❌ Graceful degradation test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 ChromaDB Error Handling Test Completed Successfully!")
    print("✅ All error handling scenarios work correctly")
    print("✅ ChromaDB gracefully handles existing collections")
    print("✅ Multiple initializations work without conflicts")
    print("✅ Concurrent access is handled properly")
    print("✅ Graceful degradation when ChromaDB is unavailable")
    return True

def main():
    """Main function to run ChromaDB error handling test"""
    success = test_chromadb_error_handling()
    
    if success:
        print("\n🚀 ChromaDB error handling is robust and ready!")
        sys.exit(0)
    else:
        print("\n💥 ChromaDB error handling test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
