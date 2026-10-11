"""
CoReOS Report Generation Script
Generates statistical summaries, paired difference comparisons on matched seeds,
and publication-ready Markdown reports from raw benchmark and ablation outputs.
"""

import sys
import argparse
from pathlib import Path

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.evaluation.reporting import ReportGenerator


def main():
    parser = argparse.ArgumentParser(description="CoReOS Statistical Reporting Generator")
    parser.add_argument(
        "--benchmark-csv",
        type=str,
        default="reports/benchmark_results.csv",
        help="Path to raw benchmark results CSV"
    )
    parser.add_argument(
        "--ablation-csv",
        type=str,
        default="reports/ablation_results.csv",
        help="Path to raw ablation results CSV"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="reports",
        help="Directory to save generated report artifacts"
    )
    args = parser.parse_args()

    bench_csv = PROJECT_ROOT / args.benchmark_csv
    abl_csv = PROJECT_ROOT / args.ablation_csv
    out_dir = PROJECT_ROOT / args.output_dir

    print("=" * 80)
    print("CoReOS: Generating Statistical Summaries & Paired Comparison Reports")
    print("=" * 80)
    print(f"Input Benchmark CSV: {bench_csv}")
    print(f"Input Ablation CSV:  {abl_csv}")
    print(f"Output Directory:    {out_dir}")

    artifacts = ReportGenerator.generate_all_reports(
        benchmark_csv=str(bench_csv),
        ablation_csv=str(abl_csv),
        output_dir=str(out_dir)
    )

    print("\nSuccessfully generated report artifacts:")
    for name, path in artifacts.items():
        print(f"  - [{name}]: {path}")

    print("\nReport generation complete.")


if __name__ == "__main__":
    main()
