"""
CoReOS Learning Environment
Gymnasium-compatible discrete MDP environment for simulated OS resource management.
METHODOLOGICAL NOTE: Transitions are generated exclusively by the dynamic simulator,
not fabricated from static dataset rows.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from src.simulation.simulator import SystemSimulator
from src.simulation.workload_generator import WorkloadGenerator
from src.simulation.process import SimulatedProcess


class CoReOSEnv:
    """
    Simulated OS Environment for Reinforcement Learning.
    Observation space: 8-dimensional continuous vector.
    Action space: 4 discrete joint coordination policies.
    """

    ACTION_MAP = {
        0: {"cpu_quantum": 8.0, "memory_reclaim_target": 2048.0, "io_policy": "SCAN"},    # Conservative/Anti-thrash
        1: {"cpu_quantum": 2.0, "memory_reclaim_target": 0.0, "io_policy": "FCFS"},       # High-responsiveness
        2: {"cpu_quantum": 4.0, "memory_reclaim_target": 1024.0, "io_policy": "SSTF"},     # Balanced
        3: {"cpu_quantum": 6.0, "memory_reclaim_target": 4096.0, "io_policy": "SCAN"}      # Heavy throughput / Deep reclaim
    }

    def __init__(self, simulator: Optional[SystemSimulator] = None, max_steps: int = 300):
        """
        Initializes the RL gym environment.
        max_steps defaults to 300 for evaluation consistency with all other benchmark baselines.
        Training pipelines explicitly pass max_steps=150 to preserve the training episode horizon.
        """
        self.simulator = simulator or SystemSimulator()
        self.max_steps = max_steps
        self.current_step = 0
        self.workload_gen = WorkloadGenerator(seed=42)

    def reset(self, seed: Optional[int] = None, workload_type: str = "steady_state") -> np.ndarray:
        if seed is not None:
            self.workload_gen.set_seed(seed)
        processes = self.workload_gen.generate_workload(num_processes=35, workload_type=workload_type)
        self.simulator.reset(processes)
        self.current_step = 0
        
        # Step once to populate state
        state = self.simulator.step(dt=1.0)
        return self._extract_obs(state)

    def _extract_obs(self, state: Dict[str, Any]) -> np.ndarray:
        return np.array([
            min(1.0, state.get("cpu_utilization", 0.0) / 100.0),
            min(1.0, state.get("memory_utilization", 0.0) / 100.0),
            min(1.0, state.get("io_saturation", 0.0) / 100.0),
            min(1.0, state.get("ready_queue_length", 0) / 30.0),
            min(1.0, state.get("io_queue_length", 0) / 30.0),
            1.0 if state.get("is_thrashing", False) else 0.0,
            min(1.0, state.get("avg_waiting_time", 0.0) / 50.0),
            min(1.0, state.get("throughput", 0.0) / 2.0)
        ], dtype=np.float32)

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, Dict[str, Any]]:
        self.current_step += 1
        params = self.ACTION_MAP.get(action, self.ACTION_MAP[2])

        state = self.simulator.step(
            dt=1.0,
            cpu_policy="ROUND_ROBIN",
            cpu_quantum=params["cpu_quantum"],
            io_policy=params["io_policy"],
            memory_reclaim_target=params["memory_reclaim_target"]
        )

        obs = self._extract_obs(state)

        # Reward formulation: Reward throughput, heavily penalize thrashing & waiting latency
        tp = state.get("throughput", 0.0)
        thrashing_penalty = 10.0 if state.get("is_thrashing", False) else 0.0
        queue_penalty = (state.get("ready_queue_length", 0) + state.get("io_queue_length", 0)) * 0.1
        reward = float(tp * 5.0 - thrashing_penalty - queue_penalty)

        done = self.current_step >= self.max_steps or self.simulator.is_done()
        return obs, reward, done, state
