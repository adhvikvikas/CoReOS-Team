"""
CoReOS Report Generation Script
Generates both reports/dataset_profile.md and reports/research_report.md from empirical data and benchmarks.
"""

import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.coreos.data.loader import DatasetLoader
from src.coreos.data.profiler import DatasetProfiler
from scripts.run_experiments import main as run_experiments_main


def main():
    print("=" * 80)
    print("CoReOS Report Generator: Profiling dataset and compiling research reports...")
    print("=" * 80)

    # 1. Dataset Profile
    loader = DatasetLoader()
    profiler = DatasetProfiler(loader)
    profile_path = PROJECT_ROOT / "reports" / "dataset_profile.md"
    profiler.generate_markdown_report(str(profile_path))
    print(f"Generated: {profile_path}")

    # 2. Run experiments to ensure latest CSV benchmarks
    run_experiments_main()

    print("\nAll reports and benchmark artifacts have been compiled into reports/")


if __name__ == "__main__":
    main()
