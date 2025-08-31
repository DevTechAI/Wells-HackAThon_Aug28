#!/usr/bin/env python3
"""
Comprehensive VectorDB Verification - Check all dataset embeddings in ChromaDB
"""

import chromadb
import json
from typing import Dict, List, Any

def check_vector_db_contents():
    """Check and display all contents in the VectorDB"""
    
    print("🔍 Checking VectorDB Contents")
    print("=" * 50)
    
    # ChromaDB path
    chroma_path = "./chroma_db"
    
    try:
        # Initialize ChromaDB client
        client = chromadb.PersistentClient(path=chroma_path)
        print(f"✅ Connected to ChromaDB at: {chroma_path}")
        
        # List all collections
        collections = client.list_collections()
        print(f"📚 Found {len(collections)} collections:")
        
        for collection in collections:
            print(f"  - {collection.name}")
        
        if not collections:
            print("❌ No collections found in ChromaDB")
            return
        
        # Check each collection
        for collection in collections:
            print(f"\n{'='*60}")
            print(f"📋 COLLECTION: {collection.name}")
            print(f"{'='*60}")
            
            # Get collection info
            try:
                # Get all documents in the collection
                results = collection.get()
                
                if results and results['documents']:
                    documents = results['documents']
                    metadatas = results['metadatas']
                    ids = results['ids']
                    
                    print(f"📊 Total Documents: {len(documents)}")
                    print(f"🆔 Total IDs: {len(ids)}")
                    print(f"📝 Total Metadatas: {len(metadatas)}")
                    
                    # Analyze content types
                    content_types = {}
                    table_types = {}
                    
                    for i, metadata in enumerate(metadatas):
                        if metadata:
                            content_type = metadata.get('content_type', 'unknown')
                            table_name = metadata.get('table', 'unknown')
                            
                            content_types[content_type] = content_types.get(content_type, 0) + 1
                            table_types[table_name] = table_types.get(table_name, 0) + 1
                    
                    print(f"\n📋 Content Types:")
                    for content_type, count in content_types.items():
                        print(f"  - {content_type}: {count} documents")
                    
                    print(f"\n🏢 Table Distribution:")
                    for table_name, count in table_types.items():
                        print(f"  - {table_name}: {count} documents")
                    
                    # Show sample documents
                    print(f"\n📄 Sample Documents (first 5):")
                    for i in range(min(5, len(documents))):
                        doc = documents[i]
                        metadata = metadatas[i] if metadatas else {}
                        doc_id = ids[i]
                        
                        print(f"\n  Document {i+1}:")
                        print(f"    ID: {doc_id}")
                        print(f"    Type: {metadata.get('content_type', 'unknown')}")
                        print(f"    Table: {metadata.get('table', 'unknown')}")
                        print(f"    Content Preview: {doc[:100]}...")
                        
                        if metadata.get('column'):
                            print(f"    Column: {metadata['column']}")
                    
                    # Check for specific expected content
                    print(f"\n🔍 Expected Content Verification:")
                    
                    expected_tables = ['customers', 'accounts', 'transactions', 'employees', 'branches']
                    expected_content_types = ['create_table', 'column_info', 'foreign_key', 'unique_values']
                    
                    missing_tables = []
                    for table in expected_tables:
                        if table not in table_types:
                            missing_tables.append(table)
                    
                    if missing_tables:
                        print(f"  ❌ Missing tables: {missing_tables}")
                    else:
                        print(f"  ✅ All expected tables present")
                    
                    missing_content_types = []
                    for content_type in expected_content_types:
                        if content_type not in content_types:
                            missing_content_types.append(content_type)
                    
                    if missing_content_types:
                        print(f"  ❌ Missing content types: {missing_content_types}")
                    else:
                        print(f"  ✅ All expected content types present")
                    
                    # Check for column values
                    column_value_docs = [i for i, metadata in enumerate(metadatas) 
                                        if metadata and metadata.get('content_type') == 'unique_values']
                    
                    if column_value_docs:
                        print(f"  ✅ Column values found: {len(column_value_docs)} documents")
                        
                        # Show sample column values
                        print(f"  📊 Sample Column Values:")
                        for i in column_value_docs[:3]:
                            doc = documents[i]
                            metadata = metadatas[i]
                            print(f"    - {metadata.get('table', 'unknown')}.{metadata.get('column', 'unknown')}: {doc[:50]}...")
                    else:
                        print(f"  ❌ No column values found")
                    
                else:
                    print(f"❌ Collection '{collection.name}' is empty")
                    
            except Exception as e:
                print(f"❌ Error accessing collection '{collection.name}': {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"📊 VECTORDB SUMMARY")
        print(f"{'='*60}")
        
        total_docs = 0
        total_tables = set()
        total_content_types = set()
        
        for collection in collections:
            try:
                results = collection.get()
                if results and results['documents']:
                    total_docs += len(results['documents'])
                    
                    for metadata in results['metadatas']:
                        if metadata:
                            if metadata.get('table'):
                                total_tables.add(metadata['table'])
                            if metadata.get('content_type'):
                                total_content_types.add(metadata['content_type'])
            except:
                pass
        
        print(f"📚 Total Collections: {len(collections)}")
        print(f"📄 Total Documents: {total_docs}")
        print(f"🏢 Total Tables: {len(total_tables)}")
        print(f"📋 Total Content Types: {len(total_content_types)}")
        
        if total_docs > 0:
            print(f"✅ VectorDB contains data")
            
            # Check if we have comprehensive coverage
            expected_doc_count = 50  # Rough estimate based on schema + column values
            if total_docs >= expected_doc_count:
                print(f"✅ Good coverage: {total_docs} documents (expected ~{expected_doc_count})")
            else:
                print(f"⚠️ Low coverage: {total_docs} documents (expected ~{expected_doc_count})")
        else:
            print(f"❌ VectorDB is empty")
        
    except Exception as e:
        print(f"❌ Error connecting to ChromaDB: {e}")
        import traceback
        traceback.print_exc()

def check_embeddings_quality():
    """Check the quality of embeddings"""
    
    print(f"\n🔍 Checking Embeddings Quality")
    print("=" * 50)
    
    try:
        from backend.embedder import EnhancedRetriever
        
        # Initialize retriever
        retriever = EnhancedRetriever()
        
        # Test queries
        test_queries = [
            "customer information",
            "account balance",
            "transaction history",
            "employee data",
            "branch location"
        ]
        
        print(f"🧪 Testing {len(test_queries)} sample queries:")
        
        for query in test_queries:
            try:
                results = retriever.retrieve_context_with_details(query, n_results=3)
                
                if results and results.get('context_items'):
                    context_items = results['context_items']
                    similarity_scores = results.get('vector_search_details', {}).get('similarity_scores', [])
                    
                    print(f"\n  Query: '{query}'")
                    print(f"    Results: {len(context_items)}")
                    print(f"    Best Score: {max(similarity_scores) if similarity_scores else 'N/A'}")
                    print(f"    Avg Score: {sum(similarity_scores)/len(similarity_scores) if similarity_scores else 'N/A':.3f}")
                    
                    # Show top result
                    if context_items:
                        top_result = context_items[0]
                        print(f"    Top Result: {top_result[:80]}...")
                else:
                    print(f"\n  Query: '{query}' - No results")
                    
            except Exception as e:
                print(f"\n  Query: '{query}' - Error: {e}")
        
        print(f"\n✅ Embeddings quality check completed")
        
    except Exception as e:
        print(f"❌ Error checking embeddings quality: {e}")

def test_specific_queries():
    """Test specific queries to verify dataset coverage"""
    
    print(f"\n🔍 Testing Specific Dataset Queries")
    print("=" * 50)
    
    try:
        from backend.embedder import EnhancedRetriever
        
        # Initialize retriever
        retriever = EnhancedRetriever()
        
        # Test specific dataset queries
        dataset_queries = [
            "customers table schema",
            "accounts table columns",
            "transactions foreign keys",
            "employees branch relationship",
            "branches manager relationship",
            "account types checking savings",
            "customer gender values",
            "employee positions",
            "branch cities",
            "transaction types"
        ]
        
        print(f"🧪 Testing {len(dataset_queries)} dataset-specific queries:")
        
        successful_queries = 0
        
        for query in dataset_queries:
            try:
                results = retriever.retrieve_context_with_details(query, n_results=2)
                
                if results and results.get('context_items'):
                    context_items = results['context_items']
                    similarity_scores = results.get('vector_search_details', {}).get('similarity_scores', [])
                    
                    best_score = max(similarity_scores) if similarity_scores else 0
                    
                    if best_score > 0.5:  # Good match threshold
                        print(f"  ✅ '{query}': {best_score:.3f} - {context_items[0][:60]}...")
                        successful_queries += 1
                    else:
                        print(f"  ⚠️ '{query}': {best_score:.3f} - Low similarity")
                else:
                    print(f"  ❌ '{query}': No results")
                    
            except Exception as e:
                print(f"  ❌ '{query}': Error - {e}")
        
        coverage_percentage = (successful_queries / len(dataset_queries)) * 100
        print(f"\n📊 Dataset Coverage: {successful_queries}/{len(dataset_queries)} ({coverage_percentage:.1f}%)")
        
        if coverage_percentage >= 80:
            print(f"✅ Excellent dataset coverage!")
        elif coverage_percentage >= 60:
            print(f"✅ Good dataset coverage")
        elif coverage_percentage >= 40:
            print(f"⚠️ Moderate dataset coverage")
        else:
            print(f"❌ Poor dataset coverage")
        
    except Exception as e:
        print(f"❌ Error testing specific queries: {e}")

def check_detailed_content():
    """Check detailed content for each table and column"""
    
    print(f"\n🔍 Checking Detailed Content")
    print("=" * 50)
    
    try:
        client = chromadb.PersistentClient(path="./chroma_db")
        collections = client.list_collections()
        
        for collection in collections:
            if collection.count() > 0:
                results = collection.get()
                documents = results['documents']
                metadatas = results['metadatas']
                
                print(f"\n📋 Collection: {collection.name}")
                print(f"📊 Total Documents: {len(documents)}")
                
                # Group by table
                table_content = {}
                for i, metadata in enumerate(metadatas):
                    if metadata:
                        table_name = metadata.get('table', 'unknown')
                        content_type = metadata.get('content_type', 'unknown')
                        column_name = metadata.get('column', 'N/A')
                        
                        if table_name not in table_content:
                            table_content[table_name] = {}
                        
                        if content_type not in table_content[table_name]:
                            table_content[table_name][content_type] = []
                        
                        table_content[table_name][content_type].append({
                            'column': column_name,
                            'content': documents[i][:100] + '...' if len(documents[i]) > 100 else documents[i]
                        })
                
                # Display detailed content
                for table_name, content_types in table_content.items():
                    print(f"\n  🏢 Table: {table_name}")
                    
                    for content_type, items in content_types.items():
                        print(f"    📋 {content_type}: {len(items)} items")
                        
                        for item in items[:3]:  # Show first 3 items
                            if item['column'] != 'N/A':
                                print(f"      - {item['column']}: {item['content']}")
                            else:
                                print(f"      - {item['content']}")
                        
                        if len(items) > 3:
                            print(f"      ... and {len(items) - 3} more")
        
    except Exception as e:
        print(f"❌ Error checking detailed content: {e}")

if __name__ == "__main__":
    check_vector_db_contents()
    check_detailed_content()
    check_embeddings_quality()
    test_specific_queries()
