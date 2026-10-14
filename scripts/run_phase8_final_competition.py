"""
Phase 8: Final Benchmark Competition and Statistical Validation Runner.

Executes an impartial, matched evaluation across all eight candidates:
- A_Conventional: Conventional Round Robin (quantum=4.0)
- B_IndependentAgents: Independent Agents
- C_CoordNoConflict: Coordination without Conflict Prediction
- D_ConflictNoHealing: Conflict Prediction without Self-Healing
- E_CompleteCoReOS: Complete CoReOS (Baseline E)
- F_ImprovedRL: Phase 7 Improved Adaptive RL Candidate
- G_ChampionCoReOS: Hybrid Champion CoReOS Architecture
- H_OriginalRL: Original Tabular RL Baseline (Phase 5 Baseline F)

Protocol:
- 30 fresh held-out seeds: [5001..5030] (verified disjoint from training/tuning/validation)
- 6 workloads: steady_state, cpu_spike, memory_thrashing, io_bottleneck, mixed, adversarial_stress
- Total: 8 candidates x 6 workloads x 30 seeds = 1,440 simulation trials
- 300-step evaluation horizon across all trials
- Frozen composite scoring formula and guardrail compliance auditing
- Paired statistical hypothesis tests with Holm-Bonferroni and Benjamini-Hochberg corrections
"""

import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
import pandas as pd
from scipy import stats

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import CoReOSConfig, SimulationConfig
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.evaluation.experiments import ExperimentSuite
from src.coreos.baselines.schedulers import ConventionalScheduler, IndependentAgentScheduler
from src.coreos.learning.environment import CoReOSGymEnv
from src.coreos.learning.train import RLAgent
from src.coreos.learning.adaptive_rl import AdaptiveCoReOSGymEnv, AdaptiveRLAgent, ImprovedRLCandidate
from src.coreos.optimization.candidates import ChampionCoReOS

# Verified fresh held-out seeds [5001..5030]
HELDOUT_SEEDS = list(range(5001, 5031))

WORKLOADS = [
    "steady_state",
    "cpu_spike",
    "memory_thrashing",
    "io_bottleneck",
    "mixed",
    "adversarial_stress"
]

CANDIDATES = [
    "G_ChampionCoReOS",
    "F_ImprovedRL",
    "H_OriginalRL",
    "E_CompleteCoReOS",
    "C_CoordNoConflict",
    "D_ConflictNoHealing",
    "A_Conventional",
    "B_IndependentAgents"
]


def compute_composite_score(m: dict) -> float:
    """Established frozen composite scoring formula."""
    comp = m["completion_rate"] / 100.0
    thru = min(1.0, m["throughput"] / 0.25)
    pt = max(0.0, 1.0 - (m.get("penalized_turnaround_time", m["avg_turnaround_time"]) - 5.0) / 295.0)
    thrash = max(0.0, 1.0 - m["thrashing_ticks"] / 150.0)
    fair = max(0.0, min(1.0, m.get("jains_fairness_index", m.get("jains_fairness", 1.0))))
    return 100.0 * (0.30 * comp + 0.25 * thru + 0.20 * pt + 0.15 * thrash + 0.10 * fair)


def check_guardrails(cand_name: str, workload: str, m: dict) -> Tuple[bool, List[str]]:
    """
    Evaluates competition guardrails:
    1. Fairness floor: Jain's Fairness >= 0.60
    2. Workload robustness: steady_state/mixed completion == 100% & turnaround <= 16.0
    3. Thrashing boundary: <= 25 ticks on non-adversarial, <= 15 ticks on adversarial
    4. Decision overhead: <= 1.0 ms per step
    """
    violations = []
    fair = m.get("jains_fairness_index", m.get("jains_fairness", 1.0))
    if fair < 0.60:
        violations.append(f"Fairness violation: {fair:.3f} < 0.60")

    if workload in ["steady_state", "mixed"]:
        if m["completion_rate"] < 100.0:
            violations.append(f"Completion regression on {workload}: {m['completion_rate']:.1f}% < 100%")
        avg_ta = m["avg_turnaround_time"]
        if avg_ta > 16.0:
            violations.append(f"Turnaround latency regression on {workload}: {avg_ta:.1f} > 16.0")

    thrash = m["thrashing_ticks"]
    max_thrash = 15.0 if workload == "adversarial_stress" else 25.0
    if thrash > max_thrash:
        violations.append(f"Thrashing ceiling exceeded on {workload}: {thrash} > {max_thrash}")

    overhead = m.get("decision_overhead_ms", 0.0)
    if overhead > 1.0:
        violations.append(f"Decision overhead ceiling exceeded: {overhead:.3f} ms > 1.0 ms")

    return (len(violations) == 0, violations)


def run_phase8_competition():
    print("=" * 90)
    print("Phase 8: Final Benchmark Competition (30 Held-Out Seeds [5001..5030], 6 Workloads, 8 Candidates)")
    print(f"Total Trials: {len(HELDOUT_SEEDS)} seeds x {len(WORKLOADS)} workloads x {len(CANDIDATES)} candidates = {len(HELDOUT_SEEDS) * len(WORKLOADS) * len(CANDIDATES)} trials")
    print("=" * 90)

    config = CoReOSConfig()
    suite = ExperimentSuite(config)
    workload_gen = WorkloadGenerator(seed=42)

    # 1. Pretrain Original RL (Baseline H) on 15 episodes of steady_state
    print("\n[1/3] Pre-training Original RL Baseline H (15 episodes of steady_state)...")
    orig_rl_agent = RLAgent()
    orig_train_env = CoReOSGymEnv(max_steps=150)
    orig_rl_agent.train(orig_train_env, num_episodes=15)
    print(f"Original RL training complete: {len(orig_rl_agent.q_table)} distinct states explored.")

    # 2. Pretrain Improved Adaptive RL (Candidate F) across all 6 workloads
    print("\n[2/3] Pre-training Improved Adaptive RL Candidate F (120 episodes across 6 workloads)...")
    imp_agent = AdaptiveRLAgent()
    imp_train_env = AdaptiveCoReOSGymEnv(max_steps=150)
    imp_agent.train_curriculum(imp_train_env, episodes_per_workload=20, base_seed=4000)
    imp_candidate = ImprovedRLCandidate(agent=imp_agent)
    print(f"Improved RL training complete: {sum(1 for c in imp_agent.visited_counts.values() if c > 0)} / 54 distinct states explored.")

    # 3. Initialize Champion CoReOS (Candidate G)
    champ = ChampionCoReOS(config)

    records = []
    t0_start = time.time()

    print("\n[3/3] Running matched evaluation trials...")
    for w_type in WORKLOADS:
        t_w0 = time.time()
        print(f"\n---> Evaluating Workload: {w_type:<20} (30 held-out seeds [5001..5030])")
        for s in HELDOUT_SEEDS:
            workload_gen.set_seed(s)
            procs = workload_gen.generate_workload(num_processes=40, workload_type=w_type)
            sim_cfg = SimulationConfig(random_seed=s)

            runs = {}

            # Candidate A: Conventional Round Robin
            runs["A_Conventional"] = ConventionalScheduler.run_round_robin(procs, quantum=4.0, config=sim_cfg)

            # Candidate B: Independent Agents
            runs["B_IndependentAgents"] = IndependentAgentScheduler.run(procs, config=sim_cfg)

            # Candidate C: Coordination without Conflict Prediction
            runs["C_CoordNoConflict"] = suite.run_baseline_c(procs, seed=s)

            # Candidate D: Conflict Prediction without Self-Healing
            runs["D_ConflictNoHealing"] = suite.run_baseline_d(procs, seed=s)

            # Candidate E: Complete CoReOS (Baseline E)
            runs["E_CompleteCoReOS"] = suite.run_baseline_e_complete(procs, seed=s)

            # Candidate F: Improved Adaptive RL (Phase 7)
            runs["F_ImprovedRL"] = imp_candidate.run_simulation(procs, seed=s, max_steps=300)

            # Candidate G: Champion CoReOS (Hybrid Architecture)
            runs["G_ChampionCoReOS"] = champ.run_simulation(procs, seed=s, max_steps=300)

            # Candidate H: Original Tabular RL (Phase 5 Baseline F)
            runs["H_OriginalRL"] = suite.run_baseline_f_rl(procs, pre_trained_agent=orig_rl_agent, seed=s, max_steps=300)

            for cand_name, m in runs.items():
                c_score = compute_composite_score(m)
                passed_guardrails, violations = check_guardrails(cand_name, w_type, m)
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
                    "decision_overhead_ms": round(m.get("decision_overhead_ms", 0.0), 4),
                    "total_recoveries": healing_m.get("total_recoveries", 0),
                    "recovery_success_rate": round(healing_m.get("success_rate", 0.0), 3),
                    "guardrail_compliant": passed_guardrails,
                    "guardrail_violations": "; ".join(violations) if violations else "NONE"
                })

        print(f"     Workload {w_type} completed in {time.time() - t_w0:.2f}s.")

    total_time = time.time() - t0_start
    print(f"\nAll 1,440 simulation trials successfully completed in {total_time:.2f}s.")

    df = pd.DataFrame(records)

    out_dir = PROJECT_ROOT / "reports" / "optimization"
    out_dir.mkdir(parents=True, exist_ok=True)

    # 1. Save Raw Trial-Level Results CSV
    raw_csv = out_dir / "phase8_final_benchmark_results.csv"
    df.to_csv(raw_csv, index=False)
    print(f"Saved raw trial-level results to {raw_csv}")

    # 2. Compute Overall Summary Statistics per Candidate
    summary_records = []
    for cand in CANDIDATES:
        sub = df[df["candidate"] == cand]
        scores = sub["composite_score"].values
        n = len(scores)
        mean_score = float(np.mean(scores))
        std_score = float(np.std(scores, ddof=1))
        median_score = float(np.median(scores))
        sem = std_score / np.sqrt(n)
        ci95 = float(stats.t.ppf(0.975, df=n - 1) * sem)

        summary_records.append({
            "candidate": cand,
            "n_trials": n,
            "composite_score_mean": round(mean_score, 2),
            "composite_score_std": round(std_score, 2),
            "composite_score_median": round(median_score, 2),
            "composite_score_ci95": round(ci95, 2),
            "completion_rate_mean": round(float(sub["completion_rate"].mean()), 2),
            "penalized_turnaround_mean": round(float(sub["penalized_turnaround"].mean()), 2),
            "throughput_mean": round(float(sub["throughput"].mean()), 4),
            "thrashing_ticks_mean": round(float(sub["thrashing_ticks"].mean()), 2),
            "jains_fairness_mean": round(float(sub["jains_fairness"].mean()), 4),
            "decision_overhead_ms_mean": round(float(sub["decision_overhead_ms"].mean()), 4),
            "guardrail_pass_rate": round(float((sub["guardrail_compliant"] == True).mean() * 100.0), 1)
        })

    summary_df = pd.DataFrame(summary_records).sort_values(by="composite_score_mean", ascending=False).reset_index(drop=True)
    summary_df["rank"] = summary_df.index + 1
    cols = ["rank", "candidate", "composite_score_mean", "composite_score_std", "composite_score_ci95",
            "completion_rate_mean", "penalized_turnaround_mean", "throughput_mean",
            "thrashing_ticks_mean", "jains_fairness_mean", "decision_overhead_ms_mean", "guardrail_pass_rate"]
    summary_df = summary_df[cols]

    summary_csv = out_dir / "phase8_final_ranking_summary.csv"
    summary_df.to_csv(summary_csv, index=False)
    print(f"Saved final aggregate ranking summary to {summary_csv}")

    # 3. Compute Per-Workload Summary Statistics
    pw_records = []
    for w in WORKLOADS:
        for cand in CANDIDATES:
            sub = df[(df["workload"] == w) & (df["candidate"] == cand)]
            scores = sub["composite_score"].values
            n = len(scores)
            mean_score = float(np.mean(scores))
            std_score = float(np.std(scores, ddof=1))
            pw_records.append({
                "workload": w,
                "candidate": cand,
                "n_seeds": n,
                "composite_score_mean": round(mean_score, 2),
                "composite_score_std": round(std_score, 2),
                "completion_rate_mean": round(float(sub["completion_rate"].mean()), 2),
                "penalized_turnaround_mean": round(float(sub["penalized_turnaround"].mean()), 2),
                "throughput_mean": round(float(sub["throughput"].mean()), 4),
                "thrashing_ticks_mean": round(float(sub["thrashing_ticks"].mean()), 2),
                "jains_fairness_mean": round(float(sub["jains_fairness"].mean()), 4),
                "decision_overhead_ms_mean": round(float(sub["decision_overhead_ms"].mean()), 4)
            })

    pw_df = pd.DataFrame(pw_records)
    pw_csv = out_dir / "phase8_per_workload_summary.csv"
    pw_df.to_csv(pw_csv, index=False)
    print(f"Saved per-workload summary to {pw_csv}")

    # 4. Compute Paired Comparisons with Multiple-Testing Corrections
    # Match trials on (workload, seed) across all candidates
    pivot_scores = df.pivot_table(index=["workload", "seed"], columns="candidate", values="composite_score")
    
    paired_rows = []
    # Test all pairs
    cand_list = summary_df["candidate"].tolist()
    m_comparisons = (len(cand_list) * (len(cand_list) - 1)) // 2

    raw_pairs = []
    for i in range(len(cand_list)):
        for j in range(i + 1, len(cand_list)):
            c1 = cand_list[i]
            c2 = cand_list[j]
            diff = pivot_scores[c1] - pivot_scores[c2]
            mean_diff = float(np.mean(diff))
            std_diff = float(np.std(diff, ddof=1))
            cohens_d = mean_diff / std_diff if std_diff > 1e-6 else 0.0

            # Paired Student's t-test
            t_res = stats.ttest_rel(pivot_scores[c1], pivot_scores[c2])
            t_stat = float(t_res.statistic)
            p_val_t = float(t_res.pvalue)

            # Wilcoxon signed-rank test
            try:
                w_res = stats.wilcoxon(pivot_scores[c1], pivot_scores[c2])
                w_stat = float(w_res.statistic)
                p_val_w = float(w_res.pvalue)
            except Exception:
                w_stat = 0.0
                p_val_w = 1.0

            raw_pairs.append({
                "candidate_A": c1,
                "candidate_B": c2,
                "mean_diff": round(mean_diff, 3),
                "std_diff": round(std_diff, 3),
                "cohens_d": round(cohens_d, 3),
                "t_stat": round(t_stat, 3),
                "p_value_t": p_val_t,
                "wilcoxon_stat": round(w_stat, 1),
                "p_value_wilcoxon": p_val_w
            })

    # Apply Multiple-Testing Corrections
    # 1. Holm-Bonferroni correction
    raw_pairs.sort(key=lambda x: x["p_value_t"])
    m_tests = len(raw_pairs)
    for idx, row in enumerate(raw_pairs):
        # Holm factor: (m_tests - idx)
        holm_p = min(1.0, row["p_value_t"] * (m_tests - idx))
        row["p_holm_bonferroni"] = holm_p

    # Enforce monotonicity for Holm
    for idx in range(1, len(raw_pairs)):
        raw_pairs[idx]["p_holm_bonferroni"] = max(raw_pairs[idx]["p_holm_bonferroni"], raw_pairs[idx - 1]["p_holm_bonferroni"])

    # 2. Benjamini-Hochberg FDR correction
    for idx, row in enumerate(raw_pairs):
        bh_p = min(1.0, row["p_value_t"] * m_tests / (idx + 1))
        row["p_benjamini_hochberg"] = bh_p

    # Enforce monotonicity backwards for BH
    for idx in range(len(raw_pairs) - 2, -1, -1):
        raw_pairs[idx]["p_benjamini_hochberg"] = min(raw_pairs[idx]["p_benjamini_hochberg"], raw_pairs[idx + 1]["p_benjamini_hochberg"])

    # Round formatting
    for row in raw_pairs:
        row["p_value_t"] = f"{row['p_value_t']:.2e}" if row["p_value_t"] < 0.001 else f"{row['p_value_t']:.4f}"
        row["p_value_wilcoxon"] = f"{row['p_value_wilcoxon']:.2e}" if row["p_value_wilcoxon"] < 0.001 else f"{row['p_value_wilcoxon']:.4f}"
        row["p_holm_bonferroni"] = f"{row['p_holm_bonferroni']:.2e}" if row["p_holm_bonferroni"] < 0.001 else f"{row['p_holm_bonferroni']:.4f}"
        row["p_benjamini_hochberg"] = f"{row['p_benjamini_hochberg']:.2e}" if row["p_benjamini_hochberg"] < 0.001 else f"{row['p_benjamini_hochberg']:.4f}"
        row["significant_alpha_0_05"] = (float(row["p_holm_bonferroni"]) < 0.05)

    comp_df = pd.DataFrame(raw_pairs)
    comp_csv = out_dir / "phase8_statistical_comparisons.csv"
    comp_df.to_csv(comp_csv, index=False)
    print(f"Saved paired statistical comparisons to {comp_csv}")

    # Print Final Standings Table
    print("\n" + "=" * 105)
    print(f"{'Rank':<5} | {'Candidate':<22} | {'Composite Score (Mean ± CI95)':<32} | {'Completion%':<12} | {'Turnaround':<11} | {'Thrash':<7}")
    print("=" * 105)
    for _, row in summary_df.iterrows():
        print(f"{row['rank']:<5} | {row['candidate']:<22} | {row['composite_score_mean']:>6.2f} ± {row['composite_score_ci95']:<4.2f} (std={row['composite_score_std']:<4.2f})           | {row['completion_rate_mean']:>6.1f}%       | {row['penalized_turnaround_mean']:>6.1f} ticks | {row['thrashing_ticks_mean']:>5.2f}")
    print("=" * 105)

    return df, summary_df, pw_df, comp_df


if __name__ == "__main__":
    run_phase8_competition()
