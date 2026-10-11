"""
CoReOS Dataset Inspection & Profiling Tool
Phase 1: Real-World Dataset Verification

Analyzes Big_data_dataset.csv from:
https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics/data
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import numpy as np

EXPECTED_COLUMNS_METADATA = {
    "cpu_utilization": {
        "unit": "% (Percentage)",
        "category": "CPU Resource",
        "description": "Percentage of CPU resources currently in use."
    },
    "memory_usage": {
        "unit": "% (Percentage)",
        "category": "Memory Resource",
        "description": "Percentage of RAM being utilized by running processes."
    },
    "disk_io": {
        "unit": "MB/s or IOPS",
        "category": "Storage / I/O",
        "description": "Rate of data being read from and written to storage."
    },
    "network_latency": {
        "unit": "ms (Milliseconds)",
        "category": "Network",
        "description": "Time delay for network packets to travel between endpoints."
    },
    "process_count": {
        "unit": "Count",
        "category": "Workload / Processes",
        "description": "Total number of active processes running on the system."
    },
    "thread_count": {
        "unit": "Count",
        "category": "Workload / Concurrency",
        "description": "Total number of active threads across all processes."
    },
    "context_switches": {
        "unit": "Count / Rate",
        "category": "CPU Scheduling Overhead",
        "description": "Number of times the CPU switches between processes/threads."
    },
    "cache_miss_rate": {
        "unit": "% or Ratio",
        "category": "Memory Hierarchy / Cache",
        "description": "Proportion of memory accesses failing in CPU cache."
    },
    "temperature": {
        "unit": "°C (Degrees Celsius)",
        "category": "Hardware / Thermals",
        "description": "System temperature, typically of CPU or mainboard."
    },
    "power_consumption": {
        "unit": "Watts (W)",
        "category": "Hardware / Energy",
        "description": "Electrical power usage of the system."
    },
    "uptime": {
        "unit": "Hours",
        "category": "System Stability",
        "description": "Total time the system has been running without a restart."
    },
    "status": {
        "unit": "Binary Indicator (0/1)",
        "category": "Target / Health Status",
        "description": "Operational status: 0 = Normal, 1 = Anomaly / Fault."
    }
}


def find_dataset(custom_path=None):
    candidate_paths = []
    if custom_path:
        candidate_paths.append(Path(custom_path))
    
    # Common repository and local locations
    base_dir = Path(__file__).resolve().parent.parent
    candidate_paths.extend([
        base_dir / "data" / "Big_data_dataset.csv",
        base_dir / "data" / "big_data_dataset.csv",
        base_dir.parent / "data" / "Big_data_dataset.csv",
        Path.home() / "Downloads" / "Big_data_dataset.csv",
        Path.home() / "Downloads" / "it-system-performance-and-resource-metrics" / "Big_data_dataset.csv",
    ])

    for p in candidate_paths:
        if p.exists() and p.is_file():
            return p
    return None


def inspect_dataset(csv_path: Path, output_report_path: Path = None):
    print(f"[CoReOS Inspector] Inspecting dataset at: {csv_path}")
    df = pd.read_csv(csv_path)

    # Basic stats
    n_rows, n_cols = df.shape
    columns = list(df.columns)
    dtypes = df.dtypes.to_dict()
    missing_vals = df.isnull().sum().to_dict()
    duplicate_rows = df.duplicated().sum()

    # Column name normalization check
    clean_cols = [c.strip().lower() for c in columns]
    col_mapping = dict(zip(columns, clean_cols))
    
    # Matching with expected columns
    matched_cols = {}
    unmatched_cols = []
    for raw_col, clean_col in col_mapping.items():
        if clean_col in EXPECTED_COLUMNS_METADATA:
            matched_cols[raw_col] = EXPECTED_COLUMNS_METADATA[clean_col]
        else:
            unmatched_cols.append(raw_col)

    missing_expected_cols = [k for k in EXPECTED_COLUMNS_METADATA if k not in clean_cols]

    # Numerical statistics
    num_df = df.select_dtypes(include=[np.number])
    stats_df = num_df.describe().T
    if not num_df.empty:
        stats_df["skew"] = num_df.skew()
        stats_df["kurtosis"] = num_df.kurtosis()

    # Temporal analysis
    # Check if explicit calendar timestamp exists (avoiding matching 'uptime')
    has_explicit_timestamp = any(
        c.lower() in ["timestamp", "datetime", "date", "time"] or 
        ("time" in c.lower() and c.lower() != "uptime")
        for c in columns
    )
    
    # Lag-1 Autocorrelation for numerical columns to evaluate whether row order reflects temporal sequence
    autocorr = {}
    for col in num_df.columns:
        if num_df[col].std() > 1e-6:
            autocorr[col] = float(num_df[col].autocorr(lag=1))
        else:
            autocorr[col] = 0.0

    # Target variable analysis
    status_col = None
    for raw_col, clean_col in col_mapping.items():
        if clean_col == "status":
            status_col = raw_col
            break

    status_dist = {}
    if status_col:
        status_dist = df[status_col].value_counts(dropna=False).to_dict()

    # Resource category mapping
    categories = {
        "CPU Metrics": [],
        "Memory Metrics": [],
        "I/O & Storage Metrics": [],
        "Network Metrics": [],
        "Process / Concurrency Workload": [],
        "Thermals & Power": [],
        "System Stability & Target": []
    }
    for col, clean_col in col_mapping.items():
        if clean_col in ["cpu_utilization", "context_switches"]:
            categories["CPU Metrics"].append(col)
        elif clean_col in ["memory_usage", "cache_miss_rate"]:
            categories["Memory Metrics"].append(col)
        elif clean_col in ["disk_io"]:
            categories["I/O & Storage Metrics"].append(col)
        elif clean_col in ["network_latency"]:
            categories["Network Metrics"].append(col)
        elif clean_col in ["process_count", "thread_count"]:
            categories["Process / Concurrency Workload"].append(col)
        elif clean_col in ["temperature", "power_consumption"]:
            categories["Thermals & Power"].append(col)
        elif clean_col in ["uptime", "status"]:
            categories["System Stability & Target"].append(col)

    # Suitability & Gap Analysis
    supports = [
        "System health and anomaly detection (binary status prediction)",
        "Correlative cross-resource modeling (e.g., CPU vs Temperature vs Power)",
        "System-level resource pressure characterization",
        "Simulation calibration: empirical probability distributions for overall system load and context switch rates"
    ]
    limitations = [
        "Lacks per-process identifiers (PID, arrival times, CPU burst lengths, memory allocations, page tables).",
        "Lacks individual I/O queue requests, disk seek times, and block sizes.",
        "Lacks high-resolution timestamps with documented sample intervals (seconds vs minutes).",
        "Does not record operating system scheduling decisions (FCFS vs Round Robin actions) or counterfactual outcomes.",
        "Crucial distinction: Real data reflects system-level operational aggregates; process-level execution trajectories must be simulated."
    ]

    # Generate Markdown Report
    report_lines = [
        "# CoReOS Dataset Profile & Verification Report",
        "",
        "> [!IMPORTANT]",
        "> **Dataset Origin**: Kaggle [IT System Performance and Resource Metrics](https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics/data)",
        f"> **File Analyzed**: `{csv_path.name}` ({os.path.getsize(csv_path) / (1024*1024):.2f} MB)",
        f"> **Total Observations**: {n_rows:,} rows",
        f"> **Total Columns**: {n_cols} columns",
        "",
        "## 1. Schema Verification and Column Metadata",
        "",
        f"Expected 12 columns confirmed: **{'YES' if len(clean_cols) == 12 and not missing_expected_cols else 'NO'}**",
        "",
        "| Column Name | Inferred Type | Missing Count | Documented Unit | Category | Description |",
        "| :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for col in columns:
        clean = col.strip().lower()
        meta = EXPECTED_COLUMNS_METADATA.get(clean, {
            "unit": "Unknown", "category": "Unmapped", "description": "Custom column"
        })
        dtype_str = str(dtypes[col])
        null_cnt = missing_vals[col]
        report_lines.append(f"| `{col}` | `{dtype_str}` | {null_cnt} | {meta['unit']} | {meta['category']} | {meta['description']} |")

    report_lines.extend([
        "",
        "## 2. Data Quality & Distribution Statistics",
        "",
        f"- **Duplicate Rows**: {duplicate_rows} ({duplicate_rows / n_rows * 100:.2f}%)",
        f"- **Missing Values**: Total {sum(missing_vals.values())} across all columns",
        "",
        "### Numerical Summary Statistics",
        "",
        "| Feature | Mean | Std | Min | 25% | 50% (Median) | 75% | Max | Skewness | Lag-1 Autocorr |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ])

    for col in num_df.columns:
        row = stats_df.loc[col]
        ac = autocorr.get(col, 0.0)
        report_lines.append(
            f"| `{col}` | {row['mean']:.2f} | {row['std']:.2f} | {row['min']:.2f} | "
            f"{row['25%']:.2f} | {row['50%']:.2f} | {row['75%']:.2f} | {row['max']:.2f} | "
            f"{row['skew']:.2f} | {ac:.4f} |"
        )

    report_lines.extend([
        "",
        "## 3. Temporal Structure & Ordering Analysis",
        "",
        f"- **Explicit Timestamp Field**: {'Present' if has_explicit_timestamp else 'None detected in dataset'}",
        f"- **Autocorrelation Analysis**:",
        "  - If observations were a contiguous time series sampled at sub-second or minute intervals, consecutive metrics would typically exhibit strong positive autocorrelation ($r > 0.7$).",
        f"  - Observed Lag-1 Autocorrelation range: `[{min(autocorr.values()):.4f}, {max(autocorr.values()):.4f}]`.",
    ])

    # Assess whether rows appear shuffled or steady
    avg_ac = np.mean(list(autocorr.values())) if autocorr else 0.0
    if abs(avg_ac) < 0.15:
        report_lines.append("  - **Finding**: Near-zero autocorrelation indicates observations may be permuted or independently sampled snapshots across distributed systems, rather than an unpermuted single-machine high-frequency time series.")
        report_lines.append("  - **Methodological Rule**: We must **NOT** assume row indices represent a continuous clock time without documented sampling intervals. For simulation calibration, empirical distributions and joint copulas must be utilized.")
    else:
        report_lines.append(f"  - **Finding**: Mild-to-moderate temporal autocorrelation ($r={avg_ac:.3f}$). Temporal split or block-based cross-validation is recommended.")

    report_lines.extend([
        "",
        "## 4. Target Label & Class Distribution",
        "",
        f"- Target Column: `{status_col}`",
    ])
    if status_col:
        for val, count in status_dist.items():
            report_lines.append(f"  - Status `{val}`: {count:,} records ({count/n_rows*100:.2f}%)")
    else:
        report_lines.append("  - No `status` column identified.")

    report_lines.extend([
        "",
        "## 5. Resource Categorization in CoReOS",
        "",
        "| Resource Domain | Dataset Features | Simulator Role |",
        "| :--- | :--- | :--- |",
        f"| **CPU Agent** | `{', '.join(categories['CPU Metrics'])}` | Drives simulated process burst times, queue length, and CPU utilization calibration |",
        f"| **Memory Agent** | `{', '.join(categories['Memory Metrics'])}` | Drives simulated memory footprint, cache contention, and page pressure |",
        f"| **I/O Agent** | `{', '.join(categories['I/O & Storage Metrics'])}` | Drives simulated I/O bursts, queue delays, and throughput limits |",
        f"| **System Context** | `{', '.join(categories['Network Metrics'] + categories['Thermals & Power'] + categories['System Stability & Target'])}` | Environmental context features for Conflict Prediction and Regression Detection |",
        "",
        "## 6. Data-to-Simulation Separation & Scope Boundaries",
        "",
        "> [!NOTE]",
        "> CoReOS strictly separates **Empirical Real Observations** from **Simulated Process-Level Data**.",
        "",
        "### Supported Real-Data Applications:",
        "".join([f"- {s}\n" for s in supports]),
        "",
        "### Inherent Limitations & Simulation Requirements:",
        "".join([f"- {lim}\n" for lim in limitations]),
        "",
        "### Synthetic Workload Generator Calibration Strategy:",
        "- Process arrival times: Poisson process calibrated to empirical `process_count` and `thread_count` distributions.",
        "- CPU burst lengths: Lognormal/Exponential distribution calibrated to `cpu_utilization` and `context_switches`.",
        "- Memory demand: Gaussian mixture calibrated to empirical `memory_usage` and `cache_miss_rate`.",
        "- I/O operations: Bursty distribution calibrated to empirical `disk_io` and `network_latency`.",
        "",
        "---",
        "*Report automatically generated by CoReOS Dataset Profiler.*"
    ])

    report_content = "\n".join(report_lines)

    if output_report_path:
        output_report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_report_path, "w") as f:
            f.write(report_content)
        print(f"[CoReOS Inspector] Saved profile report to: {output_report_path}")

    return {
        "rows": n_rows,
        "cols": n_cols,
        "columns": columns,
        "clean_cols": clean_cols,
        "missing": missing_vals,
        "duplicates": duplicate_rows,
        "status_distribution": status_dist,
        "report_content": report_content
    }


def main():
    parser = argparse.ArgumentParser(description="CoReOS Dataset Inspector")
    parser.add_argument("--data-path", type=str, default=None, help="Path to Big_data_dataset.csv")
    parser.add_argument("--report-path", type=str, default="reports/dataset_profile.md", help="Output markdown report path")
    args = parser.parse_args()

    found_path = find_dataset(args.data_path)
    if not found_path:
        print("=" * 80)
        print("[ERROR] Big_data_dataset.csv NOT FOUND LOCALLY.")
        print("=" * 80)
        print("Please follow these steps to place the dataset:")
        print("1. Download 'Big_data_dataset.csv' from Kaggle:")
        print("   https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics/data")
        print("2. Place the file in the project's data directory:")
        print(f"   Destination: {Path(__file__).resolve().parent.parent / 'data' / 'Big_data_dataset.csv'}")
        print("3. Re-run this inspection script:")
        print("   python scripts/inspect_dataset.py")
        print("=" * 80)
        sys.exit(1)

    output_path = Path(__file__).resolve().parent.parent / args.report_path
    inspect_dataset(found_path, output_path)


if __name__ == "__main__":
    main()
