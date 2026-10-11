"""
CoReOS Ablation Study Runner
Systematically evaluates the contribution of individual architecture components:
- Conflict Prediction Module (Ablation: On vs Off)
- Machine Learning Fusion (Ablation: Rule-Only vs Rule+ML)
- Self-Healing Module (Ablation: On vs Off)
- Feedback Mechanism (Ablation: Dynamic Sensitivity vs Static Threshold)
"""

import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np

# Ensure project root in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.config import SimulationConfig, ConflictConfig, SelfHealingConfig, get_standard_seeds, STANDARD_SEEDS
from src.simulation.simulator import SystemSimulator
from src.simulation.workload_generator import WorkloadGenerator
from src.agents.cpu_agent import CPUAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.io_agent import IOAgent
from src.conflict_prediction.conflict_engine import ConflictEngine
from src.coordination.coordination_agent import CoordinationAgent
from src.self_healing.regression_detector import PerformanceRegressionDetector
from src.self_healing.recovery_engine import RecoveryEngine
from src.self_healing.feedback_mechanism import FeedbackMechanism
from src.evaluation.metrics import compute_simulation_benchmark_summary


class AblationRunner:
    def __init__(self, seed: int = 42):
        self.seed = seed
        self.workload_gen = WorkloadGenerator(seed=seed)

    def run_ablation_trial(
        self,
        processes,
        enable_conflict_prediction: bool,
        use_ml_conflict: bool,
        enable_self_healing: bool,
        enable_feedback: bool,
        enable_coordination: bool = True,
        sim_seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Runs a single simulation under specified ablation flags."""
        seed = sim_seed if sim_seed is not None else self.seed
        sim = SystemSimulator(SimulationConfig(random_seed=seed))
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()

        conflict_engine = ConflictEngine(use_ml=use_ml_conflict)
        coord_ag = CoordinationAgent(
            conflict_engine=conflict_engine,
            enable_conflict_prediction=enable_conflict_prediction,
            enable_coordination=enable_coordination
        )
        detector = PerformanceRegressionDetector()
        recovery_eng = RecoveryEngine()
        feedback = FeedbackMechanism(conflict_engine)

        step_idx = 0
        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, prediction = coord_ag.coordinate(state, props)

            reg_event = None
            if enable_self_healing:
                reg_event = detector.observe_and_detect(state)
                detector.record_decision(decision)
                if reg_event is not None:
                    overrides = recovery_eng.select_corrective_action(reg_event, step_idx, state)
                    if overrides:
                        decision.update(overrides)

            if enable_feedback:
                feedback.process_feedback(prediction, reg_event, step_idx)

            if enable_self_healing:
                recovery_eng.track_recovery_progress(step_idx, state)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_idx += 1

        summary = compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            conflict_metrics=conflict_engine.get_metrics(),
            healing_metrics=recovery_eng.get_metrics(),
            total_processes=len(workload)
        )
        return summary

    def run_full_ablation_grid(
        self,
        workload_types: List[str] = None,
        num_seeds: int = 3,
        seeds: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Runs full ablation grid with standardized seeds across configurations:
        1. Full CoReOS (All enabled)
        2. No Self-Healing (Prediction Only)
        3. No Conflict Prediction (Healing Only)
        4. Rule-Only Conflict Prediction (No ML)
        5. No Feedback Tuning (Static Threshold)
        6. Baseline (Neither Prediction nor Healing, Uncoordinated)
        """
        workloads = workload_types or ["adversarial_stress", "memory_thrashing"]
        seeds_list = get_standard_seeds(num_seeds=num_seeds, explicit_seeds=seeds)
        configurations = {
            "Full_CoReOS": {
                "enable_coordination": True,
                "enable_conflict_prediction": True, "use_ml_conflict": True,
                "enable_self_healing": True, "enable_feedback": True
            },
            "No_Self_Healing": {
                "enable_coordination": True,
                "enable_conflict_prediction": True, "use_ml_conflict": True,
                "enable_self_healing": False, "enable_feedback": False
            },
            "No_Conflict_Prediction": {
                "enable_coordination": True,
                "enable_conflict_prediction": False, "use_ml_conflict": False,
                "enable_self_healing": True, "enable_feedback": False
            },
            "Rule_Only_Conflict": {
                "enable_coordination": True,
                "enable_conflict_prediction": True, "use_ml_conflict": False,
                "enable_self_healing": True, "enable_feedback": True
            },
            "No_Feedback_Tuning": {
                "enable_coordination": True,
                "enable_conflict_prediction": True, "use_ml_conflict": True,
                "enable_self_healing": True, "enable_feedback": False
            },
            "Uncoordinated_Baseline": {
                "enable_coordination": False,
                "enable_conflict_prediction": False, "use_ml_conflict": False,
                "enable_self_healing": False, "enable_feedback": False
            }
        }

        results = []
        for w_type in workloads:
            for s in seeds_list:
                # Set exact reproducible seed without arbitrary offsets
                self.workload_gen.set_seed(s)
                procs = self.workload_gen.generate_workload(num_processes=40, workload_type=w_type)

                for config_name, flags in configurations.items():
                    metrics = self.run_ablation_trial(procs, sim_seed=s, **flags)
                    results.append({
                        "configuration": config_name,
                        "workload": w_type,
                        "seed": s,
                        "total_processes": metrics["total_processes"],
                        "completed_processes": metrics["completed_processes"],
                        "unfinished_processes": metrics["unfinished_processes"],
                        "completion_rate": metrics["completion_rate"],
                        "avg_turnaround_time": metrics["avg_turnaround_time"],
                        "avg_waiting_time": metrics["avg_waiting_time"],
                        "throughput": metrics["throughput"],
                        "jains_fairness": metrics["jains_fairness_index"],
                        "thrashing_ticks": metrics["thrashing_ticks"]
                    })

        return pd.DataFrame(results)


if __name__ == "__main__":
    runner = AblationRunner()
    df = runner.run_full_ablation_grid(workload_types=["adversarial_stress"], num_seeds=2)
    print("\nAblation Grid Results (Mean):")
    print(df.groupby("configuration")[["avg_turnaround_time", "throughput", "thrashing_ticks"]].mean())
