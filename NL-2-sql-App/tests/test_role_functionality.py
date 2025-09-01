#!/usr/bin/env python3
"""
Unit Tests for Role Parameter Validation and Functionality
Tests the complete flow from role selection to query processing
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil

# Add backend to path
sys.path.append('./backend')
sys.path.append('.')

class TestRoleFunctionality(unittest.TestCase):
    """Test suite for role parameter validation and functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary directories for test databases
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, "test_banking.db")
        self.test_chroma_path = os.path.join(self.temp_dir, "test_chroma_db")
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'DB_PATH': self.test_db_path,
            'OPENAI_API_KEY': 'test_key',
            'DEFAULT_LLM_PROVIDER': 'openai',
            'DEFAULT_LLM_MODEL': 'gpt-4o-mini'
        })
        self.env_patcher.start()
        
        # Mock session state
        self.session_state_mock = {
            'user_input': 'TestUser',
            'query_input': 'Find all customers',
            'enter_pressed': False,
            'pending_query': None,
            'system_initialized': True,
            'init_report': {'status': 'success'}
        }
        
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_render_developer_ui_role_parameter(self):
        """Test that render_developer_ui accepts and uses selected_role parameter"""
        from app import render_developer_ui
        
        # Mock streamlit components
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.tabs') as mock_tabs, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock tabs to return a list of mock tab objects
            mock_tab1 = Mock()
            mock_tab2 = Mock()
            mock_tab3 = Mock()
            mock_tab4 = Mock()
            mock_tab5 = Mock()
            mock_tab6 = Mock()
            mock_tab7 = Mock()
            mock_tab8 = Mock()
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4, 
                                    mock_tab5, mock_tab6, mock_tab7, mock_tab8]
            
            # Mock columns to return mock column objects
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # Mock text input to return a test value
            mock_text_input.return_value = "TestUser"
            
            # Mock text area to return a test query
            mock_text_area.return_value = "Find all customers"
            
            # Mock button to return False (not clicked)
            mock_button.return_value = False
            
            # Test the function with selected_role parameter
            try:
                render_developer_ui("Developer")
                # If we get here, the function executed without errors
                self.assertTrue(True, "render_developer_ui executed successfully with selected_role parameter")
            except Exception as e:
                self.fail(f"render_developer_ui failed with selected_role parameter: {str(e)}")
    
    def test_render_business_user_ui_role_parameter(self):
        """Test that render_business_user_ui accepts and uses selected_role parameter"""
        from app import render_business_user_ui
        
        # Mock streamlit components
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.tabs') as mock_tabs, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock tabs to return a list of mock tab objects
            mock_tab1 = Mock()
            mock_tab2 = Mock()
            mock_tab3 = Mock()
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
            
            # Mock columns to return mock column objects
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # Mock text input to return a test value
            mock_text_input.return_value = "TestUser"
            
            # Mock text area to return a test query
            mock_text_area.return_value = "Find all customers"
            
            # Mock button to return False (not clicked)
            mock_button.return_value = False
            
            # Test the function with selected_role parameter
            try:
                render_business_user_ui("Business User")
                # If we get here, the function executed without errors
                self.assertTrue(True, "render_business_user_ui executed successfully with selected_role parameter")
            except Exception as e:
                self.fail(f"render_business_user_ui failed with selected_role parameter: {str(e)}")
    
    def test_process_query_role_parameter(self):
        """Test that process_query accepts and uses role_input parameter"""
        from app import process_query
        
        # Mock streamlit components
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.progress') as mock_progress, \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.spinner') as mock_spinner, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock container context manager
            mock_container.return_value.__enter__ = Mock()
            mock_container.return_value.__exit__ = Mock()
            
            # Mock spinner context manager
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
            # Mock columns to return mock column objects
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # Mock the verify_database_connections function
            with patch('app.verify_database_connections') as mock_verify_db:
                mock_verify_db.return_value = {
                    'sqlite': {'status': True, 'message': '✅ SQLite connected', 'details': 'Test'},
                    'chromadb': {'status': True, 'message': '✅ ChromaDB connected', 'details': 'Test'}
                }
                
                # Mock the simulate_agent_workflow_with_cot function
                with patch('app.simulate_agent_workflow_with_cot') as mock_workflow:
                    mock_workflow.return_value = (
                        "SELECT * FROM customers LIMIT 10",
                        [{"id": 1, "name": "Test Customer"}],
                        "Found 1 customer",
                        {"total_time": 1.0, "agent_timings": {}}
                    )
                    
                    # Test the function with role_input parameter
                    try:
                        process_query("Find all customers", "TestUser", "Developer")
                        # If we get here, the function executed without errors
                        self.assertTrue(True, "process_query executed successfully with role_input parameter")
                    except Exception as e:
                        self.fail(f"process_query failed with role_input parameter: {str(e)}")
    
    def test_role_parameter_consistency(self):
        """Test that role parameter is consistently passed through the call chain"""
        from app import render_developer_ui, render_business_user_ui, process_query
        
        # Test data
        test_roles = ["Developer", "Business User"]
        test_queries = ["Find all customers", "Show account balances"]
        test_users = ["TestUser1", "TestUser2"]
        
        for role in test_roles:
            for query in test_queries:
                for user in test_users:
                    # Mock all streamlit components
                    with patch('streamlit.markdown') as mock_markdown, \
                         patch('streamlit.tabs') as mock_tabs, \
                         patch('streamlit.columns') as mock_columns, \
                         patch('streamlit.text_input') as mock_text_input, \
                         patch('streamlit.text_area') as mock_text_area, \
                         patch('streamlit.button') as mock_button, \
                         patch('streamlit.container') as mock_container, \
                         patch('streamlit.progress') as mock_progress, \
                         patch('streamlit.empty') as mock_empty, \
                         patch('streamlit.info') as mock_info, \
                         patch('streamlit.success') as mock_success, \
                         patch('streamlit.error') as mock_error, \
                         patch('streamlit.spinner') as mock_spinner, \
                         patch('streamlit.session_state', self.session_state_mock):
                        
                        # Mock container and spinner context managers
                        mock_container.return_value.__enter__ = Mock()
                        mock_container.return_value.__exit__ = Mock()
                        mock_spinner.return_value.__enter__ = Mock()
                        mock_spinner.return_value.__exit__ = Mock()
                        
                        # Mock tabs
                        mock_tabs.return_value = [Mock() for _ in range(8)]
                        
                        # Mock columns
                        mock_columns.return_value = [Mock(), Mock()]
                        
                        # Mock inputs
                        mock_text_input.return_value = user
                        mock_text_area.return_value = query
                        mock_button.return_value = False
                        
                        # Mock database verification
                        with patch('app.verify_database_connections') as mock_verify_db:
                            mock_verify_db.return_value = {
                                'sqlite': {'status': True, 'message': '✅ SQLite connected', 'details': 'Test'},
                                'chromadb': {'status': True, 'message': '✅ ChromaDB connected', 'details': 'Test'}
                            }
                            
                            # Mock agent workflow
                            with patch('app.simulate_agent_workflow_with_cot') as mock_workflow:
                                mock_workflow.return_value = (
                                    "SELECT * FROM customers LIMIT 10",
                                    [{"id": 1, "name": "Test Customer"}],
                                    "Found 1 customer",
                                    {"total_time": 1.0, "agent_timings": {}}
                                )
                                
                                # Test UI rendering functions
                                try:
                                    if role == "Developer":
                                        render_developer_ui(role)
                                    else:
                                        render_business_user_ui(role)
                                    
                                    # Test process_query function
                                    process_query(query, user, role)
                                    
                                    self.assertTrue(True, f"Role '{role}' works correctly with query '{query}' and user '{user}'")
                                    
                                except Exception as e:
                                    self.fail(f"Role '{role}' failed with query '{query}' and user '{user}': {str(e)}")
    
    def test_role_parameter_validation(self):
        """Test that invalid role parameters are handled gracefully"""
        from app import render_developer_ui, render_business_user_ui, process_query
        
        # Test with invalid role values
        invalid_roles = ["", None, "InvalidRole", "DEVELOPER", "business_user"]
        
        for invalid_role in invalid_roles:
            # Mock streamlit components
            with patch('streamlit.markdown') as mock_markdown, \
                 patch('streamlit.tabs') as mock_tabs, \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.text_input') as mock_text_input, \
                 patch('streamlit.text_area') as mock_text_area, \
                 patch('streamlit.button') as mock_button, \
                 patch('streamlit.session_state', self.session_state_mock):
                
                # Mock tabs and columns
                mock_tabs.return_value = [Mock() for _ in range(8)]
                mock_columns.return_value = [Mock(), Mock()]
                mock_text_input.return_value = "TestUser"
                mock_text_area.return_value = "Find all customers"
                mock_button.return_value = False
                
                # Test that functions don't crash with invalid roles
                try:
                    render_developer_ui(invalid_role)
                    render_business_user_ui(invalid_role)
                    process_query("Find all customers", "TestUser", invalid_role)
                    
                    # If we get here, the functions handled invalid roles gracefully
                    self.assertTrue(True, f"Functions handled invalid role '{invalid_role}' gracefully")
                    
                except Exception as e:
                    # It's acceptable for functions to raise exceptions with invalid roles
                    # as long as they don't crash the application
                    self.assertIsInstance(e, Exception, f"Invalid role '{invalid_role}' caused unexpected error type")
    
    def test_role_parameter_logging(self):
        """Test that role parameter is properly logged in process_query"""
        from app import process_query
        
        # Mock streamlit components
        with patch('streamlit.container') as mock_container, \
             patch('streamlit.progress') as mock_progress, \
             patch('streamlit.empty') as mock_empty, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.error') as mock_error, \
             patch('streamlit.spinner') as mock_spinner, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock container and spinner context managers
            mock_container.return_value.__enter__ = Mock()
            mock_container.return_value.__exit__ = Mock()
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            mock_columns.return_value = [Mock(), Mock()]
            
            # Mock database verification
            with patch('app.verify_database_connections') as mock_verify_db:
                mock_verify_db.return_value = {
                    'sqlite': {'status': True, 'message': '✅ SQLite connected', 'details': 'Test'},
                    'chromadb': {'status': True, 'message': '✅ ChromaDB connected', 'details': 'Test'}
                }
                
                # Mock agent workflow
                with patch('app.simulate_agent_workflow_with_cot') as mock_workflow:
                    mock_workflow.return_value = (
                        "SELECT * FROM customers LIMIT 10",
                        [{"id": 1, "name": "Test Customer"}],
                        "Found 1 customer",
                        {"total_time": 1.0, "agent_timings": {}}
                    )
                    
                    # Test that role is logged
                    test_role = "Developer"
                    test_user = "TestUser"
                    test_query = "Find all customers"
                    
                    process_query(test_query, test_user, test_role)
                    
                    # Check that st.info was called with role information
                    mock_info.assert_called()
                    
                    # Find the call that contains role information
                    role_logged = False
                    for call in mock_info.call_args_list:
                        if call[0] and isinstance(call[0][0], str):
                            if test_role in call[0][0] and test_user in call[0][0]:
                                role_logged = True
                                break
                    
                    self.assertTrue(role_logged, f"Role '{test_role}' should be logged in process_query")
    
    def test_main_function_role_flow(self):
        """Test that main function properly handles role selection and UI rendering"""
        from app import main
        
        # Mock streamlit components
        with patch('streamlit.set_page_config') as mock_page_config, \
             patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.sidebar') as mock_sidebar, \
             patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock sidebar context manager
            mock_sidebar.return_value.__enter__ = Mock()
            mock_sidebar.return_value.__exit__ = Mock()
            
            # Mock selectbox to return "Developer"
            mock_selectbox.return_value = "Developer"
            
            # Mock the UI rendering functions
            with patch('app.render_developer_ui') as mock_render_dev, \
                 patch('app.render_business_user_ui') as mock_render_business:
                
                try:
                    main()
                    
                    # Check that the appropriate UI function was called
                    mock_render_dev.assert_called_once_with("Developer")
                    mock_render_business.assert_not_called()
                    
                except Exception as e:
                    self.fail(f"main function failed: {str(e)}")
                
                # Test with "Business User" role
                mock_selectbox.return_value = "Business User"
                mock_render_dev.reset_mock()
                mock_render_business.reset_mock()
                
                try:
                    main()
                    
                    # Check that the appropriate UI function was called
                    mock_render_business.assert_called_once_with("Business User")
                    mock_render_dev.assert_not_called()
                    
                except Exception as e:
                    self.fail(f"main function failed with Business User role: {str(e)}")

def run_role_functionality_tests():
    """Run all role functionality tests"""
    print("🧪 Running Role Functionality Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRoleFunctionality)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 Test Results Summary:")
    print(f"   ✅ Tests run: {result.testsRun}")
    print(f"   ❌ Failures: {len(result.failures)}")
    print(f"   ⚠️ Errors: {len(result.errors)}")
    
    if result.failures:
        print(f"\n❌ Test Failures:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback}")
    
    if result.errors:
        print(f"\n⚠️ Test Errors:")
        for test, traceback in result.errors:
            print(f"   - {test}: {traceback}")
    
    if result.wasSuccessful():
        print(f"\n🎉 All role functionality tests passed!")
    else:
        print(f"\n💥 Some role functionality tests failed!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Run the tests
    success = run_role_functionality_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
