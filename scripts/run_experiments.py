"""
CoReOS Reproducible Experiment Execution Script
Executes full benchmark suite and ablation studies, computing confidence intervals
and saving experiment results to reports/.

Pipeline Design & Source of Truth:
- Benchmark Results: Sourced canonically from `src.coreos.evaluation.experiments.ExperimentSuite`
  and stored in `reports/benchmark_results.csv`. If `run_benchmarks.py` has already run, this script
  uses the existing results as the documented single source of truth without silently overwriting.
- Ablation Results: Sourced from `src.evaluation.ablation_runner.AblationRunner` and stored in
  `reports/ablation_results.csv`.
- Statistical Reporting: Computes summaries, paired comparisons, and Markdown analysis across
  both datasets.
"""

import os
import sys
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import load_config
from src.coreos.evaluation.experiments import ExperimentSuite
from src.coreos.evaluation.reporting import ReportGenerator
from src.evaluation.ablation_runner import AblationRunner


def main():
    parser = argparse.ArgumentParser(description="CoReOS Reproducible Experiment Suite Runner")
    parser.add_argument(
        "--workloads",
        nargs="+",
        default=["steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "adversarial_stress"],
        help="Workloads to evaluate in benchmark suite"
    )
    parser.add_argument(
        "--ablation-workloads",
        nargs="+",
        default=["steady_state", "adversarial_stress", "memory_thrashing"],
        help="Workloads to evaluate in ablation grid"
    )
    parser.add_argument(
        "--seeds",
        type=int,
        default=3,
        help="Number of standardized seeds per scenario (default: 3)"
    )
    parser.add_argument(
        "--benchmark-csv",
        type=str,
        default="reports/benchmark_results.csv",
        help="Path to canonical benchmark results (source of truth)"
    )
    parser.add_argument(
        "--ablation-csv",
        type=str,
        default="reports/ablation_results.csv",
        help="Path to ablation results CSV"
    )
    parser.add_argument(
        "--rerun-benchmarks",
        action="store_true",
        help="Force re-running benchmark suite even if benchmark CSV exists"
    )
    args = parser.parse_args()

    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    benchmark_csv_path = PROJECT_ROOT / args.benchmark_csv
    ablation_csv_path = PROJECT_ROOT / args.ablation_csv

    # 1. Benchmark Execution or Verification (Single Documented Source of Truth)
    if benchmark_csv_path.exists() and not args.rerun_benchmarks:
        print("=" * 80)
        print(f"CoReOS: Utilizing Canonical Benchmark Source of Truth: {benchmark_csv_path}")
        print("=" * 80)
        benchmark_df = pd.read_csv(benchmark_csv_path)
    else:
        print("=" * 80)
        print(f"CoReOS: Running Benchmark Suite via Primary ExperimentSuite ({len(args.workloads)} workloads, {args.seeds} seeds)")
        print("=" * 80)
        config = load_config()
        suite = ExperimentSuite(config)
        benchmark_df = suite.run_benchmark_suite(
            workload_types=args.workloads,
            num_seeds=args.seeds
        )
        ReportGenerator.export_csv(benchmark_df, str(benchmark_csv_path))
        print(f"Saved benchmark results to: {benchmark_csv_path}")

    # Compute aggregation
    summary = benchmark_df.groupby(["workload", "baseline"])[
        ["completion_rate", "completed_processes", "unfinished_processes", "avg_turnaround_time", "avg_waiting_time", "throughput", "jains_fairness", "thrashing_ticks", "decision_overhead_ms"]
    ].agg(["mean", "std"])
    print("\nBenchmark Suite Aggregate Summary:")
    print(summary)

    # 2. Comprehensive Ablation Studies
    print("\n" + "=" * 80)
    print("CoReOS: Running Comprehensive Ablation Studies")
    print("=" * 80)
    ablation_runner = AblationRunner()
    ablation_df = ablation_runner.run_full_ablation_grid(
        workload_types=args.ablation_workloads,
        num_seeds=args.seeds
    )
    ablation_df.to_csv(ablation_csv_path, index=False)
    print(f"Saved ablation results to: {ablation_csv_path}")

    ablation_summary = ablation_df.groupby(["workload", "configuration"])[
        ["completion_rate", "completed_processes", "unfinished_processes", "avg_turnaround_time", "throughput", "thrashing_ticks"]
    ].agg(["mean", "std"])
    print("\nAblation Suite Aggregate Summary:")
    print(ablation_summary)

    # 3. Generate Complete Statistical Summaries and Markdown Analysis
    print("\n" + "=" * 80)
    print("CoReOS: Generating Research Statistical Summaries & Paired Analysis")
    print("=" * 80)
    artifacts = ReportGenerator.generate_all_reports(
        benchmark_csv=str(benchmark_csv_path),
        ablation_csv=str(ablation_csv_path),
        output_dir=str(reports_dir)
    )
    for name, path in artifacts.items():
        print(f"Generated {name} -> {path}")


if __name__ == "__main__":
    main()
