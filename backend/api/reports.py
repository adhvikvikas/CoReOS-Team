from fastapi import APIRouter
import pandas as pd
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@router.get("/ablation_summary")
def get_ablation_summary():
    ablation_csv = PROJECT_ROOT / "reports" / "optimization" / "ablation_results.csv"
    if not ablation_csv.exists():
        ablation_csv = PROJECT_ROOT / "reports" / "ablation_results.csv"
    if ablation_csv.exists():
        adf = pd.read_csv(ablation_csv)
        if "configuration" not in adf.columns and "variant" in adf.columns:
            adf["configuration"] = adf["variant"]
        # Standardize configuration naming to official CoReOS
        adf["configuration"] = adf["configuration"].replace({
            "Champion_Full": "CoReOS (Full Architecture)",
            "Full_CoReOS": "CoReOS (Full Architecture)"
        })
        asum_cols = [c for c in ["workload", "configuration", "completion_rate", "completed_processes", "unfinished_processes", "avg_turnaround_time", "throughput", "thrashing_ticks"] if c in adf.columns]
        asum = adf.groupby(["workload", "configuration"])[asum_cols[2:]].mean().reset_index()
        asum = asum.replace({float('nan'): None})
        return {"data": asum.to_dict(orient="records")}
    return {"data": []}

@router.get("/download/{filename}")
def download_report(filename: str):
    allowed_files = [
        # Final Master Canonical Phase 10 Artifacts
        "final_canonical_benchmark_results.csv",
        "final_canonical_ranking_summary.csv",
        "final_canonical_per_workload_summary.csv",
        "final_canonical_statistical_comparisons.csv",
        "final_canonical_guardrail_compliance.csv",
        "final_canonical_optimization_report.md",
        "final_canonical_reproducibility.md",
        "canonical_manifest.json",
        # Phase 8 and Phase 9 Primary Artifacts
        "phase8_final_benchmark_results.csv",
        "phase8_final_ranking_summary.csv",
        "phase8_per_workload_summary.csv",
        "phase8_statistical_comparisons.csv",
        "phase8_final_competition_report.md",
        "phase8_reproducibility.md",
        "phase9_final_audit_report.md",
        # Historical Phase 3 and Prior Baselines
        "phase3_benchmark_results.csv",
        "phase3_benchmark_summary.csv",
        "phase3_paired_comparisons.csv",
        "phase3_benchmark_report.md",
        "benchmark_results.csv",
        "benchmark_summary.csv",
        "paired_comparisons.csv",
        "ablation_summary.csv",
        "ablation_results.csv",
        "benchmark_analysis.md",
        "research_report.md"
    ]
    if filename not in allowed_files:
        return {"error": "File not allowed"}
        
    opt_path = PROJECT_ROOT / "reports" / "optimization" / filename
    if opt_path.exists():
        return FileResponse(path=str(opt_path), filename=filename)

    file_path = PROJECT_ROOT / "reports" / filename
    if file_path.exists():
        return FileResponse(path=str(file_path), filename=filename)
    return {"error": "File not found"}

@router.get("/content/{filename}")
def get_report_content(filename: str):
    allowed_files = [
        "final_canonical_optimization_report.md",
        "final_canonical_reproducibility.md",
        "phase8_final_competition_report.md",
        "phase9_final_audit_report.md",
        "phase8_reproducibility.md",
        "phase3_benchmark_report.md",
        "benchmark_analysis.md",
        "research_report.md"
    ]
    if filename not in allowed_files:
        return {"error": "File not allowed"}
        
    opt_path = PROJECT_ROOT / "reports" / "optimization" / filename
    if opt_path.exists():
        with open(opt_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}

    file_path = PROJECT_ROOT / "reports" / filename
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return {"content": f.read()}
    return {"content": ""}
