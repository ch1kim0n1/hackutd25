# backend/services/plaid_service.py
"""
Real Plaid integration service for APEX.
Replaces mock_plaid.py with actual Plaid SDK integration.
"""
import os
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta, date
from decimal import Decimal

import plaid
from plaid.api import plaid_api
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.investments_transactions_get_request import InvestmentsTransactionsGetRequest


class PlaidService:
    """Production Plaid integration service"""

    def __init__(self):
        """Initialize Plaid client with environment credentials"""
        # Get credentials from environment
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.environment = os.getenv("PLAID_ENV", "sandbox")  # sandbox, development, production

        # Set Plaid environment
        if self.environment == "sandbox":
            host = plaid.Environment.Sandbox
        elif self.environment == "development":
            host = plaid.Environment.Development
        else:
            host = plaid.Environment.Production

        # Initialize configuration
        configuration = plaid.Configuration(
            host=host,
            api_key={
                'clientId': self.client_id,
                'secret': self.secret,
            }
        )

        # Create API client
        api_client = plaid.ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)

    async def create_link_token(
        self,
        user_id: str,
        client_name: str = "APEX"
    ) -> Dict[str, str]:
        """
        Create a Link token for Plaid Link OAuth flow.

        Args:
            user_id: Unique user identifier
            client_name: Name to display in Plaid Link

        Returns:
            Dict with link_token and expiration
        """
        try:
            request = LinkTokenCreateRequest(
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                client_name=client_name,
                products=[Products("auth"), Products("transactions"), Products("investments")],
                country_codes=[CountryCode("US")],
                language="en",
            )

            response = self.client.link_token_create(request)
            return {
                "link_token": response['link_token'],
                "expiration": response['expiration'],
            }
        except plaid.ApiException as e:
            print(f"Plaid API error creating link token: {e}")
            raise

    async def exchange_public_token(self, public_token: str) -> str:
        """
        Exchange public token for access token after Plaid Link success.

        Args:
            public_token: Public token from Plaid Link

        Returns:
            Access token (store this securely, encrypted)
        """
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            return response['access_token']
        except plaid.ApiException as e:
            print(f"Plaid API error exchanging token: {e}")
            raise

    async def get_accounts(self, access_token: str) -> List[Dict[str, Any]]:
        """
        Get all accounts for a user.

        Args:
            access_token: User's Plaid access token

        Returns:
            List of account dictionaries
        """
        try:
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)

            accounts = []
            for account in response['accounts']:
                accounts.append({
                    "account_id": account['account_id'],
                    "name": account['name'],
                    "official_name": account.get('official_name'),
                    "type": account['type'],
                    "subtype": account['subtype'],
                    "mask": account.get('mask'),
                    "balance": {
                        "available": account['balances'].get('available'),
                        "current": account['balances']['current'],
                        "limit": account['balances'].get('limit'),
                        "currency": account['balances'].get('iso_currency_code', 'USD'),
                    }
                })
            return accounts
        except plaid.ApiException as e:
            print(f"Plaid API error getting accounts: {e}")
            raise

    async def get_transactions(
        self,
        access_token: str,
        start_date: date,
        end_date: date,
        account_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get transactions for date range.

        Args:
            access_token: User's Plaid access token
            start_date: Start date
            end_date: End date
            account_ids: Optional list of account IDs to filter

        Returns:
            List of transaction dictionaries
        """
        try:
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options={"account_ids": account_ids} if account_ids else None
            )

            response = self.client.transactions_get(request)
            transactions = []

            for txn in response['transactions']:
                transactions.append({
                    "transaction_id": txn['transaction_id'],
                    "account_id": txn['account_id'],
                    "amount": float(txn['amount']),
                    "date": txn['date'].isoformat() if hasattr(txn['date'], 'isoformat') else str(txn['date']),
                    "name": txn['name'],
                    "merchant_name": txn.get('merchant_name'),
                    "category": txn.get('category', []),
                    "category_id": txn.get('category_id'),
                    "pending": txn.get('pending', False),
                    "payment_channel": txn.get('payment_channel'),
                    "location": {
                        "city": txn.get('location', {}).get('city'),
                        "state": txn.get('location', {}).get('region'),
                        "country": txn.get('location', {}).get('country'),
                    }
                })

            return transactions
        except plaid.ApiException as e:
            print(f"Plaid API error getting transactions: {e}")
            raise

    async def get_recent_transactions(
        self,
        access_token: str,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get recent transactions (last N days).

        Args:
            access_token: User's Plaid access token
            days: Number of days to look back

        Returns:
            List of transactions
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        return await self.get_transactions(access_token, start_date, end_date)

    async def get_investment_holdings(
        self,
        access_token: str
    ) -> Dict[str, Any]:
        """
        Get investment holdings (stocks, ETFs, mutual funds).

        Args:
            access_token: User's Plaid access token

        Returns:
            Dict with accounts and holdings
        """
        try:
            request = InvestmentsHoldingsGetRequest(access_token=access_token)
            response = self.client.investments_holdings_get(request)

            result = {
                "accounts": [],
                "holdings": [],
                "securities": {}
            }

            # Process accounts
            for account in response['accounts']:
                result["accounts"].append({
                    "account_id": account['account_id'],
                    "name": account['name'],
                    "type": account['type'],
                    "subtype": account['subtype'],
                    "balance": account['balances']['current']
                })

            # Process holdings
            for holding in response['holdings']:
                result["holdings"].append({
                    "account_id": holding['account_id'],
                    "security_id": holding['security_id'],
                    "quantity": float(holding['quantity']),
                    "institution_price": float(holding['institution_price']),
                    "institution_value": float(holding['institution_value']),
                    "cost_basis": float(holding.get('cost_basis', 0)),
                })

            # Process securities (symbol mapping)
            for security in response['securities']:
                result["securities"][security['security_id']] = {
                    "ticker_symbol": security.get('ticker_symbol'),
                    "name": security.get('name'),
                    "type": security.get('type'),
                    "close_price": float(security.get('close_price', 0)),
                }

            return result
        except plaid.ApiException as e:
            print(f"Plaid API error getting holdings: {e}")
            raise

    async def get_investment_transactions(
        self,
        access_token: str,
        start_date: date,
        end_date: date
    ) -> List[Dict[str, Any]]:
        """
        Get investment transactions (buys, sells, dividends).

        Args:
            access_token: User's Plaid access token
            start_date: Start date
            end_date: End date

        Returns:
            List of investment transactions
        """
        try:
            request = InvestmentsTransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date
            )

            response = self.client.investments_transactions_get(request)
            transactions = []

            for txn in response['investment_transactions']:
                transactions.append({
                    "transaction_id": txn['investment_transaction_id'],
                    "account_id": txn['account_id'],
                    "security_id": txn['security_id'],
                    "date": txn['date'].isoformat() if hasattr(txn['date'], 'isoformat') else str(txn['date']),
                    "name": txn['name'],
                    "quantity": float(txn['quantity']),
                    "amount": float(txn['amount']),
                    "price": float(txn['price']),
                    "fees": float(txn.get('fees', 0)),
                    "type": txn['type'],  # buy, sell, dividend, etc.
                })

            return transactions
        except plaid.ApiException as e:
            print(f"Plaid API error getting investment transactions: {e}")
            raise

    async def calculate_net_worth(self, access_token: str) -> Dict[str, Decimal]:
        """
        Calculate total net worth across all accounts.

        Args:
            access_token: User's Plaid access token

        Returns:
            Dict with assets, liabilities, net_worth
        """
        accounts = await self.get_accounts(access_token)

        assets = Decimal(0)
        liabilities = Decimal(0)

        for account in accounts:
            balance = Decimal(str(account['balance']['current']))
            account_type = account['type']

            # Assets: depository, investment, brokerage
            if account_type in ['depository', 'investment', 'brokerage']:
                assets += balance
            # Liabilities: credit, loan
            elif account_type in ['credit', 'loan']:
                liabilities += abs(balance)

        return {
            "assets": assets,
            "liabilities": liabilities,
            "net_worth": assets - liabilities
        }

    async def categorize_transactions(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Decimal]:
        """
        Categorize transactions and calculate spending by category.

        Args:
            transactions: List of transaction dicts

        Returns:
            Dict mapping category to total amount
        """
        categories = {}

        for txn in transactions:
            # Skip pending transactions
            if txn.get('pending'):
                continue

            # Get primary category
            category_list = txn.get('category', [])
            category = category_list[0] if category_list else "Uncategorized"

            # Add to category total
            amount = Decimal(str(txn['amount']))
            if category in categories:
                categories[category] += amount
            else:
                categories[category] = amount

        return categories


# Global instance
plaid_service = PlaidService()
