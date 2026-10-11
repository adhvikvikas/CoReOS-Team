"""
CoReOS CPU Agent
Manages simulated process scheduling policies and dynamic quantum adjustments.
"""

from typing import Dict, Any
from src.agents.base_agent import BaseResourceAgent, AgentAction


class CPUAgent(BaseResourceAgent):
    def __init__(self, default_policy: str = "ROUND_ROBIN", default_quantum: float = 4.0):
        super().__init__(name="CPU_AGENT")
        self.current_policy = default_policy
        self.current_quantum = default_quantum
        self.last_observation: Dict[str, Any] = {}

    def observe(self, state: Dict[str, Any]) -> None:
        self.last_observation = state

    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        """
        Formulates candidate scheduling policy and quantum based on queue depth
        and context switch overhead.
        """
        self.observe(state)
        ready_q = state.get("ready_queue_length", 0)
        cpu_util = state.get("cpu_utilization", 0.0)
        context_switches = state.get("total_context_switches", 0)

        # Heuristic policy selection:
        # If queue is long and context switches are high, lengthen quantum to reduce thrashing
        if ready_q > 15:
            proposed_policy = "ROUND_ROBIN"
            proposed_quantum = 8.0  # Lengthen quantum to amortize switch penalty
            expected = "amortize_context_switches"
            confidence = 0.85
        elif ready_q > 5:
            proposed_policy = "ROUND_ROBIN"
            proposed_quantum = 4.0  # Standard balanced quantum
            expected = "balanced_latency"
            confidence = 0.90
        elif ready_q > 0:
            proposed_policy = "ROUND_ROBIN"
            proposed_quantum = 2.0  # Tight quantum for fast interactive response
            expected = "minimize_response_time"
            confidence = 0.95
        else:
            proposed_policy = "ROUND_ROBIN"
            proposed_quantum = self.current_quantum
            expected = "steady_idle"
            confidence = 0.99

        return AgentAction(
            agent_id=self.name,
            action_type="SET_CPU_SCHEDULE",
            parameters={
                "policy": proposed_policy,
                "quantum": proposed_quantum
            },
            confidence=confidence,
            expected_impact=expected
        )
