from fastapi import APIRouter
import pandas as pd
from pathlib import Path
from src.coreos.evaluation.experiments import ExperimentSuite

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@router.get("/")
def get_benchmarks():
    final_canonical_csv = PROJECT_ROOT / "reports" / "optimization" / "final_canonical_benchmark_results.csv"
    phase8_csv = PROJECT_ROOT / "reports" / "optimization" / "phase8_final_benchmark_results.csv"
    phase3_csv = PROJECT_ROOT / "reports" / "phase3_benchmark_results.csv"
    legacy_csv = PROJECT_ROOT / "reports" / "benchmark_results.csv"

    source_name = "live_simulation"
    if final_canonical_csv.exists():
        df_bench = pd.read_csv(final_canonical_csv)
        source_name = "final_canonical_benchmark_results.csv"
    elif phase8_csv.exists():
        df_bench = pd.read_csv(phase8_csv)
        source_name = "phase8_final_benchmark_results.csv"
    elif phase3_csv.exists():
        df_bench = pd.read_csv(phase3_csv)
        source_name = "phase3_benchmark_results.csv"
    elif legacy_csv.exists():
        df_bench = pd.read_csv(legacy_csv)
        source_name = "benchmark_results.csv"
    else:
        suite = ExperimentSuite()
        df_bench = suite.run_benchmark_suite(["adversarial_stress", "steady_state"], num_seeds=2)

    # Normalize candidate and baseline columns for cross-compatibility
    if "candidate" in df_bench.columns and "baseline" not in df_bench.columns:
        df_bench["baseline"] = df_bench["candidate"]
    elif "baseline" in df_bench.columns and "candidate" not in df_bench.columns:
        df_bench["candidate"] = df_bench["baseline"]

    # Normalize penalized turnaround
    if "penalized_turnaround" in df_bench.columns and "penalized_turnaround_time" not in df_bench.columns:
        df_bench["penalized_turnaround_time"] = df_bench["penalized_turnaround"]
    elif "penalized_turnaround_time" in df_bench.columns and "penalized_turnaround" not in df_bench.columns:
        df_bench["penalized_turnaround"] = df_bench["penalized_turnaround_time"]
    elif "penalized_turnaround_time" not in df_bench.columns and "avg_turnaround_time" in df_bench.columns:
        def _calc_pen(row):
            tot = row.get("total_processes") or 0
            if tot <= 0:
                return 0.0
            comp = row.get("completed_processes") or 0
            unfin = max(0, tot - comp)
            return round((comp * (row.get("avg_turnaround_time") or 0.0) + unfin * 300.0) / tot, 2)
        pen_col = df_bench.apply(_calc_pen, axis=1)
        df_bench["penalized_turnaround_time"] = pen_col
        df_bench["penalized_turnaround"] = pen_col

    # Normalize composite score if missing
    if "composite_score" not in df_bench.columns:
        def _calc_comp(row):
            comp = (row.get("completion_rate") or 0.0) / 100.0
            thru = min(1.0, (row.get("throughput") or 0.0) / 0.25)
            pt_val = row.get("penalized_turnaround", row.get("avg_turnaround_time", 300.0))
            pt = max(0.0, 1.0 - (pt_val - 5.0) / 295.0)
            thrash = max(0.0, 1.0 - (row.get("thrashing_ticks") or 0.0) / 150.0)
            fair = max(0.0, min(1.0, row.get("jains_fairness", 1.0)))
            return round(100.0 * (0.30 * comp + 0.25 * thru + 0.20 * pt + 0.15 * thrash + 0.10 * fair), 2)
        df_bench["composite_score"] = df_bench.apply(_calc_comp, axis=1)

    df_bench = df_bench.replace({float('nan'): None})

    # Load ranking summary and per-workload summary if available
    ranking_summary = []
    final_rank_csv = PROJECT_ROOT / "reports" / "optimization" / "final_canonical_ranking_summary.csv"
    rank_csv = PROJECT_ROOT / "reports" / "optimization" / "phase8_final_ranking_summary.csv"
    if final_rank_csv.exists():
        df_rank = pd.read_csv(final_rank_csv)
        df_rank = df_rank.replace({float('nan'): None})
        ranking_summary = df_rank.to_dict(orient="records")
    elif rank_csv.exists():
        df_rank = pd.read_csv(rank_csv)
        df_rank = df_rank.replace({float('nan'): None})
        ranking_summary = df_rank.to_dict(orient="records")

    per_workload_summary = []
    final_pw_csv = PROJECT_ROOT / "reports" / "optimization" / "final_canonical_per_workload_summary.csv"
    pw_csv = PROJECT_ROOT / "reports" / "optimization" / "phase8_per_workload_summary.csv"
    if final_pw_csv.exists():
        df_pw = pd.read_csv(final_pw_csv)
        df_pw = df_pw.replace({float('nan'): None})
        per_workload_summary = df_pw.to_dict(orient="records")
    elif pw_csv.exists():
        df_pw = pd.read_csv(pw_csv)
        df_pw = df_pw.replace({float('nan'): None})
        per_workload_summary = df_pw.to_dict(orient="records")

    cand_list = sorted(df_bench["candidate"].dropna().unique().tolist())
    active_candidates = [c for c in cand_list if c != "E_CompleteCoReOS"]

    active_ranking = []
    if ranking_summary:
        active_ranking = [dict(r) for r in ranking_summary if r.get("candidate") != "E_CompleteCoReOS"]
        for idx, r in enumerate(active_ranking, 1):
            r["rank"] = idx

    return {
        "workloads": sorted(df_bench["workload"].unique().tolist()),
        "candidates": cand_list,
        "active_candidates": active_candidates,
        "data": df_bench.to_dict(orient="records"),
        "overall_ranking": ranking_summary,
        "active_ranking": active_ranking,
        "per_workload_summary": per_workload_summary,
        "source": source_name
    }
