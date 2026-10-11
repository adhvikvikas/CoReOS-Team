"""
CoReOS Dataset Profiler
Generates statistical profiles, temporal structure assessments, and exports reports/dataset_profile.md.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from src.coreos.data.loader import DatasetLoader

COLUMN_METADATA = {
    "cpu_utilization": {"unit": "%", "category": "CPU", "desc": "Percentage of CPU resources currently in use."},
    "memory_usage": {"unit": "%", "category": "Memory", "desc": "Percentage of RAM being utilized by running processes."},
    "disk_io": {"unit": "MB/s or IOPS", "category": "Storage", "desc": "Rate of data being read from and written to storage."},
    "network_latency": {"unit": "ms", "category": "Network", "desc": "Time delay for network packets to travel between endpoints."},
    "process_count": {"unit": "Count", "category": "Workload", "desc": "Total number of active processes running on the system."},
    "thread_count": {"unit": "Count", "category": "Concurrency", "desc": "Total number of active threads across all processes."},
    "context_switches": {"unit": "Count/Rate", "category": "CPU Overhead", "desc": "Number of times the CPU switches between processes."},
    "cache_miss_rate": {"unit": "% or Ratio", "category": "Memory Hierarchy", "desc": "Proportion of memory accesses that fail in CPU cache."},
    "temperature": {"unit": "°C", "category": "Thermals", "desc": "System temperature, typically of CPU or components."},
    "power_consumption": {"unit": "Watts", "category": "Energy", "desc": "Electrical power usage of the system."},
    "uptime": {"unit": "Hours", "category": "Stability", "desc": "Total time the system has run without a restart."},
    "status": {"unit": "Binary (0/1)", "category": "Target", "desc": "Operational status: 0 = Normal, 1 = Anomaly/Fault."}
}


class DatasetProfiler:
    def __init__(self, loader: Optional[DatasetLoader] = None):
        self.loader = loader or DatasetLoader()

    def profile(self, df: Optional[pd.DataFrame] = None) -> Dict[str, Any]:
        """Runs full empirical audit and profiling on dataset."""
        if df is None:
            df = self.loader.load()

        n_rows, n_cols = df.shape
        columns = list(df.columns)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}
        missing = df.isnull().sum().to_dict()
        duplicates = int(df.duplicated().sum())

        # Check for calendar timestamp fields (not uptime duration)
        has_timestamp = any(
            c in ["timestamp", "datetime", "date", "time"] or
            ("time" in c and c != "uptime")
            for c in columns
        )

        num_df = df.select_dtypes(include=[np.number])
        stats = num_df.describe().T
        if not num_df.empty:
            stats["skew"] = num_df.skew()
            stats["kurtosis"] = num_df.kurtosis()

        # Lag-1 Autocorrelation
        autocorr = {}
        for col in num_df.columns:
            if num_df[col].std() > 1e-6:
                autocorr[col] = float(num_df[col].autocorr(lag=1))
            else:
                autocorr[col] = 0.0

        status_dist = {}
        if "status" in df.columns:
            status_dist = df["status"].value_counts(dropna=False).to_dict()

        return {
            "rows": n_rows,
            "cols": n_cols,
            "columns": columns,
            "dtypes": dtypes,
            "missing": missing,
            "duplicates": duplicates,
            "has_timestamp": has_timestamp,
            "stats": stats.to_dict(orient="index") if not num_df.empty else {},
            "autocorrelation": autocorr,
            "status_distribution": status_dist
        }

    def generate_markdown_report(self, output_path: str = "reports/dataset_profile.md") -> str:
        """Generates markdown report documenting dataset verification."""
        df = self.loader.load()
        meta = self.loader.get_metadata()
        prof = self.profile(df)

        lines = [
            "# CoReOS Dataset Profile & Verification Report",
            "",
            "> [!IMPORTANT]",
            "> **Dataset Source**: Kaggle IT System Performance and Resource Metrics",
            f"> **File**: `{meta['filename']}` ({meta['size_bytes'] / (1024*1024):.2f} MB)",
            f"> **Observations**: {prof['rows']:,} rows | **Features**: {prof['cols']} columns",
            "",
            "## 1. Verified Schema & Documented Units",
            "",
            "| Feature | Inferred Dtype | Missing | Unit | Category | Description |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |"
        ]

        for col in prof["columns"]:
            dt = prof["dtypes"].get(col, "unknown")
            miss = prof["missing"].get(col, 0)
            cm = COLUMN_METADATA.get(col, {"unit": "Unknown", "category": "Unmapped", "desc": "Custom field"})
            lines.append(f"| `{col}` | `{dt}` | {miss} | {cm['unit']} | {cm['category']} | {cm['desc']} |")

        lines.extend([
            "",
            "## 2. Statistical Summary & Autocorrelation",
            "",
            f"- **Duplicate Records**: {prof['duplicates']}",
            f"- **Explicit Calendar Timestamps**: {'Present' if prof['has_timestamp'] else 'None (Uptime is duration hours)'}",
            f"- **Observed Lag-1 Autocorrelation Range**: `[{min(prof['autocorrelation'].values()):.4f}, {max(prof['autocorrelation'].values()):.4f}]`",
            "",
            "| Feature | Mean | Std | Min | 50% (Median) | Max | Skew | Lag-1 Autocorr |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
        ])

        for col, s in prof["stats"].items():
            ac = prof["autocorrelation"].get(col, 0.0)
            lines.append(
                f"| `{col}` | {s['mean']:.2f} | {s['std']:.2f} | {s['min']:.2f} | "
                f"{s['50%']:.2f} | {s['max']:.2f} | {s.get('skew', 0.0):.2f} | {ac:.4f} |"
            )

        lines.extend([
            "",
            "## 3. Data-to-Simulation Separation Boundary",
            "",
            "> [!NOTE]",
            "> CoReOS strictly separates **Empirical Real Observations** from **Simulated Process-Level Data**.",
            "- **Real Data**: Provides empirical probability marginals and correlations for overall system pressure.",
            "- **Simulated Workload**: Generates synthetic process execution trajectories (arrival times, CPU bursts, page faults, and I/O events).",
            "",
            "---",
            "*Report automatically generated by CoReOS Dataset Profiler.*"
        ])

        content = "\n".join(lines)
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, "w") as f:
            f.write(content)

        return content
