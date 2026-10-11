"""
Unit Tests for CoReOS Resource Agents
Tests CPUAgent, MemoryAgent, IOAgent, and structured AgentAction proposals.
"""

import pytest
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent


def test_cpu_agent_proposals():
    agent = CPUAgent()
    
    # High queue
    act_high = agent.propose_action({"ready_queue_length": 20, "time": 10.0})
    assert act_high.parameters["quantum"] == 8.0

    # Low queue
    act_low = agent.propose_action({"ready_queue_length": 2, "time": 15.0})
    assert act_low.parameters["quantum"] == 2.0

    assert act_high.agent_id == "CPU_AGENT"
    assert "quantum" in act_high.parameters


def test_memory_agent_proposals():
    agent = MemoryAgent(pressure_threshold=85.0)

    # Thrashing state
    act_thrash = agent.propose_action({"memory_utilization": 95.0, "is_thrashing": True, "time": 5.0})
    assert act_thrash.action_type == "EMERGENCY_RECLAIM"
    assert act_thrash.parameters["target_free_mb"] >= 4096.0

    # Healthy state
    act_healthy = agent.propose_action({"memory_utilization": 50.0, "is_thrashing": False, "time": 6.0})
    assert act_healthy.action_type == "MONITOR_HEALTHY"
    assert act_healthy.parameters["target_free_mb"] == 0.0


def test_io_agent_proposals():
    agent = IOAgent(saturation_threshold=80.0)

    # Saturated state
    act_sat = agent.propose_action({"io_saturation": 90.0, "io_queue_length": 30, "time": 1.0})
    assert act_sat.parameters["io_policy"] == "SCAN"
    assert act_sat.parameters["throttle_low_priority"] is True

    # Idle state
    act_idle = agent.propose_action({"io_saturation": 10.0, "io_queue_length": 2, "time": 2.0})
    assert act_idle.parameters["io_policy"] == "FCFS"
