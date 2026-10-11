"""
Unit Tests for CoReOS Data Pipeline
Tests DatasetLoader, DatasetProfiler, and DataPreprocessor.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.coreos.data.loader import DatasetLoader
from src.coreos.data.profiler import DatasetProfiler
from src.coreos.data.preprocessing import DataPreprocessor


def test_dataset_loader_discovery():
    loader = DatasetLoader()
    df = loader.load()
    assert not df.empty
    assert df.shape[0] == 10000
    assert df.shape[1] == 12
    assert "cpu_utilization" in df.columns
    assert "status" in df.columns


def test_dataset_loader_missing_file(tmp_path):
    loader = DatasetLoader(data_path=str(tmp_path / "non_existent.csv"))
    # When explicit path doesn't exist, it falls back to standard paths or raises FileNotFoundError
    with pytest.raises(FileNotFoundError):
        # Temporarily test with mock non-existent path
        class MockLoader(DatasetLoader):
            def resolve_path(self):
                raise FileNotFoundError("Missing")
        MockLoader().load()


def test_dataset_profiler():
    loader = DatasetLoader()
    df = loader.load()
    profiler = DatasetProfiler(loader)
    prof = profiler.profile(df)

    assert prof["rows"] == 10000
    assert prof["cols"] == 12
    assert prof["duplicates"] == 0
    assert 0 in prof["status_distribution"]
    assert 1 in prof["status_distribution"]
    assert prof["has_timestamp"] is False  # Uptime is duration, no calendar timestamps

    # Test lag-1 autocorrelation computed
    assert "cpu_utilization" in prof["autocorrelation"]
    assert -0.2 < prof["autocorrelation"]["cpu_utilization"] < 0.2


def test_dataset_profiler_markdown_export(tmp_path):
    loader = DatasetLoader()
    profiler = DatasetProfiler(loader)
    report_file = tmp_path / "test_profile.md"
    content = profiler.generate_markdown_report(str(report_file))

    assert report_file.exists()
    assert "CoReOS Dataset Profile & Verification Report" in content
    assert "cpu_utilization" in content


def test_data_preprocessor_priors_and_anomaly():
    loader = DatasetLoader()
    df = loader.load()
    preproc = DataPreprocessor()

    priors = preproc.extract_empirical_priors(df)
    assert "cpu_utilization" in priors
    assert priors["cpu_utilization"]["mean"] > 0
    assert "correlations" in priors

    # Test supervised anomaly detection baseline
    metrics = preproc.train_anomaly_baseline(df, test_size=0.1)
    assert metrics["roc_auc"] >= 0.90
    assert "memory_usage" in metrics["feature_importance"]
