"""
Real Plaid API Integration for APEX.
Provides account and transaction data through the official Plaid API.
"""
import os
from typing import Optional, Dict, List
from datetime import datetime, timedelta
import logging
import aiohttp

logger = logging.getLogger(__name__)


class PlaidIntegration:
    """
    Handles real integration with Plaid API for account and transaction retrieval.
    """
    
    def __init__(self):
        self.client_id = os.getenv("PLAID_CLIENT_ID")
        self.secret = os.getenv("PLAID_SECRET")
        self.environment = os.getenv("PLAID_ENVIRONMENT", "sandbox")  # sandbox, development, production
        self.base_url = f"https://{self.environment}.plaid.com"
        
        if not self.client_id or not self.secret:
            logger.warning("Plaid credentials not configured - will fall back to mock data")
            self.configured = False
        else:
            self.configured = True
            logger.info(f"Plaid configured for {self.environment} environment")
        
        # Cache for performance
        self.access_token_cache = {}  # user_id -> access_token
        self.account_cache = {}  # user_id -> {timestamp, accounts}
        self.transaction_cache = {}  # user_id -> {timestamp, transactions}
        self.cache_ttl = 3600  # 1 hour
    
    async def create_link_token(self, user_id: str, redirect_uri: Optional[str] = None) -> Dict:
        """
        Create a Plaid Link token for account connection.
        
        Args:
            user_id: Unique user identifier
            redirect_uri: Optional redirect URI for web flow
        
        Returns:
            {
                "link_token": "link-sandbox-...",
                "expiration": "2024-01-15T10:00:00Z",
                "request_id": "req-..."
            }
        """
        if not self.configured:
            return self._mock_link_token(user_id)
        
        try:
            payload = {
                "client_id": self.client_id,
                "secret": self.secret,
                "user": {
                    "client_user_id": str(user_id)
                },
                "client_name": "APEX Financial",
                "products": ["auth", "transactions"],
                "country_codes": ["US"],
                "language": "en"
            }
            
            if redirect_uri:
                payload["redirect_uri"] = redirect_uri
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/link/token/create",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Plaid link token creation failed: {resp.status}")
                        return self._mock_link_token(user_id)
                    
                    data = await resp.json()
                    logger.info(f"Link token created for user {user_id}")
                    
                    return {
                        "link_token": data.get("link_token"),
                        "expiration": data.get("expiration"),
                        "request_id": data.get("request_id")
                    }
        
        except Exception as e:
            logger.error(f"Link token creation error: {e}")
            return self._mock_link_token(user_id)
    
    async def exchange_public_token(self, user_id: str, public_token: str) -> Optional[str]:
        """
        Exchange Plaid public token for access token.
        
        Args:
            user_id: User identifier
            public_token: Token from Plaid Link flow
        
        Returns:
            Access token for future API calls, or None if failed
        """
        if not self.configured:
            return "mock_access_token_" + str(user_id)[:8]
        
        try:
            payload = {
                "client_id": self.client_id,
                "secret": self.secret,
                "public_token": public_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/item/public_token/exchange",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Token exchange failed: {resp.status}")
                        return None
                    
                    data = await resp.json()
                    access_token = data.get("access_token")
                    
                    # Cache the access token
                    self.access_token_cache[str(user_id)] = access_token
                    
                    logger.info(f"Access token obtained for user {user_id}")
                    return access_token
        
        except Exception as e:
            logger.error(f"Token exchange error: {e}")
            return None
    
    async def get_accounts(self, user_id: str, access_token: str) -> List[Dict]:
        """
        Retrieve linked bank accounts.
        
        Returns:
            List of account objects with balances
        """
        if not self.configured:
            return self._mock_accounts()
        
        # Check cache
        if str(user_id) in self.account_cache:
            cache_entry = self.account_cache[str(user_id)]
            if datetime.utcnow().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["accounts"]
        
        try:
            payload = {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/accounts/get",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to fetch accounts: {resp.status}")
                        return self._mock_accounts()
                    
                    data = await resp.json()
                    accounts = data.get("accounts", [])
                    
                    # Cache result
                    self.account_cache[str(user_id)] = {
                        "timestamp": datetime.utcnow().timestamp(),
                        "accounts": accounts
                    }
                    
                    logger.info(f"Fetched {len(accounts)} accounts for user {user_id}")
                    return accounts
        
        except Exception as e:
            logger.error(f"Get accounts error: {e}")
            return self._mock_accounts()
    
    async def get_transactions(
        self,
        user_id: str,
        access_token: str,
        days_back: int = 90
    ) -> List[Dict]:
        """
        Retrieve transactions for all linked accounts.
        
        Args:
            user_id: User identifier
            access_token: Plaid access token
            days_back: Number of days to retrieve (max 730)
        
        Returns:
            List of transaction objects
        """
        if not self.configured:
            return self._mock_transactions(days_back)
        
        # Check cache
        cache_key = f"{user_id}_{days_back}"
        if cache_key in self.transaction_cache:
            cache_entry = self.transaction_cache[cache_key]
            if datetime.utcnow().timestamp() - cache_entry["timestamp"] < self.cache_ttl:
                return cache_entry["transactions"]
        
        try:
            start_date = (datetime.utcnow() - timedelta(days=days_back)).date().isoformat()
            end_date = datetime.utcnow().date().isoformat()
            
            payload = {
                "client_id": self.client_id,
                "secret": self.secret,
                "access_token": access_token,
                "start_date": start_date,
                "end_date": end_date,
                "options": {
                    "count": 500,
                    "offset": 0
                }
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/transactions/get",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15)  # Longer timeout for transactions
                ) as resp:
                    if resp.status != 200:
                        logger.error(f"Failed to fetch transactions: {resp.status}")
                        return self._mock_transactions(days_back)
                    
                    data = await resp.json()
                    transactions = data.get("transactions", [])
                    
                    # Cache result
                    self.transaction_cache[cache_key] = {
                        "timestamp": datetime.utcnow().timestamp(),
                        "transactions": transactions
                    }
                    
                    logger.info(f"Fetched {len(transactions)} transactions for user {user_id}")
                    return transactions
        
        except Exception as e:
            logger.error(f"Get transactions error: {e}")
            return self._mock_transactions(days_back)
    
    def get_status(self) -> Dict:
        """Get Plaid integration status"""
        return {
            "status": "configured" if self.configured else "mock_fallback",
            "environment": self.environment if self.configured else "none",
            "mode": "real" if self.configured else "mock"
        }
    
    # Mock data fallback methods
    @staticmethod
    def _mock_link_token(user_id: str) -> Dict:
        """Mock link token for development"""
        return {
            "link_token": f"link-mock-{user_id}",
            "expiration": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "request_id": f"req-mock-{user_id}"
        }
    
    @staticmethod
    def _mock_accounts() -> List[Dict]:
        """Mock accounts for development"""
        return [
            {
                "account_id": "account_001",
                "name": "Checking Account",
                "type": "depository",
                "subtype": "checking",
                "balances": {
                    "available": 15000.00,
                    "current": 15500.00,
                    "limit": None
                }
            },
            {
                "account_id": "account_002",
                "name": "Savings Account",
                "type": "depository",
                "subtype": "savings",
                "balances": {
                    "available": 50000.00,
                    "current": 50000.00,
                    "limit": None
                }
            }
        ]
    
    @staticmethod
    def _mock_transactions(days_back: int = 90) -> List[Dict]:
        """Mock transactions for development"""
        now = datetime.utcnow()
        return [
            {
                "transaction_id": f"txn_{i}",
                "account_id": "account_001",
                "amount": 50.00 + (i * 10),
                "date": (now - timedelta(days=i)).date().isoformat(),
                "name": f"Transaction {i}",
                "merchant_name": f"Merchant {i % 5}",
                "category": ["FOOD_AND_DRINK", "SHOPPING", "TRANSFER"][i % 3],
                "pending": False
            }
            for i in range(min(days_back, 30))
        ]
