"""
CoReOS Data Preprocessing & Baseline Anomaly Modeling
Extracts empirical priors for simulation calibration and trains real-world supervised baseline.
"""

from typing import Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score


class DataPreprocessor:
    def __init__(self, target_column: str = "status"):
        self.target_column = target_column
        self.scaler = StandardScaler()
        self.empirical_priors: Dict[str, Any] = {}

    def extract_empirical_priors(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculates statistical priors from real observations to calibrate the simulator."""
        priors = {}
        num_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != self.target_column]

        for col in num_cols:
            series = df[col]
            priors[col] = {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "p25": float(series.quantile(0.25)),
                "median": float(series.median()),
                "p75": float(series.quantile(0.75)),
                "max": float(series.max())
            }

        priors["correlations"] = df[num_cols].corr().to_dict()
        if self.target_column in df.columns:
            priors["anomaly_rate"] = float(df[self.target_column].mean())
        self.empirical_priors = priors
        return priors

    def prepare_train_test_split(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, list]:
        """Prepares scaled train/test splits for supervised anomaly detection."""
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns if c != self.target_column]
        X = df[feature_cols].values
        y = df[self.target_column].values

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state, stratify=y
        )
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)

        return X_train_scaled, X_test_scaled, y_train, y_test, feature_cols

    def train_anomaly_baseline(
        self,
        df: pd.DataFrame,
        test_size: float = 0.2,
        random_state: int = 42
    ) -> Dict[str, Any]:
        """Trains supervised Random Forest classifier to identify real IT system anomalies."""
        X_train, X_test, y_train, y_test, feature_names = self.prepare_train_test_split(
            df, test_size=test_size, random_state=random_state
        )

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

        importances = dict(zip(feature_names, [float(v) for v in clf.feature_importances_]))
        sorted_imp = dict(sorted(importances.items(), key=lambda i: i[1], reverse=True))

        return {
            "accuracy": float(report["accuracy"]),
            "anomaly_f1": f1_anomaly,
            "roc_auc": roc_auc,
            "feature_importance": sorted_imp,
            "classification_report": report
        }
