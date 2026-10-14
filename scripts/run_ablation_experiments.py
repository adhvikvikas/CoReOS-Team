"""
Phase 4: Systematic Ablation Study
Evaluates component ablations of Champion CoReOS on 15 Validation Seeds [2101..2115]
across all 6 workloads to isolate the marginal value of each architectural component.
"""

import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import CoReOSConfig, SimulationConfig
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.metrics import compute_simulation_metrics

from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism

from src.coreos.optimization.candidates import (
    AdaptiveCoordinationAgent,
    ProportionalRecoveryEngine,
    WorkloadAwareCPUAgent,
    WorkloadAwareIOAgent,
    CalibratedConflictEngine,
    ChampionCoReOS
)

VALIDATION_SEEDS = list(range(2101, 2116))
WORKLOADS = [
    "steady_state",
    "cpu_spike",
    "memory_thrashing",
    "io_bottleneck",
    "mixed",
    "adversarial_stress"
]


def compute_composite_score(m: dict) -> float:
    comp = m["completion_rate"] / 100.0
    thru = min(1.0, m["throughput"] / 0.25)
    pt = max(0.0, 1.0 - (m.get("penalized_turnaround_time", m["avg_turnaround_time"]) - 5.0) / 295.0)
    thrash = max(0.0, 1.0 - m["thrashing_ticks"] / 150.0)
    fair = max(0.0, min(1.0, m.get("jains_fairness_index", m.get("jains_fairness", 1.0))))
    return 100.0 * (0.30 * comp + 0.25 * thru + 0.20 * pt + 0.15 * thrash + 0.10 * fair)


def run_custom_pipeline(
    processes,
    cpu_ag,
    mem_ag,
    io_ag,
    coord,
    engine,
    detector,
    recovery,
    feedback,
    seed,
    max_steps=300
):
    sim = SystemSimulator(SimulationConfig(random_seed=seed))
    workload = [p.clone() for p in processes]
    sim.reset(workload)

    decision_time = 0.0
    step_i = 0
    while not sim.is_done() and step_i < max_steps:
        state = sim.get_system_state()
        t0 = time.perf_counter()

        props = {
            "CPU_AGENT": cpu_ag.propose_action(state),
            "MEMORY_AGENT": mem_ag.propose_action(state),
            "IO_AGENT": io_ag.propose_action(state)
        }
        decision, prediction = coord.coordinate(state, props)

        reg_event = detector.observe_and_detect(state) if detector else None
        if detector:
            detector.record_decision(decision)

        if reg_event is not None and recovery:
            overrides = recovery.select_corrective_action(reg_event, step_i, state)
            if overrides:
                decision.update(overrides)

        if feedback and prediction:
            feedback.process_feedback(prediction, reg_event, step_i)
        if recovery:
            recovery.track_recovery_progress(step_i, state)

        decision_time += (time.perf_counter() - t0)

        sim.step(
            dt=1.0,
            cpu_policy=decision["cpu_policy"],
            cpu_quantum=decision["cpu_quantum"],
            io_policy=decision["io_policy"],
            memory_reclaim_target=decision["memory_reclaim_target"]
        )
        step_i += 1

    overhead_ms = (decision_time * 1000.0) / max(1, step_i)
    c_m = engine.get_metrics() if engine else {}
    h_m = recovery.get_metrics() if recovery else {}
    return compute_simulation_metrics(
        sim.completed_processes,
        sim.history,
        overhead_ms,
        conflict_metrics=c_m,
        healing_metrics=h_m,
        total_processes=len(workload)
    )


def run_ablation_experiments():
    print("=" * 80)
    print("Phase 4: Systematic Ablation Experiments (15 Validation Seeds [2101..2115])")
    print("=" * 80)

    config = CoReOSConfig()
    workload_gen = WorkloadGenerator(seed=42)
    records = []

    for w_type in WORKLOADS:
        print(f"\n---> Evaluating Workload: {w_type} (15 validation seeds)")
        for s in VALIDATION_SEEDS:
            workload_gen.set_seed(s)
            procs = workload_gen.generate_workload(num_processes=40, workload_type=w_type)

            runs = {}

            # 1. Full Champion CoReOS (All components enabled)
            champ = ChampionCoReOS(config)
            runs["Champion_Full"] = champ.run_simulation(procs, seed=s, max_steps=300)

            # 2. Ablation 1: Minus Progress Scheduling (Revert CPU agent to pure Round Robin)
            eng_a1 = CalibratedConflictEngine(use_ml=True)
            runs["Ablation_MinusProgressScheduling"] = run_pipeline_a1 = run_custom_pipeline(
                procs,
                CPUAgent(), MemoryAgent(), WorkloadAwareIOAgent(),
                AdaptiveCoordinationAgent(conflict_engine=eng_a1, enable_conflict_prediction=True),
                eng_a1,
                PerformanceRegressionDetector(config.healing),
                ProportionalRecoveryEngine(config.healing),
                FeedbackMechanism(eng_a1),
                seed=s
            )

            # 3. Ablation 2: Minus Adaptive Arbitration (Revert coordinator to standard CoordinationAgent)
            eng_a2 = CalibratedConflictEngine(use_ml=True)
            runs["Ablation_MinusAdaptiveArbitration"] = run_custom_pipeline(
                procs,
                WorkloadAwareCPUAgent(), MemoryAgent(), WorkloadAwareIOAgent(),
                CoordinationAgent(conflict_engine=eng_a2, enable_conflict_prediction=True),
                eng_a2,
                PerformanceRegressionDetector(config.healing),
                ProportionalRecoveryEngine(config.healing),
                FeedbackMechanism(eng_a2),
                seed=s
            )

            # 4. Ablation 3: Minus Proportional Self-Healing (Revert recovery to standard RecoveryEngine)
            eng_a3 = CalibratedConflictEngine(use_ml=True)
            runs["Ablation_MinusProportionalHealing"] = run_custom_pipeline(
                procs,
                WorkloadAwareCPUAgent(), MemoryAgent(), WorkloadAwareIOAgent(),
                AdaptiveCoordinationAgent(conflict_engine=eng_a3, enable_conflict_prediction=True),
                eng_a3,
                PerformanceRegressionDetector(config.healing),
                RecoveryEngine(config.healing),
                FeedbackMechanism(eng_a3),
                seed=s
            )

            # 5. Ablation 4: Minus Conflict Prediction (Disable ML predictor)
            runs["Ablation_MinusConflictPrediction"] = run_custom_pipeline(
                procs,
                WorkloadAwareCPUAgent(), MemoryAgent(), WorkloadAwareIOAgent(),
                AdaptiveCoordinationAgent(conflict_engine=None, enable_conflict_prediction=False),
                None,
                PerformanceRegressionDetector(config.healing),
                ProportionalRecoveryEngine(config.healing),
                None,
                seed=s
            )

            for variant_name, m in runs.items():
                c_score = compute_composite_score(m)
                records.append({
                    "variant": variant_name,
                    "workload": w_type,
                    "seed": s,
                    "composite_score": round(c_score, 2),
                    "completion_rate": round(m["completion_rate"], 2),
                    "completed_processes": m["completed_processes"],
                    "unfinished_processes": m["unfinished_processes"],
                    "throughput": round(m["throughput"], 4),
                    "penalized_turnaround": round(m.get("penalized_turnaround_time", m["avg_turnaround_time"]), 2),
                    "avg_turnaround_time": round(m["avg_turnaround_time"], 2),
                    "thrashing_ticks": m["thrashing_ticks"],
                    "jains_fairness": round(m.get("jains_fairness_index", m.get("jains_fairness", 1.0)), 4),
                    "decision_overhead_ms": round(m["decision_overhead_ms"], 4)
                })

    df = pd.DataFrame(records)
    out_csv = PROJECT_ROOT / "reports" / "optimization" / "ablation_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved ablation results to {out_csv} ({len(df)} trials)")

    print("\n" + "=" * 80)
    print("ABLATION STUDY: OVERALL COMPOSITE SCORE (15 VALIDATION SEEDS):")
    print("=" * 80)
    overall = df.groupby("variant")["composite_score"].agg(["mean", "std", "median"]).sort_values(by="mean", ascending=False)
    print(overall.to_string())

    print("\nPER-WORKLOAD ABLATION COMPOSITE SCORES:")
    pivot = df.pivot_table(index="variant", columns="workload", values="composite_score", aggfunc="mean")
    print(pivot.to_string())


if __name__ == "__main__":
    run_ablation_experiments()
