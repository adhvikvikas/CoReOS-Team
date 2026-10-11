"""
Automated Test Suite for CoReOS
Covers Dataset Loader, Simulation Subsystems, Agents, Conflict Prediction,
Coordination, Self-Healing, and End-to-End Baselines.
"""

import pytest
import numpy as np
from pathlib import Path
from src.data.dataset_loader import SystemMetricsDataset
from src.simulation.process import SimulatedProcess, ProcessState
from src.simulation.cpu_subsystem import CPUSubsystem
from src.simulation.memory_subsystem import MemorySubsystem
from src.simulation.io_subsystem import IOSubsystem
from src.simulation.workload_generator import WorkloadGenerator
from src.simulation.simulator import SystemSimulator
from src.agents.cpu_agent import CPUAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.io_agent import IOAgent
from src.conflict_prediction.conflict_engine import ConflictEngine
from src.coordination.coordination_agent import CoordinationAgent
from src.self_healing.regression_detector import PerformanceRegressionDetector
from src.self_healing.recovery_engine import RecoveryEngine
from src.self_healing.feedback_mechanism import FeedbackMechanism
from src.evaluation.benchmark_runner import BenchmarkRunner


def test_dataset_loader_real_csv():
    ds = SystemMetricsDataset("data/Big_data_dataset.csv")
    df = ds.load_and_validate()
    assert df.shape[0] == 10000
    assert df.shape[1] == 12
    assert "cpu_utilization" in df.columns
    assert "status" in df.columns
    
    priors = ds.get_empirical_priors()
    assert priors["cpu_utilization"]["mean"] > 0
    assert priors["anomaly_rate"] < 0.05

    metrics = ds.train_system_anomaly_baseline(test_size=0.1)
    assert metrics["roc_auc"] >= 0.90
    assert "feature_importance" in metrics


def test_process_lifecycle():
    p = SimulatedProcess(
        pid=1,
        name="test_proc",
        arrival_time=0.0,
        cpu_burst_time=10.0,
        memory_demand_mb=512.0
    )
    assert p.remaining_burst == 10.0
    assert p.state == ProcessState.NEW
    
    clone_p = p.clone()
    assert clone_p.pid == p.pid
    assert clone_p.remaining_burst == 10.0


def test_cpu_subsystem_scheduling():
    cpu = CPUSubsystem(num_cores=2, default_quantum=4.0)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=8.0, memory_demand_mb=100.0)
    p2 = SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=2.0, memory_demand_mb=100.0)
    
    cpu.enqueue_ready(p1)
    cpu.enqueue_ready(p2)
    assert cpu.ready_queue_length == 2

    # Schedule next
    assignments = cpu.schedule_next(policy="ROUND_ROBIN", current_time=0.0)
    assert len(assignments) == 2
    assert cpu.active_core_count == 2

    # Step CPU by 2 time units
    finished, yielded = cpu.step(dt=2.0, current_time=2.0)
    assert len(finished) == 1  # p2 finished
    assert finished[0].pid == 2


def test_memory_subsystem_pressure():
    mem = MemorySubsystem(total_memory_mb=1000.0, pressure_threshold=0.80)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=850.0)
    
    allocated = mem.allocate(p1)
    assert allocated is True
    assert mem.is_under_pressure is True
    assert mem.is_thrashing is False

    # Simulate touching memory without page fault
    penalty = mem.touch_process_memory(p1)
    assert penalty == 0.0

    mem.release_process(p1.pid)
    assert mem.physical_used_mb == 0.0


def test_io_subsystem_queue():
    io = IOSubsystem(num_channels=1, queue_capacity=10)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=100.0)
    
    admitted = io.enqueue_request(p1, io_time=2.0, cylinder=20)
    assert admitted is True
    assert io.queue_length == 1
    
    completed = io.step(dt=2.5, policy="FCFS")
    assert len(completed) == 1
    assert completed[0].pid == 1


def test_conflict_prediction_rules():
    engine = ConflictEngine(use_ml=False)
    state = {
        "cpu_utilization": 80.0,
        "memory_utilization": 92.0,
        "io_saturation": 30.0,
        "ready_queue_length": 10,
        "io_queue_length": 2,
        "is_thrashing": True
    }
    cpu_ag = CPUAgent()
    mem_ag = MemoryAgent()
    io_ag = IOAgent()

    # Under memory thrashing, short quantum triggers Memory-CPU conflict
    actions = {
        "CPU_AGENT": cpu_ag.propose_action(state),
        "MEMORY_AGENT": mem_ag.propose_action(state),
        "IO_AGENT": io_ag.propose_action(state)
    }
    # Force short quantum
    actions["CPU_AGENT"].parameters["quantum"] = 2.0

    pred = engine.predict_conflict(state, actions)
    assert pred.is_conflict is True
    assert pred.conflict_type == "THRASHING_CPU_COLLAPSE"


def test_coordination_agent_arbitration():
    engine = ConflictEngine(use_ml=False)
    coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)
    state = {
        "cpu_utilization": 90.0,
        "memory_utilization": 92.0,
        "io_saturation": 85.0,
        "ready_queue_length": 10,
        "io_queue_length": 10,
        "is_thrashing": True
    }
    cpu_ag = CPUAgent()
    mem_ag = MemoryAgent()
    io_ag = IOAgent()

    props = {
        "CPU_AGENT": cpu_ag.propose_action(state),
        "MEMORY_AGENT": mem_ag.propose_action(state),
        "IO_AGENT": io_ag.propose_action(state)
    }
    decision, pred = coord.coordinate(state, props)
    assert pred.is_conflict is True
    assert decision["arbitration_applied"] is True
    # Coordinated quantum lengthened to protect CPU
    assert decision["cpu_quantum"] >= 6.0


def test_self_healing_recovery():
    detector = PerformanceRegressionDetector()
    recovery = RecoveryEngine()

    state = {
        "time": 10.0,
        "throughput": 0.01,
        "avg_waiting_time": 45.0,
        "memory_utilization": 95.0,
        "is_thrashing": True
    }
    event = detector.observe_and_detect(state)
    assert event is not None
    assert event.regression_type == "THRASHING_STALL"

    overrides = recovery.select_corrective_action(event, current_step=1, system_state=state)
    assert overrides is not None
    assert overrides["memory_reclaim_target"] > 0
    assert overrides["cpu_quantum"] >= 8.0


def test_benchmark_runner_smoke():
    runner = BenchmarkRunner()
    gen = WorkloadGenerator(seed=99)
    procs = gen.generate_workload(num_processes=10, workload_type="steady_state")
    
    res_a = runner.run_baseline_a_conventional(procs)
    res_e = runner.run_baseline_e_complete_coreos(procs)
    
    assert res_a["completed_processes"] == 10
    assert res_e["completed_processes"] == 10
    assert res_a["avg_turnaround_time"] > 0
    assert res_e["avg_turnaround_time"] > 0
