# backend/services/agent_debate_engine.py
"""
Agent Debate Engine for APEX.
Handles multi-agent deliberation, consensus voting, and conflict resolution.
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
import json
import logging


class AgentStance(Enum):
    """Possible agent stances on a decision"""
    AGREE = "agree"
    DISAGREE = "disagree"
    NEUTRAL = "neutral"
    ABSTAIN = "abstain"


class DebateRound:
    """Represents one round of agent debate"""

    def __init__(self, round_number: int, topic: str):
        self.round_number = round_number
        self.topic = topic
        self.timestamp = datetime.now().isoformat()
        self.agent_positions: Dict[str, Dict[str, Any]] = {}
        self.consensus_reached = False
        self.consensus_level = 0.0
        self.decision = None

    def add_position(self, agent_name: str, stance: AgentStance, reasoning: str, confidence: float):
        """Add an agent's position to the round"""
        self.agent_positions[agent_name] = {
            "stance": stance.value,
            "reasoning": reasoning,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat()
        }

    def calculate_consensus(self) -> Tuple[bool, float, str]:
        """
        Calculate if consensus is reached.
        
        Returns:
            (consensus_reached, consensus_level, dominant_decision)
        """
        if not self.agent_positions:
            return False, 0.0, "no_positions"

        # Weight stances by agent confidence
        stance_weights = {
            AgentStance.AGREE.value: [],
            AgentStance.DISAGREE.value: [],
            AgentStance.NEUTRAL.value: [],
        }

        total_weight = 0.0
        for agent_name, position in self.agent_positions.items():
            stance = position["stance"]
            confidence = position["confidence"]
            
            if stance in stance_weights:
                stance_weights[stance].append(confidence)
                total_weight += confidence

        if total_weight == 0:
            return False, 0.0, "no_valid_positions"

        # Normalize and find dominant stance
        agree_score = sum(stance_weights[AgentStance.AGREE.value]) / total_weight if total_weight > 0 else 0
        disagree_score = sum(stance_weights[AgentStance.DISAGREE.value]) / total_weight if total_weight > 0 else 0

        # Consensus threshold: 66% agreement
        consensus_threshold = 0.66
        max_score = max(agree_score, disagree_score)
        consensus_reached = max_score >= consensus_threshold

        # Dominant decision
        if agree_score > disagree_score:
            dominant = "approve"
        elif disagree_score > agree_score:
            dominant = "reject"
        else:
            dominant = "tie"

        return consensus_reached, max_score, dominant


class AgentDebateEngine:
    """
    Manages multi-agent debates and consensus building.
    Handles round-robin discussions, voting, and conflict resolution.
    """

    def __init__(self, agent_names: List[str], max_rounds: int = 3):
        """
        Initialize debate engine.
        
        Args:
            agent_names: List of agent names participating in debate
            max_rounds: Maximum number of debate rounds
        """
        self.agent_names = agent_names
        self.max_rounds = max_rounds
        self.rounds: List[DebateRound] = []
        self.current_round = 0
        self.logger = logging.getLogger(__name__)

    def start_debate(self, topic: str) -> DebateRound:
        """Start a new debate round"""
        self.current_round += 1
        if self.current_round > self.max_rounds:
            self.logger.warning(f"Max debate rounds ({self.max_rounds}) reached")
            return None

        round_obj = DebateRound(self.current_round, topic)
        self.rounds.append(round_obj)
        self.logger.info(f"Debate round {self.current_round} started: {topic}")
        return round_obj

    def record_position(
        self,
        agent_name: str,
        stance: AgentStance,
        reasoning: str,
        confidence: float = 0.8
    ) -> bool:
        """Record an agent's position in current round"""
        if not self.rounds:
            self.logger.error("No active debate round")
            return False

        current = self.rounds[-1]
        if agent_name not in self.agent_names:
            self.logger.warning(f"Unknown agent: {agent_name}")
            return False

        current.add_position(agent_name, stance, reasoning, confidence)
        self.logger.info(f"{agent_name}: {stance.value} (confidence: {confidence})")
        return True

    def check_consensus(self) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if consensus is reached in current round.
        
        Returns:
            (consensus_reached, consensus_data)
        """
        if not self.rounds:
            return False, {}

        current = self.rounds[-1]
        reached, level, decision = current.calculate_consensus()

        consensus_data = {
            "round": self.current_round,
            "topic": current.topic,
            "consensus_reached": reached,
            "consensus_level": level,
            "decision": decision,
            "positions": current.agent_positions,
            "timestamp": current.timestamp
        }

        if reached:
            current.consensus_reached = True
            current.decision = decision
            self.logger.info(f"✅ Consensus reached: {decision} ({level:.1%})")
        else:
            self.logger.info(f"❌ No consensus yet ({level:.1%})")

        return reached, consensus_data

    def resolve_conflict(
        self,
        conflict_agents: List[str],
        tiebreaker_strategy: str = "confidence"
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve conflicts when agents disagree.
        
        Strategies:
        - "confidence": Trust agent with highest confidence
        - "hierarchy": Use predefined hierarchy (Risk > Strategy > Market)
        - "majority": Vote-based decision
        - "risk_averse": Choose risk-mitigating option
        
        Returns:
            (decision, resolution_details)
        """
        if not self.rounds:
            return "error", {"reason": "no_debate_round"}

        current = self.rounds[-1]
        positions = current.agent_positions

        # Get positions of conflicting agents
        conflict_positions = {
            agent: positions[agent] for agent in conflict_agents if agent in positions
        }

        if not conflict_positions:
            return "error", {"reason": "no_positions_found"}

        resolution_details = {
            "strategy": tiebreaker_strategy,
            "conflicting_positions": conflict_positions,
            "timestamp": datetime.now().isoformat()
        }

        # Apply resolution strategy
        if tiebreaker_strategy == "confidence":
            winner = max(
                conflict_positions.items(),
                key=lambda x: x[1]["confidence"]
            )
            decision = winner[1]["stance"]
            resolution_details["winner"] = winner[0]
            resolution_details["reason"] = f"Highest confidence: {winner[1]['confidence']}"

        elif tiebreaker_strategy == "hierarchy":
            # Risk > Strategy > Market > Explainer
            hierarchy = {
                "risk_agent": 3,
                "strategy_agent": 2,
                "market_agent": 1,
                "explainer_agent": 0
            }
            winner = max(
                conflict_positions.items(),
                key=lambda x: hierarchy.get(x[0], -1)
            )
            decision = winner[1]["stance"]
            resolution_details["winner"] = winner[0]
            resolution_details["reason"] = f"Hierarchy-based decision"

        elif tiebreaker_strategy == "risk_averse":
            # Prefer "disagree" (conservative)
            disagree_agents = [
                (agent, pos) for agent, pos in conflict_positions.items()
                if pos["stance"] == "disagree"
            ]
            if disagree_agents:
                decision = "disagree"
                resolution_details["reason"] = "Risk-averse: chose conservative option"
            else:
                decision = "agree"
                resolution_details["reason"] = "Risk-averse: no conservative option"

        else:  # majority
            stances = {}
            for agent, pos in conflict_positions.items():
                stance = pos["stance"]
                stances[stance] = stances.get(stance, 0) + 1

            decision = max(stances, key=stances.get)
            resolution_details["votes"] = stances
            resolution_details["reason"] = f"Majority vote for {decision}"

        self.logger.info(f"Conflict resolved: {decision} ({tiebreaker_strategy})")
        return decision, resolution_details

    def get_debate_transcript(self) -> List[Dict[str, Any]]:
        """Get full transcript of all debate rounds"""
        transcript = []
        for round_obj in self.rounds:
            transcript.append({
                "round": round_obj.round_number,
                "topic": round_obj.topic,
                "timestamp": round_obj.timestamp,
                "consensus_reached": round_obj.consensus_reached,
                "decision": round_obj.decision,
                "positions": round_obj.agent_positions
            })
        return transcript

    def finalize_debate(self) -> Dict[str, Any]:
        """
        Finalize debate and return final decision.
        
        Returns:
            Final decision summary
        """
        if not self.rounds:
            return {"status": "error", "reason": "no_debate_started"}

        # Get final round consensus
        final_round = self.rounds[-1]
        reached, level, decision = final_round.calculate_consensus()

        summary = {
            "total_rounds": self.current_round,
            "final_decision": decision,
            "consensus_reached": reached,
            "consensus_level": level,
            "timestamp": datetime.now().isoformat(),
            "transcript": self.get_debate_transcript()
        }

        self.logger.info(f"Debate finalized: {decision} (consensus: {level:.1%})")
        return summary

    def export_to_json(self) -> str:
        """Export debate history to JSON"""
        return json.dumps(self.get_debate_transcript(), indent=2)
