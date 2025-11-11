"""
Unified Data Access Object (DAO) layer using JSON storage.
Replaces database-specific DAOs with JSON file operations.

All DAO methods perform Pydantic validation to ensure data integrity.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import ValidationError
from models.pydantic_models import (
    User, Portfolio, Trade, Goal, Account, Transaction,
    Subscription, VoiceCommand, RAGDocument
)
from services.json_storage_service import storage


class DAOValidationError(Exception):
    """Raised when data validation fails in DAO operations"""
    pass


class UserDAO:
    """Data access object for User operations"""

    @staticmethod
    def create_user(user_data: Dict[str, Any]) -> User:
        """
        Create a new user with Pydantic validation.

        Args:
            user_data: User data dictionary

        Returns:
            Validated User object

        Raises:
            DAOValidationError: If user data fails validation
        """
        try:
            # Validate user data with Pydantic
            user = User(**user_data)
            stored = storage.users.create(user.id, user.dict())
            return User(**stored)
        except ValidationError as e:
            raise DAOValidationError(f"User validation failed: {e}")

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """Get user by ID"""
        data = storage.users.read(user_id)
        return User(**data) if data else None

    @staticmethod
    def get_user_by_username(username: str) -> Optional[User]:
        """Get user by username"""
        data = storage.users.find_one(lambda u: u.get("username") == username)
        return User(**data) if data else None

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """Get user by email"""
        data = storage.users.find_one(lambda u: u.get("email") == email)
        return User(**data) if data else None

    @staticmethod
    def update_user(user_id: str, updates: Dict[str, Any]) -> Optional[User]:
        """
        Update user with validation.

        Args:
            user_id: User ID to update
            updates: Fields to update

        Returns:
            Updated User object or None if not found

        Raises:
            DAOValidationError: If update results in invalid user data
        """
        try:
            updates["updated_at"] = datetime.utcnow().isoformat()
            data = storage.users.update(user_id, updates)
            if data:
                # Validate the updated user data
                return User(**data)
            return None
        except ValidationError as e:
            raise DAOValidationError(f"User update validation failed: {e}")

    @staticmethod
    def delete_user(user_id: str) -> bool:
        """Delete user"""
        return storage.users.delete(user_id)

    @staticmethod
    def list_users() -> List[User]:
        """List all users"""
        user_ids = storage.users.list_all()
        users = []
        for user_id in user_ids:
            data = storage.users.read(user_id)
            if data:
                users.append(User(**data))
        return users


class PortfolioDAO:
    """Data access object for Portfolio operations"""

    @staticmethod
    def create_portfolio(portfolio_data: Dict[str, Any]) -> Portfolio:
        """Create a new portfolio"""
        portfolio = Portfolio(**portfolio_data)
        stored = storage.portfolios.create(portfolio.id, portfolio.dict())
        return Portfolio(**stored)

    @staticmethod
    def get_portfolio_by_id(portfolio_id: str) -> Optional[Portfolio]:
        """Get portfolio by ID"""
        data = storage.portfolios.read(portfolio_id)
        return Portfolio(**data) if data else None

    @staticmethod
    def get_portfolios_by_user(user_id: str) -> List[Portfolio]:
        """Get all portfolios for a user"""
        portfolios_data = storage.portfolios.find(lambda p: p.get("user_id") == user_id)
        return [Portfolio(**p) for p in portfolios_data]

    @staticmethod
    def update_portfolio(portfolio_id: str, updates: Dict[str, Any]) -> Optional[Portfolio]:
        """Update portfolio"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.portfolios.update(portfolio_id, updates)
        return Portfolio(**data) if data else None

    @staticmethod
    def delete_portfolio(portfolio_id: str) -> bool:
        """Delete portfolio"""
        return storage.portfolios.delete(portfolio_id)


class TradeDAO:
    """Data access object for Trade operations"""

    @staticmethod
    def create_trade(trade_data: Dict[str, Any]) -> Trade:
        """Create a new trade"""
        trade = Trade(**trade_data)
        stored = storage.trades.create(trade.id, trade.dict())
        return Trade(**stored)

    @staticmethod
    def get_trade_by_id(trade_id: str) -> Optional[Trade]:
        """Get trade by ID"""
        data = storage.trades.read(trade_id)
        return Trade(**data) if data else None

    @staticmethod
    def get_trades_by_user(user_id: str) -> List[Trade]:
        """Get all trades for a user"""
        trades_data = storage.trades.find(lambda t: t.get("user_id") == user_id)
        return [Trade(**t) for t in trades_data]

    @staticmethod
    def get_trades_by_portfolio(portfolio_id: str) -> List[Trade]:
        """Get all trades for a portfolio"""
        trades_data = storage.trades.find(lambda t: t.get("portfolio_id") == portfolio_id)
        return [Trade(**t) for t in trades_data]

    @staticmethod
    def update_trade(trade_id: str, updates: Dict[str, Any]) -> Optional[Trade]:
        """Update trade"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.trades.update(trade_id, updates)
        return Trade(**data) if data else None

    @staticmethod
    def delete_trade(trade_id: str) -> bool:
        """Delete trade"""
        return storage.trades.delete(trade_id)


class GoalDAO:
    """Data access object for Goal operations"""

    @staticmethod
    def create_goal(goal_data: Dict[str, Any]) -> Goal:
        """Create a new goal"""
        goal = Goal(**goal_data)
        stored = storage.goals.create(goal.id, goal.dict())
        return Goal(**stored)

    @staticmethod
    def get_goal_by_id(goal_id: str) -> Optional[Goal]:
        """Get goal by ID"""
        data = storage.goals.read(goal_id)
        return Goal(**data) if data else None

    @staticmethod
    def get_goals_by_user(user_id: str) -> List[Goal]:
        """Get all goals for a user"""
        goals_data = storage.goals.find(lambda g: g.get("user_id") == user_id)
        return [Goal(**g) for g in goals_data]

    @staticmethod
    def update_goal(goal_id: str, updates: Dict[str, Any]) -> Optional[Goal]:
        """Update goal"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.goals.update(goal_id, updates)
        return Goal(**data) if data else None

    @staticmethod
    def delete_goal(goal_id: str) -> bool:
        """Delete goal"""
        return storage.goals.delete(goal_id)


class AccountDAO:
    """Data access object for Account operations"""

    @staticmethod
    def create_account(account_data: Dict[str, Any]) -> Account:
        """Create a new account"""
        account = Account(**account_data)
        stored = storage.accounts.create(account.id, account.dict())
        return Account(**stored)

    @staticmethod
    def get_account_by_id(account_id: str) -> Optional[Account]:
        """Get account by ID"""
        data = storage.accounts.read(account_id)
        return Account(**data) if data else None

    @staticmethod
    def get_accounts_by_user(user_id: str) -> List[Account]:
        """Get all accounts for a user"""
        accounts_data = storage.accounts.find(lambda a: a.get("user_id") == user_id)
        return [Account(**a) for a in accounts_data]

    @staticmethod
    def update_account(account_id: str, updates: Dict[str, Any]) -> Optional[Account]:
        """Update account"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.accounts.update(account_id, updates)
        return Account(**data) if data else None

    @staticmethod
    def delete_account(account_id: str) -> bool:
        """Delete account"""
        return storage.accounts.delete(account_id)


class TransactionDAO:
    """Data access object for Transaction operations"""

    @staticmethod
    def create_transaction(transaction_data: Dict[str, Any]) -> Transaction:
        """Create a new transaction"""
        transaction = Transaction(**transaction_data)
        stored = storage.transactions.create(transaction.id, transaction.dict())
        return Transaction(**stored)

    @staticmethod
    def get_transaction_by_id(transaction_id: str) -> Optional[Transaction]:
        """Get transaction by ID"""
        data = storage.transactions.read(transaction_id)
        return Transaction(**data) if data else None

    @staticmethod
    def get_transactions_by_user(user_id: str) -> List[Transaction]:
        """Get all transactions for a user"""
        transactions_data = storage.transactions.find(lambda t: t.get("user_id") == user_id)
        return [Transaction(**t) for t in transactions_data]

    @staticmethod
    def get_transactions_by_account(account_id: str) -> List[Transaction]:
        """Get all transactions for an account"""
        transactions_data = storage.transactions.find(lambda t: t.get("account_id") == account_id)
        return [Transaction(**t) for t in transactions_data]


class SubscriptionDAO:
    """Data access object for Subscription operations"""

    @staticmethod
    def create_subscription(subscription_data: Dict[str, Any]) -> Subscription:
        """Create a new subscription"""
        subscription = Subscription(**subscription_data)
        stored = storage.subscriptions.create(subscription.id, subscription.dict())
        return Subscription(**stored)

    @staticmethod
    def get_subscription_by_user(user_id: str) -> Optional[Subscription]:
        """Get subscription for a user"""
        data = storage.subscriptions.find_one(lambda s: s.get("user_id") == user_id)
        return Subscription(**data) if data else None

    @staticmethod
    def update_subscription(subscription_id: str, updates: Dict[str, Any]) -> Optional[Subscription]:
        """Update subscription"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.subscriptions.update(subscription_id, updates)
        return Subscription(**data) if data else None


class VoiceCommandDAO:
    """Data access object for VoiceCommand operations"""

    @staticmethod
    def create_command(command_data: Dict[str, Any]) -> VoiceCommand:
        """Create a new voice command"""
        command = VoiceCommand(**command_data)
        stored = storage.voice_commands.create(command.id, command.dict())
        return VoiceCommand(**stored)

    @staticmethod
    def get_command_by_id(command_id: str) -> Optional[VoiceCommand]:
        """Get voice command by ID"""
        data = storage.voice_commands.read(command_id)
        return VoiceCommand(**data) if data else None

    @staticmethod
    def get_commands_by_user(user_id: str) -> List[VoiceCommand]:
        """Get all voice commands for a user"""
        commands_data = storage.voice_commands.find(lambda c: c.get("user_id") == user_id)
        return [VoiceCommand(**c) for c in commands_data]

    @staticmethod
    def update_command(command_id: str, updates: Dict[str, Any]) -> Optional[VoiceCommand]:
        """Update voice command"""
        data = storage.voice_commands.update(command_id, updates)
        return VoiceCommand(**data) if data else None


class RAGDocumentDAO:
    """Data access object for RAG Document operations"""

    @staticmethod
    def create_document(document_data: Dict[str, Any]) -> RAGDocument:
        """Create a new RAG document"""
        document = RAGDocument(**document_data)
        stored = storage.rag_documents.create(document.id, document.dict())
        return RAGDocument(**stored)

    @staticmethod
    def get_document_by_id(document_id: str) -> Optional[RAGDocument]:
        """Get RAG document by ID"""
        data = storage.rag_documents.read(document_id)
        return RAGDocument(**data) if data else None

    @staticmethod
    def get_documents_by_user(user_id: str) -> List[RAGDocument]:
        """Get all RAG documents for a user"""
        documents_data = storage.rag_documents.find(lambda d: d.get("user_id") == user_id)
        return [RAGDocument(**d) for d in documents_data]

    @staticmethod
    def update_document(document_id: str, updates: Dict[str, Any]) -> Optional[RAGDocument]:
        """Update RAG document"""
        updates["updated_at"] = datetime.utcnow().isoformat()
        data = storage.rag_documents.update(document_id, updates)
        return RAGDocument(**data) if data else None

    @staticmethod
    def delete_document(document_id: str) -> bool:
        """Delete RAG document"""
        return storage.rag_documents.delete(document_id)
