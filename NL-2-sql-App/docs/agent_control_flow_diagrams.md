# 🤖 SQL RAG Agent Control Flow Diagrams

## Overview
This document provides detailed text-based flow diagrams for each agent in the SQL RAG (Retrieval-Augmented Generation) system, showing the step-by-step algorithm control flow.

---

## 1. 🔍 Planner Agent Control Flow

```
START
  ↓
[Receive Natural Language Query]
  ↓
[Initialize Schema Context]
  ↓
[Extract Entities & Keywords]
  ↓
[Identify Required Tables]
  ↓
[Determine Query Type]
  ├─ SELECT → [Analyze Selection Criteria]
  ├─ COUNT → [Analyze Aggregation Needs]
  ├─ JOIN → [Analyze Relationship Requirements]
  └─ COMPLEX → [Analyze Multiple Operations]
  ↓
[Assess Query Complexity]
  ├─ SIMPLE → [Single Table, Basic Operations]
  ├─ MEDIUM → [Multiple Tables, JOINs]
  └─ COMPLEX → [Subqueries, Aggregations, Window Functions]
  ↓
[Check for Clarifications Needed]
  ├─ AMBIGUOUS_TERMS → [Request Term Definition]
  ├─ NUMERIC_THRESHOLDS → [Request Specific Values]
  ├─ DATE_RANGES → [Request Time Period]
  └─ ENTITY_REFERENCES → [Request Entity Specification]
  ↓
[Estimate Token Usage]
  ↓
[Generate Query Plan]
  ↓
[Return Analysis Results]
  ↓
END
```

### Planner Agent Decision Points:
- **Entity Recognition**: Identifies tables, columns, and relationships
- **Complexity Assessment**: Determines query difficulty level
- **Clarification Detection**: Flags ambiguous or incomplete queries
- **Resource Estimation**: Calculates expected token consumption

---

## 2. 🔍 Retriever Agent Control Flow

```
START
  ↓
[Receive Query Analysis from Planner]
  ↓
[Initialize Vector Database Connection]
  ↓
[Generate Query Embedding]
  ↓
[Search Vector Database]
  ├─ [Search Schema Context]
  ├─ [Search Column Information]
  ├─ [Search Sample Data Patterns]
  └─ [Search Query Templates]
  ↓
[Rank Retrieved Contexts by Relevance]
  ↓
[Filter Context by Tables]
  ↓
[Extract Distinct Values]
  ├─ [Get Column Unique Values]
  ├─ [Get Sample Data Ranges]
  └─ [Get Data Type Information]
  ↓
[Build Context Structure]
  ├─ [Schema Context]
  ├─ [Column Context]
  ├─ [Data Context]
  └─ [Query Context]
  ↓
[Validate Context Completeness]
  ↓
[Return Structured Context]
  ↓
END
```

### Retriever Agent Key Operations:
- **Semantic Search**: Uses embeddings to find relevant schema information
- **Context Ranking**: Prioritizes most relevant information
- **Value Extraction**: Provides actual data values for WHERE conditions
- **Structure Building**: Organizes context for SQL generation

---

## 3. 🧠 SQL Generator Agent Control Flow

```
START
  ↓
[Receive Query Plan & Context]
  ↓
[Initialize LLM Connection]
  ↓
[Build Prompt with Context]
  ├─ [System Prompt]
  ├─ [Schema Information]
  ├─ [Column Details]
  ├─ [Sample Data]
  └─ [Query Examples]
  ↓
[Generate SQL Query]
  ↓
[Validate SQL Syntax]
  ├─ VALID → [Proceed to Next Step]
  └─ INVALID → [Attempt Repair]
      ↓
      [Apply Repair Strategies]
      ├─ [Fix Syntax Errors]
      ├─ [Add Missing Keywords]
      ├─ [Correct Table References]
      └─ [Adjust JOIN Conditions]
      ↓
      [Re-validate SQL]
  ↓
[Check Query Completeness]
  ├─ COMPLETE → [Proceed]
  └─ INCOMPLETE → [Apply Fallback Logic]
      ↓
      [Generate Safe Fallback Query]
      ├─ [Use Basic SELECT]
      ├─ [Add LIMIT Clause]
      └─ [Include Error Handling]
  ↓
[Return Generated SQL]
  ↓
END
```

### SQL Generator Agent Fallback Logic:
- **Primary Generation**: Uses LLM with full context
- **Syntax Repair**: Fixes common SQL syntax issues
- **Fallback Generation**: Creates safe, basic queries when LLM fails
- **Safety Checks**: Ensures queries are executable

---

## 4. 🛡️ Validator Agent Control Flow

```
START
  ↓
[Receive Generated SQL Query]
  ↓
[Parse SQL Structure]
  ↓
[Check Security Guards]
  ├─ [DANGEROUS_OPERATIONS]
  │   ├─ DROP → [BLOCK]
  │   ├─ DELETE → [BLOCK]
  │   ├─ UPDATE → [BLOCK]
  │   └─ INSERT → [BLOCK]
  ├─ [LIMIT_INJECTION]
  │   ├─ No LIMIT → [ADD_LIMIT]
  │   └─ High LIMIT → [REDUCE_LIMIT]
  ├─ [COMPLEXITY_CHECK]
  │   ├─ Too Complex → [SIMPLIFY]
  │   └─ Acceptable → [PROCEED]
  └─ [TABLE_VALIDATION]
      ├─ Invalid Table → [REJECT]
      └─ Valid Table → [PROCEED]
  ↓
[Validate Schema Compliance]
  ├─ [Check Table Existence]
  ├─ [Check Column Existence]
  ├─ [Check Data Types]
  └─ [Check Relationships]
  ↓
[Assess Query Safety]
  ├─ SAFE → [Approve Query]
  └─ UNSAFE → [Reject Query]
      ↓
      [Generate Safety Report]
      ↓
      [Return Rejection Reason]
  ↓
[Return Validation Result]
  ↓
END
```

### Validator Agent Security Checks:
- **Operation Blocking**: Prevents destructive operations
- **Limit Enforcement**: Ensures reasonable result sizes
- **Schema Validation**: Verifies table/column existence
- **Complexity Control**: Prevents overly complex queries

---

## 5. ⚡ Executor Agent Control Flow

```
START
  ↓
[Receive Validated SQL Query]
  ↓
[Get Thread-Safe Database Connection]
  ↓
[Prepare Query Execution]
  ├─ [Set Query Timeout]
  ├─ [Set Result Limit]
  └─ [Set Error Handling]
  ↓
[Execute SQL Query]
  ↓
[Check Execution Result]
  ├─ SUCCESS → [Process Results]
  └─ ERROR → [Handle Error]
      ↓
      [Error Analysis]
      ├─ [Syntax Error] → [Return Error Details]
      ├─ [Permission Error] → [Return Access Denied]
      ├─ [Timeout Error] → [Return Timeout Message]
      └─ [Other Error] → [Return Generic Error]
      ↓
      [Return Error Response]
  ↓
[Process Query Results]
  ├─ [Convert to List of Dictionaries]
  ├─ [Handle Empty Results]
  ├─ [Format Data Types]
  └─ [Add Result Metadata]
  ↓
[Release Database Connection]
  ↓
[Return Execution Results]
  ↓
END
```

### Executor Agent Error Handling:
- **Connection Management**: Thread-safe database access
- **Timeout Protection**: Prevents hanging queries
- **Error Classification**: Categorizes different error types
- **Resource Cleanup**: Ensures proper connection release

---

## 6. 📊 Summarizer Agent Control Flow

```
START
  ↓
[Receive Query Results & Original Query]
  ↓
[Analyze Result Structure]
  ├─ [Count Total Records]
  ├─ [Identify Data Types]
  ├─ [Detect Patterns]
  └─ [Assess Result Size]
  ↓
[Generate Summary Based on Query Type]
  ├─ [COUNT_QUERY]
  │   ├─ [Extract Count Value]
  │   ├─ [Provide Context]
  │   └─ [Add Insights]
  ├─ [LIST_QUERY]
  │   ├─ [Summarize Record Count]
  │   ├─ [Highlight Key Data]
  │   └─ [Provide Overview]
  ├─ [ANALYSIS_QUERY]
  │   ├─ [Identify Trends]
  │   ├─ [Calculate Statistics]
  │   └─ [Provide Insights]
  └─ [COMPLEX_QUERY]
      ├─ [Break Down Results]
      ├─ [Explain Relationships]
      └─ [Provide Context]
  ↓
[Format Summary Output]
  ├─ [Create Natural Language Summary]
  ├─ [Add Key Statistics]
  ├─ [Include Data Insights]
  └─ [Provide Actionable Information]
  ↓
[Return Summary]
  ↓
END
```

### Summarizer Agent Analysis Types:
- **Quantitative Analysis**: Counts, averages, trends
- **Qualitative Analysis**: Patterns, relationships, insights
- **Contextual Information**: Background and relevance
- **Actionable Insights**: Recommendations and next steps

---

## 7. 🔄 Overall Workflow Control Flow

```
START
  ↓
[User Input: Natural Language Query]
  ↓
[System Initialization Check]
  ├─ [Database Ready] → [Proceed]
  ├─ [LLM Available] → [Proceed]
  ├─ [VectorDB Ready] → [Proceed]
  └─ [Any Not Ready] → [Initialize Components]
  ↓
[Planner Agent]
  ├─ [Query Analysis] → [Success]
  └─ [Clarification Needed] → [Request User Input]
  ↓
[Retriever Agent]
  ├─ [Context Retrieval] → [Success]
  └─ [Context Missing] → [Use Fallback Context]
  ↓
[SQL Generator Agent]
  ├─ [SQL Generation] → [Success]
  └─ [Generation Failed] → [Use Fallback SQL]
  ↓
[Validator Agent]
  ├─ [Validation Passed] → [Proceed]
  └─ [Validation Failed] → [Return Error]
  ↓
[Executor Agent]
  ├─ [Query Execution] → [Success]
  └─ [Execution Failed] → [Return Error]
  ↓
[Summarizer Agent]
  ├─ [Summary Generation] → [Success]
  └─ [Summary Failed] → [Use Basic Summary]
  ↓
[Return Results to User]
  ↓
END
```

### Workflow Error Handling:
- **Component Failures**: Graceful degradation with fallbacks
- **User Clarifications**: Interactive resolution of ambiguities
- **Resource Management**: Proper cleanup and connection release
- **Result Formatting**: Consistent output structure

---

## 8. 🚨 Error Handling & Recovery Flow

```
ERROR DETECTED
  ↓
[Error Classification]
  ├─ [LLM Error] → [Use Fallback Logic]
  ├─ [Database Error] → [Retry with New Connection]
  ├─ [VectorDB Error] → [Use Cached Context]
  ├─ [Validation Error] → [Return Error to User]
  └─ [Execution Error] → [Return Error Details]
  ↓
[Error Recovery Strategy]
  ├─ [Retry Operation] → [Attempt Again]
  ├─ [Use Fallback] → [Alternative Method]
  ├─ [Graceful Degradation] → [Reduced Functionality]
  └─ [User Notification] → [Request Action]
  ↓
[Error Logging]
  ↓
[Continue or Terminate]
  ↓
END
```

### Error Recovery Mechanisms:
- **Automatic Retry**: For transient failures
- **Fallback Methods**: Alternative approaches when primary fails
- **Graceful Degradation**: Reduced functionality rather than complete failure
- **User Communication**: Clear error messages and next steps

---

## 9. ⏱️ Performance Monitoring Flow

```
START
  ↓
[Initialize Timing Trackers]
  ↓
[Track Agent Execution Times]
  ├─ [Planner Time]
  ├─ [Retriever Time]
  ├─ [SQL Generator Time]
  ├─ [Validator Time]
  ├─ [Executor Time]
  └─ [Summarizer Time]
  ↓
[Track External Service Times]
  ├─ [LLM Interaction Time]
  ├─ [VectorDB Query Time]
  └─ [Database Query Time]
  ↓
[Calculate Performance Metrics]
  ├─ [Total Query Time]
  ├─ [Agent Efficiency]
  ├─ [Bottleneck Identification]
  └─ [Performance Trends]
  ↓
[Store Performance Data]
  ↓
[Display Performance Dashboard]
  ↓
END
```

### Performance Metrics:
- **Response Time**: Total time from query to result
- **Agent Efficiency**: Time per agent vs. total time
- **External Service Latency**: LLM, VectorDB, Database response times
- **Bottleneck Analysis**: Identification of slow components

---

## 10. 🔒 Security & Validation Flow

```
START
  ↓
[Input Sanitization]
  ├─ [SQL Injection Check]
  ├─ [XSS Prevention]
  └─ [Input Length Validation]
  ↓
[Query Intent Analysis]
  ├─ [Benign Query] → [Proceed]
  ├─ [Suspicious Query] → [Additional Validation]
  └─ [Malicious Query] → [Block]
  ↓
[SQL Security Validation]
  ├─ [Dangerous Operations] → [Block]
  ├─ [Resource Limits] → [Enforce]
  └─ [Schema Compliance] → [Validate]
  ↓
[Execution Safety]
  ├─ [Query Timeout] → [Enforce]
  ├─ [Result Size Limit] → [Enforce]
  └─ [Memory Usage] → [Monitor]
  ↓
[Output Sanitization]
  ↓
[Return Secure Results]
  ↓
END
```

### Security Measures:
- **Input Validation**: Prevents malicious input
- **SQL Injection Prevention**: Validates and sanitizes queries
- **Resource Limiting**: Prevents resource exhaustion
- **Output Sanitization**: Ensures safe output

---

## Summary

Each agent follows a structured control flow with:
1. **Input Validation**: Ensures proper input format and content
2. **Core Processing**: Performs the main agent function
3. **Error Handling**: Manages failures and exceptions
4. **Output Generation**: Produces structured results
5. **Resource Management**: Ensures proper cleanup

The overall system provides:
- **Robustness**: Multiple fallback mechanisms
- **Security**: Comprehensive validation and sanitization
- **Performance**: Monitoring and optimization
- **User Experience**: Clear error messages and progress tracking
