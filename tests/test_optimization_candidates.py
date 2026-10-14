"""
Unit and Regression Tests for CoReOS Optimization Candidates (A-F)
Verifies behavioral correctness, safety constraint satisfaction, and non-flapping recovery.
"""

import pytest
from src.coreos.config import CoReOSConfig, SimulationConfig
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.optimization.candidates import (
    AdaptiveCoordinationAgent,
    ProportionalRecoveryEngine,
    WorkloadAwareCPUAgent,
    WorkloadAwareIOAgent,
    CalibratedConflictEngine,
    ChampionCoReOS
)
from src.coreos.self_healing.regression_detector import RegressionEvent


def test_workload_aware_cpu_agent():
    cpu_agent = WorkloadAwareCPUAgent()
    # Light load
    state_light = {"ready_queue_length": 1, "waiting_memory_count": 0, "io_queue_length": 0, "time": 10.0}
    action = cpu_agent.propose_action(state_light)
    assert action.parameters["quantum"] == 4.0
    assert action.parameters["policy"] == "ROUND_ROBIN"

    # High load with ready queue depth
    state_heavy = {"ready_queue_length": 10, "waiting_memory_count": 5, "io_queue_length": 5, "time": 20.0}
    action = cpu_agent.propose_action(state_heavy)
    assert action.parameters["quantum"] == 8.0
    assert action.parameters["policy"] == "SRTF"


def test_workload_aware_io_agent():
    io_agent = WorkloadAwareIOAgent()
    # High I/O queue length should deploy SCAN
    state_io = {"io_queue_length": 12, "io_saturation": 75.0, "time": 15.0}
    action = io_agent.propose_action(state_io)
    assert action.parameters["io_policy"] == "SCAN"

    # Low I/O queue length should deploy FCFS
    state_low = {"io_queue_length": 1, "io_saturation": 10.0, "time": 5.0}
    action = io_agent.propose_action(state_low)
    assert action.parameters["io_policy"] == "FCFS"


def test_proportional_recovery_engine():
    recovery = ProportionalRecoveryEngine()
    state_thrash = {"memory_utilization": 96.0, "is_thrashing": True, "time": 10.0}
    event = RegressionEvent(
        timestamp=10.0,
        regression_type="THRASHING_STALL",
        severity=0.95,
        current_value=96.0,
        baseline_value=85.0,
        consecutive_violations=1,
        candidate_decisions=[]
    )
    overrides = recovery.select_corrective_action(event, current_step=10, system_state=state_thrash)
    assert overrides is not None
    assert overrides["memory_reclaim_target"] == 4096.0
    assert overrides["cpu_quantum"] == 8.0
    assert overrides["io_policy"] == "SCAN"

    # Latency spike under high memory should not clamp reclaim down to 1024
    state_latency = {"memory_utilization": 88.0, "is_thrashing": False, "time": 40.0}
    event_lat = RegressionEvent(
        timestamp=40.0,
        regression_type="LATENCY_SPIKE",
        severity=0.8,
        current_value=25.0,
        baseline_value=10.0,
        consecutive_violations=1,
        candidate_decisions=[]
    )
    overrides_lat = recovery.select_corrective_action(event_lat, current_step=40, system_state=state_latency)
    assert overrides_lat is not None
    assert overrides_lat["memory_reclaim_target"] == 2048.0
    assert overrides_lat["cpu_quantum"] == 6.0


def test_adaptive_coordination_agent():
    engine = CalibratedConflictEngine(use_ml=False)
    coord = AdaptiveCoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)
    state = {
        "memory_utilization": 90.0,
        "is_under_memory_pressure": True,
        "is_thrashing": False,
        "io_queue_length": 10,
        "io_saturation": 70.0,
        "ready_queue_length": 2,
        "waiting_memory_count": 4,
        "time": 25.0
    }
    cpu_agent = WorkloadAwareCPUAgent()
    mem_agent = SystemSimulator().memory  # dummy
    from src.coreos.agents.memory_agent import MemoryAgent
    mem_agent = MemoryAgent()
    io_agent = WorkloadAwareIOAgent()

    props = {
        "CPU_AGENT": cpu_agent.propose_action(state),
        "MEMORY_AGENT": mem_agent.propose_action(state),
        "IO_AGENT": io_agent.propose_action(state)
    }
    decision, _ = coord.coordinate(state, props)
    assert decision["io_policy"] == "SCAN"
    assert decision["memory_reclaim_target"] >= 2048.0
    assert decision["cpu_quantum"] >= 6.0


def test_champion_coreos_simulation_run():
    champion = ChampionCoReOS()
    gen = WorkloadGenerator(seed=42)
    procs = gen.generate_workload(num_processes=20, workload_type="steady_state")
    metrics = champion.run_simulation(procs, seed=42, max_steps=300)
    assert metrics["total_processes"] == 20
    assert metrics["completed_processes"] == 20
    assert metrics["completion_rate"] == 100.0
    assert metrics["thrashing_ticks"] == 0
    assert metrics["decision_overhead_ms"] < 1.0
