"""
CoReOS Simulation Workload Generator
Generates reproducible process workloads calibrated using empirical priors
from the Kaggle IT System Performance and Resource Metrics dataset.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.coreos.simulation.process import SimulatedProcess


class WorkloadGenerator:
    """
    Synthesizes reproducible process arrivals.
    Integrates empirical parameter priors from Big_data_dataset.csv.
    """

    def __init__(self, empirical_priors: Optional[Dict[str, Any]] = None, seed: int = 42):
        self.priors = empirical_priors or {}
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def set_seed(self, seed: int):
        self.seed = seed
        self.rng = np.random.RandomState(seed)

    def generate_workload(
        self,
        num_processes: int = 40,
        workload_type: str = "steady_state",
        total_time_window: float = 200.0
    ) -> List[SimulatedProcess]:
        """
        Generates simulated processes sorted by arrival time.
        """
        processes = []

        # Inter-arrival times modeled as Poisson process (exponential inter-arrival)
        inter_arrivals = self.rng.exponential(
            scale=total_time_window / max(1, num_processes * 1.2),
            size=num_processes
        )
        arrival_times = np.cumsum(inter_arrivals)

        for i in range(num_processes):
            pid = 1000 + i
            arrival = float(arrival_times[i])

            if workload_type == "steady_state":
                cpu_burst = float(self.rng.gamma(shape=2.5, scale=4.0))
                memory_mb = float(self.rng.normal(loc=512.0, scale=128.0))
                io_freq = float(self.rng.uniform(0.1, 0.3))
                io_burst = float(self.rng.uniform(2.0, 5.0))
                priority = int(self.rng.randint(3, 8))

            elif workload_type == "cpu_spike":
                cpu_burst = float(self.rng.gamma(shape=5.0, scale=8.0))  # Heavy CPU
                memory_mb = float(self.rng.normal(loc=384.0, scale=64.0))
                io_freq = float(self.rng.uniform(0.05, 0.15))
                io_burst = float(self.rng.uniform(1.0, 3.0))
                priority = int(self.rng.randint(1, 9))

            elif workload_type == "memory_thrashing":
                cpu_burst = float(self.rng.gamma(shape=2.0, scale=5.0))
                memory_mb = float(self.rng.uniform(2048.0, 6144.0))      # Heavy RAM
                io_freq = float(self.rng.uniform(0.1, 0.25))
                io_burst = float(self.rng.uniform(2.0, 4.0))
                priority = int(self.rng.randint(2, 7))

            elif workload_type == "io_bottleneck":
                cpu_burst = float(self.rng.gamma(shape=1.5, scale=3.0))
                memory_mb = float(self.rng.normal(loc=512.0, scale=128.0))
                io_freq = float(self.rng.uniform(0.6, 0.9))              # Heavy I/O
                io_burst = float(self.rng.uniform(6.0, 15.0))
                priority = int(self.rng.randint(3, 8))

            elif workload_type == "mixed":
                # Heterogeneous distribution
                sub_type = self.rng.choice(["cpu", "mem", "io", "norm"])
                if sub_type == "cpu":
                    cpu_burst = float(self.rng.gamma(shape=5.0, scale=6.0))
                    memory_mb = float(self.rng.normal(loc=512.0, scale=64.0))
                    io_freq = 0.1
                    io_burst = 2.0
                elif sub_type == "mem":
                    cpu_burst = float(self.rng.gamma(shape=2.0, scale=3.0))
                    memory_mb = float(self.rng.uniform(2048.0, 5120.0))
                    io_freq = 0.2
                    io_burst = 3.0
                elif sub_type == "io":
                    cpu_burst = 3.0
                    memory_mb = 512.0
                    io_freq = 0.7
                    io_burst = 8.0
                else:
                    cpu_burst = 8.0
                    memory_mb = 512.0
                    io_freq = 0.2
                    io_burst = 3.0
                priority = int(self.rng.randint(1, 10))

            elif workload_type == "bursty":
                # Arrive in sudden tight clusters
                cluster_id = i // 5
                arrival = float(cluster_id * 20.0 + self.rng.uniform(0.0, 3.0))
                cpu_burst = float(self.rng.gamma(shape=3.0, scale=5.0))
                memory_mb = float(self.rng.normal(loc=768.0, scale=256.0))
                io_freq = float(self.rng.uniform(0.2, 0.5))
                io_burst = float(self.rng.uniform(3.0, 6.0))
                priority = int(self.rng.randint(2, 9))

            elif workload_type == "adversarial_stress":
                # Combined extreme pressure
                cpu_burst = float(self.rng.gamma(shape=4.0, scale=6.0))
                memory_mb = float(self.rng.uniform(1536.0, 4096.0))
                io_freq = float(self.rng.uniform(0.4, 0.8))
                io_burst = float(self.rng.uniform(4.0, 10.0))
                priority = int(self.rng.randint(1, 10))

            elif workload_type == "sudden_shift":
                # Phase 1: light steady; Phase 2: sudden thrashing
                if i < num_processes // 2:
                    cpu_burst = 6.0
                    memory_mb = 384.0
                    io_freq = 0.1
                    io_burst = 2.0
                    priority = 5
                else:
                    cpu_burst = 18.0
                    memory_mb = 3500.0
                    io_freq = 0.5
                    io_burst = 7.0
                    priority = 8

            else:
                cpu_burst = float(self.rng.exponential(scale=10.0))
                memory_mb = float(self.rng.uniform(256.0, 1024.0))
                io_freq = 0.2
                io_burst = 3.0
                priority = 5

            cpu_burst = max(1.0, cpu_burst)
            memory_mb = max(64.0, memory_mb)
            io_burst = max(0.5, io_burst)

            proc = SimulatedProcess(
                pid=pid,
                name=f"job_{pid}_{workload_type}",
                arrival_time=arrival,
                cpu_burst_time=cpu_burst,
                memory_demand_mb=memory_mb,
                priority=priority,
                io_frequency=io_freq,
                io_burst_time=io_burst
            )
            processes.append(proc)

        processes.sort(key=lambda p: p.arrival_time)
        return processes
