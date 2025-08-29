class SummarizerAgent:
    def __init__(self, max_preview=5):
        self.max_preview = max_preview

    def summarize(self, query: str, result: dict) -> dict:
        if not result.get("success", False):
            return {"summary": f"⚠️ **Query Failed**\n\n**Your Question:** {query}\n\n**Error:** {result.get('error')}"}

        rows = result.get("results", [])
        if not rows:
            return {"summary": f"❌ **No Results Found**\n\n**Your Question:** {query}\n\nNo data matches your criteria. Try refining your search or ask a different question."}

        query_lower = query.lower()
        
        # Handle count queries
        if any(word in query_lower for word in ["count", "rows", "each table", "by table", "table count"]):
            if len(rows) > 1:
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
        
        # Handle branch transaction queries
        if any(word in query_lower for word in ["transaction", "transactions"]) and any(word in query_lower for word in ["branch", "branches"]):
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
        
        # Handle account balance queries
        if any(word in query_lower for word in ["balance", "account"]) and any(word in query_lower for word in ["maximum", "max", "highest", "top"]):
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
        
        # Handle employee salary queries
        if any(word in query_lower for word in ["salary", "employee"]) and any(word in query_lower for word in ["maximum", "max", "highest", "top"]):
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
        
        # Handle transaction queries
        if any(word in query_lower for word in ["transaction", "transactions"]) and not any(word in query_lower for word in ["branch", "branches"]):
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
        
        # Generic handling for other queries
        if len(rows) == 1:
            return {
                "summary": f"✅ **Query Result**\n\n**Your Question:** {query}\n\nFound 1 result for your query.",
                "table": rows
            }
        else:
            return {
                "summary": f"✅ **Query Results**\n\n**Your Question:** {query}\n\nFound {len(rows)} results for your query.",
                "table": rows
            }
