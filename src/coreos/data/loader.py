"""
CoReOS Dataset Loader
Robust discovery, validation, and loading of the Kaggle IT System Performance dataset.
"""

from pathlib import Path
from typing import Optional, List, Tuple
import pandas as pd


class DatasetLoader:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.resolved_path: Optional[Path] = None

    def resolve_path(self) -> Path:
        """Discovers the dataset path using standard project locations and fallbacks."""
        if self.data_path:
            p = Path(self.data_path)
            if p.exists() and p.is_file():
                self.resolved_path = p
                return p

        # Search candidates in order of preference
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        candidates = [
            base_dir / "data" / "raw" / "Big_data_dataset.csv",
            base_dir / "data" / "Big_data_dataset.csv",
            base_dir / "data" / "processed" / "Big_data_dataset.csv",
            Path("data/raw/Big_data_dataset.csv"),
            Path("data/Big_data_dataset.csv"),
            Path.home() / "Downloads" / "Big_data_dataset.csv"
        ]

        for cand in candidates:
            if cand.exists() and cand.is_file():
                self.resolved_path = cand.resolve()
                return self.resolved_path

        raise FileNotFoundError(
            "Big_data_dataset.csv not found. Please place the downloaded Kaggle file at "
            "'data/raw/Big_data_dataset.csv' or 'data/Big_data_dataset.csv'."
        )

    def load(self) -> pd.DataFrame:
        """Loads and performs schema validation on the CSV."""
        path = self.resolve_path()
        try:
            df = pd.read_csv(path)
        except Exception as e:
            raise ValueError(f"Failed to parse CSV file at {path}: {e}")

        if df.empty:
            raise ValueError(f"The dataset file at {path} is empty.")

        # Standardize column headers
        df.columns = [c.strip().lower() for c in df.columns]
        return df

    def get_metadata(self) -> dict:
        """Returns metadata about the file on disk."""
        path = self.resolve_path()
        return {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "filename": path.name
        }
