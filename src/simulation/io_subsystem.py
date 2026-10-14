"""
CoReOS Simulation: I/O Subsystem
Simulates disk/storage I/O queues, device latency, saturation, and scheduling.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from src.simulation.process import SimulatedProcess, ProcessState


@dataclass
class IORequest:
    process: SimulatedProcess
    remaining_io_time: float
    cylinder: int = 50                  # For disk arm simulation
    is_throttled: bool = False


class IOSubsystem:
    def __init__(
        self,
        num_channels: int = 2,
        base_latency: float = 3.0,
        queue_capacity: int = 50,
        bandwidth_mb_s: float = 250.0
    ):
        self.num_channels = num_channels
        self.base_latency = base_latency
        self.queue_capacity = queue_capacity
        self.bandwidth_mb_s = bandwidth_mb_s
        
        self.active_channels: List[Optional[IORequest]] = [None] * num_channels
        self.io_queue: List[IORequest] = []
        
        # Telemetry
        self.total_io_requests_served: int = 0
        self.total_io_wait_time: float = 0.0
        self.current_disk_head: int = 0
        self.disk_direction: int = 1     # 1 for up, -1 for down

    @property
    def queue_length(self) -> int:
        return len(self.io_queue)

    @property
    def saturation_ratio(self) -> float:
        return min(1.0, self.queue_length / self.queue_capacity)

    @property
    def is_saturated(self) -> bool:
        return self.saturation_ratio >= 0.80

    def enqueue_request(self, process: SimulatedProcess, io_time: float = 3.0, cylinder: int = 50) -> bool:
        """
        Enqueues an I/O request for the process.
        Returns True if admitted, False if queue is at capacity.
        """
        if self.queue_length >= self.queue_capacity:
            return False

        process.state = ProcessState.WAITING_IO
        req = IORequest(process=process, remaining_io_time=io_time, cylinder=cylinder)
        self.io_queue.append(req)
        return True

    def sort_io_queue(self, policy: str = "FCFS"):
        effective_policy = policy
        if policy == "SSTF" and any(req.process.total_io_wait_time >= 25.0 for req in self.io_queue):
            effective_policy = "SCAN"

        if effective_policy == "FCFS":
            pass
        elif effective_policy == "SSTF":
            # Shortest Seek Time First
            self.io_queue.sort(key=lambda r: abs(r.cylinder - self.current_disk_head))
        elif effective_policy == "SCAN":
            # Elevator algorithm
            ahead = [r for r in self.io_queue if (r.cylinder - self.current_disk_head) * self.disk_direction >= 0]
            behind = [r for r in self.io_queue if (r.cylinder - self.current_disk_head) * self.disk_direction < 0]
            ahead.sort(key=lambda r: (r.cylinder - self.current_disk_head) * self.disk_direction)
            behind.sort(key=lambda r: -(r.cylinder - self.current_disk_head) * self.disk_direction)
            self.io_queue = ahead + behind

    def step(self, dt: float, policy: str = "FCFS") -> List[SimulatedProcess]:
        """
        Advances I/O channels by dt time units.
        Returns list of processes that completed I/O.
        """
        completed = []
        self.sort_io_queue(policy)

        # Track queue wait time for processes waiting in line
        for req in self.io_queue:
            req.process.total_io_wait_time += dt
            self.total_io_wait_time += dt

        # Service active channels
        for ch in range(self.num_channels):
            active_req = self.active_channels[ch]

            # If channel is idle, pull from queue
            if active_req is None and self.io_queue:
                active_req = self.io_queue.pop(0)
                self.active_channels[ch] = active_req
                self.current_disk_head = active_req.cylinder

            if active_req is not None:
                # Contention-adjusted service rate
                contention_multiplier = 1.0 + (self.saturation_ratio * 0.5)
                effective_dt = dt / contention_multiplier
                active_req.remaining_io_time -= effective_dt

                if active_req.remaining_io_time <= 1e-6:
                    # I/O completed
                    proc = active_req.process
                    proc.state = ProcessState.READY
                    completed.append(proc)
                    self.active_channels[ch] = None
                    self.total_io_requests_served += 1

        return completed
