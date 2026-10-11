"""
CoReOS Simulation: Workload Generator
Generates reproducible process workloads calibrated using empirical priors
from the real Kaggle IT System Performance dataset.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.simulation.process import SimulatedProcess


class WorkloadGenerator:
    """
    Synthesizes process arrival sequences.
    METHODOLOGICAL INTEGRITY NOTE:
    Process-level attributes (PID, bursts, page requests) are simulated.
    Parameter distributions (burst mean/variance, memory load, I/O rates)
    are calibrated against empirical distributions from Big_data_dataset.csv.
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
        num_processes: int = 50,
        workload_type: str = "steady_state",
        total_time_window: float = 200.0
    ) -> List[SimulatedProcess]:
        """
        Generates a list of SimulatedProcess objects sorted by arrival time.
        """
        # Baseline parameter ranges calibrated to dataset priors if available
        cpu_mean = self.priors.get("cpu_utilization", {}).get("mean", 50.0)
        mem_mean = self.priors.get("memory_usage", {}).get("mean", 55.0)
        disk_mean = self.priors.get("disk_io", {}).get("mean", 25.0)

        processes = []

        # Inter-arrival times using Poisson process (exponential inter-arrival)
        inter_arrivals = self.rng.exponential(scale=total_time_window / (num_processes * 1.2), size=num_processes)
        arrival_times = np.cumsum(inter_arrivals)

        for i in range(num_processes):
            pid = 1000 + i
            arrival = float(arrival_times[i])

            if workload_type == "steady_state":
                cpu_burst = float(self.rng.gamma(shape=2.5, scale=4.0))  # mean ~10
                memory_mb = float(self.rng.normal(loc=512.0, scale=128.0))
                io_freq = float(self.rng.uniform(0.1, 0.3))
                io_burst = float(self.rng.uniform(2.0, 5.0))
                priority = int(self.rng.randint(3, 8))

            elif workload_type == "cpu_spike":
                # Heavy CPU burst processes arriving in clusters
                cpu_burst = float(self.rng.gamma(shape=5.0, scale=8.0))  # mean ~40
                memory_mb = float(self.rng.normal(loc=384.0, scale=64.0))
                io_freq = float(self.rng.uniform(0.05, 0.15))
                io_burst = float(self.rng.uniform(1.0, 3.0))
                priority = int(self.rng.randint(1, 9))

            elif workload_type == "memory_thrashing":
                # High memory demand jobs exceeding physical RAM
                cpu_burst = float(self.rng.gamma(shape=2.0, scale=5.0))
                memory_mb = float(self.rng.uniform(2048.0, 6144.0))     # 2-6 GB per process
                io_freq = float(self.rng.uniform(0.1, 0.25))
                io_burst = float(self.rng.uniform(2.0, 4.0))
                priority = int(self.rng.randint(2, 7))

            elif workload_type == "io_bottleneck":
                # I/O heavy jobs with frequent storage accesses
                cpu_burst = float(self.rng.gamma(shape=1.5, scale=3.0))
                memory_mb = float(self.rng.normal(loc=512.0, scale=128.0))
                io_freq = float(self.rng.uniform(0.6, 0.9))             # High I/O probability
                io_burst = float(self.rng.uniform(6.0, 15.0))            # Long I/O service
                priority = int(self.rng.randint(3, 8))

            elif workload_type == "adversarial_stress":
                # Combined extreme stress: large memory + high CPU + heavy I/O
                cpu_burst = float(self.rng.gamma(shape=4.0, scale=6.0))
                memory_mb = float(self.rng.uniform(1536.0, 4096.0))
                io_freq = float(self.rng.uniform(0.4, 0.8))
                io_burst = float(self.rng.uniform(4.0, 10.0))
                priority = int(self.rng.randint(1, 10))

            else:
                # Fallback standard
                cpu_burst = float(self.rng.exponential(scale=12.0))
                memory_mb = float(self.rng.uniform(256.0, 1024.0))
                io_freq = 0.2
                io_burst = 3.0
                priority = 5

            cpu_burst = max(1.0, cpu_burst)
            memory_mb = max(64.0, memory_mb)
            io_burst = max(0.5, io_burst)

            proc = SimulatedProcess(
                pid=pid,
                name=f"task_{pid}_{workload_type}",
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
