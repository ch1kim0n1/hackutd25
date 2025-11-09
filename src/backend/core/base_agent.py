"""
APEX Base Agent
Unified abstract base class for all agents in the system.
Provides common initialization, logging, and communication patterns.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional, TYPE_CHECKING
import logging

from .types import AgentType, AgentMessage, MessageType, MessageImportance

if TYPE_CHECKING:
    from .agent_network import AgentNetwork


class BaseAgent(ABC):
    """
    Abstract base class for all APEX agents.
    
    All specialized agents (Market, Strategy, Risk, Executor, Explainer)
    inherit from this class to ensure consistent:
    - Initialization and shutdown
    - Logging and status tracking
    - Communication patterns
    - Error handling
    - Performance monitoring
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        agent_network: 'AgentNetwork',
        api_key: str,
        model: str = "nvidia/llama-3.1-nemotron-70b-instruct",
        enable_logging: bool = True
    ):
        """
        Initialize base agent.
        
        Args:
            agent_type: Type of agent (from AgentType enum)
            agent_network: Reference to AgentNetwork for communication
            api_key: API key for LLM service (OpenRouter or Anthropic)
            model: Model identifier (full model path)
            enable_logging: Whether to print status messages
        """
        self.agent_type = agent_type
        self.name = self._get_agent_name(agent_type)
        self.emoji = self._get_agent_emoji(agent_type)
        self.agent_network = agent_network
        self.model = model
        self.logging_enabled = enable_logging
        
        # Performance tracking
        self.execution_count = 0
        self.total_execution_time = 0.0
        self.error_count = 0
        self.last_execution_time = None
        self.last_error = None
        
        # Setup logging
        self.logger = logging.getLogger(f"apex.{self.name.lower().replace(' ', '_')}")
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                f'[%(asctime)s] {self.emoji} %(name)s: %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.DEBUG if enable_logging else logging.WARNING)
        
        self.log(f"✅ Initialized with {self._get_model_display_name()}")
    
    @staticmethod
    def _get_agent_name(agent_type: AgentType) -> str:
        """Get human-readable name for agent type."""
        names = {
            AgentType.MARKET: "Market Agent",
            AgentType.STRATEGY: "Strategy Agent",
            AgentType.RISK: "Risk Agent",
            AgentType.EXECUTOR: "Executor Agent",
            AgentType.EXPLAINER: "Explainer Agent",
            AgentType.USER: "User Agent"
        }
        return names.get(agent_type, str(agent_type))
    
    @staticmethod
    def _get_agent_emoji(agent_type: AgentType) -> str:
        """Get emoji for agent type."""
        emojis = {
            AgentType.MARKET: "🔍",
            AgentType.STRATEGY: "🧠",
            AgentType.RISK: "⚠️",
            AgentType.EXECUTOR: "⚡",
            AgentType.EXPLAINER: "💬",
            AgentType.USER: "👤"
        }
        return emojis.get(agent_type, "🤖")
    
    def _get_model_display_name(self) -> str:
        """Get human-readable model name from full model identifier."""
        if '70b' in self.model.lower():
            return "NVIDIA Llama 3.1 Nemotron 70B"
        elif '49b' in self.model.lower():
            return "NVIDIA Nemotron Super 49B"
        elif '9b' in self.model.lower():
            return "NVIDIA Nemotron Nano 9B"
        elif 'claude' in self.model.lower():
            return "Claude (Anthropic)"
        else:
            return self.model
    
    def log(self, message: str, level: str = "info"):
        """
        Log a message with agent context.
        
        Args:
            message: Message to log
            level: Log level (info, warning, error, debug)
        """
        if not self.logging_enabled:
            return
        
        log_func = {
            "debug": self.logger.debug,
            "info": self.logger.info,
            "warning": self.logger.warning,
            "error": self.logger.error
        }.get(level, self.logger.info)
        
        log_func(message)
    
    async def broadcast_message(
        self,
        message: str,
        to_agent: Optional[str] = None,
        message_type: MessageType = MessageType.AGENT_COMMUNICATION,
        importance: MessageImportance = MessageImportance.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Broadcast a message to other agents or all agents.
        
        Args:
            message: Message content
            to_agent: Recipient agent name (None = broadcast to all)
            message_type: Type of message
            importance: Importance level
            metadata: Additional context
        """
        await self.agent_network.broadcast_agent_communication(
            from_agent=self.name,
            to_agent=to_agent,
            message=message,
            message_type=message_type,
            importance=importance,
            metadata=metadata
        )
    
    @abstractmethod
    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize the agent.
        Must be implemented by subclasses.
        
        Returns:
            Status dict with initialization details
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the agent's primary function.
        Must be implemented by subclasses.
        
        Args:
            input_data: Input data for execution
            
        Returns:
            Execution result dictionary
        """
        pass
    
    async def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """
        Handle agent errors gracefully.
        
        Args:
            error: The exception that occurred
            context: Context about what the agent was doing
            
        Returns:
            Error response dictionary
        """
        self.error_count += 1
        self.last_error = {
            "error": str(error),
            "context": context,
            "timestamp": datetime.now().isoformat()
        }
        
        self.log(f"❌ Error in {context}: {str(error)}", level="error")
        
        await self.broadcast_message(
            f"⚠️ Error encountered: {str(error)}",
            message_type=MessageType.ALERT,
            importance=MessageImportance.HIGH,
            metadata={"context": context}
        )
        
        return {
            "status": "error",
            "error": str(error),
            "agent": self.name,
            "timestamp": datetime.now().isoformat()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get agent status and performance metrics.
        
        Returns:
            Status dictionary with execution statistics
        """
        avg_time = (
            self.total_execution_time / self.execution_count 
            if self.execution_count > 0 
            else 0
        )
        
        return {
            "agent": self.name,
            "type": self.agent_type.value,
            "model": self._get_model_display_name(),
            "status": "healthy" if self.error_count == 0 else "degraded",
            "execution_count": self.execution_count,
            "error_count": self.error_count,
            "average_execution_time": avg_time,
            "last_execution_time": self.last_execution_time,
            "last_error": self.last_error
        }
    
    async def shutdown(self) -> None:
        """
        Gracefully shutdown the agent.
        Override in subclasses if needed.
        """
        self.log(f"🛑 Shutting down {self.name}")
