"""
Phase 7: Diagnostic Evaluation Script for RL Baseline Audit and Improvement.

Compares:
1. Original RL Baseline (F_LearningRL):
   - 15-episode steady_state tabular Q-learning
   - 8-dimensional sparse state representation
   - 4-action action map (all ROUND_ROBIN)
   - Unseen state argmax tie-break (defaults to action 0)
2. Improved Adaptive RL Baseline (Candidate_ImprovedRL):
   - 120-episode multi-workload curriculum tabular Q-learning
   - 4-dimensional compact state representation (54 states)
   - 6-action action map (including progress-aware SRTF, deep reclamation, SCAN)
   - Nearest-neighbor generalization for unvisited states
   - Completion- and backlog-aligned reward signal

Evaluates across all 6 workloads on seeds [42, 43, 44, 45, 46] (5 seeds x 6 workloads = 30 trials per agent).
Computes:
- Visited states
- Unseen state evaluations
- Action distribution
- Completion rate (%)
- Throughput (procs/tick)
- Penalized turnaround (ticks)
- Thrashing ticks
- Jain's fairness index
- Composite score
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List
import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import CoReOSConfig, SimulationConfig
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.learning.environment import CoReOSGymEnv
from src.coreos.learning.train import RLAgent
from src.coreos.learning.adaptive_rl import AdaptiveCoReOSGymEnv, AdaptiveRLAgent

WORKLOADS = [
    "steady_state",
    "cpu_spike",
    "memory_thrashing",
    "io_bottleneck",
    "mixed",
    "adversarial_stress"
]

DIAGNOSTIC_SEEDS = [42, 43, 44, 45, 46]


def compute_composite_score(m: dict) -> float:
    comp = m["completion_rate"] / 100.0
    thru = min(1.0, m["throughput"] / 0.25)
    pt = max(0.0, 1.0 - (m.get("penalized_turnaround_time", m["avg_turnaround_time"]) - 5.0) / 295.0)
    thrash = max(0.0, 1.0 - m["thrashing_ticks"] / 150.0)
    fair = max(0.0, min(1.0, m.get("jains_fairness_index", m.get("jains_fairness", 1.0))))
    return 100.0 * (0.30 * comp + 0.25 * thru + 0.20 * pt + 0.15 * thrash + 0.10 * fair)


def run_diagnostic_evaluation() -> pd.DataFrame:
    print("=" * 85)
    print("Phase 7: RL Baseline Audit and Improvement — Diagnostic Evaluation")
    print(f"Workloads: {len(WORKLOADS)} | Seeds: {DIAGNOSTIC_SEEDS} | Horizon: 300 steps")
    print("=" * 85)

    # 1. Train Original RL Baseline
    print("\n[1/3] Pre-training Original RL Baseline (15 episodes of steady_state)...")
    orig_agent = RLAgent()
    orig_train_env = CoReOSGymEnv(max_steps=150)
    orig_agent.train(orig_train_env, num_episodes=15)
    orig_states_count = len(orig_agent.q_table)
    print(f"Original RL Training Complete: {orig_states_count} distinct states explored.")

    # 2. Train Improved Adaptive RL Baseline
    print("\n[2/3] Pre-training Improved Adaptive RL Baseline (20 ep/workload x 6 workloads = 120 ep)...")
    improved_agent = AdaptiveRLAgent()
    imp_train_env = AdaptiveCoReOSGymEnv(max_steps=150)
    improved_agent.train_curriculum(imp_train_env, episodes_per_workload=20, base_seed=4000)
    imp_states_count = sum(1 for cnt in improved_agent.visited_counts.values() if cnt > 0)
    print(f"Improved RL Training Complete: {imp_states_count} / 54 distinct states explored.")

    # 3. Diagnostic Evaluation
    print("\n[3/3] Evaluating Both Policies Across All 6 Workloads...")
    workload_gen = WorkloadGenerator(seed=42)
    rows = []

    for w_type in WORKLOADS:
        for s in DIAGNOSTIC_SEEDS:
            workload_gen.set_seed(s)
            procs = workload_gen.generate_workload(num_processes=40, workload_type=w_type)
            sim_cfg = SimulationConfig(random_seed=s)

            # --- Eval Original RL ---
            sim_orig = SystemSimulator(sim_cfg)
            w_orig = [p.clone() for p in procs]
            sim_orig.reset(w_orig)
            env_orig = CoReOSGymEnv(simulator=sim_orig, max_steps=300)
            obs_orig = env_orig._extract_obs(sim_orig.get_system_state())

            done = False
            step_i = 0
            t0 = time.perf_counter()
            orig_acts = {}
            orig_unseen = 0

            while not done and step_i < 300:
                s_key = orig_agent._discretize_obs(obs_orig)
                if s_key not in orig_agent.q_table:
                    orig_unseen += 1
                act = orig_agent.select_action(obs_orig, evaluate=True)
                orig_acts[act] = orig_acts.get(act, 0) + 1
                obs_orig, _, done, _ = env_orig.step(act)
                step_i += 1

            overhead_ms_orig = (time.perf_counter() - t0) * 1000.0 / max(1, step_i)
            m_orig = compute_simulation_metrics(sim_orig.completed_processes, sim_orig.history, overhead_ms_orig, total_processes=len(w_orig))
            score_orig = compute_composite_score(m_orig)

            rows.append({
                "agent": "Original_RL",
                "workload": w_type,
                "seed": s,
                "composite_score": round(score_orig, 2),
                "completion_rate": round(m_orig["completion_rate"], 2),
                "throughput": round(m_orig["throughput"], 4),
                "penalized_turnaround": round(m_orig.get("penalized_turnaround_time", m_orig["avg_turnaround_time"]), 2),
                "thrashing_ticks": m_orig["thrashing_ticks"],
                "jains_fairness": round(m_orig.get("jains_fairness_index", 1.0), 4),
                "unseen_steps": orig_unseen,
                "actions": str(orig_acts)
            })

            # --- Eval Improved RL ---
            sim_imp = SystemSimulator(sim_cfg)
            w_imp = [p.clone() for p in procs]
            sim_imp.reset(w_imp)
            env_imp = AdaptiveCoReOSGymEnv(simulator=sim_imp, max_steps=300)
            state_imp = env_imp.discretize_state(sim_imp.get_system_state())

            done = False
            step_i = 0
            t0 = time.perf_counter()
            imp_acts = {}
            imp_unseen = 0

            while not done and step_i < 300:
                if improved_agent.visited_counts.get(state_imp, 0) == 0:
                    imp_unseen += 1
                act = improved_agent.select_action(state_imp, evaluate=True)
                imp_acts[act] = imp_acts.get(act, 0) + 1
                state_imp, _, done, _ = env_imp.step(act)
                step_i += 1

            overhead_ms_imp = (time.perf_counter() - t0) * 1000.0 / max(1, step_i)
            m_imp = compute_simulation_metrics(sim_imp.completed_processes, sim_imp.history, overhead_ms_imp, total_processes=len(w_imp))
            score_imp = compute_composite_score(m_imp)

            rows.append({
                "agent": "Improved_RL",
                "workload": w_type,
                "seed": s,
                "composite_score": round(score_imp, 2),
                "completion_rate": round(m_imp["completion_rate"], 2),
                "throughput": round(m_imp["throughput"], 4),
                "penalized_turnaround": round(m_imp.get("penalized_turnaround_time", m_imp["avg_turnaround_time"]), 2),
                "thrashing_ticks": m_imp["thrashing_ticks"],
                "jains_fairness": round(m_imp.get("jains_fairness_index", 1.0), 4),
                "unseen_steps": imp_unseen,
                "actions": str(imp_acts)
            })

    df = pd.DataFrame(rows)

    # Save diagnostic results to reports/diagnostic_rl_audit.csv
    out_dir = PROJECT_ROOT / "reports"
    out_file = out_dir / "diagnostic_rl_audit.csv"
    df.to_csv(out_file, index=False)
    print(f"\nSaved raw diagnostic trial data to {out_file}")

    print("\n" + "=" * 105)
    print(f"{'Workload':<20} | {'Policy':<13} | {'Composite':<9} | {'Comp%':<7} | {'Thru':<7} | {'PT':<7} | {'Thrsh':<5} | {'Fair':<6} | {'Unseen':<6}")
    print("=" * 105)

    summary_records = []
    for w in WORKLOADS:
        for pol in ["Original_RL", "Improved_RL"]:
            sub = df[(df["workload"] == w) & (df["agent"] == pol)]
            c_score = sub["composite_score"].mean()
            comp = sub["completion_rate"].mean()
            thru = sub["throughput"].mean()
            pt = sub["penalized_turnaround"].mean()
            thrash = sub["thrashing_ticks"].mean()
            fair = sub["jains_fairness"].mean()
            unseen = sub["unseen_steps"].mean()

            summary_records.append({
                "Workload": w,
                "Policy": pol,
                "Composite": round(c_score, 2),
                "Completion%": round(comp, 2),
                "Throughput": round(thru, 4),
                "PenalizedTurnaround": round(pt, 2),
                "ThrashingTicks": round(thrash, 2),
                "Fairness": round(fair, 3),
                "UnseenSteps": round(unseen, 1)
            })

            print(f"{w:<20} | {pol:<13} | {c_score:>9.2f} | {comp:>6.1f}% | {thru:>7.4f} | {pt:>7.1f} | {thrash:>5.1f} | {fair:>6.3f} | {unseen:>6.1f}")
        print("-" * 105)

    summary_df = pd.DataFrame(summary_records)
    print("\nOVERALL MEAN COMPOSITE SCORE:")
    for pol in ["Original_RL", "Improved_RL"]:
        mean_score = summary_df[summary_df["Policy"] == pol]["Composite"].mean()
        print(f"  {pol:<15}: {mean_score:.2f}")

    return df


if __name__ == "__main__":
    run_diagnostic_evaluation()
