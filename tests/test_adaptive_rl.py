"""
Unit and regression tests for Phase 7 Adaptive Reinforcement Learning baseline.
Verifies:
1. State discretization and bounded state space.
2. State coverage under multi-workload curriculum vs original RL.
3. Action selection, tie-breaking, and nearest-neighbor generalization.
4. Objective-aligned reward dynamics (completions, thrashing penalty, backlog penalty).
5. Reproducibility under evaluation mode.
6. ImprovedRLCandidate interface compatibility.
"""

import pytest
import numpy as np
from src.coreos.learning.adaptive_rl import (
    AdaptiveCoReOSGymEnv,
    AdaptiveRLAgent,
    ImprovedRLCandidate
)
from src.coreos.simulation.workload import WorkloadGenerator


def test_state_discretization_bounds():
    env = AdaptiveCoReOSGymEnv()

    # Normal state
    s1 = env.discretize_state({
        "ready_queue_length": 1,
        "waiting_memory_count": 0,
        "memory_utilization": 40.0,
        "io_queue_length": 2,
        "io_saturation": 30.0,
        "is_thrashing": False
    })
    assert s1 == (0, 0, 0, 0)

    # Moderate pressure state
    s2 = env.discretize_state({
        "ready_queue_length": 5,
        "waiting_memory_count": 0,
        "memory_utilization": 75.0,
        "io_queue_length": 6,
        "io_saturation": 60.0,
        "is_thrashing": False
    })
    assert s2 == (1, 1, 1, 0)

    # Critical pressure and thrashing state
    s3 = env.discretize_state({
        "ready_queue_length": 15,
        "waiting_memory_count": 3,
        "memory_utilization": 92.0,
        "io_queue_length": 14,
        "io_saturation": 88.0,
        "is_thrashing": True
    })
    assert s3 == (2, 2, 2, 1)


def test_reward_dynamics(monkeypatch):
    env = AdaptiveCoReOSGymEnv(max_steps=10)
    env.reset(seed=101, workload_type="steady_state")

    # Step in normal conditions
    obs, r_normal, done, state = env.step(action=0)
    assert isinstance(r_normal, float)

    # Inject thrashing via memory subsystem property
    monkeypatch.setattr(type(env.simulator.memory), "is_thrashing", property(lambda self: True))
    _, r_thrash, _, _ = env.step(action=0)
    assert r_thrash < r_normal, f"Thrashing reward {r_thrash} must be lower than normal {r_normal}"


def test_training_curriculum_state_coverage():
    np.random.seed(42)
    env = AdaptiveCoReOSGymEnv(max_steps=100)
    agent = AdaptiveRLAgent()

    # Train for a curriculum
    rewards = agent.train_curriculum(env, episodes_per_workload=5, base_seed=100)
    assert len(rewards) == 30
    visited_states = sum(1 for cnt in agent.visited_counts.values() if cnt > 0)

    # Must visit substantially more states than the original 4-5 steady-state states
    assert visited_states >= 10, f"Expected >= 10 visited states, got {visited_states}"


def test_action_selection_and_nearest_neighbor():
    agent = AdaptiveRLAgent()
    # Explicitly populate one visited state
    known_state = (0, 0, 0, 0)
    agent.q_table[known_state] = np.array([10.0, 50.0, 20.0, 5.0, 2.0, 1.0], dtype=np.float32)
    agent.visited_counts[known_state] = 10

    # Greedy choice on visited state must be action 1 (Q=50.0)
    act = agent.select_action(known_state, evaluate=True)
    assert act == 1

    # Unvisited neighboring state: (0, 1, 0, 0)
    unvisited_neighbor = (0, 1, 0, 0)
    assert agent.visited_counts.get(unvisited_neighbor, 0) == 0

    # Nearest-neighbor must resolve to known_state's best action (1) rather than defaulting to 0
    act_nn = agent.select_action(unvisited_neighbor, evaluate=True)
    assert act_nn == 1


def test_deterministic_evaluation_reproducibility():
    np.random.seed(42)
    agent = AdaptiveRLAgent()
    env = AdaptiveCoReOSGymEnv(max_steps=50)
    agent.train_curriculum(env, episodes_per_workload=2, base_seed=500)

    wgen = WorkloadGenerator(seed=42)
    procs1 = wgen.generate_workload(num_processes=20, workload_type="cpu_spike")
    procs2 = [p.clone() for p in procs1]

    cand = ImprovedRLCandidate(agent=agent)
    m1 = cand.run_simulation(procs1, seed=999, max_steps=100)
    m2 = cand.run_simulation(procs2, seed=999, max_steps=100)

    assert m1["completed_processes"] == m2["completed_processes"]
    assert m1["throughput"] == m2["throughput"]
    assert m1["thrashing_ticks"] == m2["thrashing_ticks"]
    assert m1["completion_rate"] == m2["completion_rate"]


def test_candidate_interface_metrics():
    wgen = WorkloadGenerator(seed=42)
    procs = wgen.generate_workload(num_processes=15, workload_type="steady_state")
    agent = AdaptiveRLAgent()
    agent.q_table[(0, 0, 0, 0)] = np.zeros(6, dtype=np.float32)
    agent.visited_counts[(0, 0, 0, 0)] = 1

    candidate = ImprovedRLCandidate(agent=agent)
    m = candidate.run_simulation(procs, seed=123, max_steps=50)

    required_keys = [
        "completion_rate",
        "completed_processes",
        "unfinished_processes",
        "throughput",
        "avg_turnaround_time",
        "penalized_turnaround_time",
        "thrashing_ticks",
        "jains_fairness_index"
    ]
    for k in required_keys:
        assert k in m, f"Missing metric key: {k}"
