#!/usr/bin/env python3
"""
Test the comprehensive schema context generation
"""

def test_schema_context():
    """Test schema context generation"""
    
    print("🔍 Testing Comprehensive Schema Context")
    print("=" * 50)
    
    # Simulate the schema context generation
    table_schemas = {
        "branches": "CREATE TABLE branches (id TEXT PRIMARY KEY, name TEXT NOT NULL, address TEXT, city TEXT, state TEXT, zip_code TEXT, manager_id TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP);",
        "employees": "CREATE TABLE employees (id TEXT PRIMARY KEY, branch_id TEXT NOT NULL, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT, position TEXT, hire_date DATE, salary REAL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (branch_id) REFERENCES branches(id));",
    }
    
    table_descriptions = {
        "branches": "Branches table contains bank branch information including location, manager, and contact details. Each branch can have multiple employees and customers.",
        "employees": "Employees table contains staff information including their position, salary, and which branch they work at. The manager_id in branches table references employees.id.",
    }
    
    comprehensive_schema = []
    
    # Build comprehensive schema context
    for table_name, schema in table_schemas.items():
        comprehensive_schema.append(f"Table: {table_name}")
        comprehensive_schema.append(f"Schema: {schema}")
        comprehensive_schema.append(f"Description: {table_descriptions[table_name]}")
        comprehensive_schema.append("")
    
    # Add relationship information
    comprehensive_schema.append("Key Relationships:")
    comprehensive_schema.append("- branches.manager_id → employees.id (branch managers)")
    comprehensive_schema.append("")
    
    print(f"📚 Generated {len(comprehensive_schema)} schema items")
    print("\n📋 Schema Context Preview:")
    for i, item in enumerate(comprehensive_schema):
        print(f"  {i+1}. {item}")
    
    # Test if it contains the right information for branch/manager query
    query = "List all branches and their managers' names. Include branches without a manager."
    print(f"\n🔍 Testing query: {query}")
    
    schema_text = "\n".join(comprehensive_schema)
    if "branches.manager_id" in schema_text and "employees.id" in schema_text:
        print("✅ Schema contains branch-manager relationship")
    else:
        print("❌ Schema missing branch-manager relationship")
    
    if "LEFT JOIN" in schema_text or "JOIN" in schema_text:
        print("✅ Schema mentions JOIN operations")
    else:
        print("❌ Schema missing JOIN information")
    
    return len(comprehensive_schema) > 0

if __name__ == "__main__":
    test_schema_context()
