from fastapi import APIRouter
import pandas as pd
from pathlib import Path
from backend.state import state_store

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@router.get("/")
def get_overview():
    final_canonical_csv = PROJECT_ROOT / "reports" / "optimization" / "final_canonical_benchmark_results.csv"
    phase8_csv = PROJECT_ROOT / "reports" / "optimization" / "phase8_final_benchmark_results.csv"
    phase3_csv = PROJECT_ROOT / "reports" / "phase3_benchmark_results.csv"
    legacy_csv = PROJECT_ROOT / "reports" / "benchmark_results.csv"

    bench_csv = None
    if final_canonical_csv.exists():
        bench_csv = final_canonical_csv
    elif phase8_csv.exists():
        bench_csv = phase8_csv
    elif phase3_csv.exists():
        bench_csv = phase3_csv
    elif legacy_csv.exists():
        bench_csv = legacy_csv

    stress_comparison = None
    turnaround_val = "N/A"
    turnaround_desc = "Benchmark data unavailable"
    num_candidates = 8
    highlights = []

    if bench_csv and bench_csv.exists():
        try:
            bdf = pd.read_csv(bench_csv)
            cand_col = "candidate" if "candidate" in bdf.columns else "baseline"
            if "baseline" not in bdf.columns and "candidate" in bdf.columns:
                bdf["baseline"] = bdf["candidate"]

            num_candidates = int(bdf[cand_col].nunique())

            # Ensure penalized_turnaround_time is calculated
            if "penalized_turnaround_time" not in bdf.columns and "penalized_turnaround" in bdf.columns:
                bdf["penalized_turnaround_time"] = bdf["penalized_turnaround"]
            elif "penalized_turnaround_time" not in bdf.columns and "avg_turnaround_time" in bdf.columns:
                def _calc_pen(row):
                    tot = row.get("total_processes") or 0
                    if tot <= 0:
                        return 0.0
                    comp = row.get("completed_processes") or 0
                    unfin = max(0, tot - comp)
                    return round((comp * (row.get("avg_turnaround_time") or 0.0) + unfin * 300.0) / tot, 2)
                bdf["penalized_turnaround_time"] = bdf.apply(_calc_pen, axis=1)

            summary_cols = [c for c in ["workload", cand_col, "total_processes", "completed_processes", "completion_rate", "avg_turnaround_time", "penalized_turnaround_time", "throughput", "thrashing_ticks"] if c in bdf.columns]
            summary = bdf.groupby(["workload", cand_col])[[c for c in summary_cols if c not in ["workload", cand_col]]].mean().reset_index()
            summary = summary.replace({float('nan'): None})
            highlights = summary.head(16).to_dict(orient="records")

            adv_conv = bdf[(bdf["workload"] == "adversarial_stress") & (bdf[cand_col] == "A_Conventional")]
            # Prefer Champion CoReOS, then Complete CoReOS
            core_cand_name = "G_ChampionCoReOS" if "G_ChampionCoReOS" in bdf[cand_col].values else "E_CompleteCoReOS"
            adv_core = bdf[(bdf["workload"] == "adversarial_stress") & (bdf[cand_col] == core_cand_name)]

            if not adv_conv.empty and not adv_core.empty:
                conv_comp = float(adv_conv["completion_rate"].mean())
                core_comp = float(adv_core["completion_rate"].mean())
                conv_tp = float(adv_conv["throughput"].mean())
                core_tp = float(adv_core["throughput"].mean())
                conv_turn = float(adv_conv["avg_turnaround_time"].mean())
                core_turn = float(adv_core["avg_turnaround_time"].mean())
                conv_pen = float(adv_conv["penalized_turnaround_time"].mean())
                core_pen = float(adv_core["penalized_turnaround_time"].mean())
                conv_thrash = float(adv_conv["thrashing_ticks"].mean())
                core_thrash = float(adv_core["thrashing_ticks"].mean())
                thrash_red = float(((conv_thrash - core_thrash) / conv_thrash) * 100.0) if conv_thrash > 0 else 0.0

                label_core = "CoReOS"
                turnaround_val = f"{core_turn:.1f} vs {conv_turn:.1f} ticks"
                turnaround_desc = f"{label_core} vs Conventional ({core_comp:.1f}% vs {conv_comp:.1f}% completion)"

                comp_diff = core_comp - conv_comp
                tp_pct = ((core_tp - conv_tp) / conv_tp) * 100.0 if conv_tp > 0 else 0.0

                stress_comparison = {
                    "workload": "adversarial_stress",
                    "baseline_conv": "A_Conventional",
                    "baseline_coreos": core_cand_name,
                    "conv_completion_rate": round(conv_comp, 1),
                    "coreos_completion_rate": round(core_comp, 1),
                    "comp_diff_pct": round(comp_diff, 1),
                    "comp_diff_text": f"{comp_diff:+.1f}% advantage" if comp_diff >= 0 else f"{comp_diff:.1f}% deficit",
                    "conv_throughput": round(conv_tp, 4),
                    "coreos_throughput": round(core_tp, 4),
                    "tp_diff_pct": round(tp_pct, 1),
                    "tp_diff_text": f"{tp_pct:+.1f}% jobs/tick",
                    "conv_completed_turnaround": round(conv_turn, 2),
                    "coreos_completed_turnaround": round(core_turn, 2),
                    "conv_penalized_turnaround": round(conv_pen, 2),
                    "coreos_penalized_turnaround": round(core_pen, 2),
                    "conv_thrashing": round(conv_thrash, 1),
                    "coreos_thrashing": round(core_thrash, 1),
                    "thrashing_reduction_pct": round(thrash_red, 1),
                    "survivorship_notice": f"Average turnaround time is measured strictly across completed processes. In adversarial stress, completion rates differ ({core_comp:.1f}% vs {conv_comp:.1f}%), making completed-job turnaround reflect survivorship bias. Penalized turnaround incorporates the 300-tick evaluation cutoff penalty for unfinished jobs."
                }
        except Exception:
            pass

    state_store.initialize_defaults()
    telemetry = []
    if state_store.latest_simulation_result:
        telemetry = state_store.latest_simulation_result.get("history", [])

    dataset_file = PROJECT_ROOT / "data" / "raw" / "Big_data_dataset.csv"
    unresolved_count = 0
    conflict_data_available = False
    if state_store._initialized and state_store.conflicts:
        conflict_data_available = True
        unresolved_count = sum(1 for c in state_store.conflicts if c.get("status") in ["Unresolved", "Ignored"])

    health = {
        "dataset_available": dataset_file.exists(),
        "latest_sim_status": "Completed" if state_store.latest_simulation_result else "Pending",
        "conflict_data_available": conflict_data_available,
        "unresolved_conflicts": unresolved_count,
        "total_conflicts": len(state_store.conflicts) if state_store._initialized else 0
    }

    return {
        "dataset_records": "10,000",
        "dataset_nulls": "Dataset Records",
        "evaluated_baselines": str(num_candidates),
        "evaluated_baselines_desc": "Evaluated Candidates (Final Canonical)",
        "decision_latency": f"{state_store.decision_overhead_ms:.2f} ms",
        "decision_latency_desc": "Decision Latency",
        "turnaround_improvement": turnaround_val,
        "turnaround_improvement_desc": turnaround_desc,
        "stress_comparison": stress_comparison,
        "highlights": highlights,
        "telemetry": telemetry,
        "workload_info": state_store.workload_info,
        "health": health
    }

