"""
CoReOS Base Agent Interface
Defines the contract for resource agents: observing state, proposing actions, and structured telemetry.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


@dataclass
class AgentAction:
    agent_id: str                      # "CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"
    action_type: str                   # Specific action name
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0            # Confidence in proposal (0.0 to 1.0)
    reason: str = "nominal"            # Human-readable justification
    expected_impact: str = "neutral"   # Expected direction of outcome
    timestamp: float = 0.0             # Simulation clock tick

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "confidence": round(self.confidence, 3),
            "reason": self.reason,
            "expected_impact": self.expected_impact,
            "timestamp": round(self.timestamp, 2)
        }


class BaseResourceAgent(ABC):
    """
    Shared Base Resource Agent Interface.
    Agents cannot directly mutate simulator state; all proposals must be
    submitted through the central Coordination Agent for validation.
    """

    def __init__(self, name: str):
        self.name = name
        self.decision_history: List[Dict[str, Any]] = []

    @abstractmethod
    def observe(self, state: Dict[str, Any]) -> None:
        """Processes current system telemetry snapshot."""
        pass

    @abstractmethod
    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        """Formulates candidate resource-management proposal."""
        pass

    def record_decision(self, action: AgentAction, outcome: Optional[Dict[str, Any]] = None):
        self.decision_history.append({
            "action": action.to_dict(),
            "outcome": outcome
        })

    def get_decision_history(self) -> List[Dict[str, Any]]:
        return list(self.decision_history)
