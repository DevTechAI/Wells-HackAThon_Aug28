#!/usr/bin/env python3
"""
Unit tests for QueryHistory and render_recent_queries_sidebar functionality
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Add the current directory to the path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

class TestQueryHistory(unittest.TestCase):
    """Test cases for QueryHistory class"""
    
    def setUp(self):
        """Set up test environment"""
        # Mock streamlit session state
        self.mock_session_state = {}
        
    def test_query_history_initialization(self):
        """Test QueryHistory initialization"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            # Test fresh initialization
            query_history = QueryHistory()
            self.assertIn('query_history', self.mock_session_state)
            self.assertEqual(self.mock_session_state['query_history'], [])
            
            # Test that get_history returns a list
            history = query_history.get_history()
            self.assertIsInstance(history, list)
            self.assertEqual(len(history), 0)
    
    def test_query_history_add_query(self):
        """Test adding queries to history"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            query_history = QueryHistory()
            
            # Add a test query
            test_query = "Find all customers"
            test_sql = "SELECT * FROM customers"
            test_results_count = 5
            test_timestamp = "10:30:00"
            
            query_history.add_query(test_query, test_sql, test_results_count, test_timestamp)
            
            # Verify the query was added
            history = query_history.get_history()
            self.assertEqual(len(history), 1)
            
            entry = history[0]
            self.assertEqual(entry['query'], test_query)
            self.assertEqual(entry['sql'], test_sql)
            self.assertEqual(entry['results_count'], test_results_count)
            self.assertEqual(entry['timestamp'], test_timestamp)
    
    def test_query_history_limit(self):
        """Test that query history is limited to 10 entries"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            query_history = QueryHistory()
            
            # Add 12 queries
            for i in range(12):
                query_history.add_query(f"Query {i}", f"SELECT * FROM table{i}", i, f"10:{i:02d}:00")
            
            # Verify only 10 are kept
            history = query_history.get_history()
            self.assertEqual(len(history), 10)
            
            # Verify the most recent query is first
            self.assertEqual(history[0]['query'], "Query 11")
            self.assertEqual(history[9]['query'], "Query 2")
    
    def test_query_history_corrupted_state(self):
        """Test handling of corrupted session state"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            # Simulate corrupted state (not a list)
            self.mock_session_state['query_history'] = "not a list"
            
            query_history = QueryHistory()
            
            # Should reset to empty list
            self.assertEqual(self.mock_session_state['query_history'], [])
            
            # Should return empty list
            history = query_history.get_history()
            self.assertIsInstance(history, list)
            self.assertEqual(len(history), 0)
    
    def test_query_history_add_query_with_corrupted_state(self):
        """Test adding query when session state is corrupted"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            # Simulate corrupted state
            self.mock_session_state['query_history'] = "not a list"
            
            query_history = QueryHistory()
            query_history.add_query("Test query", "SELECT * FROM test", 1, "10:00:00")
            
            # Should work correctly
            history = query_history.get_history()
            self.assertEqual(len(history), 1)
            self.assertEqual(history[0]['query'], "Test query")

class TestRenderRecentQueriesSidebar(unittest.TestCase):
    """Test cases for render_recent_queries_sidebar function"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_session_state = {}
        self.mock_st = Mock()
        
    def test_render_recent_queries_sidebar_empty_history(self):
        """Test rendering with empty history"""
        with patch('streamlit.session_state', self.mock_session_state), \
             patch('streamlit.sidebar', self.mock_st):
            
            from app import render_recent_queries_sidebar
            
            # Test with no query_history in session state
            render_recent_queries_sidebar()
            
            # Should call sidebar.info with "No recent queries"
            self.mock_st.info.assert_called_with("No recent queries")
    
    def test_render_recent_queries_sidebar_with_valid_history(self):
        """Test rendering with valid history"""
        with patch('streamlit.session_state', self.mock_session_state), \
             patch('streamlit.sidebar', self.mock_st):
            
            from app import QueryHistory, render_recent_queries_sidebar
            
            # Create a QueryHistory instance and add some queries
            query_history = QueryHistory()
            query_history.add_query("Find customers", "SELECT * FROM customers", 5, "10:00:00")
            query_history.add_query("Find accounts", "SELECT * FROM accounts", 3, "10:01:00")
            
            # Mock the sidebar methods
            mock_expander = Mock()
            mock_expander.write = Mock()
            self.mock_st.expander.return_value.__enter__.return_value = mock_expander
            
            render_recent_queries_sidebar()
            
            # Should call expander for each query
            self.assertEqual(self.mock_st.expander.call_count, 2)
            
            # Verify expander calls
            calls = self.mock_st.expander.call_args_list
            self.assertIn("Query 1: Find customers", calls[0][0][0])
            self.assertIn("Query 2: Find accounts", calls[1][0][0])
    
    def test_render_recent_queries_sidebar_with_corrupted_history(self):
        """Test rendering with corrupted history"""
        with patch('streamlit.session_state', self.mock_session_state), \
             patch('streamlit.sidebar', self.mock_st):
            
            from app import render_recent_queries_sidebar
            
            # Simulate corrupted query_history (not a QueryHistory object)
            self.mock_session_state['query_history'] = "not a QueryHistory object"
            
            render_recent_queries_sidebar()
            
            # Should show "No recent queries" for corrupted state
            self.mock_st.info.assert_called_with("No recent queries")
    
    def test_render_recent_queries_sidebar_with_invalid_entries(self):
        """Test rendering with invalid entries in history"""
        with patch('streamlit.session_state', self.mock_session_state), \
             patch('streamlit.sidebar', self.mock_st):
            
            from app import render_recent_queries_sidebar
            
            # Create history with invalid entries
            self.mock_session_state['query_history'] = [
                {"query": "Valid query", "sql": "SELECT * FROM test", "results_count": 1, "timestamp": "10:00:00"},
                "not a dict",  # Invalid entry
                {"invalid": "missing query key"},  # Invalid entry
                {"query": "Another valid query", "sql": "SELECT * FROM test2", "results_count": 2, "timestamp": "10:01:00"}
            ]
            
            # Mock the sidebar methods
            mock_expander = Mock()
            mock_expander.write = Mock()
            self.mock_st.expander.return_value.__enter__.return_value = mock_expander
            
            render_recent_queries_sidebar()
            
            # Should call expander only for valid entries
            self.assertEqual(self.mock_st.expander.call_count, 2)
            
            # Should show warnings for invalid entries
            warning_calls = [call for call in self.mock_st.warning.call_args_list if "Invalid query entry format" in str(call)]
            self.assertEqual(len(warning_calls), 2)

class TestQueryHistoryIntegration(unittest.TestCase):
    """Integration tests for QueryHistory with real session state"""
    
    def setUp(self):
        """Set up test environment"""
        self.mock_session_state = {}
        
    def test_full_query_history_workflow(self):
        """Test complete workflow of adding and retrieving queries"""
        with patch('streamlit.session_state', self.mock_session_state):
            from app import QueryHistory
            
            # Create QueryHistory instance
            query_history = QueryHistory()
            
            # Add multiple queries
            queries = [
                ("Find customers", "SELECT * FROM customers", 10, "10:00:00"),
                ("Find accounts", "SELECT * FROM accounts", 5, "10:01:00"),
                ("Find transactions", "SELECT * FROM transactions", 15, "10:02:00"),
            ]
            
            for query, sql, count, timestamp in queries:
                query_history.add_query(query, sql, count, timestamp)
            
            # Verify history
            history = query_history.get_history()
            self.assertEqual(len(history), 3)
            
            # Verify order (most recent first)
            self.assertEqual(history[0]['query'], "Find transactions")
            self.assertEqual(history[1]['query'], "Find accounts")
            self.assertEqual(history[2]['query'], "Find customers")
            
            # Verify data integrity
            for i, (query, sql, count, timestamp) in enumerate(queries[::-1]):  # Reverse order
                entry = history[i]
                self.assertEqual(entry['query'], query)
                self.assertEqual(entry['sql'], sql)
                self.assertEqual(entry['results_count'], count)
                self.assertEqual(entry['timestamp'], timestamp)

def run_tests():
    """Run all tests"""
    print("🧪 Running QueryHistory Unit Tests")
    print("=" * 50)
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test classes
    test_suite.addTest(unittest.makeSuite(TestQueryHistory))
    test_suite.addTest(unittest.makeSuite(TestRenderRecentQueriesSidebar))
    test_suite.addTest(unittest.makeSuite(TestQueryHistoryIntegration))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests PASSED!")
        return True
    else:
        print("❌ Some tests FAILED!")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
