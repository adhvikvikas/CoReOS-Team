"""
CoReOS Simulation: Memory Subsystem
Simulates physical memory allocation, memory pressure, paging, swap space, and thrashing.
"""

from typing import Dict, List, Optional, Tuple
from src.simulation.process import SimulatedProcess, ProcessState


class MemorySubsystem:
    def __init__(
        self,
        total_memory_mb: float = 16384.0,
        swap_capacity_mb: float = 8192.0,
        pressure_threshold: float = 0.85,
        page_fault_cost: float = 5.0
    ):
        self.total_memory_mb = total_memory_mb
        self.swap_capacity_mb = swap_capacity_mb
        self.pressure_threshold = pressure_threshold
        self.page_fault_cost = page_fault_cost

        # State tracking: pid -> allocated_mb
        self.physical_allocations: Dict[int, float] = {}
        self.swap_allocations: Dict[int, float] = {}
        
        # Telemetry
        self.total_page_faults: int = 0
        self.total_reclamations: int = 0
        self.thrashing_ticks: int = 0

    @property
    def physical_used_mb(self) -> float:
        return sum(self.physical_allocations.values())

    @property
    def physical_free_mb(self) -> float:
        return max(0.0, self.total_memory_mb - self.physical_used_mb)

    @property
    def physical_utilization_ratio(self) -> float:
        return min(1.0, self.physical_used_mb / self.total_memory_mb)

    @property
    def swap_used_mb(self) -> float:
        return sum(self.swap_allocations.values())

    @property
    def is_under_pressure(self) -> bool:
        return self.physical_utilization_ratio >= self.pressure_threshold

    @property
    def is_thrashing(self) -> bool:
        # Thrashing occurs when memory is near saturation and swap is actively engaged
        return self.physical_utilization_ratio >= 0.92 and self.swap_used_mb > 0.05 * self.swap_capacity_mb

    def allocate(self, process: SimulatedProcess) -> bool:
        """
        Attempts to allocate physical memory for a process.
        Returns True if successful, False if blocked by capacity.
        """
        demand = process.memory_demand_mb
        if process.pid in self.physical_allocations:
            return True

        if self.physical_free_mb >= demand:
            self.swap_allocations.pop(process.pid, None)
            self.physical_allocations[process.pid] = demand
            process.memory_allocated_mb = demand
            process.is_paged_out = False
            return True

        # Need to handle memory pressure: try to page out or reclaim from other processes
        return False

    def reclaim_memory(
        self,
        target_free_mb: float,
        active_processes: List[SimulatedProcess]
    ) -> float:
        """
        Reclaims memory by paging out lowest-priority or idle processes to swap.
        Returns amount of MB reclaimed.
        """
        reclaimed = 0.0
        # Sort candidates: prioritize I/O waiting processes, then lowest priority first
        candidates = sorted(
            [p for p in active_processes if p.pid in self.physical_allocations and p.state != ProcessState.RUNNING],
            key=lambda p: (
                0 if p.state == ProcessState.WAITING_IO else 1,
                p.priority,
                -self.physical_allocations.get(p.pid, 0.0)
            )
        )

        for p in candidates:
            if self.physical_free_mb >= target_free_mb:
                break
            alloc = self.physical_allocations.pop(p.pid, 0.0)
            if alloc > 0:
                self.swap_allocations[p.pid] = alloc
                p.is_paged_out = True
                p.memory_allocated_mb = 0.0
                reclaimed += alloc
                self.total_reclamations += 1

        return reclaimed

    def touch_process_memory(self, process: SimulatedProcess) -> float:
        """
        Simulates memory access when process executes.
        If paged out, incurs page fault penalty.
        Returns time penalty (in time units).
        """
        penalty = 0.0
        if process.is_paged_out or process.pid in self.swap_allocations:
            # Page fault occurs
            self.total_page_faults += 1
            process.page_fault_count += 1
            penalty += self.page_fault_cost
            
            # Swap back in if space allows
            swap_alloc = self.swap_allocations.get(process.pid, process.memory_demand_mb)
            if self.physical_free_mb >= swap_alloc:
                self.swap_allocations.pop(process.pid, None)
                self.physical_allocations[process.pid] = swap_alloc
                process.memory_allocated_mb = swap_alloc
                process.is_paged_out = False
            else:
                # Still in swap; incur heavy penalty
                self.swap_allocations[process.pid] = swap_alloc

        if self.is_thrashing:
            self.thrashing_ticks += 1
            penalty += self.page_fault_cost * 0.5

        return penalty

    def release_process(self, pid: int):
        """Frees memory when process terminates."""
        self.physical_allocations.pop(pid, None)
        self.swap_allocations.pop(pid, None)
