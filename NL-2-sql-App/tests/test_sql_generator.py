"""Test cases for SQL Generator"""
import unittest
from backend.sql_generator import SQLGeneratorAgent

class TestSQLGenerator(unittest.TestCase):
    def setUp(self):
        """Set up test environment with schema"""
        self.schema_tables = {
            "branches": [
                "id", "name", "address", "city", "state", "zip_code",
                "manager_id", "created_at", "updated_at"
            ],
            "employees": [
                "id", "branch_id", "name", "email", "phone", "position",
                "hire_date", "salary", "created_at", "updated_at"
            ],
            "customers": [
                "id", "email", "phone", "address", "first_name", "last_name",
                "date_of_birth", "gender", "national_id", "created_at",
                "updated_at", "branch_id"
            ],
            "accounts": [
                "id", "customer_id", "account_number", "type", "balance",
                "opened_at", "interest_rate", "status", "branch_id",
                "created_at", "updated_at"
            ],
            "transactions": [
                "id", "account_id", "transaction_date", "amount", "type",
                "description", "status", "created_at", "updated_at",
                "employee_id"
            ]
        }
        self.generator = SQLGeneratorAgent(temperature=0.1)

    def test_branch_manager_query(self):
        """Test branch and manager listing query"""
        query = "List all branches and their managers' names. Include branches without a manager."
        expected_patterns = [
            "SELECT", "branches", "LEFT JOIN", "employees",
            "manager_id", "ORDER BY"
        ]
        
        sql = self.generator.generate(
            query, {}, {"schema_context": []}, self.schema_tables
        )
        
        # Check for required patterns
        for pattern in expected_patterns:
            self.assertIn(pattern.lower(), sql.lower())
        
        # Check correct table alias usage
        self.assertIn("AS branch_name", sql)
        self.assertIn("AS manager_name", sql)

    def test_employee_salary_query(self):
        """Test employee salary query"""
        queries = [
            "Show me the highest paid employees",
            "List employees with salary greater than 50000",
            "Who are the top 10 employees by salary?"
        ]
        
        for query in queries:
            sql = self.generator.generate(
                query, {}, {"schema_context": []}, self.schema_tables
            )
            
            # Check basic patterns
            self.assertIn("SELECT", sql.upper())
            self.assertIn("employees", sql.lower())
            self.assertIn("salary", sql.lower())
            
            # Check specific patterns
            if "highest" in query or "top" in query:
                self.assertIn("ORDER BY", sql.upper())
                self.assertIn("DESC", sql.upper())
            if "top 10" in query:
                self.assertIn("LIMIT 10", sql.upper())

    def test_transaction_query(self):
        """Test transaction-related queries"""
        queries = [
            "Show recent transactions",
            "List all transactions with amount > 1000",
            "Show me transactions from last week"
        ]
        
        for query in queries:
            sql = self.generator.generate(
                query, {}, {"schema_context": []}, self.schema_tables
            )
            
            # Check basic patterns
            self.assertIn("SELECT", sql.upper())
            self.assertIn("transactions", sql.lower())
            self.assertIn("transaction_date", sql.lower())
            
            # Check joins
            if "customer" in query:
                self.assertIn("JOIN accounts", sql.lower())
                self.assertIn("JOIN customers", sql.lower())

    def test_account_balance_query(self):
        """Test account balance queries"""
        queries = [
            "Show accounts with highest balance",
            "List accounts with balance less than 1000",
            "Which accounts have negative balance?"
        ]
        
        for query in queries:
            sql = self.generator.generate(
                query, {}, {"schema_context": []}, self.schema_tables
            )
            
            # Check basic patterns
            self.assertIn("SELECT", sql.upper())
            self.assertIn("accounts", sql.lower())
            self.assertIn("balance", sql.lower())
            
            # Check specific patterns
            if "highest" in query:
                self.assertIn("ORDER BY balance DESC", sql.lower())
            if "negative" in query:
                self.assertIn("balance < 0", sql.lower())

    def test_customer_query(self):
        """Test customer-related queries"""
        queries = [
            "Show all customers from Texas",
            "List customers with multiple accounts",
            "Find customers who made transactions over 5000"
        ]
        
        for query in queries:
            sql = self.generator.generate(
                query, {}, {"schema_context": []}, self.schema_tables
            )
            
            # Check basic patterns
            self.assertIn("SELECT", sql.upper())
            self.assertIn("customers", sql.lower())
            
            # Check specific patterns
            if "Texas" in query:
                self.assertIn("state = 'TX'", sql.lower())
            if "multiple accounts" in query:
                self.assertIn("COUNT", sql.upper())
                self.assertIn("GROUP BY", sql.upper())
            if "transactions" in query:
                self.assertIn("JOIN accounts", sql.lower())
                self.assertIn("JOIN transactions", sql.lower())

    def test_validation(self):
        """Test schema validation"""
        # Test non-existent table
        sql = self.generator.generate(
            "Show all managers",
            {},
            {"schema_context": []},
            self.schema_tables
        )
        self.assertIn("ERROR:", sql)
        
        # Test non-existent column
        sql = self.generator.generate(
            "Show employee age",
            {},
            {"schema_context": []},
            self.schema_tables
        )
        self.assertIn("ERROR:", sql)

if __name__ == '__main__':
    unittest.main()
