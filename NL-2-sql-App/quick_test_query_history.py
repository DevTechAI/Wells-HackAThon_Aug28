#!/usr/bin/env python3
"""
Quick test script for QueryHistory functionality
"""

import sys
import os
from unittest.mock import Mock, patch

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_query_history_basic():
    """Basic test for QueryHistory functionality"""
    print("🧪 Testing QueryHistory Basic Functionality")
    print("-" * 40)
    
    # Mock streamlit session state
    mock_session_state = {}
    
    with patch('streamlit.session_state', mock_session_state):
        try:
            from app import QueryHistory
            
            # Test 1: Initialization
            print("✅ Test 1: Initialization")
            query_history = QueryHistory()
            assert 'query_history' in mock_session_state
            assert isinstance(mock_session_state['query_history'], list)
            assert len(mock_session_state['query_history']) == 0
            print("   ✓ QueryHistory initialized correctly")
            
            # Test 2: Adding queries
            print("✅ Test 2: Adding queries")
            query_history.add_query("Find customers", "SELECT * FROM customers", 5, "10:00:00")
            query_history.add_query("Find accounts", "SELECT * FROM accounts", 3, "10:01:00")
            
            history = query_history.get_history()
            assert len(history) == 2
            assert history[0]['query'] == "Find accounts"  # Most recent first
            assert history[1]['query'] == "Find customers"
            print("   ✓ Queries added correctly")
            
            # Test 3: History limit
            print("✅ Test 3: History limit (10 entries)")
            for i in range(10):
                query_history.add_query(f"Query {i}", f"SELECT * FROM table{i}", i, f"10:{i:02d}:00")
            
            history = query_history.get_history()
            assert len(history) == 10  # Should be limited to 10
            print("   ✓ History limited to 10 entries")
            
            # Test 4: Corrupted state handling
            print("✅ Test 4: Corrupted state handling")
            mock_session_state['query_history'] = "not a list"
            query_history = QueryHistory()
            history = query_history.get_history()
            assert isinstance(history, list)
            assert len(history) == 0
            print("   ✓ Corrupted state handled correctly")
            
            print("\n🎉 All basic tests PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_render_function_mock():
    """Test render_recent_queries_sidebar with mocks"""
    print("\n🧪 Testing render_recent_queries_sidebar (Mock)")
    print("-" * 40)
    
    mock_session_state = {}
    mock_st = Mock()
    
    with patch('streamlit.session_state', mock_session_state), \
         patch('streamlit.sidebar', mock_st):
        
        try:
            from app import QueryHistory, render_recent_queries_sidebar
            
            # Test empty history
            print("✅ Test 1: Empty history")
            render_recent_queries_sidebar()
            mock_st.info.assert_called_with("No recent queries")
            print("   ✓ Empty history handled correctly")
            
            # Test with valid history
            print("✅ Test 2: Valid history")
            query_history = QueryHistory()
            query_history.add_query("Test query", "SELECT * FROM test", 1, "10:00:00")
            
            # Mock expander
            mock_expander = Mock()
            mock_expander.write = Mock()
            mock_st.expander.return_value.__enter__.return_value = mock_expander
            
            render_recent_queries_sidebar()
            
            # Should call expander once
            assert mock_st.expander.call_count == 1
            print("   ✓ Valid history rendered correctly")
            
            print("\n🎉 All render tests PASSED!")
            return True
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Run all tests"""
    print("🚀 QueryHistory Validation Tests")
    print("=" * 50)
    
    # Run basic tests
    basic_success = test_query_history_basic()
    
    # Run render tests
    render_success = test_render_function_mock()
    
    # Summary
    print("\n" + "=" * 50)
    if basic_success and render_success:
        print("✅ ALL TESTS PASSED!")
        print("🎯 QueryHistory functionality is working correctly")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("🔧 Please check the error messages above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
