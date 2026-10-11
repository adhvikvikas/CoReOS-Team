"""
CoReOS Standalone Simulation Execution Script
Allows CLI execution of individual simulation runs under customizable policies and workloads.
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import load_config
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism


def main():
    parser = argparse.ArgumentParser(description="CoReOS Simulation Runner")
    parser.add_argument("--workload", type=str, default="adversarial_stress",
                        choices=["steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "mixed", "adversarial_stress"])
    parser.add_argument("--processes", type=int, default=40, help="Number of simulated processes")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--mode", type=str, default="coreos",
                        choices=["coreos", "conventional", "independent", "no_conflict"])
    args = parser.parse_args()

    config = load_config()
    config.simulation.random_seed = args.seed
    sim = SystemSimulator(config.simulation)
    gen = WorkloadGenerator(seed=args.seed)
    processes = gen.generate_workload(num_processes=args.processes, workload_type=args.workload)
    sim.reset(processes)

    cpu_ag = CPUAgent()
    mem_ag = MemoryAgent()
    io_ag = IOAgent()
    conflict_engine = ConflictEngine(use_ml=True)
    coord_ag = CoordinationAgent(conflict_engine, enable_conflict_prediction=(args.mode == "coreos"))
    detector = PerformanceRegressionDetector(config.healing)
    recovery = RecoveryEngine(config.healing)
    feedback = FeedbackMechanism(conflict_engine)

    print(f"=== CoReOS Simulation: Mode={args.mode.upper()}, Workload={args.workload}, Procs={args.processes}, Seed={args.seed} ===")

    step_idx = 0
    while not sim.is_done() and step_idx < 300:
        state = sim.get_system_state()

        if args.mode == "conventional":
            reclaim_target = 1024.0 if state.get("is_under_memory_pressure", False) else 0.0
            sim.step(dt=1.0, cpu_policy="ROUND_ROBIN", cpu_quantum=4.0, io_policy="FCFS", memory_reclaim_target=reclaim_target)
        elif args.mode == "independent":
            c = cpu_ag.propose_action(state)
            m = mem_ag.propose_action(state)
            i = io_ag.propose_action(state)
            sim.step(
                dt=1.0,
                cpu_policy=c.parameters.get("policy", "ROUND_ROBIN"),
                cpu_quantum=c.parameters.get("quantum", 4.0),
                io_policy=i.parameters.get("io_policy", "FCFS"),
                memory_reclaim_target=m.parameters.get("target_free_mb", 0.0)
            )
        else:  # coreos or no_conflict
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, pred = coord_ag.coordinate(state, props)
            if args.mode == "coreos":
                reg = detector.observe_and_detect(state)
                detector.record_decision(decision)
                if reg:
                    ov = recovery.select_corrective_action(reg, step_idx, state)
                    if ov:
                        decision.update(ov)
                feedback.process_feedback(pred, reg, step_idx)
                recovery.track_recovery_progress(step_idx, state)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )

        step_idx += 1

    final_state = sim.get_system_state()
    total_procs = getattr(sim, "total_processes", args.processes)
    completed_procs = final_state.get('completed_processes_count', len(sim.completed_processes))
    unfinished_procs = max(0, total_procs - completed_procs)
    completion_rate = (completed_procs / total_procs) * 100.0 if total_procs > 0 else 0.0
    thrashing_ticks = sum(1 for h in sim.history if h.get("is_thrashing", False))
    print("\n--- Simulation Complete ---")
    print(f"Total Workload Processes: {total_procs}")
    print(f"Completed Jobs: {completed_procs}/{total_procs} ({completion_rate:.1f}%)")
    print(f"Unfinished Jobs: {unfinished_procs}")
    print(f"Completion Rate: {completion_rate:.2f}%")
    print(f"Total Time Units: {final_state['time']}")
    print(f"Average Turnaround Time (completed jobs only): {final_state['avg_turnaround_time']}")
    print(f"Average Waiting Time (completed jobs only): {final_state['avg_waiting_time']}")
    print(f"Throughput: {final_state['throughput']} jobs/unit time")
    print(f"Total Context Switches: {final_state['total_context_switches']}")
    print(f"Total Page Faults: {final_state['total_page_faults']}")
    print(f"Thrashing Ticks: {thrashing_ticks}")


if __name__ == "__main__":
    main()
