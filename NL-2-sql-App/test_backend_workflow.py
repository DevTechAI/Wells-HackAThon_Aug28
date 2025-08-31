#!/usr/bin/env python3
"""
Test script to verify backend workflow functionality
"""

import os
import sys
sys.path.append('./backend')

from backend.pipeline import NL2SQLPipeline, PipelineConfig
from backend.planner import PlannerAgent
from backend.retriever import RetrieverAgent
from backend.llm_sql_generator import LLMSQLGenerator
from backend.validator import ValidatorAgent
from backend.executor import ExecutorAgent
from backend.summarizer import SummarizerAgent
from backend.db_manager import get_db_manager

def test_backend_workflow():
    """Test the complete backend workflow"""
    print("🧪 Testing Backend Workflow")
    print("=" * 50)
    
    try:
        # Set environment variables
        os.environ["DB_PATH"] = "banking.db"
        os.environ["CHROMA_PERSIST_DIR"] = "./chroma_db"
        
        # Test query
        query = "Find all customers who have both checking and savings accounts"
        print(f"📝 Query: {query}")
        
        # Initialize database manager
        db_path = os.getenv("DB_PATH", "banking.db")
        db_manager = get_db_manager(db_path)
        print(f"🗄️ Database: {db_path}")
        
        # Get schema tables
        schema_tables = {}
        try:
            conn = db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            print(f"📋 Tables found: {tables}")
            
            for table in tables:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                schema_tables[table] = columns
                print(f"  {table}: {columns}")
            
            db_manager.release_connection(conn)
        except Exception as e:
            print(f"❌ Error getting schema: {e}")
            return False
        
        # Initialize agents
        print("\n🤖 Initializing agents...")
        planner = PlannerAgent()
        retriever = RetrieverAgent()
        generator = LLMSQLGenerator()
        validator = ValidatorAgent()
        executor = ExecutorAgent(db_path, db_manager)
        summarizer = SummarizerAgent()
        
        # Configure pipeline
        config = PipelineConfig(max_retries=2, sql_row_limit=100)
        
        # Create pipeline
        pipeline = NL2SQLPipeline(
            planner=planner,
            retriever=retriever,
            generator=generator,
            validator=validator,
            executor=executor,
            summarizer=summarizer,
            schema_tables=schema_tables,
            config=config
        )
        
        print("✅ Pipeline created successfully")
        
        # Execute pipeline
        print("\n🚀 Executing pipeline...")
        result = pipeline.run(query)
        
        # Check result
        if result.get("success", False):
            print("✅ Pipeline executed successfully!")
            print(f"📊 SQL: {result.get('sql', 'N/A')}")
            print(f"📊 Results: {len(result.get('results', []))} rows")
            print(f"📊 Summary: {result.get('summary', 'N/A')[:100]}...")
            
            # Show diagnostics
            diagnostics = result.get("diagnostics", {})
            timings = diagnostics.get("timings_ms", {})
            print(f"⏱️ Timings: {timings}")
            
            return True
        else:
            print("❌ Pipeline failed!")
            print(f"📊 Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_backend_workflow()
    if success:
        print("\n🎉 Backend workflow test PASSED!")
    else:
        print("\n💥 Backend workflow test FAILED!")
        sys.exit(1)
