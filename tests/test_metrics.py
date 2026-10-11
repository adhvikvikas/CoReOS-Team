"""
Unit Tests for CoReOS Metrics
Tests Jain's Fairness Index edge cases and simulation summary calculations.
"""

import pytest
from src.coreos.simulation.metrics import compute_jains_fairness_index, compute_simulation_metrics
from src.coreos.simulation.process import SimulatedProcess


def test_jains_fairness_index():
    # Empty list
    assert compute_jains_fairness_index([]) == 1.0

    # Perfectly equal allocation
    assert abs(compute_jains_fairness_index([10.0, 10.0, 10.0, 10.0]) - 1.0) < 1e-4

    # Skewed allocation (1 person gets all work, others 0)
    skewed = compute_jains_fairness_index([100.0, 0.0001, 0.0001, 0.0001])
    assert 0.20 <= skewed <= 0.30


def test_simulation_summary_metrics_edge_cases():
    # Empty workload
    m_empty = compute_simulation_metrics([], [])
    assert m_empty["total_processes"] == 0
    assert m_empty["completed_processes"] == 0
    assert m_empty["unfinished_processes"] == 0
    assert m_empty["completion_rate"] == 0.0
    assert m_empty["throughput"] == 0.0
    assert m_empty["avg_turnaround_time"] == 0.0

    # Populated mock process
    p = SimulatedProcess(1, "p1", 0.0, 10.0, 100.0)
    p.start_time = 0.0
    p.completion_time = 12.0
    p.total_waiting_time = 2.0
    history = [{"cpu_utilization": 50.0, "memory_utilization": 60.0, "io_saturation": 10.0, "time": 12.0, "is_thrashing": False}]

    m = compute_simulation_metrics([p], history)
    assert m["total_processes"] == 1
    assert m["completed_processes"] == 1
    assert m["unfinished_processes"] == 0
    assert m["completion_rate"] == 100.0
    assert m["avg_turnaround_time"] == 12.0
    assert m["avg_waiting_time"] == 2.0
    assert m["avg_response_time"] == 0.0


def test_metrics_all_processes_finish():
    """Workload where all admitted jobs finish within the horizon."""
    procs = []
    for i in range(1, 5):
        p = SimulatedProcess(pid=i, name=f"p{i}", arrival_time=0.0, cpu_burst_time=10.0, memory_demand_mb=128.0)
        p.start_time = float(i)
        p.completion_time = float(i * 10)
        p.total_waiting_time = float(i * 2)
        procs.append(p)

    history = [{"time": 40.0, "cpu_utilization": 75.0, "memory_utilization": 50.0, "io_saturation": 20.0}]
    m = compute_simulation_metrics(procs, history, total_processes=4)

    assert m["total_processes"] == 4
    assert m["completed_processes"] == 4
    assert m["unfinished_processes"] == 0
    assert m["completion_rate"] == 100.0
    # Mean of [10.0, 20.0, 30.0, 40.0] = 25.0
    assert m["avg_turnaround_time"] == 25.0
    # Mean of [2.0, 4.0, 6.0, 8.0] = 5.0
    assert m["avg_waiting_time"] == 5.0
    # Mean of [1.0, 2.0, 3.0, 4.0] = 2.5
    assert m["avg_response_time"] == 2.5
    assert m["throughput"] == 0.1  # 4 / 40.0


def test_metrics_partial_completion_and_survivorship_transparency():
    """
    Workload where only some admitted jobs finish.
    Verifies that unfinished jobs are NOT silently averaged into turnaround times,
    and completion metrics expose the incomplete workload.
    """
    completed = []
    for i in range(1, 4):
        p = SimulatedProcess(pid=i, name=f"p{i}", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=128.0)
        p.start_time = float(i)
        p.completion_time = float(10 + i * 2)  # 12, 14, 16
        p.total_waiting_time = float(i)
        completed.append(p)

    history = [{"time": 300.0, "cpu_utilization": 95.0, "memory_utilization": 90.0, "io_saturation": 40.0}]
    # Total admitted processes is 10, but only 3 completed
    m = compute_simulation_metrics(completed, history, total_processes=10)

    assert m["total_processes"] == 10
    assert m["completed_processes"] == 3
    assert m["unfinished_processes"] == 7
    assert m["completion_rate"] == 30.0
    # Average turnaround strictly reflects completed processes: (12 + 14 + 16) / 3 = 14.0
    assert m["avg_turnaround_time"] == 14.0
    assert m["avg_waiting_time"] == 2.0
    # Throughput accounts for 3 completed over 300 units = 0.01
    assert m["throughput"] == 0.01


def test_metrics_zero_processes_finish():
    """Workload where no jobs finish within the evaluation horizon."""
    history = [{"time": 300.0, "cpu_utilization": 100.0, "memory_utilization": 98.0, "io_saturation": 80.0, "is_thrashing": True}]
    m = compute_simulation_metrics([], history, total_processes=8)

    assert m["total_processes"] == 8
    assert m["completed_processes"] == 0
    assert m["unfinished_processes"] == 8
    assert m["completion_rate"] == 0.0
    assert m["avg_turnaround_time"] == 0.0
    assert m["p95_turnaround_time"] == 0.0
    assert m["avg_waiting_time"] == 0.0
    assert m["avg_response_time"] == 0.0
    assert m["throughput"] == 0.0
    assert m["jains_fairness_index"] == 1.0


def test_metrics_empty_workload_safety():
    """Empty workload where total_processes is 0 or unpopulated."""
    m_zero = compute_simulation_metrics([], [], total_processes=0)
    assert m_zero["total_processes"] == 0
    assert m_zero["completed_processes"] == 0
    assert m_zero["unfinished_processes"] == 0
    assert m_zero["completion_rate"] == 0.0

    m_none = compute_simulation_metrics([], [], total_processes=None)
    assert m_none["total_processes"] == 0
    assert m_none["completed_processes"] == 0
    assert m_none["unfinished_processes"] == 0
    assert m_none["completion_rate"] == 0.0


def test_benchmark_summary_metrics_parity():
    """Verifies src.evaluation.metrics.compute_simulation_benchmark_summary parity."""
    from src.evaluation.metrics import compute_simulation_benchmark_summary

    # Partial completion test
    completed = [
        SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=64.0),
        SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=64.0)
    ]
    completed[0].start_time = 0.0
    completed[0].completion_time = 10.0
    completed[0].total_waiting_time = 2.0
    completed[1].start_time = 1.0
    completed[1].completion_time = 20.0
    completed[1].total_waiting_time = 4.0

    history = [{"time": 50.0}]
    summary = compute_simulation_benchmark_summary(completed, history, total_processes=5)

    assert summary["total_processes"] == 5
    assert summary["completed_processes"] == 2
    assert summary["unfinished_processes"] == 3
    assert summary["completion_rate"] == 40.0
    assert summary["avg_turnaround_time"] == 15.0
    assert summary["avg_waiting_time"] == 3.0
    assert summary["throughput"] == 0.04


def test_simulator_runtime_completion_tracking():
    """Verifies SystemSimulator tracks total admitted processes and calculates completion rate."""
    from src.coreos.simulation.environment import SystemSimulator

    sim = SystemSimulator()
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=2.0, memory_demand_mb=64.0)
    p2 = SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=2.0, memory_demand_mb=64.0)
    p3 = SimulatedProcess(pid=3, name="p3", arrival_time=0.0, cpu_burst_time=200.0, memory_demand_mb=64.0)

    sim.reset([p1, p2, p3])
    assert sim.total_processes == 3

    # Step for 10 units: p1 and p2 should finish, p3 remains running/ready
    for _ in range(10):
        sim.step(dt=1.0)

    state = sim.get_system_state()
    assert state["total_processes"] == 3
    assert state["completed_processes_count"] == 2
    assert state["unfinished_processes_count"] == 1
    assert state["completion_rate"] == 66.67

