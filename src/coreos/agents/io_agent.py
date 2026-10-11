"""
CoReOS I/O Agent
Manages storage queues, disk scheduling algorithms (FCFS, SSTF, SCAN), and queue throttling.
"""

from typing import Dict, Any
from src.coreos.agents.base import BaseResourceAgent, AgentAction


class IOAgent(BaseResourceAgent):
    def __init__(self, saturation_threshold: float = 80.0):
        super().__init__(name="IO_AGENT")
        self.saturation_threshold = saturation_threshold
        self.last_observation: Dict[str, Any] = {}

    def observe(self, state: Dict[str, Any]) -> None:
        self.last_observation = state

    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        self.observe(state)
        io_q = state.get("io_queue_length", 0)
        io_sat = state.get("io_saturation", 0.0)
        is_saturated = state.get("is_io_saturated", False)
        curr_time = state.get("time", 0.0)

        if is_saturated or io_sat >= self.saturation_threshold or io_q >= 25:
            action_type = "THROTTLE_AND_ELEVATOR"
            policy = "SCAN"
            throttle = True
            reason = "Severe I/O queue congestion: Engage elevator SCAN and throttle background tasks"
            expected = "relieve_io_bottleneck"
            confidence = 0.90
        elif io_q >= 8:
            action_type = "OPTIMIZE_SEEK_TIME"
            policy = "SSTF"
            throttle = False
            reason = "Moderate I/O queue: Engage SSTF to optimize disk arm seek latency"
            expected = "minimize_head_movement"
            confidence = 0.85
        else:
            action_type = "DIRECT_DISPATCH"
            policy = "FCFS"
            throttle = False
            reason = "Low traffic: Simple FCFS zero-reorder dispatch"
            expected = "zero_reorder_latency"
            confidence = 0.95

        return AgentAction(
            agent_id=self.name,
            action_type=action_type,
            parameters={"io_policy": policy, "throttle_low_priority": throttle},
            confidence=confidence,
            reason=reason,
            expected_impact=expected,
            timestamp=curr_time
        )
