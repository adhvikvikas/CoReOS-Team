"""
Tests for Priority 3: RL Horizon Standardization & Reproducible Seed Strategy
Verifies:
1. RL environment evaluation horizon (300 steps) vs training horizon (150 steps).
2. Termination at horizon and early termination on workload completion.
3. Consistent throughput calculation using actual simulation duration.
4. Standardized seed derivation and removal of arbitrary offsets.
5. Paired workload equivalence across competing baselines and runners.
6. Process isolation via cloning (no accidental state mutation across baselines).
"""

import pytest
import numpy as np
from src.coreos.config import STANDARD_SEEDS, get_standard_seeds
from src.coreos.learning.environment import CoReOSGymEnv
from src.learning.env import CoReOSEnv
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.process import SimulatedProcess, ProcessState
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.evaluation.benchmark_runner import BenchmarkRunner
from src.evaluation.ablation_runner import AblationRunner


def test_rl_environment_configured_horizon():
    """Verify default horizon is 300 for evaluation and customizable for training."""
    env_eval = CoReOSGymEnv()
    assert env_eval.max_steps == 300, "Evaluation horizon must be 300 to match benchmark baselines"

    env_train = CoReOSGymEnv(max_steps=150)
    assert env_train.max_steps == 150, "Training horizon must be 150 to preserve training exploration"

    # Legacy environment mirroring
    env_legacy_eval = CoReOSEnv()
    assert env_legacy_eval.max_steps == 300
    env_legacy_train = CoReOSEnv(max_steps=150)
    assert env_legacy_train.max_steps == 150


def test_rl_evaluation_horizon_termination_at_max_steps():
    """Verify that an unfinished workload terminates exactly at max_steps."""
    sim = SystemSimulator()
    # A single process with very large burst that won't complete within 50 steps
    long_proc = SimulatedProcess(
        pid=1,
        name="LongJob",
        arrival_time=0.0,
        cpu_burst_time=500.0,
        memory_demand_mb=512.0
    )
    sim.reset([long_proc])
    env = CoReOSGymEnv(simulator=sim, max_steps=50)

    done = False
    steps = 0
    while not done:
        obs, reward, done, state = env.step(action=2)
        steps += 1

    assert steps == 50, f"Expected termination at max_steps=50, got {steps}"
    assert done is True
    assert sim.current_time == 50.0


def test_rl_early_termination_on_completion():
    """Verify that the RL environment terminates early when all processes finish."""
    sim = SystemSimulator()
    short_proc = SimulatedProcess(
        pid=1,
        name="ShortJob",
        arrival_time=0.0,
        cpu_burst_time=3.0,
        memory_demand_mb=512.0,
        io_frequency=0.0
    )
    sim.reset([short_proc])
    env = CoReOSGymEnv(simulator=sim, max_steps=300)

    done = False
    steps = 0
    while not done and steps < 300:
        obs, reward, done, state = env.step(action=2)
        steps += 1

    assert done is True
    assert steps < 300, "Should terminate before 300 steps once process is done"
    assert sim.is_done() is True


def test_throughput_consistent_duration():
    """Verify throughput comparisons use actual simulated duration consistently."""
    p1 = SimulatedProcess(pid=1, name="P1", arrival_time=0.0, cpu_burst_time=10.0, memory_demand_mb=512.0)
    p2 = SimulatedProcess(pid=2, name="P2", arrival_time=0.0, cpu_burst_time=10.0, memory_demand_mb=512.0)
    p1.completion_time = 10.0
    p2.completion_time = 20.0
    completed = [p1, p2]
    history = [{"time": 10.0}, {"time": 20.0}]

    metrics = compute_simulation_metrics(completed, history)
    # Throughput must be completed / total_time = 2 / 20.0 = 0.1
    assert metrics["throughput"] == 0.1
    assert metrics["total_time"] == 20.0


def test_standard_seeds_definition_and_derivation():
    """Verify STANDARD_SEEDS list, get_standard_seeds helper, and deterministic derivation."""
    assert STANDARD_SEEDS == [42, 101, 202]

    seeds_3 = get_standard_seeds(num_seeds=3)
    assert seeds_3 == [42, 101, 202]

    seeds_1 = get_standard_seeds(num_seeds=1)
    assert seeds_1 == [42]

    seeds_5 = get_standard_seeds(num_seeds=5)
    assert seeds_5 == [42, 101, 202, 302, 402]

    explicit = get_standard_seeds(explicit_seeds=[7, 13])
    assert explicit == [7, 13]


def test_paired_workload_instance_equivalence():
    """
    Verify that generating workloads with identical seed produces bit-for-bit identical
    process specifications across independent generator instances.
    """
    gen1 = WorkloadGenerator(seed=42)
    procs1 = gen1.generate_workload(num_processes=40, workload_type="adversarial_stress")

    gen2 = WorkloadGenerator(seed=42)
    procs2 = gen2.generate_workload(num_processes=40, workload_type="adversarial_stress")

    assert len(procs1) == len(procs2) == 40
    for p1, p2 in zip(procs1, procs2):
        assert p1.pid == p2.pid
        assert p1.arrival_time == p2.arrival_time
        assert p1.cpu_burst_time == p2.cpu_burst_time
        assert p1.memory_demand_mb == p2.memory_demand_mb
        assert p1.priority == p2.priority
        assert p1.io_frequency == p2.io_frequency


def test_competing_baselines_receive_cloned_workloads():
    """
    Verify that executing a simulation on a workload clones the processes and leaves
    the original workload unmutated for competing configurations.
    """
    gen = WorkloadGenerator(seed=42)
    base_procs = gen.generate_workload(num_processes=10, workload_type="steady_state")

    # Record initial states
    initial_states = [(p.state, p.memory_allocated_mb) for p in base_procs]

    runner = BenchmarkRunner()
    # Run Baseline A on base_procs
    res_a = runner.run_baseline_a_conventional(base_procs, seed=42)

    # Verify original base_procs was not mutated
    for i, p in enumerate(base_procs):
        assert (p.state, p.memory_allocated_mb) == initial_states[i], (
            f"Process {p.pid} was mutated during execution of baseline!"
        )


def test_complete_coreos_benchmark_and_ablation_paired_equivalence():
    """
    Priority 3 audit reconciliation:
    Verify that BenchmarkRunner (Complete CoReOS) and AblationRunner (Full CoReOS)
    yield identical performance metrics when given identical seeds and workloads.
    """
    seed = 42
    workload_type = "steady_state"

    b_runner = BenchmarkRunner()
    a_runner = AblationRunner(seed=seed)

    # Generate identical workload
    gen = WorkloadGenerator(seed=seed)
    procs = gen.generate_workload(num_processes=20, workload_type=workload_type)

    b_res = b_runner.run_baseline_e_complete_coreos(procs, seed=seed)
    a_res = a_runner.run_ablation_trial(
        procs,
        enable_conflict_prediction=True,
        use_ml_conflict=True,
        enable_self_healing=True,
        enable_feedback=True,
        sim_seed=seed
    )

    assert b_res["completed_processes"] == a_res["completed_processes"]
    assert b_res["throughput"] == a_res["throughput"]
    assert pytest.approx(b_res["avg_turnaround_time"], 0.01) == a_res["avg_turnaround_time"]
    assert b_res["thrashing_ticks"] == a_res["thrashing_ticks"]
