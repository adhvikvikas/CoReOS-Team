"""
CoReOS CPU Agent
Manages simulated CPU scheduling policies and dynamic quantum adjustments.
"""

from typing import Dict, Any
from src.coreos.agents.base import BaseResourceAgent, AgentAction


class CPUAgent(BaseResourceAgent):
    def __init__(self, default_policy: str = "ROUND_ROBIN", default_quantum: float = 4.0):
        super().__init__(name="CPU_AGENT")
        self.current_policy = default_policy
        self.current_quantum = default_quantum
        self.last_observation: Dict[str, Any] = {}

    def observe(self, state: Dict[str, Any]) -> None:
        self.last_observation = state

    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        self.observe(state)
        ready_q = state.get("ready_queue_length", 0)
        curr_time = state.get("time", 0.0)

        # Policy & quantum heuristic
        if ready_q > 15:
            policy = "ROUND_ROBIN"
            quantum = 8.0
            reason = "High queue depth: Lengthen quantum to amortize context switch overhead"
            expected = "amortize_context_switches"
            confidence = 0.85
        elif ready_q > 5:
            policy = "ROUND_ROBIN"
            quantum = 4.0
            reason = "Moderate queue: Standard balanced Round Robin quantum"
            expected = "balanced_latency"
            confidence = 0.90
        elif ready_q > 0:
            policy = "ROUND_ROBIN"
            quantum = 2.0
            reason = "Light load: Tight quantum for interactive responsiveness"
            expected = "minimize_response_time"
            confidence = 0.95
        else:
            policy = "ROUND_ROBIN"
            quantum = self.current_quantum
            reason = "Idle system: Maintain steady quantum"
            expected = "steady_idle"
            confidence = 0.99

        return AgentAction(
            agent_id=self.name,
            action_type="SET_CPU_SCHEDULE",
            parameters={"policy": policy, "quantum": quantum},
            confidence=confidence,
            reason=reason,
            expected_impact=expected,
            timestamp=curr_time
        )
