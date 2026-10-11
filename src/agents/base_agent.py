"""
CoReOS Agent Abstraction
Defines base agent contracts, action payloads, and telemetry interfaces.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class AgentAction:
    agent_id: str                      # "CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"
    action_type: str                   # Specific action name
    parameters: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 1.0            # Confidence in decision (0.0 to 1.0)
    expected_impact: str = "neutral"   # Qualitative or quantitative expected outcome
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "action_type": self.action_type,
            "parameters": self.parameters,
            "confidence": round(self.confidence, 3),
            "expected_impact": self.expected_impact
        }


class BaseResourceAgent(ABC):
    def __init__(self, name: str):
        self.name = name
        self.decision_history: list = []

    @abstractmethod
    def observe(self, state: Dict[str, Any]) -> None:
        """Processes current system observation snapshot."""
        pass

    @abstractmethod
    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        """Formulates candidate resource-management decision."""
        pass

    def record_decision(self, action: AgentAction, outcome: Optional[Dict[str, Any]] = None):
        self.decision_history.append({
            "action": action.to_dict(),
            "outcome": outcome
        })
