#!/usr/bin/env python3
"""
Repopulate VectorDB with Complete Dataset Information
"""

import sqlite3
import os
import sys
from pathlib import Path

def repopulate_vector_db():
    """Repopulate the VectorDB with complete dataset information"""
    
    print("🔄 Repopulating VectorDB with Complete Dataset Information")
    print("=" * 60)
    
    try:
        # Initialize database connection
        db_path = "banking.db"
        if not os.path.exists(db_path):
            print(f"❌ Database file not found: {db_path}")
            return
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"📋 Found {len(tables)} tables: {tables}")
        
        # Extract schema information
        schema_info = {}
        column_values = {}
        
        for table_name in tables:
            print(f"\n🔍 Processing table: {table_name}")
            
            # Get CREATE TABLE statement
            cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = cursor.fetchone()[0]
            
            # Get column information
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            # Get foreign key information
            cursor.execute(f"PRAGMA foreign_key_list({table_name})")
            foreign_keys = cursor.fetchall()
            
            schema_info[table_name] = {
                'create_sql': create_sql,
                'columns': columns,
                'foreign_keys': foreign_keys
            }
            
            print(f"  📊 Columns: {len(columns)}")
            print(f"  🔗 Foreign Keys: {len(foreign_keys)}")
            
            # Extract column values
            column_values[table_name] = {}
            
            for col_info in columns:
                col_name = col_info[1]
                col_type = col_info[2]
                
                # Skip system columns
                if col_name in ['created_at', 'updated_at']:
                    continue
                
                try:
                    # Get unique values for this column
                    cursor.execute(f"SELECT DISTINCT {col_name} FROM {table_name} WHERE {col_name} IS NOT NULL LIMIT 20")
                    unique_values = [str(row[0]) for row in cursor.fetchall()]
                    
                    if unique_values:
                        column_values[table_name][col_name] = {
                            'unique_values': unique_values,
                            'count': len(unique_values)
                        }
                        print(f"    📝 {col_name}: {len(unique_values)} unique values")
                        
                        # Show sample values
                        if len(unique_values) <= 5:
                            print(f"      Values: {', '.join(unique_values)}")
                        else:
                            print(f"      Sample: {', '.join(unique_values[:5])}...")
                    
                except Exception as e:
                    print(f"    ⚠️ Error getting values for {col_name}: {e}")
        
        conn.close()
        
        print(f"\n✅ Schema and column information extracted")
        print(f"📋 Tables: {len(schema_info)}")
        print(f"📊 Total columns with values: {sum(len(cols) for cols in column_values.values())}")
        
        # Now populate the VectorDB
        print(f"\n🔄 Populating VectorDB...")
        
        from backend.embedder import EnhancedRetriever
        
        # Initialize retriever
        retriever = EnhancedRetriever()
        
        # Populate vector database
        retriever.populate_vector_db(schema_info, column_values)
        
        print(f"✅ VectorDB populated successfully!")
        
        # Verify the population
        print(f"\n🔍 Verifying VectorDB population...")
        
        # Test a few queries
        test_queries = [
            "customers table schema",
            "account types",
            "customer gender values",
            "employee positions"
        ]
        
        successful_queries = 0
        
        for query in test_queries:
            try:
                results = retriever.retrieve_context_with_details(query, n_results=2)
                
                if results and results.get('context_items'):
                    context_items = results['context_items']
                    similarity_scores = results.get('vector_search_details', {}).get('similarity_scores', [])
                    
                    best_score = max(similarity_scores) if similarity_scores else 0
                    
                    if best_score > 0.3:  # Lower threshold for verification
                        print(f"  ✅ '{query}': {best_score:.3f} - Found {len(context_items)} results")
                        successful_queries += 1
                    else:
                        print(f"  ⚠️ '{query}': {best_score:.3f} - Low similarity")
                else:
                    print(f"  ❌ '{query}': No results")
                    
            except Exception as e:
                print(f"  ❌ '{query}': Error - {e}")
        
        coverage_percentage = (successful_queries / len(test_queries)) * 100
        print(f"\n📊 Verification Results: {successful_queries}/{len(test_queries)} ({coverage_percentage:.1f}%)")
        
        if coverage_percentage >= 75:
            print(f"✅ VectorDB population successful!")
        else:
            print(f"⚠️ VectorDB population may need improvement")
        
    except Exception as e:
        print(f"❌ Error repopulating VectorDB: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    repopulate_vector_db()
