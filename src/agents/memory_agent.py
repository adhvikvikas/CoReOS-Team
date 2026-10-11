"""
CoReOS Memory Agent
Manages memory pressure, capacity limits, page allocation limits, and reclamation.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseResourceAgent, AgentAction


class MemoryAgent(BaseResourceAgent):
    def __init__(self, pressure_threshold: float = 85.0):
        super().__init__(name="MEMORY_AGENT")
        self.pressure_threshold = pressure_threshold
        self.last_observation: Dict[str, Any] = {}

    def observe(self, state: Dict[str, Any]) -> None:
        self.last_observation = state

    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        """
        Formulates candidate memory management actions based on RAM utilization,
        page fault frequency, and thrashing indicators.
        """
        self.observe(state)
        mem_util = state.get("memory_utilization", 0.0)
        is_pressure = state.get("is_under_memory_pressure", False)
        is_thrashing = state.get("is_thrashing", False)
        page_faults = state.get("total_page_faults", 0)

        if is_thrashing or mem_util >= 92.0:
            # Critical thrashing: aggressive reclamation required
            action_type = "EMERGENCY_RECLAIM"
            target_free_mb = 4096.0  # Free up 4 GB
            expected = "arrest_thrashing_cascade"
            confidence = 0.95
        elif is_pressure or mem_util >= self.pressure_threshold:
            # Preemptive reclamation to maintain safe headroom
            action_type = "PREEMPTIVE_RECLAIM"
            target_free_mb = 2048.0  # Free up 2 GB
            expected = "prevent_memory_saturation"
            confidence = 0.85
        elif mem_util >= 70.0:
            action_type = "CONSERVATIVE_HEADROOM"
            target_free_mb = 1024.0
            expected = "maintain_safe_margin"
            confidence = 0.90
        else:
            action_type = "MONITOR_HEALTHY"
            target_free_mb = 0.0
            expected = "adequate_headroom"
            confidence = 0.99

        return AgentAction(
            agent_id=self.name,
            action_type=action_type,
            parameters={
                "target_free_mb": target_free_mb,
                "reclaim_priority_cutoff": 4
            },
            confidence=confidence,
            expected_impact=expected
        )
