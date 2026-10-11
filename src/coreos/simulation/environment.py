"""
CoReOS Discrete-Event OS Simulation Environment
Orchestrates simulated CPU cores, physical memory, paging/swap, and storage channels.
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from src.coreos.config import SimulationConfig
from src.coreos.simulation.process import SimulatedProcess, ProcessState


class CPUSubsystem:
    def __init__(self, num_cores: int = 4, context_switch_penalty: float = 0.5, default_quantum: float = 4.0):
        self.num_cores = num_cores
        self.context_switch_penalty = context_switch_penalty
        self.default_quantum = default_quantum
        
        self.cores: List[Optional[SimulatedProcess]] = [None] * num_cores
        self.core_time_in_quantum: List[float] = [0.0] * num_cores
        self.ready_queue: List[SimulatedProcess] = []
        
        self.total_context_switches: int = 0
        self.total_busy_time: float = 0.0
        self.total_idle_time: float = 0.0

    @property
    def ready_queue_length(self) -> int:
        return len(self.ready_queue)

    @property
    def active_core_count(self) -> int:
        return sum(1 for c in self.cores if c is not None)

    @property
    def utilization_percentage(self) -> float:
        return (self.active_core_count / self.num_cores) * 100.0

    def enqueue_ready(self, process: SimulatedProcess):
        process.state = ProcessState.READY
        self.ready_queue.append(process)

    def sort_ready_queue(self, policy: str):
        if policy == "FCFS":
            self.ready_queue.sort(key=lambda p: p.arrival_time)
        elif policy == "PRIORITY":
            self.ready_queue.sort(key=lambda p: (-p.priority, p.arrival_time))
        elif policy == "SRTF":
            self.ready_queue.sort(key=lambda p: (p.remaining_burst, p.arrival_time))
        elif policy == "ROUND_ROBIN":
            pass

    def schedule_next(self, policy: str = "ROUND_ROBIN", current_time: float = 0.0):
        self.sort_ready_queue(policy)
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

    def step(
        self,
        dt: float,
        policy: str = "ROUND_ROBIN",
        quantum: Optional[float] = None,
        current_time: float = 0.0,
        slowdown_factor: float = 1.0
    ) -> Tuple[List[SimulatedProcess], List[SimulatedProcess]]:
        effective_quantum = quantum if quantum is not None else self.default_quantum
        finished = []
        yielded = []

        for proc in self.ready_queue:
            proc.total_waiting_time += dt

        for core_id in range(self.num_cores):
            proc = self.cores[core_id]
            if proc is None:
                self.total_idle_time += dt
                continue

            self.total_busy_time += dt
            effective_dt = dt / max(1.0, slowdown_factor)
            exec_time = min(effective_dt, proc.remaining_burst)
            proc.remaining_burst -= exec_time
            self.core_time_in_quantum[core_id] += exec_time

            if proc.remaining_burst <= 1e-6:
                proc.remaining_burst = 0.0
                proc.completion_time = current_time
                proc.state = ProcessState.TERMINATED
                finished.append(proc)
                self.cores[core_id] = None
                self.core_time_in_quantum[core_id] = 0.0

            elif policy == "ROUND_ROBIN" and self.core_time_in_quantum[core_id] >= effective_quantum:
                proc.state = ProcessState.READY
                yielded.append(proc)
                self.cores[core_id] = None
                self.core_time_in_quantum[core_id] = 0.0

        self.schedule_next(policy, current_time + dt)
        return finished, yielded

    def preempt_core(self, core_id: int):
        if 0 <= core_id < self.num_cores and self.cores[core_id] is not None:
            proc = self.cores[core_id]
            proc.state = ProcessState.READY
            self.cores[core_id] = None
            self.core_time_in_quantum[core_id] = 0.0
            self.ready_queue.insert(0, proc)
            self.total_context_switches += 1
            proc.context_switch_count += 1


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

        self.physical_allocations: Dict[int, float] = {}
        self.swap_allocations: Dict[int, float] = {}
        self.total_page_faults: int = 0
        self.total_reclamations: int = 0

    @property
    def physical_used_mb(self) -> float:
        return sum(self.physical_allocations.values())

    @property
    def physical_free_mb(self) -> float:
        return max(0.0, self.total_memory_mb - self.physical_used_mb)

    @property
    def utilization_ratio(self) -> float:
        return min(1.0, self.physical_used_mb / self.total_memory_mb)

    @property
    def swap_used_mb(self) -> float:
        return sum(self.swap_allocations.values())

    @property
    def is_under_pressure(self) -> bool:
        return self.utilization_ratio >= self.pressure_threshold

    @property
    def is_thrashing(self) -> bool:
        return self.utilization_ratio >= 0.92 and self.swap_used_mb > 0.05 * self.swap_capacity_mb

    def allocate(self, process: SimulatedProcess) -> bool:
        demand = process.memory_demand_mb
        if process.pid in self.physical_allocations:
            return True

        if self.physical_free_mb >= demand:
            self.swap_allocations.pop(process.pid, None)
            self.physical_allocations[process.pid] = demand
            process.memory_allocated_mb = demand
            process.is_paged_out = False
            return True
        return False

    def reclaim_memory(self, target_free_mb: float, active_processes: List[SimulatedProcess]) -> float:
        reclaimed = 0.0
        candidates = sorted(
            [p for p in active_processes if p.pid in self.physical_allocations and p.state != ProcessState.RUNNING],
            key=lambda p: (p.priority, -self.physical_allocations.get(p.pid, 0.0))
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
        penalty = 0.0
        if process.is_paged_out or process.pid in self.swap_allocations:
            self.total_page_faults += 1
            process.page_fault_count += 1
            penalty += self.page_fault_cost
            alloc = self.swap_allocations.get(process.pid, process.memory_demand_mb)
            if self.physical_free_mb >= alloc:
                self.swap_allocations.pop(process.pid, None)
                self.physical_allocations[process.pid] = alloc
                process.memory_allocated_mb = alloc
                process.is_paged_out = False
            else:
                self.swap_allocations[process.pid] = alloc

        if self.is_thrashing:
            penalty += self.page_fault_cost * 0.5

        return penalty

    def release_process(self, pid: int):
        self.physical_allocations.pop(pid, None)
        self.swap_allocations.pop(pid, None)


class IOSubsystem:
    def __init__(self, num_channels: int = 2, base_latency: float = 3.0, queue_capacity: int = 50, bandwidth_mb_s: float = 250.0):
        self.num_channels = num_channels
        self.base_latency = base_latency
        self.queue_capacity = queue_capacity
        self.bandwidth_mb_s = bandwidth_mb_s

        self.active_channels: List[Optional[Tuple[SimulatedProcess, float, int]]] = [None] * num_channels
        self.io_queue: List[Tuple[SimulatedProcess, float, int]] = []
        self.current_disk_head: int = 0
        self.disk_direction: int = 1
        self.total_io_requests: int = 0

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
        if self.queue_length >= self.queue_capacity:
            return False
        process.state = ProcessState.WAITING_IO
        self.io_queue.append((process, io_time, cylinder))
        self.total_io_requests += 1
        return True

    def sort_io_queue(self, policy: str):
        if policy == "SSTF":
            self.io_queue.sort(key=lambda item: abs(item[2] - self.current_disk_head))
        elif policy == "SCAN":
            ahead = [r for r in self.io_queue if (r[2] - self.current_disk_head) * self.disk_direction >= 0]
            behind = [r for r in self.io_queue if (r[2] - self.current_disk_head) * self.disk_direction < 0]
            ahead.sort(key=lambda r: (r[2] - self.current_disk_head) * self.disk_direction)
            behind.sort(key=lambda r: -(r[2] - self.current_disk_head) * self.disk_direction)
            self.io_queue = ahead + behind

    def step(self, dt: float, policy: str = "FCFS") -> List[SimulatedProcess]:
        completed = []
        self.sort_io_queue(policy)

        for proc, _, _ in self.io_queue:
            proc.total_io_wait_time += dt

        for ch in range(self.num_channels):
            active = self.active_channels[ch]
            if active is None and self.io_queue:
                active = self.io_queue.pop(0)
                self.active_channels[ch] = active
                self.current_disk_head = active[2]

            if active is not None:
                proc, rem_time, cyl = active
                contention = 1.0 + (self.saturation_ratio * 0.5)
                effective_dt = dt / contention
                new_rem = rem_time - effective_dt

                if new_rem <= 1e-6:
                    proc.state = ProcessState.READY
                    completed.append(proc)
                    self.active_channels[ch] = None
                else:
                    self.active_channels[ch] = (proc, new_rem, cyl)

        return completed


class SystemSimulator:
    """
    Master Discrete-Event OS Simulation Engine for CoReOS.
    """

    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
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

        self.current_time: float = 0.0
        self.pending_arrivals: List[SimulatedProcess] = []
        self.waiting_memory_queue: List[SimulatedProcess] = []
        self.active_processes: Dict[int, SimulatedProcess] = {}
        self.completed_processes: List[SimulatedProcess] = []
        self.total_processes: int = 0
        self.history: List[Dict[str, Any]] = []
        self.rng = np.random.RandomState(self.config.random_seed)

    def reset(self, processes: Optional[List[SimulatedProcess]] = None):
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
        cnt = len(self.completed_processes)
        total_p = getattr(self, "total_processes", cnt)
        unfinished_cnt = max(0, total_p - cnt)
        comp_rate = round(cnt / total_p * 100.0, 2) if total_p > 0 else 0.0
        avg_wait = float(np.mean([p.total_waiting_time for p in self.completed_processes])) if cnt > 0 else 0.0
        avg_turnaround = float(np.mean([p.turnaround_time for p in self.completed_processes if p.turnaround_time is not None])) if cnt > 0 else 0.0
        throughput = float(cnt / self.current_time) if self.current_time > 0 else 0.0

        return {
            "time": round(self.current_time, 2),
            "cpu_utilization": round(self.cpu.utilization_percentage, 2),
            "memory_utilization": round(self.memory.utilization_ratio * 100.0, 2),
            "memory_used_mb": round(self.memory.physical_used_mb, 2),
            "swap_used_mb": round(self.memory.swap_used_mb, 2),
            "io_queue_length": self.io.queue_length,
            "io_saturation": round(self.io.saturation_ratio * 100.0, 2),
            "ready_queue_length": self.cpu.ready_queue_length,
            "waiting_memory_count": len(self.waiting_memory_queue),
            "active_processes_count": len(self.active_processes),
            "total_processes": total_p,
            "completed_processes_count": cnt,
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
        while self.pending_arrivals and self.pending_arrivals[0].arrival_time <= self.current_time:
            proc = self.pending_arrivals.pop(0)
            self.active_processes[proc.pid] = proc
            if self.memory.allocate(proc):
                self.cpu.enqueue_ready(proc)
            else:
                proc.state = ProcessState.WAITING_MEMORY
                self.waiting_memory_queue.append(proc)

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
        self.current_time += dt

        self._admit_new_processes()

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

        finished_procs, yielded_procs = self.cpu.step(
            dt=dt,
            policy=cpu_policy,
            quantum=cpu_quantum,
            current_time=self.current_time,
            slowdown_factor=slowdown
        )

        for proc in finished_procs:
            self.memory.release_process(proc.pid)
            self.completed_processes.append(proc)
            self.active_processes.pop(proc.pid, None)

        for proc in yielded_procs:
            if proc.remaining_burst > 0.0:
                if self.rng.uniform(0.0, 1.0) < proc.io_frequency:
                    admitted = self.io.enqueue_request(
                        process=proc,
                        io_time=proc.io_burst_time,
                        cylinder=int(self.rng.randint(0, 100))
                    )
                    if not admitted:
                        self.cpu.enqueue_ready(proc)
                else:
                    self.cpu.enqueue_ready(proc)

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

        state = self.get_system_state()
        self.history.append(state)
        return state

    def is_done(self) -> bool:
        return (
            len(self.pending_arrivals) == 0 and
            len(self.active_processes) == 0 and
            self.cpu.ready_queue_length == 0 and
            self.io.queue_length == 0 and
            self.cpu.active_core_count == 0
        )
