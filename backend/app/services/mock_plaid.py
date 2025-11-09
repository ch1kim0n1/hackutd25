import random
from datetime import datetime, timedelta
from typing import List, Dict

class MockPlaidData:
    def __init__(self):
        self.accounts = self._generate_accounts()
        self.transactions = self._generate_transactions()
        self.subscriptions = self._detect_subscriptions()
    
    def _generate_accounts(self) -> List[Dict]:
        return [
            {
                "id": "acc_checking_001",
                "name": "Chase Total Checking",
                "type": "depository",
                "subtype": "checking",
                "institution": "Chase",
                "balance": 12543.67,
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "acc_savings_001",
                "name": "Chase Savings",
                "type": "depository",
                "subtype": "savings",
                "institution": "Chase",
                "balance": 45230.12,
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "acc_credit_001",
                "name": "Chase Sapphire Reserve",
                "type": "credit",
                "subtype": "credit card",
                "institution": "Chase",
                "balance": -2847.35,
                "available_credit": 27152.65,
                "credit_limit": 30000,
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "acc_investment_001",
                "name": "Vanguard 401k",
                "type": "investment",
                "subtype": "401k",
                "institution": "Vanguard",
                "balance": 187650.45,
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            },
            {
                "id": "acc_credit_002",
                "name": "American Express Gold",
                "type": "credit",
                "subtype": "credit card",
                "institution": "American Express",
                "balance": -1523.88,
                "available_credit": 23476.12,
                "credit_limit": 25000,
                "currency": "USD",
                "last_updated": datetime.now().isoformat()
            }
        ]
    
    def _generate_transactions(self) -> List[Dict]:
        transactions = []
        categories = [
            ("Groceries", ["Whole Foods", "Trader Joe's", "Kroger", "Safeway"], -80, -250, "expense"),
            ("Dining", ["Chipotle", "Starbucks", "Panera", "Local Restaurant"], -15, -75, "expense"),
            ("Transportation", ["Uber", "Lyft", "Shell Gas", "Chevron"], -10, -60, "expense"),
            ("Utilities", ["PG&E", "Comcast", "AT&T", "Water District"], -50, -200, "expense"),
            ("Entertainment", ["Netflix", "Spotify", "AMC Theaters", "Steam"], -10, -50, "expense"),
            ("Shopping", ["Amazon", "Target", "Best Buy", "Apple Store"], -25, -300, "expense"),
            ("Healthcare", ["CVS Pharmacy", "Kaiser", "Walgreens"], -20, -150, "expense"),
            ("Income", ["Direct Deposit - Employer"], 3500, 8000, "income"),
        ]
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        
        for category, merchants, min_amt, max_amt, txn_type in categories:
            if txn_type == "income":
                for i in range(3):
                    txn_date = end_date - timedelta(days=30 * i)
                    transactions.append({
                        "id": f"txn_{category.lower()}_{i}",
                        "account_id": "acc_checking_001",
                        "date": txn_date.strftime("%Y-%m-%d"),
                        "amount": random.uniform(min_amt, max_amt),
                        "merchant": random.choice(merchants),
                        "category": category,
                        "type": txn_type,
                        "pending": False
                    })
            else:
                num_transactions = random.randint(5, 15)
                for i in range(num_transactions):
                    days_ago = random.randint(0, 90)
                    txn_date = end_date - timedelta(days=days_ago)
                    transactions.append({
                        "id": f"txn_{category.lower()}_{i}",
                        "account_id": random.choice(["acc_checking_001", "acc_credit_001", "acc_credit_002"]),
                        "date": txn_date.strftime("%Y-%m-%d"),
                        "amount": random.uniform(min_amt, max_amt),
                        "merchant": random.choice(merchants),
                        "category": category,
                        "type": txn_type,
                        "pending": i < 2
                    })
        
        recurring_subscriptions = [
            ("Netflix", -15.99, "Entertainment", "acc_credit_001"),
            ("Spotify", -10.99, "Entertainment", "acc_credit_001"),
            ("Amazon Prime", -14.99, "Shopping", "acc_credit_002"),
            ("ChatGPT Plus", -20.00, "Software", "acc_credit_001"),
            ("GitHub Copilot", -10.00, "Software", "acc_credit_002"),
            ("Adobe Creative Cloud", -54.99, "Software", "acc_credit_001"),
            ("Gym Membership", -49.99, "Health & Fitness", "acc_credit_002"),
            ("NY Times Digital", -17.00, "News & Media", "acc_credit_001"),
        ]
        
        for merchant, amount, category, account_id in recurring_subscriptions:
            for i in range(3):
                txn_date = end_date - timedelta(days=30 * i)
                transactions.append({
                    "id": f"txn_subscription_{merchant.lower().replace(' ', '_')}_{i}",
                    "account_id": account_id,
                    "date": txn_date.strftime("%Y-%m-%d"),
                    "amount": amount,
                    "merchant": merchant,
                    "category": category,
                    "type": "expense",
                    "pending": False,
                    "recurring": True
                })
        
        transactions.sort(key=lambda x: x['date'], reverse=True)
        return transactions
    
    def _detect_subscriptions(self) -> List[Dict]:
        subscription_map = {}
        for txn in self.transactions:
            if txn.get('recurring', False):
                merchant = txn['merchant']
                if merchant not in subscription_map:
                    subscription_map[merchant] = {
                        "merchant": merchant,
                        "amount": txn['amount'],
                        "category": txn['category'],
                        "frequency": "monthly",
                        "account_id": txn['account_id'],
                        "last_charge": txn['date'],
                        "annual_cost": abs(txn['amount']) * 12
                    }
        
        return list(subscription_map.values())
    
    def get_accounts(self) -> List[Dict]:
        return self.accounts
    
    def get_transactions(self, days: int = 90) -> List[Dict]:
        cutoff_date = datetime.now() - timedelta(days=days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        return [txn for txn in self.transactions if txn['date'] >= cutoff_str]
    
    def get_subscriptions(self) -> List[Dict]:
        return self.subscriptions
    
    def get_net_worth(self) -> Dict:
        assets = sum(acc['balance'] for acc in self.accounts if acc['balance'] > 0)
        liabilities = abs(sum(acc['balance'] for acc in self.accounts if acc['balance'] < 0))
        return {
            "assets": assets,
            "liabilities": liabilities,
            "net_worth": assets - liabilities
        }
    
    def get_cash_flow(self, days: int = 30) -> Dict:
        recent_txns = self.get_transactions(days)
        income = sum(txn['amount'] for txn in recent_txns if txn['type'] == 'income')
        expenses = abs(sum(txn['amount'] for txn in recent_txns if txn['type'] == 'expense'))
        return {
            "period_days": days,
            "income": income,
            "expenses": expenses,
            "net_cash_flow": income - expenses,
            "savings_rate": ((income - expenses) / income * 100) if income > 0 else 0
        }
    
    def calculate_health_score(self) -> Dict:
        net_worth_data = self.get_net_worth()
        cash_flow = self.get_cash_flow(30)
        
        emergency_fund = next((acc['balance'] for acc in self.accounts if acc['subtype'] == 'savings'), 0)
        monthly_expenses = cash_flow['expenses']
        emergency_fund_months = emergency_fund / monthly_expenses if monthly_expenses > 0 else 0
        
        score = 0
        factors = []
        
        if emergency_fund_months >= 6:
            score += 30
            factors.append({"factor": "Emergency Fund", "score": 30, "status": "excellent"})
        elif emergency_fund_months >= 3:
            score += 20
            factors.append({"factor": "Emergency Fund", "score": 20, "status": "good"})
        else:
            score += 10
            factors.append({"factor": "Emergency Fund", "score": 10, "status": "needs improvement"})
        
        debt_to_income = net_worth_data['liabilities'] / (cash_flow['income'] * 12) if cash_flow['income'] > 0 else 0
        if debt_to_income < 0.1:
            score += 25
            factors.append({"factor": "Debt Management", "score": 25, "status": "excellent"})
        elif debt_to_income < 0.3:
            score += 15
            factors.append({"factor": "Debt Management", "score": 15, "status": "good"})
        else:
            score += 5
            factors.append({"factor": "Debt Management", "score": 5, "status": "needs improvement"})
        
        if cash_flow['savings_rate'] >= 20:
            score += 25
            factors.append({"factor": "Savings Rate", "score": 25, "status": "excellent"})
        elif cash_flow['savings_rate'] >= 10:
            score += 15
            factors.append({"factor": "Savings Rate", "score": 15, "status": "good"})
        else:
            score += 5
            factors.append({"factor": "Savings Rate", "score": 5, "status": "needs improvement"})
        
        investment_balance = next((acc['balance'] for acc in self.accounts if acc['type'] == 'investment'), 0)
        investment_ratio = investment_balance / net_worth_data['net_worth'] if net_worth_data['net_worth'] > 0 else 0
        if investment_ratio >= 0.3:
            score += 20
            factors.append({"factor": "Investment Allocation", "score": 20, "status": "excellent"})
        elif investment_ratio >= 0.15:
            score += 10
            factors.append({"factor": "Investment Allocation", "score": 10, "status": "good"})
        else:
            score += 5
            factors.append({"factor": "Investment Allocation", "score": 5, "status": "needs improvement"})
        
        return {
            "score": score,
            "rating": "Excellent" if score >= 80 else "Good" if score >= 60 else "Fair" if score >= 40 else "Needs Improvement",
            "factors": factors,
            "emergency_fund_months": emergency_fund_months,
            "debt_to_income_ratio": debt_to_income * 100,
            "savings_rate": cash_flow['savings_rate']
        }

mock_plaid_data = MockPlaidData()
