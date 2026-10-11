"""
CoReOS Benchmark Execution Script
Runs Baselines A through F across specified workloads and exports reports/benchmark_results.csv.
"""

import sys
import argparse
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.config import load_config
from src.coreos.evaluation.experiments import ExperimentSuite
from src.coreos.evaluation.reporting import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="CoReOS Benchmark Suite Runner")
    parser.add_argument("--workloads", nargs="+", default=["steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "adversarial_stress"])
    parser.add_argument("--seeds", type=int, default=3, help="Number of random seeds per scenario")
    parser.add_argument("--output", type=str, default="reports/benchmark_results.csv")
    args = parser.parse_args()

    config = load_config()
    suite = ExperimentSuite(config)

    print("=" * 80)
    print(f"Executing CoReOS Benchmark Suite across {len(args.workloads)} workloads ({args.seeds} seeds each)...")
    print("=" * 80)

    df = suite.run_benchmark_suite(workload_types=args.workloads, num_seeds=args.seeds)
    out_path = PROJECT_ROOT / args.output
    ReportGenerator.export_csv(df, str(out_path))

    print(f"\nSaved benchmark results to: {out_path}")
    summary = ReportGenerator.compute_summary_table(df)
    print("\nBenchmark Summary (Mean ± 95% CI):")
    cols_to_print = ["workload", "baseline", "avg_turnaround_time_mean", "avg_turnaround_time_ci95", "throughput_mean", "jains_fairness_mean"]
    print(summary[[c for c in cols_to_print if c in summary.columns]])

    # Generate complete statistical summary and paired comparisons
    bench_summary_df = ReportGenerator.compute_statistical_summary(df, group_cols=["workload", "baseline"])
    bench_summary_path = out_path.parent / "benchmark_summary.csv"
    bench_summary_df.to_csv(bench_summary_path, index=False)
    print(f"Saved benchmark summary to: {bench_summary_path}")

    paired_df = ReportGenerator.compute_paired_comparisons(df)
    paired_path = out_path.parent / "paired_comparisons.csv"
    paired_df.to_csv(paired_path, index=False)
    print(f"Saved paired comparisons to: {paired_path}")


if __name__ == "__main__":
    main()
