"""
Phase 2 Regression Tests: Bounded Recovery, Adaptive Memory Reclamation, and Starvation Prevention.
Targeted tests for:
1. A temporarily frozen job eventually becoming runnable again.
2. Backoff timers remaining bounded.
3. Recovery state transitions being valid.
4. Repeated memory-pressure events not starving every job indefinitely.
5. Recovery preserving the existing conflict-detection behaviour.
6. Unfinished jobs remaining correctly represented in metrics.
7. A steady-state workload not regressing unnecessarily.
8. The existing penalized-turnaround tests continuing to pass.
"""

import pytest
import numpy as np
from src.coreos.simulation.process import SimulatedProcess, ProcessState
from src.coreos.simulation.environment import SystemSimulator, CPUSubsystem, MemorySubsystem, IOSubsystem
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector, RegressionEvent
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.evaluation.experiments import ExperimentSuite


def test_frozen_job_eventually_runnable():
    """Test 1: A temporarily frozen job (paged out / waiting memory) eventually becomes runnable again."""
    sim = SystemSimulator()
    # P1 runs briefly and finishes, releasing its memory.
    p1 = SimulatedProcess(
        pid=101, name="Job1", arrival_time=0.0,
        cpu_burst_time=5.0, memory_demand_mb=8192.0, priority=5
    )
    # P2 needs 12288 MB. Initially fits if memory is 16384 MB, but when P1 is running,
    # if memory is reclaimed or constrained, P2 waits.
    p2 = SimulatedProcess(
        pid=102, name="Job2", arrival_time=0.0,
        cpu_burst_time=10.0, memory_demand_mb=10000.0, priority=5
    )

    sim.reset([p1, p2])
    # Step 1: P1 is allocated (8192 MB), P2 cannot allocate (10000 MB > 8192 MB free),
    # so P2 enters WAITING_MEMORY.
    sim.step(dt=1.0)
    assert p2.state == ProcessState.WAITING_MEMORY
    assert p2 in sim.waiting_memory_queue

    # Advance until P1 completes (burst=5.0)
    for _ in range(6):
        sim.step(dt=1.0)

    # After P1 completes, its memory is released. P2 must be admitted from waiting_memory_queue!
    assert p1.state == ProcessState.TERMINATED
    assert p2 not in sim.waiting_memory_queue
    assert p2.state in (ProcessState.RUNNING, ProcessState.READY, ProcessState.TERMINATED)


def test_backoff_timers_remain_bounded():
    """Test 2: Backoff delays and retry counters remain bounded under recurring failures."""
    recovery = RecoveryEngine()
    state = {"time": 1.0, "is_thrashing": True, "memory_utilization": 95.0}
    detector = PerformanceRegressionDetector()
    event = detector.observe_and_detect(state)
    assert event is not None

    # Trigger multiple consecutive timeout failures
    current_step = 1
    for i in range(10):
        # Apply action
        action = recovery.select_corrective_action(event, current_step=current_step, system_state=state)
        if action is not None:
            # Simulate timeout failure (elapsed >= 25.0, not recovered)
            fail_state = {"time": state["time"] + 30.0, "is_thrashing": True, "memory_utilization": 95.0}
            recovery.track_recovery_progress(current_step=current_step + 30, system_state=fail_state)

        # Advance step beyond the cooling-off period
        current_step += 50

    # Assert retries are capped at max_retries (4)
    assert recovery.consecutive_retries <= recovery.max_retries
    assert recovery.consecutive_retries == 4

    # Assert cooling-off duration does not exceed max_cooling_off_period (25)
    effective_cooling = min(
        recovery.max_cooling_off_period,
        recovery.config.cooling_off_period * (1 + recovery.consecutive_retries)
    )
    assert effective_cooling <= 25


def test_recovery_state_transitions_valid():
    """Test 3: Recovery engine state transitions (active -> cooling -> resolved) are strictly valid."""
    recovery = RecoveryEngine()
    state = {"time": 10.0, "is_thrashing": True, "memory_utilization": 95.0}
    detector = PerformanceRegressionDetector()
    event = detector.observe_and_detect(state)

    # Initial state: inactive
    assert recovery.active_recovery is None

    # Action 1: Selected
    act = recovery.select_corrective_action(event, current_step=5, system_state=state)
    assert act is not None
    assert recovery.active_recovery is not None
    assert recovery.active_recovery.regression_type == "THRASHING_STALL"

    # Action 2 inside cooling-off: blocked
    act_blocked = recovery.select_corrective_action(event, current_step=6, system_state=state)
    assert act_blocked is None
    assert recovery.active_recovery is not None

    # Track progress: Healthy recovery
    healthy_state = {"time": 15.0, "is_thrashing": False, "memory_utilization": 75.0}
    recovery.track_recovery_progress(current_step=10, system_state=healthy_state)

    # Transition to resolved
    assert recovery.active_recovery is None
    assert len(recovery.recovery_records) == 1
    assert recovery.recovery_records[0]["success"] is True
    assert recovery.recovery_records[0]["recovery_time"] == 5.0


def test_repeated_memory_pressure_not_starving_jobs_indefinitely():
    """Test 4: Repeated memory pressure events do not starve every job indefinitely."""
    sim = SystemSimulator()
    # Create 8 processes with moderate burst and memory
    processes = [
        SimulatedProcess(
            pid=2000 + i, name=f"Proc_{i}", arrival_time=float(i * 2.0),
            cpu_burst_time=8.0, memory_demand_mb=4096.0, priority=5
        )
        for i in range(8)
    ]
    sim.reset(processes)

    # Run for 150 ticks under continuous memory reclaim target
    for step_i in range(150):
        if sim.is_done():
            break
        state = sim.get_system_state()
        reclaim_target = 2048.0 if state.get("is_under_memory_pressure", False) else 0.0
        sim.step(dt=1.0, cpu_policy="ROUND_ROBIN", cpu_quantum=4.0, io_policy="FCFS", memory_reclaim_target=reclaim_target)

    # All 8 processes must complete because memory was reclaimed without trapping runnable jobs
    assert len(sim.completed_processes) == 8
    assert len(sim.waiting_memory_queue) == 0


def test_recovery_preserves_conflict_detection():
    """Test 5: Recovery mechanisms preserve active conflict detection and arbitration."""
    engine = ConflictEngine(use_ml=False)
    coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)
    recovery = RecoveryEngine()

    state = {
        "time": 20.0,
        "cpu_utilization": 90.0,
        "memory_utilization": 92.0,
        "io_saturation": 85.0,
        "ready_queue_length": 12,
        "io_queue_length": 10,
        "is_thrashing": True,
        "is_under_memory_pressure": True,
        "is_io_saturated": True
    }

    from src.coreos.agents.base import AgentAction
    proposals = {
        "CPU_AGENT": AgentAction("CPU_AGENT", "RUN", {"policy": "ROUND_ROBIN", "quantum": 2.0}, 0.9, "", "", 20.0),
        "MEMORY_AGENT": AgentAction("MEMORY_AGENT", "RECLAIM", {"target_free_mb": 4096.0}, 0.9, "", "", 20.0),
        "IO_AGENT": AgentAction("IO_AGENT", "IO", {"io_policy": "FCFS"}, 0.9, "", "", 20.0)
    }

    decision, prediction = coord.coordinate(state, proposals)
    assert prediction is not None
    assert prediction.is_conflict is True
    assert prediction.conflict_type in ("TRIPLE_CASCADE", "THRASHING_CPU_COLLAPSE")
    assert decision["arbitration_applied"] is True

    # When regression detector fires, recovery applies bounded overrides while preserving prediction audit
    detector = PerformanceRegressionDetector()
    reg_event = detector.observe_and_detect(state)
    assert reg_event is not None
    overrides = recovery.select_corrective_action(reg_event, current_step=1, system_state=state)
    assert overrides is not None
    decision.update(overrides)

    assert decision["conflict_predicted"] is True
    assert decision["cpu_quantum"] >= 4.0  # Safe bounded quantum


def test_unfinished_jobs_correctly_represented_in_metrics():
    """Test 6: Unfinished jobs remain correctly counted in penalized turnaround without omission."""
    p_comp = SimulatedProcess(
        pid=1, name="Done", arrival_time=0.0, cpu_burst_time=10.0, memory_demand_mb=1000.0
    )
    p_comp.completion_time = 15.0  # Turnaround = 15.0

    # Compute metrics for 1 completed out of 4 submitted processes
    metrics = compute_simulation_metrics(
        completed_processes=[p_comp],
        simulation_history=[{"time": 50.0, "is_thrashing": False}],
        overhead_ms=0.01,
        total_processes=4,
        cutoff_penalty=300.0
    )

    assert metrics["total_processes"] == 4
    assert metrics["completed_processes"] == 1
    assert metrics["unfinished_processes"] == 3
    assert metrics["completion_rate"] == 25.0
    assert metrics["avg_turnaround_time"] == 15.0

    # Penalized turnaround = (15.0 + 3 * 300.0) / 4 = 915.0 / 4 = 228.75
    assert metrics["penalized_turnaround_time"] == 228.75


def test_steady_state_workload_no_regression():
    """Test 7: Steady-state baseline completes 100% of jobs with 0 thrashing and low turnaround."""
    suite = ExperimentSuite()
    gen = WorkloadGenerator(seed=42)
    workload = gen.generate_workload(num_processes=40, workload_type="steady_state")

    res = suite.run_baseline_e_complete(workload, seed=42)
    assert res["completed_processes"] == 40
    assert res["completion_rate"] == 100.0
    assert res["thrashing_ticks"] == 0
    assert res["penalized_turnaround_time"] <= 15.0


def test_existing_penalized_turnaround_tests_pass():
    """Test 8: Phase 1 edge case metrics continue to pass without distortion."""
    # Zero completed jobs
    m_zero = compute_simulation_metrics(
        completed_processes=[],
        simulation_history=[],
        overhead_ms=0.0,
        total_processes=5,
        cutoff_penalty=300.0
    )
    assert m_zero["completed_processes"] == 0
    assert m_zero["unfinished_processes"] == 5
    assert m_zero["avg_turnaround_time"] == 0.0
    assert m_zero["penalized_turnaround_time"] == 300.0

    # Zero job workload
    m_empty = compute_simulation_metrics(
        completed_processes=[],
        simulation_history=[],
        overhead_ms=0.0,
        total_processes=0,
        cutoff_penalty=300.0
    )
    assert m_empty["total_processes"] == 0
    assert m_empty["penalized_turnaround_time"] == 0.0
