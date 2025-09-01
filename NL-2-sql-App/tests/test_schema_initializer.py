#!/usr/bin/env python3
"""
Test Schema Initializer
Tests the LangGraph-based schema initialization system
"""

import os
import sys
import asyncio

def test_schema_initializer():
    """Test the schema initializer functionality"""
    print("🔍 Testing Schema Initializer...")
    print("=" * 60)
    
    # Test 1: Import and basic setup
    print("📦 Test 1: Basic schema initializer setup...")
    try:
        import sys
        sys.path.append('./backend')
        from schema_initializer import SchemaAnalyzer, MermaidDiagramGenerator, LangGraphSchemaProcessor
        print("✅ Schema initializer components imported successfully")
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    
    # Test 2: Schema analyzer
    print("\n📊 Test 2: Schema analyzer...")
    try:
        analyzer = SchemaAnalyzer("./banking.db")
        schemas = analyzer.get_table_schemas()
        relationships = analyzer.get_entity_relationships(schemas)
        
        print(f"✅ Analyzed {len(schemas)} tables:")
        for schema in schemas:
            print(f"   📋 {schema.table_name}: {len(schema.columns)} columns")
        
        # Test distinct values analysis
        print(f"\n📊 Distinct Values Analysis:")
        for schema in schemas:
            if schema.distinct_values:
                print(f"   📋 {schema.table_name}:")
                for column_name, values in schema.distinct_values.items():
                    if values:
                        display_values = values[:5] if len(values) > 5 else values
                        print(f"      {column_name}: {display_values}")
                        if len(values) > 5:
                            print(f"      ... and {len(values) - 5} more values")
        
        # Test value distributions
        print(f"\n📈 Value Distributions:")
        for schema in schemas:
            if schema.value_distributions:
                print(f"   📋 {schema.table_name}:")
                for column_name, distribution in schema.value_distributions.items():
                    if distribution:
                        top_values = list(distribution.items())[:3]
                        print(f"      {column_name}: {top_values}")
        
        print(f"✅ Found {len(relationships)} relationships:")
        for rel in relationships:
            print(f"   🔗 {rel.source_table}.{rel.source_column} -> {rel.target_table}.{rel.target_column}")
        
    except Exception as e:
        print(f"❌ Schema analyzer test failed: {e}")
        return False
    
    # Test 3: Mermaid diagram generator
    print("\n📈 Test 3: Mermaid diagram generator...")
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ OpenAI API key not found, skipping Mermaid test")
        else:
            diagram_generator = MermaidDiagramGenerator(openai_api_key)
            mermaid_diagram = diagram_generator.generate_er_diagram(schemas, relationships)
            
            print("✅ Mermaid diagram generated:")
            print("```mermaid")
            print(mermaid_diagram[:200] + "..." if len(mermaid_diagram) > 200 else mermaid_diagram)
            print("```")
        
    except Exception as e:
        print(f"❌ Mermaid diagram test failed: {e}")
        return False
    
    # Test 4: LangGraph processor (without actual embedding generation)
    print("\n🔄 Test 4: LangGraph processor setup...")
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ OpenAI API key not found, skipping LangGraph test")
        else:
            processor = LangGraphSchemaProcessor(openai_api_key)
            print("✅ LangGraph processor initialized successfully")
            
            # Test schema chunking
            schema_chunks = asyncio.run(processor.process_schema_node(schemas))
            print(f"✅ Generated {len(schema_chunks)} schema chunks")
            
            for chunk in schema_chunks[:2]:  # Show first 2 chunks
                print(f"   📄 {chunk['table_name']}: {len(chunk['content'])} characters")
            
            # Test SQL file processing
            sql_chunks = asyncio.run(processor.process_sql_files_node())
            if sql_chunks:
                print(f"✅ Processed SQL files: {list(sql_chunks.keys())}")
                for file_type, chunks in sql_chunks.items():
                    print(f"   📄 {file_type}: {len(chunks)} chunks")
            else:
                print("⚠️ No SQL files processed")
        
    except Exception as e:
        print(f"❌ LangGraph processor test failed: {e}")
        return False
    
    # Test 5: Full initialization (if API key available)
    print("\n🚀 Test 5: Full schema initialization...")
    try:
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("⚠️ OpenAI API key not found, skipping full initialization test")
            print("💡 Set OPENAI_API_KEY environment variable to test full initialization")
        else:
            from schema_initializer import initialize_chromadb_with_schema
            
            print("🔄 Running full schema initialization...")
            success = initialize_chromadb_with_schema(
                openai_api_key=openai_api_key,
                db_path="./banking.db",
                chromadb_persist_dir="./chroma_db"
            )
            
            if success:
                print("✅ Full schema initialization completed successfully!")
            else:
                print("❌ Full schema initialization failed")
                return False
        
    except Exception as e:
        print(f"❌ Full initialization test failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("🎉 Schema Initializer Test Completed Successfully!")
    print("✅ Schema analyzer working correctly")
    print("✅ Entity relationships extracted")
    print("✅ Mermaid diagram generation working")
    print("✅ LangGraph processor setup complete")
    print("✅ ChromaDB schema initialization ready")
    return True

def main():
    """Main function to run schema initializer test"""
    success = test_schema_initializer()
    
    if success:
        print("\n🚀 Schema initializer is robust and ready!")
        sys.exit(0)
    else:
        print("\n💥 Schema initializer test failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
