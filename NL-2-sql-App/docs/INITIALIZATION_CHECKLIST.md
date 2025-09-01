# 🔍 Critical Initialization Checklist for SQL RAG Agent

## Overview
This document outlines the critical initialization steps required before allowing user queries to prevent workflow breaks and ensure system reliability.

---

## 1. 🌍 Environment & Configuration Initialization

### Status: ⏳ Pending
**Impact**: System-wide configuration and environment setup
**Failure Scenario**: Missing API keys, incorrect paths, permission issues
**Recovery Strategy**: Auto-detect and prompt for missing configurations

### Integration Tests:
- ✅ Environment variables validation
- ✅ Configuration file loading
- ✅ File permissions check
- ✅ API key validation

### Sample Checks:
```python
# Test environment variables
required_vars = ["OPENAI_API_KEY", "CHROMA_PERSIST_DIR", "DB_PATH"]
for var in required_vars:
    if not os.getenv(var):
        raise InitializationError(f"Missing {var}")

# Test file permissions
test_dirs = ["./chroma_db", "./reports", "./logs"]
for dir_path in test_dirs:
    if not os.path.exists(dir_path):
        os.makedirs(dir_path, exist_ok=True)
    # Test write permission
    test_file = os.path.join(dir_path, "test_write.tmp")
    with open(test_file, 'w') as f:
        f.write("test")
    os.remove(test_file)
```

---

## 2. 🗄️ Database Initialization

### Status: ⏳ Pending
**Impact**: Core data storage and schema availability
**Failure Scenario**: Database corruption, schema mismatch, data loss
**Recovery Strategy**: Recreate database from schema files

### Integration Tests:
- ✅ Database connection establishment
- ✅ Schema creation and validation
- ✅ Data loading verification
- ✅ Thread safety validation

### Sample Checks:
```python
# Test database initialization
initializer = DatabaseInitializer()
db_conn = initializer.initialize_database()

# Verify tables exist
cursor = db_conn.cursor()
cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
table_count = cursor.fetchone()[0]
assert table_count > 0, "No tables found in database"

# Verify data exists
for table in ["customers", "accounts", "transactions", "branches", "employees"]:
    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    assert count > 0, f"No data in {table} table"
```

---

## 3. 🧠 LLM Provider Initialization

### Status: ⏳ Pending
**Impact**: Natural language processing and SQL generation
**Failure Scenario**: API key invalid, service unavailable, rate limits
**Recovery Strategy**: Fallback to alternative providers or local models

### Integration Tests:
- ✅ LLM provider connectivity
- ✅ API key validation
- ✅ Model availability check
- ✅ Response time measurement

### Sample Checks:
```python
# Test LLM connectivity
provider = llm_config.get_default_provider()
api_key = llm_config.get_api_key(provider)

if provider == "openai":
    import openai
    openai.api_key = api_key
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=5
    )
    assert response.choices[0].message.content, "LLM not responding"

# Test embedding generation
embedder = LLMEmbedder(provider, api_key, llm_config.get_default_embedding_model())
test_embedding = embedder.generate_embedding("Test embedding")
assert len(test_embedding) > 0, "Embedding generation failed"
```

---

## 4. 🔍 Vector Database (ChromaDB) Initialization

### Status: ⏳ Pending
**Impact**: Schema context retrieval and semantic search
**Failure Scenario**: VectorDB corruption, embedding failures, search issues
**Recovery Strategy**: Rebuild vector database from schema

### Integration Tests:
- ✅ ChromaDB connection establishment
- ✅ Collection creation and management
- ✅ Document storage and retrieval
- ✅ Vector search functionality

### Sample Checks:
```python
# Test ChromaDB initialization
chroma_manager = ChromaDBManager("./chroma_db")
collection = chroma_manager.get_or_create_collection("test_collection")
assert collection is not None, "ChromaDB collection creation failed"

# Test document storage
documents = ["Test document 1", "Test document 2"]
metadatas = [{"type": "test"}, {"type": "test"}]
ids = ["doc1", "doc2"]
chroma_manager.add_documents("test_collection", documents, metadatas, ids)

# Test vector search
results = chroma_manager.query("test_collection", ["test query"], n_results=2)
assert results and "documents" in results, "Vector search failed"
```

---

## 5. 🤖 Agent Initialization

### Status: ⏳ Pending
**Impact**: Core workflow execution and query processing
**Failure Scenario**: Agent failures, dependency issues, resource constraints
**Recovery Strategy**: Reinitialize agents with fallback configurations

### Integration Tests:
- ✅ Planner agent initialization
- ✅ Retriever agent setup
- ✅ SQL generator configuration
- ✅ Validator agent setup
- ✅ Executor agent initialization
- ✅ Summarizer agent setup

### Sample Checks:
```python
# Test Planner Agent
schema_tables = {"customers": ["id", "name"], "accounts": ["id", "customer_id"]}
planner = PlannerAgent(schema_tables)
test_analysis = planner.analyze_query("Find customers with accounts")
assert "tables_needed" in test_analysis, "Planner agent not working"

# Test Retriever Agent
retriever = EnhancedRetriever("./chroma_db")
test_context = retriever.retrieve_context("Find customer information")
assert test_context is not None, "Retriever agent not working"

# Test Validator Agent
validator = ValidatorAgent(schema_tables)
is_safe, _ = validator.is_safe_sql("SELECT * FROM customers LIMIT 10")
assert is_safe, "Validator agent not working"

# Test Executor Agent
executor = ExecutorAgent(":memory:")
test_result = executor.run_query("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
assert test_result.get("success"), "Executor agent not working"

# Test Summarizer Agent
summarizer = SummarizerAgent()
test_summary = summarizer.summarize_results([{"name": "Test"}], "Test query")
assert test_summary, "Summarizer agent not working"
```

---

## 6. 🔄 Workflow Integration Testing

### Status: ⏳ Pending
**Impact**: End-to-end query processing and result generation
**Failure Scenario**: Workflow breaks, data flow issues, integration failures
**Recovery Strategy**: Isolate and fix broken components

### Integration Tests:
- ✅ End-to-end workflow execution
- ✅ Data flow validation
- ✅ Error handling verification
- ✅ Performance benchmarking

### Sample Checks:
```python
# Test complete workflow
test_query = "Find all customers"
schema_tables = {"customers": ["id", "name", "email"]}

# Initialize all agents
planner = PlannerAgent(schema_tables)
validator = ValidatorAgent(schema_tables)
executor = ExecutorAgent(":memory:")

# Run workflow steps
plan = planner.analyze_query(test_query)
test_sql = "SELECT * FROM customers LIMIT 5"
is_safe, _ = validator.is_safe_sql(test_sql)
result = executor.run_query(test_sql)

assert plan and is_safe and result.get("success"), "End-to-end workflow failed"
```

---

## 7. 🛡️ Security & Validation Setup

### Status: ⏳ Pending
**Impact**: Query safety and system security
**Failure Scenario**: Security bypasses, unsafe queries, validation failures
**Recovery Strategy**: Strengthen validation rules and security measures

### Integration Tests:
- ✅ Security guard initialization
- ✅ Validation rule setup
- ✅ SQL injection prevention
- ✅ Resource limit enforcement

### Sample Checks:
```python
# Test security guards
schema_tables = {"customers": ["id", "name"]}
validator = ValidatorAgent(schema_tables)

# Test dangerous operations are blocked
dangerous_queries = [
    "DROP TABLE customers",
    "DELETE FROM customers",
    "UPDATE customers SET name = 'hacked'",
    "INSERT INTO customers VALUES (999, 'hacker')"
]

for query in dangerous_queries:
    is_safe, reason = validator.is_safe_sql(query)
    assert not is_safe, f"Dangerous query allowed: {query}"

# Test safe queries are allowed
safe_queries = [
    "SELECT * FROM customers LIMIT 10",
    "SELECT COUNT(*) FROM customers",
    "SELECT name FROM customers WHERE id = 1"
]

for query in safe_queries:
    is_safe, _ = validator.is_safe_sql(query)
    assert is_safe, f"Safe query blocked: {query}"
```

---

## 8. 📊 Performance & Monitoring Setup

### Status: ⏳ Pending
**Impact**: System performance tracking and optimization
**Failure Scenario**: Performance degradation, monitoring failures, resource exhaustion
**Recovery Strategy**: Performance optimization and resource management

### Integration Tests:
- ✅ Performance monitoring initialization
- ✅ Timing tracker setup
- ✅ Resource usage monitoring
- ✅ Performance baseline establishment

### Sample Checks:
```python
# Test performance monitoring
import time

# Test agent performance
start_time = time.time()
schema_tables = {"customers": ["id", "name"]}
planner = PlannerAgent(schema_tables)
planner.analyze_query("Find customers")
end_time = time.time()

duration = end_time - start_time
assert duration < 1.0, f"Agent performance too slow: {duration:.3f}s"

# Test LLM response time
start_time = time.time()
# Simulate LLM call
time.sleep(0.1)  # Simulate 100ms response
end_time = time.time()

llm_duration = end_time - start_time
assert llm_duration < 0.5, f"LLM response too slow: {llm_duration:.3f}s"
```

---

## 🚀 Initialization Sequence

### Phase 1: Environment Setup
1. Load environment variables
2. Validate configuration
3. Check file permissions
4. Initialize logging

### Phase 2: Core Services
1. Initialize database
2. Setup LLM provider
3. Initialize VectorDB
4. Configure agents

### Phase 3: Integration Testing
1. Run component tests
2. Execute workflow tests
3. Validate security measures
4. Establish performance baselines

### Phase 4: System Readiness
1. Final validation
2. Status reporting
3. User notification
4. Enable query processing

---

## 📋 Initialization Status Dashboard

| Component | Status | Last Check | Issues | Actions |
|-----------|--------|------------|--------|---------|
| Environment | ⏳ Pending | - | - | Run environment tests |
| Database | ⏳ Pending | - | - | Initialize database |
| LLM Provider | ⏳ Pending | - | - | Test LLM connectivity |
| VectorDB | ⏳ Pending | - | - | Setup ChromaDB |
| Agents | ⏳ Pending | - | - | Initialize all agents |
| Workflow | ⏳ Pending | - | - | Test end-to-end flow |
| Security | ⏳ Pending | - | - | Setup validation |
| Performance | ⏳ Pending | - | - | Initialize monitoring |

---

## 🔧 Recovery Procedures

### Environment Issues:
```python
# Auto-recovery for missing environment variables
missing_vars = []
for var in required_vars:
    if not os.getenv(var):
        missing_vars.append(var)

if missing_vars:
    print(f"Missing environment variables: {missing_vars}")
    print("Please set these variables and restart the application")
    sys.exit(1)
```

### Database Issues:
```python
# Auto-recovery for database issues
try:
    db_conn = initializer.initialize_database()
except Exception as e:
    print(f"Database initialization failed: {e}")
    print("Attempting to recreate database...")
    # Recreate database from schema files
    db_conn = initializer.recreate_database()
```

### LLM Issues:
```python
# Auto-recovery for LLM issues
try:
    # Test LLM connectivity
    test_response = llm.generate_response("test")
except Exception as e:
    print(f"LLM connectivity failed: {e}")
    print("Switching to fallback provider...")
    # Switch to alternative provider
    llm = llm_config.get_fallback_provider()
```

---

## ✅ Success Criteria

### All Components Must Pass:
- [ ] Environment variables loaded successfully
- [ ] Database initialized with schema and data
- [ ] LLM provider responding within 500ms
- [ ] VectorDB storing and retrieving documents
- [ ] All agents initialized and functional
- [ ] End-to-end workflow completing successfully
- [ ] Security validation blocking dangerous queries
- [ ] Performance monitoring active

### System Ready When:
- All integration tests pass
- No critical errors in logs
- Performance within acceptable limits
- Security measures active
- User interface responsive

---

## 🚨 Failure Handling

### Critical Failures:
- **Database corruption**: Recreate from schema files
- **LLM unavailability**: Switch to fallback provider
- **VectorDB issues**: Rebuild from schema information
- **Agent failures**: Reinitialize with default settings

### Non-Critical Failures:
- **Performance degradation**: Optimize and retry
- **Minor validation issues**: Log and continue
- **Monitoring failures**: Continue without monitoring

### User Communication:
- Clear error messages
- Recovery progress updates
- Alternative options when available
- Contact information for support
