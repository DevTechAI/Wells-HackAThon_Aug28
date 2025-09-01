#!/usr/bin/env python3
"""
Test Enhanced Pipeline with Rich Schema Metadata
Demonstrates the enhanced retriever, planner, and SQL generator with schema context
"""

import sys
import os
sys.path.append('./backend')

from retriever import RetrieverAgent
from planner import PlannerAgent
from llm_sql_generator import LLMSQLGenerator

def test_enhanced_pipeline():
    """Test the enhanced pipeline with rich schema metadata"""
    
    print("🚀 Testing Enhanced Pipeline with Rich Schema Metadata")
    print("=" * 60)
    
    # Initialize agents
    print("\n1️⃣ Initializing Enhanced Agents...")
    retriever = RetrieverAgent('./chroma_db')
    planner = PlannerAgent({
        'customers': ['id', 'name', 'email', 'balance', 'status'],
        'accounts': ['id', 'customer_id', 'account_type', 'balance'],
        'transactions': ['id', 'account_id', 'amount', 'type', 'date']
    })
    generator = LLMSQLGenerator()
    
    print("✅ Enhanced agents initialized")
    
    # Test query
    query = "Show me customers with high balance who are active"
    print(f"\n2️⃣ Testing Query: '{query}'")
    
    # Step 1: Enhanced Retrieval with Schema Metadata
    print("\n🔍 Step 1: Enhanced Retrieval with Schema Metadata")
    print("-" * 40)
    
    # Simulate rich schema context (since ChromaDB needs API key)
    rich_schema_context = {
        'schema_metadata': {
            'customers': {
                'table_name': 'customers',
                'column_count': 5,
                'has_primary_key': True,
                'distinct_values_count': 3,
                'value_distributions_count': 2
            },
            'accounts': {
                'table_name': 'accounts',
                'column_count': 4,
                'has_primary_key': True,
                'distinct_values_count': 2,
                'value_distributions_count': 1
            }
        },
        'distinct_values': {
            'customers': {
                'balance': [1000, 5000, 10000, 25000, 50000],
                'status': ['active', 'inactive', 'suspended'],
                'email': ['john@example.com', 'jane@example.com', 'bob@example.com']
            },
            'accounts': {
                'account_type': ['savings', 'checking', 'credit'],
                'balance': [500, 2000, 5000, 15000, 30000]
            }
        },
        'where_suggestions': {
            'customers': [
                'balance > 10000',
                'balance > 25000',
                'status = active',
                'status = inactive'
            ],
            'accounts': [
                'account_type = savings',
                'account_type = checking',
                'balance > 5000'
            ]
        },
        'schema_context': [
            {
                'content': 'Table: customers\nColumns:\n- id: INTEGER PRIMARY KEY\n- name: TEXT\n- email: TEXT\n- balance: DECIMAL\n- status: TEXT\n\nDistinct Values (for WHERE conditions):\n- balance: [1000, 5000, 10000, 25000, 50000]\n- status: [active, inactive, suspended]',
                'metadata': {
                    'table_name': 'customers',
                    'column_count': 5,
                    'distinct_values_count': 3
                }
            }
        ]
    }
    
    print(f"📊 Retrieved schema metadata for {len(rich_schema_context['schema_metadata'])} tables")
    print(f"📊 Found distinct values for {len(rich_schema_context['distinct_values'])} tables")
    print(f"📊 Generated WHERE suggestions for {len(rich_schema_context['where_suggestions'])} tables")
    
    # Show sample distinct values
    for table_name, columns in rich_schema_context['distinct_values'].items():
        print(f"  📋 {table_name}:")
        for column_name, values in columns.items():
            print(f"    - {column_name}: {values[:3]}...")
    
    # Step 2: Enhanced Planning with Schema Metadata
    print("\n📋 Step 2: Enhanced Planning with Schema Metadata")
    print("-" * 40)
    
    enhanced_plan = planner.plan_with_schema_metadata(query, rich_schema_context)
    
    print(f"📊 Table details extracted for {len(enhanced_plan['table_details'])} tables")
    print(f"📊 Column mappings identified for {len(enhanced_plan['column_mappings'])} tables")
    print(f"📊 WHERE conditions suggested: {len(enhanced_plan['where_conditions'])}")
    print(f"📊 JOIN requirements identified: {len(enhanced_plan['join_requirements'])}")
    print(f"📊 Value constraints extracted for {len(enhanced_plan['value_constraints'])} tables")
    
    # Show enhanced plan details
    if enhanced_plan['table_details']:
        print("\n  📋 Table Details:")
        for table_name, details in enhanced_plan['table_details'].items():
            print(f"    - {table_name}: {details['column_count']} columns, {details['distinct_values_count']} distinct values")
    
    if enhanced_plan['column_mappings']:
        print("\n  📋 Column Mappings:")
        for table_name, columns in enhanced_plan['column_mappings'].items():
            print(f"    - {table_name}: {', '.join(columns)}")
    
    if enhanced_plan['where_conditions']:
        print("\n  📋 WHERE Conditions:")
        for condition in enhanced_plan['where_conditions'][:3]:
            print(f"    - {condition}")
    
    # Step 3: Enhanced SQL Generation with Schema Context
    print("\n🧠 Step 3: Enhanced SQL Generation with Schema Context")
    print("-" * 40)
    
    # Build enhanced prompt
    enhanced_prompt = generator._build_enhanced_prompt(
        query=query,
        schema_metadata=rich_schema_context['schema_metadata'],
        distinct_values=rich_schema_context['distinct_values'],
        where_suggestions=rich_schema_context['where_suggestions'],
        table_details=enhanced_plan['table_details'],
        column_mappings=enhanced_plan['column_mappings'],
        where_conditions=enhanced_plan['where_conditions'],
        join_requirements=enhanced_plan['join_requirements'],
        value_constraints=enhanced_plan['value_constraints']
    )
    
    print(f"📝 Enhanced prompt created: {len(enhanced_prompt)} characters")
    print("\n📝 Sample Enhanced Prompt:")
    print("-" * 30)
    print(enhanced_prompt[:800] + "..." if len(enhanced_prompt) > 800 else enhanced_prompt)
    
    # Step 4: Demonstrate WHERE Condition Suggestions
    print("\n🎯 Step 4: WHERE Condition Suggestions")
    print("-" * 40)
    
    # Test WHERE suggestions for specific columns
    where_suggestions = retriever.get_where_condition_suggestions(
        query="customers with high balance",
        table_name="customers",
        column_name="balance"
    )
    
    print(f"🎯 WHERE suggestions for customers.balance: {len(where_suggestions)}")
    for suggestion in where_suggestions[:3]:
        print(f"  - {suggestion}")
    
    # Step 5: Show Complete Pipeline Flow
    print("\n🔄 Step 5: Complete Enhanced Pipeline Flow")
    print("-" * 40)
    
    print("""
    Enhanced Pipeline Flow:
    
    1. 🔍 RETRIEVER AGENT (Enhanced)
       ↓ Retrieves from multiple ChromaDB collections:
       - database_schema (table structures + distinct values)
       - sql_schema (table definitions)
       - sql_sample_data (real data examples)
       - entity_relationships (Mermaid diagrams)
       ↓ Extracts:
       - Schema metadata (column counts, constraints)
       - Distinct values for WHERE conditions
       - WHERE condition suggestions
       - Value distributions
    
    2. 📋 PLANNER AGENT (Enhanced)
       ↓ Analyzes with rich context:
       - Table details (column counts, constraints)
       - Column mappings (relevant columns)
       - WHERE conditions (suggested filters)
       - JOIN requirements (table relationships)
       - Value constraints (exact values)
    
    3. 🧠 SQL GENERATOR (Enhanced)
       ↓ Generates SQL with:
       - Exact table and column names
       - Precise WHERE conditions using distinct values
       - Proper JOIN conditions
       - Value constraints for filtering
       - Optimized queries with real data
    
    4. ✅ Result: Schema-aware, precise SQL generation!
    """)
    
    print("✅ Enhanced Pipeline Test Complete!")
    print("🎯 Key Benefits:")
    print("  - Schema metadata provides table structure context")
    print("  - Distinct values enable precise WHERE conditions")
    print("  - WHERE suggestions guide SQL generation")
    print("  - Value constraints ensure accurate filtering")
    print("  - Real data examples improve query quality")

if __name__ == "__main__":
    test_enhanced_pipeline()
