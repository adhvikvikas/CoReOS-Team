from fastapi import APIRouter
import pandas as pd
from fastapi.responses import FileResponse
from pathlib import Path

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@router.get("/ablation_summary")
def get_ablation_summary():
    ablation_csv = PROJECT_ROOT / "reports" / "ablation_results.csv"
    if ablation_csv.exists():
        adf = pd.read_csv(ablation_csv)
        asum_cols = [c for c in ["workload", "configuration", "completion_rate", "completed_processes", "unfinished_processes", "avg_turnaround_time", "throughput", "thrashing_ticks"] if c in adf.columns]
        asum = adf.groupby(["workload", "configuration"])[asum_cols[2:]].mean().reset_index()
        asum = asum.replace({float('nan'): None})
        return {"data": asum.to_dict(orient="records")}
    return {"data": []}

@router.get("/download/{filename}")
def download_report(filename: str):
    allowed_files = [
        "benchmark_results.csv",
        "benchmark_summary.csv",
        "paired_comparisons.csv",
        "ablation_summary.csv",
        "benchmark_analysis.md",
        "research_report.md"
    ]
    if filename not in allowed_files:
        return {"error": "File not allowed"}
        
    file_path = PROJECT_ROOT / "reports" / filename
    if file_path.exists():
        return FileResponse(path=str(file_path), filename=filename)
    return {"error": "File not found"}

@router.get("/content/{filename}")
def get_report_content(filename: str):
    allowed_files = ["benchmark_analysis.md", "research_report.md"]
    if filename not in allowed_files:
        return {"error": "File not allowed"}
        
    file_path = PROJECT_ROOT / "reports" / filename
    if file_path.exists():
        with open(file_path, "r") as f:
            return {"content": f.read()}
    return {"content": ""}
