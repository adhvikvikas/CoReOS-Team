"""
Unit Tests for CoReOS Simulation Engine
Tests Process lifecycle, CPU/Memory/IO subsystems, WorkloadGenerator, and Simulator.
"""

import pytest
from src.coreos.simulation.process import SimulatedProcess, ProcessState
from src.coreos.simulation.environment import SystemSimulator, CPUSubsystem, MemorySubsystem, IOSubsystem
from src.coreos.simulation.workload import WorkloadGenerator


def test_process_creation_and_cloning():
    p = SimulatedProcess(
        pid=1001,
        name="test_proc",
        arrival_time=0.0,
        cpu_burst_time=12.0,
        memory_demand_mb=512.0
    )
    assert p.remaining_burst == 12.0
    assert p.state == ProcessState.NEW

    replica = p.clone()
    assert replica.pid == p.pid
    assert replica.remaining_burst == 12.0
    assert replica.state == ProcessState.NEW


def test_cpu_subsystem_execution():
    cpu = CPUSubsystem(num_cores=2, default_quantum=4.0)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=6.0, memory_demand_mb=128.0)
    p2 = SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=2.0, memory_demand_mb=128.0)

    cpu.enqueue_ready(p1)
    cpu.enqueue_ready(p2)
    cpu.schedule_next(policy="ROUND_ROBIN", current_time=0.0)

    assert cpu.active_core_count == 2
    finished, yielded = cpu.step(dt=2.0, current_time=2.0)

    # p2 should have completed burst (2.0 dt)
    assert len(finished) == 1
    assert finished[0].pid == 2


def test_memory_subsystem_pressure_and_thrashing():
    mem = MemorySubsystem(total_memory_mb=1000.0, swap_capacity_mb=500.0, pressure_threshold=0.80)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=10.0, memory_demand_mb=850.0)

    allocated = mem.allocate(p1)
    assert allocated is True
    assert mem.is_under_pressure is True
    assert mem.is_thrashing is False

    # Simulate paging out to swap
    reclaimed = mem.reclaim_memory(target_free_mb=500.0, active_processes=[p1])
    assert reclaimed == 850.0
    assert p1.is_paged_out is True
    assert mem.swap_used_mb == 850.0

    # Touching memory triggers page fault penalty
    penalty = mem.touch_process_memory(p1)
    assert penalty > 0.0
    assert mem.total_page_faults == 1


def test_io_subsystem_elevator_scan():
    io = IOSubsystem(num_channels=1, queue_capacity=10)
    p1 = SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=64.0)
    p2 = SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=5.0, memory_demand_mb=64.0)

    io.enqueue_request(p1, io_time=2.0, cylinder=20)
    io.enqueue_request(p2, io_time=2.0, cylinder=80)
    assert io.queue_length == 2

    completed = io.step(dt=2.5, policy="SCAN")
    assert len(completed) >= 1


def test_workload_generator_reproducibility():
    gen1 = WorkloadGenerator(seed=123)
    w1 = gen1.generate_workload(num_processes=10, workload_type="steady_state")

    gen2 = WorkloadGenerator(seed=123)
    w2 = gen2.generate_workload(num_processes=10, workload_type="steady_state")

    for p1, p2 in zip(w1, w2):
        assert p1.pid == p2.pid
        assert p1.cpu_burst_time == p2.cpu_burst_time
        assert p1.memory_demand_mb == p2.memory_demand_mb


def test_simulator_end_to_end():
    sim = SystemSimulator()
    gen = WorkloadGenerator(seed=42)
    processes = gen.generate_workload(num_processes=15, workload_type="steady_state")
    sim.reset(processes)

    steps = 0
    while not sim.is_done() and steps < 200:
        sim.step(dt=1.0)
        steps += 1

    assert sim.is_done() is True
    assert len(sim.completed_processes) == 15
    state = sim.get_system_state()
    assert state["avg_turnaround_time"] > 0


def test_simulation_no_livelock_under_thrashing():
    """Verifies that thrashing applies execution slowdown rather than an infinite preemption live-lock."""
    from src.coreos.config import SimulationConfig
    config = SimulationConfig(
        total_memory_mb=1000.0,
        swap_capacity_mb=500.0,
        memory_pressure_threshold=0.80,
        cpu_cores=2
    )
    sim = SystemSimulator(config)

    # 4 processes of 400 MB each (total 1600 MB > 1000 MB physical RAM)
    procs = [
        SimulatedProcess(pid=1, name="p1", arrival_time=0.0, cpu_burst_time=6.0, memory_demand_mb=400.0),
        SimulatedProcess(pid=2, name="p2", arrival_time=0.0, cpu_burst_time=6.0, memory_demand_mb=400.0),
        SimulatedProcess(pid=3, name="p3", arrival_time=1.0, cpu_burst_time=6.0, memory_demand_mb=400.0),
        SimulatedProcess(pid=4, name="p4", arrival_time=1.0, cpu_burst_time=6.0, memory_demand_mb=400.0),
    ]
    sim.reset(procs)

    # Run for 30 steps with memory reclamation active
    for _ in range(30):
        if sim.is_done():
            break
        sim.step(dt=1.0, memory_reclaim_target=400.0)

    # Processes must make progress and complete rather than deadlocking
    assert len(sim.completed_processes) > 0
    # Context switches should remain reasonable (not thousands of empty preemption cycles)
    assert sim.cpu.total_context_switches < 100


def test_memory_pressure_process_state_transitions():
    """Verifies valid state transitions: NEW -> WAITING_MEMORY -> READY -> RUNNING -> TERMINATED."""
    from src.coreos.config import SimulationConfig
    config = SimulationConfig(total_memory_mb=1000.0, swap_capacity_mb=500.0, cpu_cores=1)
    sim = SystemSimulator(config)

    p1 = SimulatedProcess(pid=101, name="p1", arrival_time=0.0, cpu_burst_time=3.0, memory_demand_mb=800.0)
    p2 = SimulatedProcess(pid=102, name="p2", arrival_time=0.0, cpu_burst_time=3.0, memory_demand_mb=800.0)
    sim.reset([p1, p2])

    # Step 1: p1 is admitted, p2 cannot fit into RAM and must wait in WAITING_MEMORY
    sim.step(dt=1.0)
    assert p1.state == ProcessState.RUNNING or p1.state == ProcessState.READY
    assert p2.state == ProcessState.WAITING_MEMORY
    assert p2 in sim.waiting_memory_queue

    # Step until p1 completes
    while p1.state != ProcessState.TERMINATED:
        sim.step(dt=1.0)

    # With p1 finished and its memory released, p2 must be admitted to READY / RUNNING
    sim.step(dt=1.0)
    assert p2.state in {ProcessState.RUNNING, ProcessState.READY, ProcessState.TERMINATED}
    assert p2.memory_allocated_mb == 800.0


def test_eventual_completion_feasible_overcommitted_workload():
    """Verifies that an overcommitted memory workload reaches full completion without stalling."""
    from src.coreos.config import SimulationConfig
    config = SimulationConfig(total_memory_mb=1200.0, swap_capacity_mb=800.0, cpu_cores=2)
    sim = SystemSimulator(config)

    # 4 jobs demanding 500 MB each (2000 MB total > 1200 MB physical RAM)
    procs = [
        SimulatedProcess(pid=i, name=f"p_{i}", arrival_time=float(i * 2), cpu_burst_time=4.0, memory_demand_mb=500.0)
        for i in range(1, 5)
    ]
    sim.reset(procs)

    steps = 0
    while not sim.is_done() and steps < 100:
        sim.step(dt=1.0, memory_reclaim_target=500.0)
        steps += 1

    assert sim.is_done() is True
    assert len(sim.completed_processes) == 4
    for p in sim.completed_processes:
        assert p.state == ProcessState.TERMINATED
        assert p.remaining_burst <= 1e-6
