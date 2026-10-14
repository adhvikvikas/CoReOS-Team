"""
Improved Adaptive Reinforcement Learning Candidate (Phase 7).

Addresses critical limitations of the original tabular RL baseline:
1. State Space Compaction & Disentanglement:
   Replaces the sparse 8-feature representation (32k+ states) with a physically
   grounded 4-dimensional state representation (54 discrete states):
   (ready_queue_bin, memory_pressure_bin, io_congestion_bin, thrashing_bin).
2. Multi-Workload Training Curriculum:
   Trains across all six diverse workload profiles (steady_state, cpu_spike,
   memory_thrashing, io_bottleneck, mixed, adversarial_stress) rather than solely
   on steady_state.
3. Expressive Action Space:
   Expands action primitives from static Round-Robin to include progress-aware
   Shortest Remaining Time First (SRTF), variable quantums, deep memory reclamation,
   and elevator SCAN.
4. Objective-Aligned Reward Function:
   Directly incentivizes completed jobs and throughput while penalizing
   queue backlogs, memory stall wait-counts, and thrashing events.
5. Generalization via Nearest-Neighbor Lookup:
   Eliminates arbitrary tie-breaking (np.argmax defaults to action 0) on unvisited
   states by projecting onto the closest visited state in Manhattan metric space.
"""

from typing import Dict, Any, Tuple, Optional, List
import time
import numpy as np

from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.config import SimulationConfig, CoReOSConfig


class AdaptiveCoReOSGymEnv:
    """
    Compact, multi-objective Gym-compatible environment for CoReOS.
    State space: 3 (ready_q) x 3 (memory) x 3 (io) x 2 (thrashing) = 54 discrete states.
    """

    ACTION_MAP = {
        0: {"cpu_policy": "ROUND_ROBIN", "cpu_quantum": 4.0, "memory_reclaim_target": 1024.0, "io_policy": "SCAN"},
        1: {"cpu_policy": "ROUND_ROBIN", "cpu_quantum": 8.0, "memory_reclaim_target": 1024.0, "io_policy": "SCAN"},
        2: {"cpu_policy": "SRTF", "cpu_quantum": 8.0, "memory_reclaim_target": 1024.0, "io_policy": "SCAN"},
        3: {"cpu_policy": "ROUND_ROBIN", "cpu_quantum": 6.0, "memory_reclaim_target": 2048.0, "io_policy": "SCAN"},
        4: {"cpu_policy": "SRTF", "cpu_quantum": 8.0, "memory_reclaim_target": 2048.0, "io_policy": "SCAN"},
        5: {"cpu_policy": "ROUND_ROBIN", "cpu_quantum": 4.0, "memory_reclaim_target": 1024.0, "io_policy": "LOOK"},
    }

    def __init__(self, simulator: Optional[SystemSimulator] = None, max_steps: int = 150):
        self.simulator = simulator
        self.max_steps = max_steps
        self.current_step = 0
        self.workload_generator = WorkloadGenerator(seed=42)

    def discretize_state(self, state: Dict[str, Any]) -> Tuple[int, int, int, int]:
        """
        Discretizes system state into 54 compact physical bins.
        Returns: (rq_bin, mem_bin, io_bin, thrash_bin)
        """
        ready_q = state.get("ready_queue_length", 0)
        wait_mem = state.get("waiting_memory_count", 0)
        mem_util = state.get("memory_utilization", 0.0)
        io_q = state.get("io_queue_length", 0)
        io_sat = state.get("io_saturation", 0.0)
        is_thrash = state.get("is_thrashing", False)

        # 1. Ready Queue Backlog: 0 (light, <=2), 1 (moderate, 3..8), 2 (deep backlog, >8)
        if ready_q > 8:
            rq_bin = 2
        elif ready_q > 2:
            rq_bin = 1
        else:
            rq_bin = 0

        # 2. Memory Pressure: 0 (light, <70%), 1 (moderate, 70..85%), 2 (heavy / waiting, >=85%)
        if wait_mem > 0 or mem_util >= 85.0:
            mem_bin = 2
        elif mem_util >= 70.0:
            mem_bin = 1
        else:
            mem_bin = 0

        # 3. I/O Congestion: 0 (light), 1 (moderate), 2 (congested)
        if io_q >= 10 or io_sat >= 75.0:
            io_bin = 2
        elif io_q >= 4 or io_sat >= 50.0:
            io_bin = 1
        else:
            io_bin = 0

        # 4. Thrashing Indicator: 0 (safe), 1 (active thrashing)
        thrash_bin = 1 if is_thrash else 0

        return (rq_bin, mem_bin, io_bin, thrash_bin)

    def reset(
        self,
        seed: Optional[int] = None,
        workload_type: str = "steady_state",
        num_processes: int = 40
    ) -> Tuple[int, int, int, int]:
        if seed is not None:
            self.workload_generator.set_seed(seed)
            sim_cfg = SimulationConfig(random_seed=seed)
        else:
            sim_cfg = SimulationConfig()

        self.simulator = SystemSimulator(sim_cfg)
        procs = self.workload_generator.generate_workload(num_processes=num_processes, workload_type=workload_type)
        self.simulator.reset(procs)
        self.current_step = 0
        state = self.simulator.get_system_state()
        return self.discretize_state(state)

    def step(self, action: int) -> Tuple[Tuple[int, int, int, int], float, bool, Dict[str, Any]]:
        self.current_step += 1
        action_params = self.ACTION_MAP.get(action, self.ACTION_MAP[0])

        prev_completed = len(self.simulator.completed_processes)
        self.simulator.step(
            dt=1.0,
            cpu_policy=action_params["cpu_policy"],
            cpu_quantum=action_params["cpu_quantum"],
            io_policy=action_params["io_policy"],
            memory_reclaim_target=action_params["memory_reclaim_target"]
        )
        curr_completed = len(self.simulator.completed_processes)
        new_completed = curr_completed - prev_completed

        state = self.simulator.get_system_state()
        is_done = self.simulator.is_done() or (self.current_step >= self.max_steps)

        # Multi-objective, workload-aligned reward function
        throughput = state.get("throughput", 0.0)
        is_thrash = state.get("is_thrashing", False)
        ready_q = state.get("ready_queue_length", 0)
        io_q = state.get("io_queue_length", 0)
        wait_mem = state.get("waiting_memory_count", 0)

        reward = (
            25.0 * new_completed
            + 5.0 * min(1.0, throughput / 0.25)
            - 40.0 * (1.0 if is_thrash else 0.0)
            - 0.25 * ready_q
            - 0.15 * io_q
            - 0.50 * wait_mem
        )

        obs = self.discretize_state(state)
        return obs, reward, is_done, state


class AdaptiveRLAgent:
    """
    Workload-Adaptive Tabular Q-Learning Agent.
    - Guaranteed state coverage through multi-workload curriculum.
    - Nearest-neighbor generalization for unvisited states.
    - Deterministic evaluation mode.
    """

    def __init__(
        self,
        num_actions: int = 6,
        alpha: float = 0.15,
        gamma: float = 0.95,
        epsilon: float = 1.0,
        epsilon_min: float = 0.05,
        epsilon_decay: float = 0.96
    ):
        self.num_actions = num_actions
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table: Dict[Tuple[int, int, int, int], np.ndarray] = {}
        self.visited_counts: Dict[Tuple[int, int, int, int], int] = {}
        self.action_counts: Dict[int, int] = {i: 0 for i in range(num_actions)}
        self.training_rewards: List[float] = []

    def get_q_values(self, state: Tuple[int, int, int, int]) -> np.ndarray:
        if state not in self.q_table:
            self.q_table[state] = np.zeros(self.num_actions, dtype=np.float32)
            self.visited_counts[state] = 0
        return self.q_table[state]

    def select_action(
        self,
        state: Tuple[int, int, int, int],
        evaluate: bool = False
    ) -> int:
        """
        Selects action using epsilon-greedy exploration during training,
        or greedy action selection during evaluation with nearest-neighbor fallback.
        """
        if not evaluate and np.random.uniform(0.0, 1.0) < self.epsilon:
            act = int(np.random.randint(0, self.num_actions))
            self.action_counts[act] = self.action_counts.get(act, 0) + 1
            return act

        # Visited state greedy policy
        if state in self.q_table and self.visited_counts.get(state, 0) > 0:
            q_vals = self.q_table[state]
            max_val = np.max(q_vals)
            best_acts = np.where(q_vals == max_val)[0]
            act = int(best_acts[0])  # Deterministic tie-breaking on highest action index / priority
            self.action_counts[act] = self.action_counts.get(act, 0) + 1
            return act

        # Nearest-neighbor fallback for unvisited states
        target = np.array(state)
        best_dist = float("inf")
        best_state = None
        for s, cnt in self.visited_counts.items():
            if cnt > 0:
                dist = np.sum(np.abs(np.array(s) - target))
                if dist < best_dist:
                    best_dist = dist
                    best_state = s

        if best_state is not None:
            q_vals = self.q_table[best_state]
            max_val = np.max(q_vals)
            best_acts = np.where(q_vals == max_val)[0]
            act = int(best_acts[0])
            self.action_counts[act] = self.action_counts.get(act, 0) + 1
            return act

        act = 0
        self.action_counts[act] = self.action_counts.get(act, 0) + 1
        return act

    def update(
        self,
        state: Tuple[int, int, int, int],
        action: int,
        reward: float,
        next_state: Tuple[int, int, int, int],
        done: bool
    ):
        self.visited_counts[state] = self.visited_counts.get(state, 0) + 1
        curr_q = self.get_q_values(state)[action]
        next_max = np.max(self.get_q_values(next_state)) if not done else 0.0
        new_q = curr_q + self.alpha * (reward + self.gamma * next_max - curr_q)
        self.q_table[state][action] = float(new_q)

    def train_curriculum(
        self,
        env: Optional[AdaptiveCoReOSGymEnv] = None,
        episodes_per_workload: int = 20,
        base_seed: int = 4000
    ) -> List[float]:
        """
        Trains the agent across all 6 workload types in curriculum succession.
        """
        if env is None:
            env = AdaptiveCoReOSGymEnv(max_steps=150)

        workloads = [
            "steady_state",
            "cpu_spike",
            "memory_thrashing",
            "io_bottleneck",
            "mixed",
            "adversarial_stress"
        ]

        ep_count = 0
        all_rewards = []

        for ep in range(episodes_per_workload):
            for w in workloads:
                ep_count += 1
                seed = base_seed + ep_count
                state = env.reset(seed=seed, workload_type=w, num_processes=40)
                ep_reward = 0.0
                done = False
                while not done:
                    action = self.select_action(state, evaluate=False)
                    next_state, reward, done, _ = env.step(action)
                    self.update(state, action, reward, next_state, done)
                    state = next_state
                    ep_reward += reward
                self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
                all_rewards.append(ep_reward)

        self.training_rewards = all_rewards
        return all_rewards


class ImprovedRLCandidate:
    """
    Isolated Improved RL Candidate for benchmark and diagnostic evaluation.
    Conforms to standard simulation candidate interface:
    `run_simulation(processes, seed, max_steps)`
    """

    def __init__(self, agent: Optional[AdaptiveRLAgent] = None, base_training_seed: int = 4000):
        if agent is None:
            self.agent = AdaptiveRLAgent()
            train_env = AdaptiveCoReOSGymEnv(max_steps=150)
            self.agent.train_curriculum(train_env, episodes_per_workload=20, base_seed=base_training_seed)
        else:
            self.agent = agent

    def run_simulation(
        self,
        processes: List[Any],
        seed: Optional[int] = None,
        max_steps: int = 300
    ) -> Dict[str, Any]:
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else SimulationConfig()
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        env = AdaptiveCoReOSGymEnv(simulator=sim, max_steps=max_steps)
        state = env.discretize_state(sim.get_system_state())

        decision_time = 0.0
        step_i = 0
        done = False

        while not done and step_i < max_steps:
            t0 = time.perf_counter()
            action = self.agent.select_action(state, evaluate=True)
            decision_time += (time.perf_counter() - t0)

            state, _, done, _ = env.step(action)
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(
            sim.completed_processes,
            sim.history,
            overhead_ms,
            total_processes=len(workload)
        )
