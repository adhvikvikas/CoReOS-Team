"""
CoReOS Simulation Engine
Discrete-event operating system simulation orchestrating CPU, Memory, and I/O subsystems.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from src.config import SimulationConfig
from src.simulation.process import SimulatedProcess, ProcessState
from src.simulation.cpu_subsystem import CPUSubsystem
from src.simulation.memory_subsystem import MemorySubsystem
from src.simulation.io_subsystem import IOSubsystem


class SystemSimulator:
    """
    Core Discrete-Event Simulation Engine for CoReOS.
    Executes simulated process scheduling, memory allocation, and I/O handling.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        
        # Subsystems
        self.cpu = CPUSubsystem(
            num_cores=self.config.cpu_cores,
            context_switch_penalty=self.config.context_switch_penalty,
            default_quantum=self.config.default_quantum
        )
        self.memory = MemorySubsystem(
            total_memory_mb=self.config.total_memory_mb,
            swap_capacity_mb=self.config.swap_capacity_mb,
            pressure_threshold=self.config.memory_pressure_threshold,
            page_fault_cost=self.config.page_fault_cost
        )
        self.io = IOSubsystem(
            num_channels=self.config.io_channels,
            base_latency=self.config.base_io_latency,
            queue_capacity=self.config.io_queue_capacity,
            bandwidth_mb_s=self.config.io_bandwidth_mb_per_s
        )

        # Simulation clock and queues
        self.current_time: float = 0.0
        self.pending_arrivals: List[SimulatedProcess] = []
        self.waiting_memory_queue: List[SimulatedProcess] = []
        self.active_processes: Dict[int, SimulatedProcess] = {}
        self.completed_processes: List[SimulatedProcess] = []
        self.total_processes: int = 0

        # Step history for metrics, regressions, and analytics
        self.history: List[Dict[str, Any]] = []
        self.rng = np.random.RandomState(self.config.random_seed)

    def reset(self, processes: Optional[List[SimulatedProcess]] = None):
        """Resets simulation state with a new process workload."""
        self.current_time = 0.0
        self.cpu = CPUSubsystem(
            num_cores=self.config.cpu_cores,
            context_switch_penalty=self.config.context_switch_penalty,
            default_quantum=self.config.default_quantum
        )
        self.memory = MemorySubsystem(
            total_memory_mb=self.config.total_memory_mb,
            swap_capacity_mb=self.config.swap_capacity_mb,
            pressure_threshold=self.config.memory_pressure_threshold,
            page_fault_cost=self.config.page_fault_cost
        )
        self.io = IOSubsystem(
            num_channels=self.config.io_channels,
            base_latency=self.config.base_io_latency,
            queue_capacity=self.config.io_queue_capacity,
            bandwidth_mb_s=self.config.io_bandwidth_mb_per_s
        )
        self.waiting_memory_queue.clear()
        self.active_processes.clear()
        self.completed_processes.clear()
        self.history.clear()
        self.rng = np.random.RandomState(self.config.random_seed)

        if processes:
            self.total_processes = len(processes)
            self.pending_arrivals = sorted(processes, key=lambda p: p.arrival_time)
        else:
            self.total_processes = 0
            self.pending_arrivals = []

    def get_system_state(self) -> Dict[str, Any]:
        """Returns instantaneous system observation snapshot."""
        completed_cnt = len(self.completed_processes)
        total_p = getattr(self, "total_processes", completed_cnt)
        unfinished_cnt = max(0, total_p - completed_cnt)
        comp_rate = round(completed_cnt / total_p * 100.0, 2) if total_p > 0 else 0.0
        avg_wait = (
            float(np.mean([p.total_waiting_time for p in self.completed_processes]))
            if completed_cnt > 0 else 0.0
        )
        avg_turnaround = (
            float(np.mean([p.turnaround_time for p in self.completed_processes if p.turnaround_time is not None]))
            if completed_cnt > 0 else 0.0
        )
        throughput = (
            completed_cnt / self.current_time
            if self.current_time > 0 else 0.0
        )

        return {
            "time": round(self.current_time, 2),
            "cpu_utilization": round(self.cpu.instantaneous_utilization, 2),
            "memory_utilization": round(self.memory.physical_utilization_ratio * 100.0, 2),
            "memory_used_mb": round(self.memory.physical_used_mb, 2),
            "swap_used_mb": round(self.memory.swap_used_mb, 2),
            "io_queue_length": self.io.queue_length,
            "io_saturation": round(self.io.saturation_ratio * 100.0, 2),
            "ready_queue_length": self.cpu.ready_queue_length,
            "waiting_memory_count": len(self.waiting_memory_queue),
            "active_processes_count": len(self.active_processes),
            "total_processes": total_p,
            "completed_processes_count": completed_cnt,
            "unfinished_processes_count": unfinished_cnt,
            "completion_rate": comp_rate,
            "total_context_switches": self.cpu.total_context_switches,
            "total_page_faults": self.memory.total_page_faults,
            "is_under_memory_pressure": self.memory.is_under_pressure,
            "is_thrashing": self.memory.is_thrashing,
            "is_io_saturated": self.io.is_saturated,
            "avg_waiting_time": round(avg_wait, 2),
            "avg_turnaround_time": round(avg_turnaround, 2),
            "throughput": round(throughput, 4)
        }

    def _admit_new_processes(self):
        """Admits arriving processes whose arrival_time <= current_time."""
        while self.pending_arrivals and self.pending_arrivals[0].arrival_time <= self.current_time:
            proc = self.pending_arrivals.pop(0)
            self.active_processes[proc.pid] = proc

            # Attempt initial memory allocation
            if self.memory.allocate(proc):
                self.cpu.enqueue_ready(proc)
            else:
                proc.state = ProcessState.WAITING_MEMORY
                self.waiting_memory_queue.append(proc)

        # Try to admit waiting memory processes if space freed up
        still_waiting = []
        for proc in self.waiting_memory_queue:
            if self.memory.allocate(proc):
                self.cpu.enqueue_ready(proc)
            else:
                still_waiting.append(proc)
        self.waiting_memory_queue = still_waiting

    def step(
        self,
        dt: float = 1.0,
        cpu_policy: str = "ROUND_ROBIN",
        cpu_quantum: Optional[float] = None,
        io_policy: str = "FCFS",
        memory_reclaim_target: float = 0.0
    ) -> Dict[str, Any]:
        """
        Advances the simulation by dt time units.
        """
        self.current_time += dt

        for proc in self.waiting_memory_queue:
            proc.total_waiting_time += dt

        # 1. Admit new process arrivals
        self._admit_new_processes()

        # 2. Check for memory reclamation if requested by MemoryAgent
        if memory_reclaim_target > 0.0:
            active_list = list(self.active_processes.values())
            self.memory.reclaim_memory(memory_reclaim_target, active_list)
            # Reclaimed processes that are paged out must wait for memory before scheduling
            for proc in active_list:
                if proc.is_paged_out and proc.state == ProcessState.READY:
                    if proc in self.cpu.ready_queue:
                        self.cpu.ready_queue.remove(proc)
                    proc.state = ProcessState.WAITING_MEMORY
                    if proc not in self.waiting_memory_queue:
                        self.waiting_memory_queue.append(proc)

        # 3. Handle memory access for running processes (detect page faults / thrashing)
        for core_id, proc in enumerate(self.cpu.cores):
            if proc is not None:
                penalty = self.memory.touch_process_memory(proc)
                if proc.is_paged_out or proc.pid not in self.memory.physical_allocations:
                    # Memory could not be allocated; process must wait for memory
                    proc.state = ProcessState.WAITING_MEMORY
                    self.waiting_memory_queue.append(proc)
                    self.cpu.cores[core_id] = None
                    self.cpu.core_time_in_quantum[core_id] = 0.0
                    self.cpu.total_context_switches += 1
                    proc.context_switch_count += 1
                elif penalty > 0.0:
                    proc.total_waiting_time += penalty

        # If any cores were vacated by processes waiting for memory, schedule available ready processes
        self.cpu.schedule_next(policy=cpu_policy, current_time=self.current_time)

        # Thrashing causes execution slowdown (paging overhead), not total execution stall
        slowdown = 2.0 if self.memory.is_thrashing else 1.0

        # 4. Advance CPU execution
        finished_procs, yielded_procs = self.cpu.step(
            dt=dt,
            policy=cpu_policy,
            quantum=cpu_quantum,
            current_time=self.current_time,
            slowdown_factor=slowdown
        )

        # 5. Handle finished processes (release resources)
        for proc in finished_procs:
            self.memory.release_process(proc.pid)
            self.completed_processes.append(proc)
            self.active_processes.pop(proc.pid, None)

        # 6. Check yielded processes: do they need I/O or return to CPU ready queue?
        for proc in yielded_procs:
            if proc.remaining_burst > 0.0:
                # Stochastic check if process needs I/O burst
                if self.rng.uniform(0.0, 1.0) < proc.io_frequency:
                    admitted = self.io.enqueue_request(
                        process=proc,
                        io_time=proc.io_burst_time,
                        cylinder=int(self.rng.randint(0, 100))
                    )
                    if not admitted:
                        # I/O queue full: returns to CPU ready queue
                        self.cpu.enqueue_ready(proc)
                else:
                    self.cpu.enqueue_ready(proc)

        # 7. Advance I/O subsystem
        io_finished_procs = self.io.step(dt=dt, policy=io_policy)
        for proc in io_finished_procs:
            if proc.remaining_burst > 0.0:
                self.cpu.enqueue_ready(proc)
            else:
                proc.state = ProcessState.TERMINATED
                proc.completion_time = self.current_time
                self.memory.release_process(proc.pid)
                self.completed_processes.append(proc)
                self.active_processes.pop(proc.pid, None)

        # 8. Record snapshot
        state = self.get_system_state()
        self.history.append(state)
        return state

    def is_done(self) -> bool:
        """Returns True when all workloads have terminated and queues are empty."""
        return (
            len(self.pending_arrivals) == 0 and
            len(self.active_processes) == 0 and
            self.cpu.ready_queue_length == 0 and
            self.io.queue_length == 0 and
            self.cpu.active_core_count == 0
        )
