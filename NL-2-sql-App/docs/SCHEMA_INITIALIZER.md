# ChromaDB Schema Initializer with LangGraph

## 🎯 **Overview**
The ChromaDB Schema Initializer implements a LangGraph-based pipeline to automatically analyze database schemas, extract entity relationships, generate Mermaid diagrams, and store everything as embeddings in ChromaDB for enhanced NL2SQL query processing.

## 🏗️ **Architecture**

### **LangGraph Pipeline Flow:**
```
Database Schema → Schema Analyzer → LangGraph Nodes → ChromaDB Embeddings
     ↓
1. Schema Analysis Node
2. Embedding Generation Node  
3. Vector Store Loading Node
4. Entity Relationship Processing Node
```

## 📁 **Components**

### **1. SchemaAnalyzer**
- **Purpose**: Extracts table schemas and entity relationships from SQLite database
- **Features**:
  - Table schema extraction with column details
  - Primary key and foreign key detection
  - Unique constraint analysis
  - Sample data extraction
  - Entity relationship mapping

### **2. MermaidDiagramGenerator**
- **Purpose**: Generates Mermaid entity relationship diagrams
- **Features**:
  - Automatic ER diagram generation
  - Relationship type detection (one-to-one, one-to-many, many-to-many)
  - Visual representation of database structure

### **3. LangGraphSchemaProcessor**
- **Purpose**: Orchestrates the LangGraph pipeline
- **Nodes**:
  - **Node 1**: Schema preprocessing and chunking
  - **Node 2**: OpenAI embedding generation
  - **Node 3**: ChromaDB vector storage
  - **Node 4**: Entity relationship processing

## 🔧 **Key Features**

### **Schema Analysis**
```python
analyzer = SchemaAnalyzer("./banking.db")
schemas = analyzer.get_table_schemas()
relationships = analyzer.get_entity_relationships(schemas)
```

### **Mermaid Diagram Generation**
```python
diagram_generator = MermaidDiagramGenerator(openai_api_key)
mermaid_diagram = diagram_generator.generate_er_diagram(schemas, relationships)
```

### **LangGraph Pipeline**
```python
processor = LangGraphSchemaProcessor(openai_api_key)
success = await processor.run_pipeline("./banking.db")
```

## 📊 **Database Schema Analysis Results**

### **Tables Analyzed:**
- **branches**: 9 columns
- **employees**: 10 columns  
- **accounts**: 11 columns
- **transactions**: 10 columns
- **customers**: 12 columns

### **Entity Relationships Found:**
- `employees.branch_id` → `branches.id`
- `accounts.branch_id` → `branches.id`
- `accounts.customer_id` → `customers.id`
- `transactions.employee_id` → `employees.id`
- `transactions.account_id` → `accounts.id`
- `customers.branch_id` → `branches.id`

## 🚀 **Usage Examples**

### **Basic Initialization**
```python
from backend.schema_initializer import initialize_chromadb_with_schema

success = initialize_chromadb_with_schema(
    openai_api_key="your-api-key",
    db_path="./banking.db",
    chromadb_persist_dir="./chroma_db"
)
```

### **Integration with Main App**
```python
# In app.py - automatic initialization at startup
if not st.session_state.schema_initialized:
    success = initialize_chromadb_with_schema(openai_api_key)
    if success:
        st.session_state.schema_initialized = True
```

### **Manual Schema Analysis**
```python
from backend.schema_initializer import SchemaAnalyzer

analyzer = SchemaAnalyzer("./banking.db")
schemas = analyzer.get_table_schemas()

for schema in schemas:
    print(f"Table: {schema.table_name}")
    print(f"Columns: {len(schema.columns)}")
    print(f"Primary Key: {schema.primary_key}")
```

## 🧪 **Test Results**

### **Schema Analyzer Test:**
```
✅ Analyzed 5 tables:
   📋 branches: 9 columns
   📋 employees: 10 columns
   📋 accounts: 11 columns
   📋 transactions: 10 columns
   📋 customers: 12 columns

✅ Found 6 relationships:
   🔗 employees.branch_id -> branches.id
   🔗 accounts.branch_id -> branches.id
   🔗 accounts.customer_id -> customers.id
   🔗 transactions.employee_id -> employees.id
   🔗 transactions.account_id -> accounts.id
   🔗 customers.branch_id -> branches.id
```

## 📈 **Generated Mermaid Diagram**

```mermaid
erDiagram
    branches {
        INTEGER id PK
        TEXT name
        TEXT address
        TEXT city
        TEXT state
        TEXT zip_code
        TEXT phone
        TEXT email
        TEXT manager_name
    }
    employees {
        INTEGER id PK
        TEXT first_name
        TEXT last_name
        TEXT email
        TEXT phone
        TEXT hire_date
        TEXT job_title
        DECIMAL salary
        INTEGER branch_id
        TEXT manager_id
        TEXT status
    }
    accounts {
        INTEGER id PK
        TEXT account_number
        TEXT account_type
        DECIMAL balance
        TEXT status
        TEXT open_date
        TEXT close_date
        INTEGER customer_id
        INTEGER branch_id
        TEXT account_manager
        TEXT last_transaction_date
    }
    transactions {
        INTEGER id PK
        TEXT transaction_type
        DECIMAL amount
        TEXT description
        TEXT transaction_date
        TEXT status
        INTEGER account_id
        INTEGER employee_id
        TEXT reference_number
        TEXT notes
    }
    customers {
        INTEGER id PK
        TEXT first_name
        TEXT last_name
        TEXT email
        TEXT phone
        TEXT address
        TEXT city
        TEXT state
        TEXT zip_code
        TEXT date_of_birth
        INTEGER branch_id
        TEXT customer_since
    }
    employees }--|| branches : "employees.branch_id references branches.id"
    accounts }--|| branches : "accounts.branch_id references branches.id"
    accounts }--|| customers : "accounts.customer_id references customers.id"
    transactions }--|| employees : "transactions.employee_id references employees.id"
    transactions }--|| accounts : "transactions.account_id references accounts.id"
    customers }--|| branches : "customers.branch_id references branches.id"
```

## 🗂️ **ChromaDB Collections**

### **database_schema Collection**
- **Purpose**: Stores table schema embeddings
- **Content**: Detailed table descriptions with columns, constraints, and sample data
- **Metadata**: Table name, column count, primary key info, unique constraints

### **entity_relationships Collection**
- **Purpose**: Stores entity relationship embeddings
- **Content**: Relationship descriptions and Mermaid diagrams
- **Metadata**: Source/target tables, relationship types, column mappings

## 🔄 **LangGraph Node Details**

### **Node 1: Schema Preprocessing**
- Splits schema data into meaningful chunks
- Creates detailed table descriptions
- Extracts metadata for embedding context

### **Node 2: Embedding Generation**
- Uses OpenAI text-embedding-3-small model
- Generates embeddings for schema chunks
- Handles rate limiting and retries

### **Node 3: Vector Storage**
- Stores embeddings in ChromaDB
- Organizes by collection type
- Maintains metadata for retrieval

### **Node 4: Relationship Processing**
- Generates Mermaid diagrams
- Creates relationship descriptions
- Stores as separate embeddings

## 🛡️ **Error Handling**

### **Graceful Degradation**
- Continues without embeddings if OpenAI API unavailable
- Logs warnings for debugging
- Maintains application functionality

### **Rate Limiting**
- Exponential backoff for API calls
- Retry logic for failed requests
- Progress tracking for long operations

## 🎯 **Benefits for NL2SQL**

### **Enhanced Context**
- Rich schema information available for queries
- Entity relationships guide JOIN operations
- Sample data provides value examples

### **Improved Accuracy**
- Better understanding of table structures
- Relationship-aware query generation
- Constraint-aware SQL validation

### **Visual Understanding**
- Mermaid diagrams for complex relationships
- Visual representation of database structure
- Easy debugging of query logic

## 🔮 **Future Enhancements**

### **Planned Features**
- Dynamic schema updates
- Relationship strength scoring
- Query pattern analysis
- Performance optimization

### **Advanced Analytics**
- Schema change tracking
- Query performance correlation
- Usage pattern analysis
- Automated optimization suggestions

---

## 📝 **Summary**

The ChromaDB Schema Initializer provides a robust, LangGraph-based solution for automatically analyzing database schemas and creating rich embeddings for enhanced NL2SQL query processing. The system:

1. **Analyzes** database structure comprehensively
2. **Generates** visual representations with Mermaid diagrams
3. **Creates** embeddings for semantic search
4. **Integrates** seamlessly with existing ChromaDB singleton
5. **Enhances** NL2SQL query accuracy and context

This implementation significantly improves the quality and accuracy of natural language to SQL query conversion by providing rich schema context and entity relationship information.
