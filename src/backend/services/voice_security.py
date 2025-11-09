"""
Voice Command Security Service for APEX.
Implements trade confirmation, rate limiting, and voice command validation.
"""
import time
from typing import Optional, Dict, List
from uuid import UUID
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Types of voice commands that may require confirmation"""
    BUY = "buy"
    SELL = "sell"
    REBALANCE = "rebalance"
    SET_GOAL = "set_goal"
    CANCEL_ORDER = "cancel_order"


class VoiceCommandTracker:
    """
    Tracks voice commands per user for rate limiting and confirmation.
    In production, use Redis instead of in-memory dict.
    """
    
    def __init__(self):
        # {user_id: {command_id: {timestamp, command_type, amount, symbol, confirmed}}}
        self.pending_commands: Dict[str, Dict[str, dict]] = {}
        # {user_id: [timestamp1, timestamp2, ...]} for rate limiting
        self.command_timestamps: Dict[str, List[float]] = {}
        self.RATE_LIMIT_WINDOW = 60  # seconds
        self.MAX_COMMANDS_PER_WINDOW = 5  # 5 commands per minute
        self.CONFIRMATION_TIMEOUT = 30  # seconds to confirm command
    
    def check_rate_limit(self, user_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if user exceeds rate limit (5 commands per minute).
        
        Returns:
            (is_allowed: bool, error_message: Optional[str])
        """
        user_id_str = str(user_id)
        now = time.time()
        
        # Initialize tracking for new users
        if user_id_str not in self.command_timestamps:
            self.command_timestamps[user_id_str] = []
        
        # Remove old timestamps outside the window
        self.command_timestamps[user_id_str] = [
            ts for ts in self.command_timestamps[user_id_str]
            if now - ts < self.RATE_LIMIT_WINDOW
        ]
        
        # Check if limit exceeded
        command_count = len(self.command_timestamps[user_id_str])
        if command_count >= self.MAX_COMMANDS_PER_WINDOW:
            return False, f"Rate limit exceeded: {command_count}/{self.MAX_COMMANDS_PER_WINDOW} commands in last minute"
        
        # Record this command
        self.command_timestamps[user_id_str].append(now)
        
        return True, None
    
    def create_pending_command(
        self,
        user_id: UUID,
        command_id: str,
        command_type: CommandType,
        amount: float,
        symbol: str = None,
        metadata: dict = None
    ) -> dict:
        """
        Create a pending voice command awaiting confirmation.
        
        Args:
            user_id: User ID
            command_id: Unique command identifier
            command_type: Type of command (BUY, SELL, etc.)
            amount: Trade amount or order quantity
            symbol: Stock symbol (for trades)
            metadata: Additional command data
        
        Returns:
            Pending command dict with confirmation requirement
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_commands:
            self.pending_commands[user_id_str] = {}
        
        # Require confirmation for high-value trades (>$10k)
        requires_confirmation = amount > 10000 or command_type in [
            CommandType.REBALANCE,
            CommandType.CANCEL_ORDER
        ]
        
        pending_command = {
            "command_id": command_id,
            "command_type": command_type.value,
            "amount": amount,
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat(),
            "confirmed": False,
            "requires_confirmation": requires_confirmation,
            "confirmation_token": self._generate_confirmation_token() if requires_confirmation else None,
            "metadata": metadata or {}
        }
        
        self.pending_commands[user_id_str][command_id] = pending_command
        
        if requires_confirmation:
            logger.info(f"Pending command created for user {user_id}: {command_type.value} ${amount}")
        
        return pending_command
    
    def confirm_command(
        self,
        user_id: UUID,
        command_id: str,
        confirmation_phrase: str
    ) -> tuple[bool, Optional[str]]:
        """
        Confirm a pending voice command with explicit phrase.
        
        Args:
            user_id: User ID
            command_id: Command identifier
            confirmation_phrase: User's confirmation phrase (e.g., "yes, confirm")
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        user_id_str = str(user_id)
        
        # Find the pending command
        if user_id_str not in self.pending_commands:
            return False, "No pending commands for this user"
        
        if command_id not in self.pending_commands[user_id_str]:
            return False, f"Command {command_id} not found"
        
        pending = self.pending_commands[user_id_str][command_id]
        
        # Check if already confirmed
        if pending["confirmed"]:
            return False, "Command already confirmed"
        
        # Check if timeout exceeded
        cmd_time = datetime.fromisoformat(pending["timestamp"])
        if datetime.utcnow() - cmd_time > timedelta(seconds=self.CONFIRMATION_TIMEOUT):
            del self.pending_commands[user_id_str][command_id]
            return False, "Confirmation timeout exceeded (30s)"
        
        # Validate confirmation phrase
        valid_phrases = ["yes", "confirm", "execute", "proceed", "approved"]
        if confirmation_phrase.lower().strip() not in valid_phrases:
            return False, f"Invalid confirmation phrase. Use one of: {', '.join(valid_phrases)}"
        
        # Mark as confirmed
        pending["confirmed"] = True
        logger.info(f"Command {command_id} confirmed for user {user_id}")
        
        return True, None
    
    def reject_command(self, user_id: UUID, command_id: str) -> tuple[bool, Optional[str]]:
        """
        Reject a pending voice command.
        
        Returns:
            (success: bool, error_message: Optional[str])
        """
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_commands:
            return False, "No pending commands"
        
        if command_id not in self.pending_commands[user_id_str]:
            return False, "Command not found"
        
        del self.pending_commands[user_id_str][command_id]
        logger.info(f"Command {command_id} rejected for user {user_id}")
        
        return True, None
    
    def get_pending_command(self, user_id: UUID, command_id: str) -> Optional[dict]:
        """Get a pending command for display to user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_commands:
            return None
        
        return self.pending_commands[user_id_str].get(command_id)
    
    def list_pending_commands(self, user_id: UUID) -> List[dict]:
        """List all pending commands for a user"""
        user_id_str = str(user_id)
        
        if user_id_str not in self.pending_commands:
            return []
        
        return list(self.pending_commands[user_id_str].values())
    
    def _generate_confirmation_token(self) -> str:
        """Generate a simple confirmation token"""
        import uuid
        return str(uuid.uuid4())[:8].upper()


# Global instance
voice_command_tracker = VoiceCommandTracker()


class VoiceCommandValidator:
    """Validates voice commands for safety and correctness"""
    
    # Minimum and maximum order sizes
    MIN_ORDER_SIZE = 1  # 1 share
    MAX_ORDER_SIZE = 10000  # 10k shares
    
    # Symbols that are permanently blocked
    BLOCKED_SYMBOLS = []  # Add specific symbols if needed
    
    # Symbols that require extra confirmation
    RISKY_SYMBOLS = ["TSLA", "GME", "AMC", "NVDA"]  # Highly volatile
    
    @staticmethod
    def validate_order(
        symbol: str,
        quantity: float,
        price: Optional[float] = None,
        account_balance: float = 0
    ) -> tuple[bool, Optional[str]]:
        """
        Validate a voice trade order.
        
        Args:
            symbol: Stock symbol
            quantity: Number of shares
            price: Order price (if known)
            account_balance: User's cash balance
        
        Returns:
            (is_valid: bool, error_message: Optional[str])
        """
        # Validate symbol format
        if not symbol or not isinstance(symbol, str):
            return False, "Invalid symbol"
        
        symbol = symbol.upper().strip()
        
        if len(symbol) < 1 or len(symbol) > 5:
            return False, f"Symbol must be 1-5 characters, got {len(symbol)}"
        
        if not symbol.isalpha():
            return False, "Symbol must contain only letters"
        
        # Check blocked symbols
        if symbol in VoiceCommandValidator.BLOCKED_SYMBOLS:
            return False, f"Symbol {symbol} is blocked for voice trading"
        
        # Validate quantity
        if not isinstance(quantity, (int, float)) or quantity <= 0:
            return False, "Quantity must be positive number"
        
        if quantity < VoiceCommandValidator.MIN_ORDER_SIZE:
            return False, f"Minimum order size is {VoiceCommandValidator.MIN_ORDER_SIZE} shares"
        
        if quantity > VoiceCommandValidator.MAX_ORDER_SIZE:
            return False, f"Maximum order size is {VoiceCommandValidator.MAX_ORDER_SIZE} shares"
        
        # Check if order would exceed account balance (if price known)
        if price and price > 0:
            total_cost = quantity * price
            if total_cost > account_balance * 1.5:  # Allow 50% margin
                return False, f"Insufficient buying power for ${total_cost:.2f} order (balance: ${account_balance:.2f})"
        
        return True, None
    
    @staticmethod
    def requires_extra_confirmation(symbol: str, quantity: float) -> tuple[bool, str]:
        """
        Check if an order should require extra confirmation beyond rate limiting.
        
        Returns:
            (requires_extra: bool, reason: str)
        """
        symbol = symbol.upper()
        
        # High-value orders
        if quantity > 100:
            return True, "Large order size (>100 shares)"
        
        # Risky symbols
        if symbol in VoiceCommandValidator.RISKY_SYMBOLS:
            return True, f"High-volatility symbol {symbol}"
        
        return False, ""
    
    @staticmethod
    def sanitize_voice_input(text: str) -> str:
        """
        Sanitize voice input by removing common transcription errors.
        
        Args:
            text: Raw voice transcription
        
        Returns:
            Cleaned text
        """
        # Convert to uppercase for symbol matching
        text = text.upper().strip()
        
        # Remove common transcription artifacts
        replacements = {
            "PLEASE": "",
            "THANK YOU": "",
            "THANKS": "",
            "COMMA": ",",
            "PERIOD": ".",
            "DASH": "-",
            " BUY ": " BUY ",  # Already correct
        }
        
        for artifact, replacement in replacements.items():
            text = text.replace(artifact, replacement)
        
        return text.strip()


class VoiceCommandLogger:
    """Audit logging for voice commands (PII-sensitive)"""
    
    @staticmethod
    def log_command(
        user_id: UUID,
        command_type: str,
        status: str,
        details: dict = None,
        error: Optional[str] = None
    ):
        """
        Log voice command with audit trail.
        
        Args:
            user_id: User ID
            command_type: Type of command
            status: 'pending', 'confirmed', 'executed', 'rejected', 'error'
            details: Command details (symbol, amount, etc)
            error: Error message if failed
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": str(user_id),
            "command_type": command_type,
            "status": status,
            "details": details or {},
            "error": error
        }
        
        if status == "error":
            logger.error(f"Voice command error: {log_entry}")
        elif status == "executed":
            logger.info(f"Voice command executed: {command_type} for user {user_id}")
        else:
            logger.debug(f"Voice command: {log_entry}")
