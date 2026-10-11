"""
CoReOS Simulation & Evaluation Metrics
Computes turnaround times, response times, Jain's fairness index,
conflict prediction confusion metrics, and recovery statistics.
"""

from typing import List, Dict, Any, Optional
import numpy as np
from src.coreos.simulation.process import SimulatedProcess


def compute_jains_fairness_index(turnaround_times: List[float]) -> float:
    """
    Computes Jain's Fairness Index bounded in [1/n, 1.0].
    Handles empty arrays and zero division gracefully.
    """
    if not turnaround_times:
        return 1.0
    arr = np.array(turnaround_times, dtype=np.float64)
    arr = np.maximum(arr, 1e-6)
    n = len(arr)
    numerator = float(np.sum(arr) ** 2)
    denominator = float(n * np.sum(arr ** 2))
    return float(numerator / denominator) if denominator > 0 else 1.0


def compute_simulation_metrics(
    completed_processes: List[SimulatedProcess],
    simulation_history: List[Dict[str, Any]],
    overhead_ms: float = 0.0,
    conflict_metrics: Optional[Dict[str, Any]] = None,
    healing_metrics: Optional[Dict[str, Any]] = None,
    total_processes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculates standardized metrics across a simulation run.

    NOTE ON SURVIVORSHIP BIAS & UNFINISHED PROCESSES:
    - avg_turnaround_time, p95_turnaround_time, avg_waiting_time, and avg_response_time
      are computed strictly over completed_processes.
    - Jain's Fairness Index evaluates the turnaround-time distribution exclusively among
      completed_processes.
    - In incomplete workloads (e.g. adversarial stress or under-provisioned memory),
      measuring only completed processes can introduce survivorship bias if a scheduler
      finishes a small number of short jobs while starving longer jobs.
    - To prevent survivorship bias, completion metrics (total_processes, completed_processes,
      unfinished_processes, completion_rate) are explicitly reported and must be analyzed
      alongside turnaround times.
    """
    n_procs = len(completed_processes)
    total_procs = int(total_processes) if total_processes is not None else n_procs
    unfinished_procs = max(0, total_procs - n_procs)
    completion_rate = round((n_procs / total_procs * 100.0), 2) if total_procs > 0 else 0.0

    if n_procs > 0:
        wait_times = [p.total_waiting_time for p in completed_processes]
        turnarounds = [p.turnaround_time for p in completed_processes if p.turnaround_time is not None]
        resp_times = [p.response_time for p in completed_processes if p.response_time is not None]

        avg_wait = float(np.mean(wait_times)) if wait_times else 0.0
        avg_turnaround = float(np.mean(turnarounds)) if turnarounds else 0.0
        p95_turnaround = float(np.percentile(turnarounds, 95)) if turnarounds else 0.0
        avg_response = float(np.mean(resp_times)) if resp_times else 0.0
        fairness = compute_jains_fairness_index(turnarounds)
    else:
        avg_wait = avg_turnaround = p95_turnaround = avg_response = 0.0
        fairness = 1.0

    if simulation_history:
        cpu_utils = [h.get("cpu_utilization", 0.0) for h in simulation_history]
        mem_utils = [h.get("memory_utilization", 0.0) for h in simulation_history]
        io_sats = [h.get("io_saturation", 0.0) for h in simulation_history]
        total_time = simulation_history[-1].get("time", 1.0)
        thrashing_ticks = sum(1 for h in simulation_history if h.get("is_thrashing", False))

        avg_cpu = float(np.mean(cpu_utils))
        avg_mem = float(np.mean(mem_utils))
        avg_io = float(np.mean(io_sats))
        throughput = float(n_procs / total_time) if total_time > 0 else 0.0
    else:
        avg_cpu = avg_mem = avg_io = throughput = 0.0
        total_time = 0.0
        thrashing_ticks = 0

    return {
        "total_processes": total_procs,
        "completed_processes": n_procs,
        "unfinished_processes": unfinished_procs,
        "completion_rate": completion_rate,
        "total_time": round(total_time, 2),
        "avg_waiting_time": round(avg_wait, 2),
        "avg_turnaround_time": round(avg_turnaround, 2),
        "p95_turnaround_time": round(p95_turnaround, 2),
        "avg_response_time": round(avg_response, 2),
        "throughput": round(throughput, 4),
        "jains_fairness_index": round(fairness, 4),
        "avg_cpu_utilization": round(avg_cpu, 2),
        "avg_memory_utilization": round(avg_mem, 2),
        "avg_io_saturation": round(avg_io, 2),
        "thrashing_ticks": thrashing_ticks,
        "decision_overhead_ms": round(overhead_ms, 3),
        "conflict_metrics": conflict_metrics or {},
        "healing_metrics": healing_metrics or {}
    }
