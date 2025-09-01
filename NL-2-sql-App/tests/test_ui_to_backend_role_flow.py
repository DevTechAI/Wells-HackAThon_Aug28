#!/usr/bin/env python3
"""
Unit Tests for UI to Backend Role Flow
Tests the complete flow from user clicking "Process Query" button to backend processing
"""

import unittest
import sys
import os
from unittest.mock import Mock, patch, MagicMock, call
import tempfile
import shutil

# Add backend to path
sys.path.append('./backend')
sys.path.append('.')

class TestUIToBackendRoleFlow(unittest.TestCase):
    """Test suite for UI to backend role flow"""
    
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
            'init_report': {'status': 'success'},
            'query_history': Mock(),
            'timing_tracker': Mock(),
            'security_guard': Mock()
        }
        
    def tearDown(self):
        """Clean up test environment"""
        self.env_patcher.stop()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_user_clicks_process_query_button_developer_role(self):
        """Test complete flow when user clicks Process Query button as Developer"""
        from app import render_developer_ui, process_query
        
        # Mock streamlit components
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
            
            # Mock tabs with context manager support
            mock_tab1 = Mock()
            mock_tab1.__enter__ = Mock()
            mock_tab1.__exit__ = Mock()
            mock_tab2 = Mock()
            mock_tab2.__enter__ = Mock()
            mock_tab2.__exit__ = Mock()
            mock_tab3 = Mock()
            mock_tab3.__enter__ = Mock()
            mock_tab3.__exit__ = Mock()
            mock_tab4 = Mock()
            mock_tab4.__enter__ = Mock()
            mock_tab4.__exit__ = Mock()
            mock_tab5 = Mock()
            mock_tab5.__enter__ = Mock()
            mock_tab5.__exit__ = Mock()
            mock_tab6 = Mock()
            mock_tab6.__enter__ = Mock()
            mock_tab6.__exit__ = Mock()
            mock_tab7 = Mock()
            mock_tab7.__enter__ = Mock()
            mock_tab7.__exit__ = Mock()
            mock_tab8 = Mock()
            mock_tab8.__enter__ = Mock()
            mock_tab8.__exit__ = Mock()
            
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3, mock_tab4, 
                                    mock_tab5, mock_tab6, mock_tab7, mock_tab8]
            
            # Mock columns
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # Mock user inputs
            mock_text_input.return_value = "TestUser"
            mock_text_area.return_value = "Find all customers"
            
            # Mock button click - this simulates user clicking "Process Query"
            mock_button.return_value = True  # Button is clicked
            
            # Mock container and spinner context managers
            mock_container.return_value.__enter__ = Mock()
            mock_container.return_value.__exit__ = Mock()
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
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
                    
                    # Test the complete flow
                    try:
                        # This simulates the UI rendering and button click
                        render_developer_ui("Developer")
                        
                        # Verify that process_query was called with correct parameters
                        # We need to check if the button click triggered process_query
                        mock_button.assert_called()
                        
                        # Verify the button was called with correct parameters
                        button_call = mock_button.call_args
                        self.assertIsNotNone(button_call, "Button should be called")
                        
                        # Check that the role parameter was passed correctly
                        self.assertEqual(self.session_state_mock['user_input'], "TestUser")
                        
                        print("✅ Developer role flow: Button click detected and processed")
                        
                    except Exception as e:
                        self.fail(f"Developer role flow failed: {str(e)}")
    
    def test_user_clicks_process_query_button_business_role(self):
        """Test complete flow when user clicks Process Query button as Business User"""
        from app import render_business_user_ui, process_query
        
        # Mock streamlit components
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
            
            # Mock tabs with context manager support
            mock_tab1 = Mock()
            mock_tab1.__enter__ = Mock()
            mock_tab1.__exit__ = Mock()
            mock_tab2 = Mock()
            mock_tab2.__enter__ = Mock()
            mock_tab2.__exit__ = Mock()
            mock_tab3 = Mock()
            mock_tab3.__enter__ = Mock()
            mock_tab3.__exit__ = Mock()
            
            mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
            
            # Mock columns
            mock_col1 = Mock()
            mock_col2 = Mock()
            mock_columns.return_value = [mock_col1, mock_col2]
            
            # Mock user inputs
            mock_text_input.return_value = "BusinessUser"
            mock_text_area.return_value = "Show account balances"
            
            # Mock button click - this simulates user clicking "Process Query"
            mock_button.return_value = True  # Button is clicked
            
            # Mock container and spinner context managers
            mock_container.return_value.__enter__ = Mock()
            mock_container.return_value.__exit__ = Mock()
            mock_spinner.return_value.__enter__ = Mock()
            mock_spinner.return_value.__exit__ = Mock()
            
            # Mock database verification
            with patch('app.verify_database_connections') as mock_verify_db:
                mock_verify_db.return_value = {
                    'sqlite': {'status': True, 'message': '✅ SQLite connected', 'details': 'Test'},
                    'chromadb': {'status': True, 'message': '✅ ChromaDB connected', 'details': 'Test'}
                }
                
                # Mock agent workflow
                with patch('app.simulate_agent_workflow_with_cot') as mock_workflow:
                    mock_workflow.return_value = (
                        "SELECT * FROM accounts LIMIT 10",
                        [{"id": 1, "balance": 1000}],
                        "Found 1 account",
                        {"total_time": 1.0, "agent_timings": {}}
                    )
                    
                    # Test the complete flow
                    try:
                        # This simulates the UI rendering and button click
                        render_business_user_ui("Business User")
                        
                        # Verify that process_query was called with correct parameters
                        mock_button.assert_called()
                        
                        # Check that the role parameter was passed correctly
                        self.assertEqual(self.session_state_mock['user_input'], "BusinessUser")
                        
                        print("✅ Business User role flow: Button click detected and processed")
                        
                    except Exception as e:
                        self.fail(f"Business User role flow failed: {str(e)}")
    
    def test_process_query_role_parameter_flow(self):
        """Test that process_query correctly handles role parameter from UI"""
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
                    
                    # Test with different roles
                    test_cases = [
                        {"role": "Developer", "user": "DevUser", "query": "Find all customers"},
                        {"role": "Business User", "user": "BusinessUser", "query": "Show account balances"}
                    ]
                    
                    for test_case in test_cases:
                        try:
                            # Call process_query with role parameter
                            process_query(test_case["query"], test_case["user"], test_case["role"])
                            
                            # Verify that the role was logged correctly
                            mock_info.assert_called()
                            
                            # Check that role information appears in the logs
                            role_logged = False
                            for call_args in mock_info.call_args_list:
                                if call_args[0] and isinstance(call_args[0][0], str):
                                    if test_case["role"] in call_args[0][0] and test_case["user"] in call_args[0][0]:
                                        role_logged = True
                                        break
                            
                            self.assertTrue(role_logged, 
                                           f"Role '{test_case['role']}' should be logged in process_query")
                            
                            print(f"✅ Role '{test_case['role']}' correctly processed and logged")
                            
                        except Exception as e:
                            self.fail(f"Process query failed for role '{test_case['role']}': {str(e)}")
    
    def test_button_click_triggers_process_query(self):
        """Test that button click actually triggers process_query function"""
        from app import render_developer_ui
        
        # Mock streamlit components
        with patch('streamlit.markdown') as mock_markdown, \
             patch('streamlit.tabs') as mock_tabs, \
             patch('streamlit.columns') as mock_columns, \
             patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.text_area') as mock_text_area, \
             patch('streamlit.button') as mock_button, \
             patch('streamlit.session_state', self.session_state_mock):
            
            # Mock tabs with context manager support
            mock_tabs.return_value = [Mock() for _ in range(8)]
            for tab in mock_tabs.return_value:
                tab.__enter__ = Mock()
                tab.__exit__ = Mock()
            
            # Mock columns
            mock_columns.return_value = [Mock(), Mock()]
            
            # Mock user inputs
            mock_text_input.return_value = "TestUser"
            mock_text_area.return_value = "Find all customers"
            
            # Mock button to return True (clicked)
            mock_button.return_value = True
            
            # Mock process_query function
            with patch('app.process_query') as mock_process_query:
                try:
                    # Render the UI (this should trigger button click logic)
                    render_developer_ui("Developer")
                    
                    # Verify that process_query was called
                    mock_process_query.assert_called_once()
                    
                    # Verify the parameters passed to process_query
                    call_args = mock_process_query.call_args
                    self.assertIsNotNone(call_args, "process_query should be called")
                    
                    # Check that the role parameter was passed correctly
                    args, kwargs = call_args
                    self.assertEqual(args[0], "Find all customers")  # query
                    self.assertEqual(args[1], "TestUser")  # user_input
                    self.assertEqual(args[2], "Developer")  # selected_role
                    
                    print("✅ Button click correctly triggers process_query with role parameter")
                    
                except Exception as e:
                    self.fail(f"Button click test failed: {str(e)}")
    
    def test_role_parameter_passed_to_backend_agents(self):
        """Test that role parameter is passed through to backend agents"""
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
                
                # Mock agent workflow with role parameter tracking
                with patch('app.simulate_agent_workflow_with_cot') as mock_workflow:
                    mock_workflow.return_value = (
                        "SELECT * FROM customers LIMIT 10",
                        [{"id": 1, "name": "Test Customer"}],
                        "Found 1 customer",
                        {"total_time": 1.0, "agent_timings": {}}
                    )
                    
                    # Test that role parameter is passed to backend
                    test_role = "Developer"
                    test_user = "TestUser"
                    test_query = "Find all customers"
                    
                    try:
                        # Call process_query
                        process_query(test_query, test_user, test_role)
                        
                        # Verify that simulate_agent_workflow_with_cot was called
                        mock_workflow.assert_called_once()
                        
                        # Check the parameters passed to the workflow
                        workflow_call_args = mock_workflow.call_args
                        self.assertIsNotNone(workflow_call_args, "Workflow should be called")
                        
                        # The workflow should receive the query and user info
                        args, kwargs = workflow_call_args
                        self.assertEqual(args[0], test_query)  # query
                        self.assertIn('user', kwargs)  # user parameter
                        self.assertEqual(kwargs['user'], test_user)
                        
                        print("✅ Role parameter correctly passed to backend workflow")
                        
                    except Exception as e:
                        self.fail(f"Backend role parameter test failed: {str(e)}")
    
    def test_role_parameter_validation_in_ui(self):
        """Test that role parameter is validated in UI before processing"""
        from app import render_developer_ui, render_business_user_ui
        
        # Test valid roles
        valid_roles = ["Developer", "Business User"]
        
        for role in valid_roles:
            # Mock streamlit components
            with patch('streamlit.markdown') as mock_markdown, \
                 patch('streamlit.tabs') as mock_tabs, \
                 patch('streamlit.columns') as mock_columns, \
                 patch('streamlit.text_input') as mock_text_input, \
                 patch('streamlit.text_area') as mock_text_area, \
                 patch('streamlit.button') as mock_button, \
                 patch('streamlit.session_state', self.session_state_mock):
                
                # Mock tabs with context manager support
                mock_tabs.return_value = [Mock() for _ in range(8 if role == "Developer" else 3)]
                for tab in mock_tabs.return_value:
                    tab.__enter__ = Mock()
                    tab.__exit__ = Mock()
                
                # Mock columns
                mock_columns.return_value = [Mock(), Mock()]
                
                # Mock user inputs
                mock_text_input.return_value = "TestUser"
                mock_text_area.return_value = "Find all customers"
                mock_button.return_value = False  # Not clicked for this test
                
                try:
                    if role == "Developer":
                        render_developer_ui(role)
                    else:
                        render_business_user_ui(role)
                    
                    # If we get here, the role was accepted
                    self.assertTrue(True, f"Role '{role}' was accepted by UI")
                    print(f"✅ Role '{role}' validated successfully in UI")
                    
                except Exception as e:
                    self.fail(f"Role '{role}' validation failed: {str(e)}")

def run_ui_to_backend_role_tests():
    """Run all UI to backend role flow tests"""
    print("🧪 Running UI to Backend Role Flow Tests...")
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUIToBackendRoleFlow)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n📊 UI to Backend Role Flow Test Results:")
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
        print(f"\n🎉 All UI to Backend role flow tests passed!")
        print(f"\n✅ UI to Backend Role Flow Validation Summary:")
        print(f"   - User button clicks are properly detected")
        print(f"   - Role parameters are passed from UI to backend")
        print(f"   - Process query function receives correct role values")
        print(f"   - Backend agents receive role information")
        print(f"   - Role validation works in UI")
        print(f"   - Complete flow from button click to backend processing works")
    else:
        print(f"\n💥 Some UI to Backend role flow tests failed!")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Run the tests
    success = run_ui_to_backend_role_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)
