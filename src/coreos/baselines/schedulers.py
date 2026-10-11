"""
CoReOS Conventional Baseline Schedulers
Implements non-learning, standard OS policies (FCFS, static Round Robin, Priority, and Independent Agents).
"""

from typing import Dict, Any, List, Optional
import time
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.process import SimulatedProcess
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent


class ConventionalScheduler:
    """
    Baseline A: Conventional static operating system policies.
    """

    @staticmethod
    def run_fcfs(
        processes: List[SimulatedProcess],
        config=None,
        enable_watermark_paging: bool = True,
        watermark_reclaim_mb: float = 1024.0
    ) -> Dict[str, Any]:
        """
        Baseline A (FCFS): Static FCFS CPU and I/O scheduling with standard static watermark paging.
        """
        sim = SystemSimulator(config)
        workload = [p.clone() for p in processes]
        sim.reset(workload)
        t0 = time.perf_counter()
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            reclaim_target = watermark_reclaim_mb if (enable_watermark_paging and state.get("is_under_memory_pressure", False)) else 0.0
            sim.step(dt=1.0, cpu_policy="FCFS", io_policy="FCFS", memory_reclaim_target=reclaim_target)
            step_i += 1
        overhead_ms = (time.perf_counter() - t0) * 1000.0 / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, total_processes=len(workload))

    @staticmethod
    def run_round_robin(
        processes: List[SimulatedProcess],
        quantum: float = 4.0,
        config=None,
        enable_watermark_paging: bool = True,
        watermark_reclaim_mb: float = 1024.0
    ) -> Dict[str, Any]:
        """
        Baseline A (Round Robin): Static Round Robin CPU (fixed quantum) and FCFS I/O
        with standard static watermark paging (kswapd daemon model).
        """
        sim = SystemSimulator(config)
        workload = [p.clone() for p in processes]
        sim.reset(workload)
        t0 = time.perf_counter()
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            reclaim_target = watermark_reclaim_mb if (enable_watermark_paging and state.get("is_under_memory_pressure", False)) else 0.0
            sim.step(dt=1.0, cpu_policy="ROUND_ROBIN", cpu_quantum=quantum, io_policy="FCFS", memory_reclaim_target=reclaim_target)
            step_i += 1
        overhead_ms = (time.perf_counter() - t0) * 1000.0 / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, total_processes=len(workload))


class IndependentAgentScheduler:
    """
    Baseline B: Independent CPU, Memory, and I/O agents making uncoordinated decisions.
    """

    @staticmethod
    def run(processes: List[SimulatedProcess], config=None) -> Dict[str, Any]:
        sim = SystemSimulator(config)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()

        decision_time = 0.0
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            t0 = time.perf_counter()
            cpu_act = cpu_ag.propose_action(state)
            mem_act = mem_ag.propose_action(state)
            io_act = io_ag.propose_action(state)
            decision_time += (time.perf_counter() - t0)

            sim.step(
                dt=1.0,
                cpu_policy=cpu_act.parameters.get("policy", "ROUND_ROBIN"),
                cpu_quantum=cpu_act.parameters.get("quantum", 4.0),
                io_policy=io_act.parameters.get("io_policy", "FCFS"),
                memory_reclaim_target=mem_act.parameters.get("target_free_mb", 0.0)
            )
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, total_processes=len(workload))
