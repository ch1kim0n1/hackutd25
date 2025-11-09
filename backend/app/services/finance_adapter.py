# backend/services/finance_adapter.py
"""
Smart adapter for switching between mock and real Plaid.
Automatically uses real Plaid if credentials available, falls back to mock.
"""

import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class FinanceAdapter:
    """Smart adapter for Finance services (Plaid or Mock)"""

    def __init__(self):
        """Initialize with real or mock Plaid based on environment"""
        self.use_real_plaid = self._should_use_real_plaid()
        
        if self.use_real_plaid:
            try:
                from app.services.plaid_integration import PlaidIntegration
                self.plaid_service = PlaidIntegration()
                logger.info("✅ Using REAL Plaid integration")
            except Exception as e:
                logger.warning(f"Failed to initialize real Plaid: {e}. Falling back to mock.")
                self.use_real_plaid = False
                from app.services.mock_plaid import mock_plaid_data
                self.mock_plaid = mock_plaid_data
        else:
            from app.services.mock_plaid import mock_plaid_data
            self.mock_plaid = mock_plaid_data
            logger.info("📋 Using mock Plaid data (no credentials)")

    def _should_use_real_plaid(self) -> bool:
        """Check if real Plaid should be used"""
        return bool(
            os.getenv("PLAID_CLIENT_ID") and
            os.getenv("PLAID_SECRET")
        )

    async def get_accounts(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Get user accounts"""
        if self.use_real_plaid and access_token:
            try:
                return await self.plaid_service.get_accounts(access_token)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.get_accounts()
        else:
            return self.mock_plaid.get_accounts()

    async def get_transactions(self, days: int = 90, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Get recent transactions"""
        if self.use_real_plaid and access_token:
            try:
                return await self.plaid_service.get_transactions(access_token, days)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.get_transactions(days)
        else:
            return self.mock_plaid.get_transactions(days)

    async def get_subscriptions(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Detect recurring subscriptions"""
        if self.use_real_plaid and access_token:
            try:
                return await self.plaid_service.get_recurring_transactions(access_token)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.get_subscriptions()
        else:
            return self.mock_plaid.get_subscriptions()

    def get_net_worth(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Calculate net worth"""
        if self.use_real_plaid and access_token:
            try:
                return self.plaid_service.get_net_worth(access_token)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.get_net_worth()
        else:
            return self.mock_plaid.get_net_worth()

    def get_cash_flow(self, days: int = 30, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Analyze cash flow"""
        if self.use_real_plaid and access_token:
            try:
                return self.plaid_service.get_cash_flow(access_token, days)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.get_cash_flow(days)
        else:
            return self.mock_plaid.get_cash_flow(days)

    def calculate_health_score(self, access_token: Optional[str] = None) -> Dict[str, Any]:
        """Calculate financial health score"""
        if self.use_real_plaid and access_token:
            try:
                return self.plaid_service.calculate_health_score(access_token)
            except Exception as e:
                logger.error(f"Plaid API error: {e}. Falling back to mock.")
                return self.mock_plaid.calculate_health_score()
        else:
            return self.mock_plaid.calculate_health_score()

    def create_link_token(self, user_id: str, redirect_url: str) -> Optional[str]:
        """Create Plaid Link token for account connection"""
        if self.use_real_plaid:
            try:
                return self.plaid_service.create_link_token(user_id, redirect_url)
            except Exception as e:
                logger.error(f"Failed to create link token: {e}")
                return None
        else:
            logger.warning("Link token creation not available in mock mode")
            return None

    def exchange_public_token(self, public_token: str, metadata: Dict) -> Optional[str]:
        """Exchange Plaid public token for access token"""
        if self.use_real_plaid:
            try:
                return self.plaid_service.exchange_public_token(public_token)
            except Exception as e:
                logger.error(f"Failed to exchange token: {e}")
                return None
        else:
            logger.warning("Token exchange not available in mock mode")
            return None

    def get_status(self) -> Dict[str, Any]:
        """Get adapter status"""
        return {
            "using_real_plaid": self.use_real_plaid,
            "mode": "production" if self.use_real_plaid else "sandbox",
            "message": "Connected to Plaid API" if self.use_real_plaid else "Using mock data (development)"
        }
