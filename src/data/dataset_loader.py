"""
CoReOS Dataset Loader & Empirical Prior Estimator
Phase 2: Data Pipeline

Loads and validates Big_data_dataset.csv, extracts empirical priors,
and trains a real-world system anomaly detection baseline on actual data.
"""

from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score, f1_score


class SystemMetricsDataset:
    """Encapsulates real-world IT system metrics from Kaggle dataset."""

    FEATURE_COLUMNS = [
        "cpu_utilization",
        "memory_usage",
        "disk_io",
        "network_latency",
        "process_count",
        "thread_count",
        "context_switches",
        "cache_miss_rate",
        "temperature",
        "power_consumption",
        "uptime"
    ]
    TARGET_COLUMN = "status"

    def __init__(self, csv_path: str = "data/Big_data_dataset.csv"):
        self.csv_path = Path(csv_path)
        self.df: Optional[pd.DataFrame] = None
        self.scaler = StandardScaler()
        self.empirical_priors: Dict[str, Any] = {}
        self.anomaly_model: Optional[RandomForestClassifier] = None
        self.anomaly_metrics: Dict[str, Any] = {}

    def load_and_validate(self) -> pd.DataFrame:
        if not self.csv_path.exists():
            raise FileNotFoundError(
                f"Dataset not found at {self.csv_path}. Please place Big_data_dataset.csv in the data directory."
            )
        
        df = pd.read_csv(self.csv_path)
        df.columns = [c.strip().lower() for c in df.columns]

        # Verify columns
        missing_cols = [c for c in self.FEATURE_COLUMNS + [self.TARGET_COLUMN] if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Dataset missing required columns: {missing_cols}")

        self.df = df
        self._compute_empirical_priors()
        return self.df

    def _compute_empirical_priors(self):
        """Extract empirical distributions from real observations for simulation calibration."""
        if self.df is None:
            return

        priors = {}
        for col in self.FEATURE_COLUMNS:
            series = self.df[col]
            priors[col] = {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "p25": float(series.quantile(0.25)),
                "median": float(series.median()),
                "p75": float(series.quantile(0.75)),
                "p95": float(series.quantile(0.95)),
                "max": float(series.max())
            }

        # Cross-resource correlations
        priors["correlations"] = self.df[self.FEATURE_COLUMNS].corr().to_dict()
        
        # Anomaly rate in real data
        priors["anomaly_rate"] = float(self.df[self.TARGET_COLUMN].mean())
        self.empirical_priors = priors

    def get_empirical_priors(self) -> Dict[str, Any]:
        if not self.empirical_priors:
            self.load_and_validate()
        return self.empirical_priors

    def train_system_anomaly_baseline(self, test_size: float = 0.2, random_state: int = 42) -> Dict[str, Any]:
        """
        Trains a supervised anomaly detector on real status labels.
        Demonstrates the genuine task supported by the Kaggle dataset.
        """
        if self.df is None:
            self.load_and_validate()

        X = self.df[self.FEATURE_COLUMNS]
        y = self.df[self.TARGET_COLUMN]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )

        # Handle class imbalance (since status 1 is ~0.97%)
        clf = RandomForestClassifier(
            n_estimators=100,
            class_weight="balanced",
            random_state=random_state,
            n_jobs=-1
        )
        clf.fit(X_train, y_train)

        y_pred = clf.predict(X_test)
        y_prob = clf.predict_proba(X_test)[:, 1]

        report = classification_report(y_test, y_pred, output_dict=True)
        roc_auc = float(roc_auc_score(y_test, y_prob)) if len(np.unique(y_test)) > 1 else 0.5
        f1_anomaly = float(report["1"]["f1-score"]) if "1" in report else 0.0

        # Feature importances
        feature_importance = dict(zip(self.FEATURE_COLUMNS, [float(v) for v in clf.feature_importances_]))
        sorted_importance = dict(sorted(feature_importance.items(), key=lambda item: item[1], reverse=True))

        self.anomaly_model = clf
        self.anomaly_metrics = {
            "test_accuracy": float(report["accuracy"]),
            "anomaly_f1": f1_anomaly,
            "roc_auc": roc_auc,
            "classification_report": report,
            "feature_importance": sorted_importance
        }
        return self.anomaly_metrics


if __name__ == "__main__":
    ds = SystemMetricsDataset()
    df = ds.load_and_validate()
    print(f"Loaded real dataset: {df.shape[0]} rows, {df.shape[1]} columns.")
    metrics = ds.train_system_anomaly_baseline()
    print(f"Anomaly Baseline ROC-AUC: {metrics['roc_auc']:.4f}, Anomaly F1: {metrics['anomaly_f1']:.4f}")
    print("Top Predictive Real Features for Status Anomaly:")
    for feat, imp in list(metrics["feature_importance"].items())[:5]:
        print(f"  {feat}: {imp:.4f}")
