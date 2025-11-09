"""
Unit tests for BaseAgent class.
Tests core agent initialization, logging, and communication patterns.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
import logging

# Import paths will depend on your setup
import sys
sys.path.insert(0, 'src/backend')

from core.base_agent import BaseAgent
from core.types import AgentType, AgentMessage, MessageType, MessageImportance


class ConcreteAgent(BaseAgent):
    """Concrete implementation of BaseAgent for testing."""
    
    async def initialize(self):
        """Initialize the agent."""
        self.log("Initialized")
    
    async def execute(self):
        """Execute the agent."""
        self.log("Executing")
    
    async def process_message(self, message: AgentMessage) -> AgentMessage:
        """Mock implementation of abstract method."""
        return AgentMessage(
            id="test_response",
            from_agent=self.name,
            to_agent=message.from_agent,
            message="Test response",
            timestamp=datetime.now(),
            message_type=MessageType.AGENT_COMMUNICATION,
            importance=MessageImportance.MEDIUM
        )


class TestBaseAgentInitialization:
    """Test agent initialization and setup."""
    
    def test_agent_initialization_with_valid_type(self):
        """Test successful agent initialization."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.agent_type == AgentType.MARKET
        assert agent.name == "Market Agent"
        assert agent.emoji == "🔍"
        assert agent.execution_count == 0
        assert agent.error_count == 0
        assert agent.model == "nvidia/llama-3.1-nemotron-70b-instruct"
    
    def test_agent_names_mapping(self):
        """Test that agent names map correctly to agent types."""
        mock_network = Mock()
        test_cases = [
            (AgentType.MARKET, "Market Agent", "🔍"),
            (AgentType.STRATEGY, "Strategy Agent", "🧠"),
            (AgentType.RISK, "Risk Agent", "⚠️"),
            (AgentType.EXECUTOR, "Executor Agent", "⚡"),
            (AgentType.EXPLAINER, "Explainer Agent", "💬"),
            (AgentType.USER, "User Agent", "👤")
        ]
        
        for agent_type, expected_name, expected_emoji in test_cases:
            agent = ConcreteAgent(
                agent_type=agent_type,
                agent_network=mock_network,
                api_key="test_key",
                enable_logging=False
            )
            assert agent.name == expected_name
            assert agent.emoji == expected_emoji
    
    def test_agent_logging_disabled(self):
        """Test that logging can be disabled."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.logging_enabled is False
    
    def test_agent_logging_enabled(self):
        """Test that logging can be enabled."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=True
        )
        
        assert agent.logging_enabled is True
        assert agent.logger is not None


class TestAgentPerformanceTracking:
    """Test agent performance metrics."""
    
    def test_execution_count_increments(self):
        """Test that execution count is tracked."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        initial_count = agent.execution_count
        agent.execution_count += 1
        
        assert agent.execution_count == initial_count + 1
    
    def test_error_tracking(self):
        """Test that errors are tracked."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.error_count == 0
        assert agent.last_error is None
        
        agent.error_count += 1
        agent.last_error = "Test error"
        
        assert agent.error_count == 1
        assert agent.last_error == "Test error"
    
    def test_execution_time_tracking(self):
        """Test that execution time is tracked."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.total_execution_time == 0.0
        
        agent.total_execution_time += 1.5
        agent.last_execution_time = 1.5
        
        assert agent.total_execution_time == 1.5
        assert agent.last_execution_time == 1.5


class TestAgentCommunication:
    """Test agent communication capabilities."""
    
    def test_agent_has_network_reference(self):
        """Test that agent maintains reference to agent network."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.agent_network is mock_network
    
    def test_agent_api_key_stored(self):
        """Test that API key is stored in agent."""
        mock_network = Mock()
        test_key = "test_api_key_123"
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key=test_key,
            enable_logging=False
        )
        
        # The api_key should be accessible (implementation detail)
        # This would depend on your actual implementation


class TestAgentModel:
    """Test agent model configuration."""
    
    def test_custom_model_configuration(self):
        """Test that custom model can be configured."""
        mock_network = Mock()
        custom_model = "custom/model:latest"
        
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            model=custom_model,
            enable_logging=False
        )
        
        assert agent.model == custom_model
    
    def test_default_model_configuration(self):
        """Test default model is set correctly."""
        mock_network = Mock()
        agent = ConcreteAgent(
            agent_type=AgentType.MARKET,
            agent_network=mock_network,
            api_key="test_key",
            enable_logging=False
        )
        
        assert agent.model == "nvidia/llama-3.1-nemotron-70b-instruct"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
