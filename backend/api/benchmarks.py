from fastapi import APIRouter
import pandas as pd
from pathlib import Path
from src.coreos.evaluation.experiments import ExperimentSuite

router = APIRouter()
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@router.get("/")
def get_benchmarks():
    bench_csv = PROJECT_ROOT / "reports" / "benchmark_results.csv"
    if bench_csv.exists():
        df_bench = pd.read_csv(bench_csv)
    else:
        suite = ExperimentSuite()
        df_bench = suite.run_benchmark_suite(["adversarial_stress", "steady_state"], num_seeds=2)

    df_bench = df_bench.replace({float('nan'): None})
    return {
        "workloads": sorted(df_bench["workload"].unique().tolist()),
        "data": df_bench.to_dict(orient="records")
    }
