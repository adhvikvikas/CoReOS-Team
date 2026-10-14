"""
Phase 3 Candidate Benchmark Runner
Evaluates Candidates A, B, C, D, and F (Hybrid Champion) against the Control (Baseline E)
and Baselines A and F on 15 Tuning Seeds [2001..2015] across all 6 workloads.
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
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.evaluation.experiments import ExperimentSuite
from src.coreos.baselines.schedulers import ConventionalScheduler
from src.coreos.learning.environment import CoReOSGymEnv
from src.coreos.learning.train import RLAgent

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

TUNING_SEEDS = list(range(2001, 2016))
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


def run_pipeline(
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


def run_candidate_experiments():
    print("=" * 80)
    print("Phase 3: Candidate Architecture Experiments (15 Tuning Seeds [2001..2015])")
    print("=" * 80)

    config = CoReOSConfig()
    suite = ExperimentSuite(config)
    workload_gen = WorkloadGenerator(seed=42)

    # Pretrain RL agent on 150 steps
    print("\nPre-training RL agent for Baseline F...")
    rl_agent = RLAgent()
    train_env = CoReOSGymEnv(max_steps=150)
    rl_agent.train(train_env, num_episodes=15)
    print("RL training complete.")

    records = []

    for w_type in WORKLOADS:
        print(f"\n---> Evaluating Workload: {w_type} (15 tuning seeds)")
        for s in TUNING_SEEDS:
            workload_gen.set_seed(s)
            procs = workload_gen.generate_workload(num_processes=40, workload_type=w_type)
            sim_cfg = SimulationConfig(random_seed=s)

            runs = {}

            # 1. Baseline A (Conventional)
            runs["A_Conventional"] = ConventionalScheduler.run_round_robin(procs, quantum=4.0, config=sim_cfg)

            # 2. Control: Baseline E (Complete CoReOS)
            runs["E_Control_CompleteCoReOS"] = suite.run_baseline_e_complete(procs, seed=s)

            # 3. Baseline F (RL)
            runs["F_LearningRL"] = suite.run_baseline_f_rl(procs, pre_trained_agent=rl_agent, seed=s, max_steps=300)

            # 4. Candidate A: Adaptive Arbitration
            eng_a = ConflictEngine(use_ml=True)
            runs["Cand_A_AdaptiveArbitration"] = run_pipeline(
                procs,
                CPUAgent(), MemoryAgent(), IOAgent(),
                AdaptiveCoordinationAgent(conflict_engine=eng_a, enable_conflict_prediction=True),
                eng_a,
                PerformanceRegressionDetector(config.healing),
                RecoveryEngine(config.healing),
                FeedbackMechanism(eng_a),
                seed=s
            )

            # 5. Candidate B: Proportional Recovery
            eng_b = ConflictEngine(use_ml=True)
            runs["Cand_B_ProportionalHealing"] = run_pipeline(
                procs,
                CPUAgent(), MemoryAgent(), IOAgent(),
                CoordinationAgent(conflict_engine=eng_b, enable_conflict_prediction=True),
                eng_b,
                PerformanceRegressionDetector(config.healing),
                ProportionalRecoveryEngine(config.healing),
                FeedbackMechanism(eng_b),
                seed=s
            )

            # 6. Candidate C: Workload-Aware Scheduling
            eng_c = ConflictEngine(use_ml=True)
            runs["Cand_C_ProgressScheduling"] = run_pipeline(
                procs,
                WorkloadAwareCPUAgent(), MemoryAgent(), WorkloadAwareIOAgent(),
                CoordinationAgent(conflict_engine=eng_c, enable_conflict_prediction=True),
                eng_c,
                PerformanceRegressionDetector(config.healing),
                RecoveryEngine(config.healing),
                FeedbackMechanism(eng_c),
                seed=s
            )

            # 7. Candidate D: Calibrated Prediction
            eng_d = CalibratedConflictEngine(use_ml=True)
            runs["Cand_D_CalibratedPrediction"] = run_pipeline(
                procs,
                CPUAgent(), MemoryAgent(), IOAgent(),
                CoordinationAgent(conflict_engine=eng_d, enable_conflict_prediction=True),
                eng_d,
                PerformanceRegressionDetector(config.healing),
                RecoveryEngine(config.healing),
                FeedbackMechanism(eng_d),
                seed=s
            )

            # 8. Candidate F: Hybrid Champion
            champ = ChampionCoReOS(config)
            runs["Cand_F_ChampionCoReOS"] = champ.run_simulation(procs, seed=s, max_steps=300)

            for cand_name, m in runs.items():
                c_score = compute_composite_score(m)
                conflict_m = m.get("conflict_metrics", {})
                healing_m = m.get("healing_metrics", {})

                records.append({
                    "candidate": cand_name,
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
                    "decision_overhead_ms": round(m["decision_overhead_ms"], 4),
                    "total_recoveries": healing_m.get("total_recoveries", 0),
                    "recovery_success_rate": round(healing_m.get("success_rate", 0.0), 3)
                })

    df = pd.DataFrame(records)
    out_csv = PROJECT_ROOT / "reports" / "optimization" / "candidate_results.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nSaved detailed candidate results to {out_csv} ({len(df)} trials)")

    # Produce candidate summary
    summary = df.groupby(["candidate", "workload"])[
        ["composite_score", "completion_rate", "throughput", "penalized_turnaround", "thrashing_ticks", "jains_fairness"]
    ].mean().reset_index()

    overall = df.groupby("candidate")[
        ["composite_score", "completion_rate", "throughput", "penalized_turnaround", "thrashing_ticks", "jains_fairness"]
    ].agg(["mean", "std", "median"]).reset_index()

    summary_csv = PROJECT_ROOT / "reports" / "optimization" / "candidate_summary.csv"
    summary.to_csv(summary_csv, index=False)
    print(f"Saved candidate summary to {summary_csv}")

    print("\n" + "=" * 80)
    print("OVERALL CANDIDATE RANKING ACROSS ALL 6 WORKLOADS (15 TUNING SEEDS):")
    print("=" * 80)
    rank_df = df.groupby("candidate")["composite_score"].agg(["mean", "std", "median"]).sort_values(by="mean", ascending=False)
    print(rank_df.to_string())

    print("\nPER-WORKLOAD COMPOSITE SCORES:")
    pivot = df.pivot_table(index="candidate", columns="workload", values="composite_score", aggfunc="mean")
    print(pivot.to_string())


if __name__ == "__main__":
    run_candidate_experiments()
