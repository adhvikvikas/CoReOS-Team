"""
CoReOS Simulation Process Model
Defines lifecycle states, scheduling attributes, and telemetry for simulated processes.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional, Dict, Any


class ProcessState(Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING_IO = "WAITING_IO"
    WAITING_MEMORY = "WAITING_MEMORY"
    TERMINATED = "TERMINATED"


@dataclass
class SimulatedProcess:
    """
    Simulated OS Process entity.
    METHODOLOGICAL INTEGRITY: All process burst times, arrival times, and memory demands
    are generated in simulation (calibrated by real Kaggle dataset distributions).
    """
    pid: int
    name: str
    arrival_time: float
    cpu_burst_time: float
    memory_demand_mb: float
    priority: int = 5                   # 1 (lowest) to 10 (highest)
    io_frequency: float = 0.2           # Probability of requiring I/O during time slice
    io_burst_time: float = 3.0          # Time units required in I/O queue
    deadline: Optional[float] = None    # Optional SLA deadline
    
    # Dynamic lifecycle tracking
    state: ProcessState = ProcessState.NEW
    remaining_burst: float = field(init=False)
    memory_allocated_mb: float = 0.0
    start_time: Optional[float] = None
    completion_time: Optional[float] = None
    
    # Cumulative telemetry
    total_waiting_time: float = 0.0
    total_io_wait_time: float = 0.0
    page_fault_count: int = 0
    context_switch_count: int = 0
    is_paged_out: bool = False

    def __post_init__(self):
        self.remaining_burst = float(self.cpu_burst_time)

    @property
    def turnaround_time(self) -> Optional[float]:
        if self.completion_time is not None:
            return self.completion_time - self.arrival_time
        return None

    @property
    def response_time(self) -> Optional[float]:
        if self.start_time is not None:
            return self.start_time - self.arrival_time
        return None

    def is_finished(self) -> bool:
        return self.remaining_burst <= 1e-6 and self.state == ProcessState.TERMINATED

    def clone(self) -> 'SimulatedProcess':
        """Creates an identical unexecuted replica for fair baseline comparison."""
        return SimulatedProcess(
            pid=self.pid,
            name=self.name,
            arrival_time=self.arrival_time,
            cpu_burst_time=self.cpu_burst_time,
            memory_demand_mb=self.memory_demand_mb,
            priority=self.priority,
            io_frequency=self.io_frequency,
            io_burst_time=self.io_burst_time,
            deadline=self.deadline
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pid": self.pid,
            "name": self.name,
            "arrival_time": round(self.arrival_time, 2),
            "cpu_burst_time": round(self.cpu_burst_time, 2),
            "remaining_burst": round(self.remaining_burst, 2),
            "memory_demand_mb": round(self.memory_demand_mb, 2),
            "memory_allocated_mb": round(self.memory_allocated_mb, 2),
            "priority": self.priority,
            "state": self.state.value,
            "waiting_time": round(self.total_waiting_time, 2),
            "turnaround_time": round(self.turnaround_time, 2) if self.turnaround_time is not None else None,
            "response_time": round(self.response_time, 2) if self.response_time is not None else None,
            "page_fault_count": self.page_fault_count,
            "is_paged_out": self.is_paged_out
        }
