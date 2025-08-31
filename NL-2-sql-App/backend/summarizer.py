class SummarizerAgent:
    def __init__(self, max_preview=5):
        self.max_preview = max_preview

    def summarize(self, query: str, result: dict) -> dict:
        print(f"📝 SUMMARIZER AGENT: Starting result summarization")
        print(f"📝 SUMMARIZER AGENT: Original query: {query}")
        print(f"📊 SUMMARIZER AGENT: Result success: {result.get('success', False)}")
        print(f"📊 SUMMARIZER AGENT: Number of rows: {len(result.get('results', []))}")
        
        if not result.get("success", False):
            print(f"❌ SUMMARIZER AGENT: Query failed - creating error summary")
            return {"summary": f"⚠️ **Query Failed**\n\n**Your Question:** {query}\n\n**Error:** {result.get('error')}"}

        rows = result.get("results", [])
        if not rows:
            print(f"⚠️ SUMMARIZER AGENT: No results found - creating empty result summary")
            return {"summary": f"❌ **No Results Found**\n\n**Your Question:** {query}\n\nNo data matches your criteria. Try refining your search or ask a different question."}

        query_lower = query.lower()
        
        # Handle count queries - only if results have the expected structure
        if any(word in query_lower for word in ["count", "rows", "each table", "by table", "table count"]):
            # Check if results have the expected structure for count queries
            if len(rows) > 1 and all('table_name' in row and 'row_count' in row for row in rows):
                summary_parts = []
                total_rows = 0
                for row in rows:
                    table_name = row.get('table_name', 'Unknown')
                    count = row.get('row_count', 0)
                    total_rows += count
                    summary_parts.append(f"• **{table_name}**: {count:,} rows")
                
                # Find the largest table
                largest_table = max(rows, key=lambda x: x.get('row_count', 0))
                largest_name = largest_table.get('table_name', 'Unknown')
                largest_count = largest_table.get('row_count', 0)
                largest_percentage = (largest_count / total_rows * 100) if total_rows > 0 else 0
                
                return {
                    "summary": f"📊 **Database Overview**\n\n**Your Question:** {query}\n\n" + "\n".join(summary_parts) + f"\n\n**Key Insights:**\n• Total records across all tables: **{total_rows:,}**\n• Largest table: **{largest_name}** ({largest_percentage:.1f}% of total data)\n• Database contains comprehensive banking data with {len(rows)} main entities",
                    "table": rows,
                    "suggestions": [
                        "Show me the top 10 branches by transaction volume",
                        "What's the average account balance?",
                        "Show me employee distribution by branch",
                        "Which accounts have the highest balances?"
                    ]
                }
            # If it's a count query but doesn't have the right structure, fall through to generic handling
        
        # Handle branch transaction queries - only if results have expected structure
        if any(word in query_lower for word in ["transaction", "transactions"]) and any(word in query_lower for word in ["branch", "branches"]):
            # Check if results have the expected structure for branch transaction queries
            if len(rows) > 0 and all('name' in row and 'transaction_count' in row for row in rows):
                if len(rows) == 1:
                    # Single branch result
                    branch = rows[0]
                    name = branch.get('name', 'Unknown Branch')
                    city = branch.get('city', 'Unknown City')
                    state = branch.get('state', 'Unknown State')
                    count = branch.get('transaction_count', 0)
                    
                    # Calculate percentage of total transactions
                    total_transactions = sum(row.get('transaction_count', 0) for row in rows)
                    percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
                    
                    return {
                        "summary": f"🏆 **Top Performing Branch**\n\n**Your Question:** {query}\n\n**{name}** in {city}, {state} leads with **{count:,} transactions** ({percentage:.1f}% of total branch transactions).\n\nThis branch is your highest-performing location in terms of transaction volume.",
                        "table": rows,
                        "suggestions": [
                            "Show me the top 5 branches by transaction volume",
                            "What's the average transaction amount for this branch?",
                            "Show me employee performance at this branch",
                            "Compare this branch with others by revenue"
                        ]
                    }
                else:
                    # Multiple branches
                    top_branch = rows[0]
                    name = top_branch.get('name', 'Unknown Branch')
                    city = top_branch.get('city', 'Unknown City')
                    state = top_branch.get('state', 'Unknown State')
                    count = top_branch.get('transaction_count', 0)
                    total_branches = len(rows)
                    
                    # Calculate insights
                    total_transactions = sum(row.get('transaction_count', 0) for row in rows)
                    avg_transactions = total_transactions / total_branches if total_branches > 0 else 0
                    top_percentage = (count / total_transactions * 100) if total_transactions > 0 else 0
                    
                    # Find the lowest performing branch in the list
                    lowest_branch = rows[-1]
                    lowest_count = lowest_branch.get('transaction_count', 0)
                    performance_gap = count - lowest_count
                    
                    return {
                        "summary": f"🏆 **Top {total_branches} Branches by Transaction Volume**\n\n**Your Question:** {query}\n\n**{name}** in {city}, {state} leads with **{count:,} transactions** ({top_percentage:.1f}% of total).\n\n**Key Insights:**\n• Average transactions per branch: **{avg_transactions:,.0f}**\n• Performance gap between top and bottom: **{performance_gap:,} transactions**\n• Total transactions across top {total_branches} branches: **{total_transactions:,}**\n\nBelow are the top {total_branches} branches ranked by their transaction activity.",
                        "table": rows,
                        "suggestions": [
                            "Show me the bottom 5 performing branches",
                            "What's the average transaction amount by branch?",
                            "Show me branch performance by month",
                            "Compare branch performance by employee count"
                        ]
                    }
            # If it's a branch transaction query but doesn't have the right structure, fall through to generic handling
        
        # Handle account balance queries - only if results have expected structure
        if any(word in query_lower for word in ["balance", "account"]) and any(word in query_lower for word in ["maximum", "max", "highest", "top"]):
            # Check if results have the expected structure for account balance queries
            if len(rows) > 0 and all('account_number' in row and 'balance' in row for row in rows):
                if len(rows) == 1:
                    account = rows[0]
                    account_num = account.get('account_number', 'Unknown')
                    balance = account.get('balance', 0)
                    account_type = account.get('type', 'Unknown Type')
                    customer_id = account.get('customer_id', 'Unknown')
                    
                    return {
                        "summary": f"💰 **Highest Balance Account**\n\n**Your Question:** {query}\n\nAccount **{account_num}** ({account_type}) has the highest balance of **${balance:,.2f}**.\n\n**Account Details:**\n• Customer ID: {customer_id}\n• Account Type: {account_type}\n• This represents the wealthiest account in your banking system",
                        "table": rows,
                        "suggestions": [
                            "Show me the top 10 accounts by balance",
                            "What's the average account balance?",
                            "Show me account distribution by type",
                            "Which customers have multiple accounts?"
                        ]
                    }
            # If it's an account balance query but doesn't have the right structure, fall through to generic handling
        
        # Handle employee salary queries - only if results have expected structure
        if any(word in query_lower for word in ["salary", "employee"]) and any(word in query_lower for word in ["maximum", "max", "highest", "top"]):
            # Check if results have the expected structure for employee salary queries
            if len(rows) > 0 and all('name' in row and 'salary' in row for row in rows):
                if len(rows) == 1:
                    employee = rows[0]
                    name = employee.get('name', 'Unknown')
                    position = employee.get('position', 'Unknown Position')
                    salary = employee.get('salary', 0)
                    branch_id = employee.get('branch_id', 'Unknown')
                    
                    return {
                        "summary": f"👔 **Highest Paid Employee**\n\n**Your Question:** {query}\n\n**{name}** ({position}) has the highest salary of **${salary:,.2f}**.\n\n**Employee Details:**\n• Branch ID: {branch_id}\n• Position: {position}\n• This represents your highest-compensated employee",
                        "table": rows,
                        "suggestions": [
                            "Show me the top 10 highest paid employees",
                            "What's the average employee salary?",
                            "Show me salary distribution by position",
                            "Which branches have the highest paid employees?"
                        ]
                    }
            # If it's an employee salary query but doesn't have the right structure, fall through to generic handling
        
        # Handle customer queries
        if any(word in query_lower for word in ["customer", "customers"]) and any(word in query_lower for word in ["checking", "savings", "account", "accounts"]):
            if len(rows) == 1:
                return {
                    "summary": f"👤 **Customer Account Information**\n\n**Your Question:** {query}\n\nFound 1 customer matching your criteria.",
                    "table": rows
                }
            else:
                return {
                    "summary": f"👥 **Customer Account Analysis**\n\n**Your Question:** {query}\n\nFound **{len(rows)} customers** who have both checking and savings accounts.\n\n**Key Insights:**\n• These customers maintain multiple account types\n• They represent active banking relationships\n• This data can be used for targeted marketing and service improvements",
                    "table": rows,
                    "suggestions": [
                        "Show me customers with only checking accounts",
                        "What's the average balance for these customers?",
                        "Show me customers with the highest total balance",
                        "Which branches serve these customers?"
                    ]
                }
        
        # Handle transaction queries - only if results have expected structure
        if any(word in query_lower for word in ["transaction", "transactions"]) and not any(word in query_lower for word in ["branch", "branches"]):
            # Check if results have the expected structure for transaction queries
            if len(rows) > 0 and all('transaction_id' in row or 'amount' in row for row in rows):
                if len(rows) == 1:
                    return {
                        "summary": f"💳 **Latest Transaction**\n\n**Your Question:** {query}\n\nHere's the most recent transaction from your database.",
                        "table": rows
                    }
                else:
                    return {
                        "summary": f"💳 **Recent Transactions**\n\n**Your Question:** {query}\n\nHere are the {len(rows)} most recent transactions from your database.",
                        "table": rows
                    }
            # If it's a transaction query but doesn't have the right structure, fall through to generic handling
        
        # Generic handling for other queries
        if len(rows) == 1:
            print(f"✅ SUMMARIZER AGENT: Creating single result summary")
            result_dict = {
                "summary": f"✅ **Query Result**\n\n**Your Question:** {query}\n\nFound 1 result for your query.",
                "table": rows
            }
        else:
            print(f"✅ SUMMARIZER AGENT: Creating multiple results summary")
            result_dict = {
                "summary": f"✅ **Query Results**\n\n**Your Question:** {query}\n\nFound {len(rows)} results for your query.",
                "table": rows
            }
        
        print(f"✅ SUMMARIZER AGENT: Summarization complete - returning to orchestrator")
        return result_dict
