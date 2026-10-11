"""
CoReOS Simulation: CPU Subsystem
Manages simulated CPU cores, ready queues, context switches, and scheduling policies.
"""

from typing import List, Optional, Tuple, Dict
from src.simulation.process import SimulatedProcess, ProcessState


class CPUSubsystem:
    def __init__(
        self,
        num_cores: int = 4,
        context_switch_penalty: float = 0.5,
        default_quantum: float = 4.0
    ):
        self.num_cores = num_cores
        self.context_switch_penalty = context_switch_penalty
        self.default_quantum = default_quantum
        
        # Cores: None if idle, or SimulatedProcess
        self.cores: List[Optional[SimulatedProcess]] = [None] * num_cores
        self.core_time_in_quantum: List[float] = [0.0] * num_cores
        self.ready_queue: List[SimulatedProcess] = []
        
        # Telemetry
        self.total_context_switches: int = 0
        self.total_cpu_busy_time: float = 0.0
        self.total_cpu_idle_time: float = 0.0
        self.completed_processes: List[SimulatedProcess] = []

    @property
    def ready_queue_length(self) -> int:
        return len(self.ready_queue)

    @property
    def active_core_count(self) -> int:
        return sum(1 for c in self.cores if c is not None)

    @property
    def instantaneous_utilization(self) -> float:
        return (self.active_core_count / self.num_cores) * 100.0

    def enqueue_ready(self, process: SimulatedProcess):
        process.state = ProcessState.READY
        self.ready_queue.append(process)

    def sort_ready_queue(self, policy: str):
        """Sorts ready queue according to scheduling policy."""
        if policy == "FCFS":
            self.ready_queue.sort(key=lambda p: p.arrival_time)
        elif policy == "PRIORITY":
            # Higher priority number executed first
            self.ready_queue.sort(key=lambda p: (-p.priority, p.arrival_time))
        elif policy == "SRTF":
            # Shortest Remaining Time First
            self.ready_queue.sort(key=lambda p: (p.remaining_burst, p.arrival_time))
        elif policy == "ROUND_ROBIN":
            pass  # FIFO queue maintained naturally for RR

    def schedule_next(self, policy: str = "ROUND_ROBIN", current_time: float = 0.0) -> List[Tuple[int, int]]:
        """
        Assigns ready processes to idle cores.
        Returns list of (core_id, pid) assignments made.
        """
        self.sort_ready_queue(policy)
        assignments = []

        for core_id in range(self.num_cores):
            if self.cores[core_id] is None and self.ready_queue:
                proc = self.ready_queue.pop(0)
                proc.state = ProcessState.RUNNING
                if proc.start_time is None:
                    proc.start_time = current_time
                self.cores[core_id] = proc
                self.core_time_in_quantum[core_id] = 0.0
                self.total_context_switches += 1
                proc.context_switch_count += 1
                assignments.append((core_id, proc.pid))

        return assignments

    def step(
        self,
        dt: float,
        policy: str = "ROUND_ROBIN",
        quantum: Optional[float] = None,
        current_time: float = 0.0,
        slowdown_factor: float = 1.0
    ) -> Tuple[List[SimulatedProcess], List[SimulatedProcess]]:
        """
        Advances CPU execution by dt time units.
        Returns:
            finished_processes: Processes that completed CPU burst.
            yielded_processes: Processes that exhausted time quantum or need I/O.
        """
        effective_quantum = quantum if quantum is not None else self.default_quantum
        finished = []
        yielded = []

        # Account for waiting time of ready queue
        for proc in self.ready_queue:
            proc.total_waiting_time += dt

        for core_id in range(self.num_cores):
            proc = self.cores[core_id]
            if proc is None:
                self.total_cpu_idle_time += dt
                continue

            self.total_cpu_busy_time += dt
            effective_dt = dt / max(1.0, slowdown_factor)
            exec_time = min(effective_dt, proc.remaining_burst)
            proc.remaining_burst -= exec_time
            self.core_time_in_quantum[core_id] += exec_time

            # Check completion
            if proc.remaining_burst <= 1e-6:
                proc.remaining_burst = 0.0
                proc.completion_time = current_time
                proc.state = ProcessState.TERMINATED
                finished.append(proc)
                self.cores[core_id] = None
                self.core_time_in_quantum[core_id] = 0.0

            # Check RR quantum expiration
            elif policy == "ROUND_ROBIN" and self.core_time_in_quantum[core_id] >= effective_quantum:
                proc.state = ProcessState.READY
                yielded.append(proc)
                self.cores[core_id] = None
                self.core_time_in_quantum[core_id] = 0.0

        # Refill idle cores
        self.schedule_next(policy, current_time + dt)
        return finished, yielded

    def preempt_core(self, core_id: int) -> Optional[SimulatedProcess]:
        """Preempts running process on specified core and returns it to ready queue."""
        if 0 <= core_id < self.num_cores and self.cores[core_id] is not None:
            proc = self.cores[core_id]
            proc.state = ProcessState.READY
            self.cores[core_id] = None
            self.core_time_in_quantum[core_id] = 0.0
            self.ready_queue.insert(0, proc)
            self.total_context_switches += 1
            proc.context_switch_count += 1
            return proc
        return None
