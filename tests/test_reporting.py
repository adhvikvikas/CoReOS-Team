"""
Unit Tests for CoReOS Statistical Reporting & Artifact Generation
Tests Student's t confidence intervals, small sample limits, matched-seed paired differences,
missing/unmatched seed handling, and deterministic report generation.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest
from scipy import stats

from src.coreos.evaluation.reporting import ReportGenerator


def test_confidence_interval_standard_calculation():
    """Verifies Student's t confidence interval against direct analytic formulation."""
    vals = [10.0, 12.0, 14.0]
    mean_val, std_val, ci_half, ci_low, ci_high = ReportGenerator.calculate_confidence_interval(vals, confidence=0.95)

    assert mean_val == 12.0
    assert std_val == 2.0

    # Manual analytical calculation: N=3, df=2
    # t_crit for 95% two-tailed is stats.t.ppf(0.975, df=2)
    expected_t = stats.t.ppf(0.975, df=2)
    expected_half = expected_t * (2.0 / np.sqrt(3))

    assert abs(ci_half - expected_half) < 1e-6
    assert abs(ci_low - (12.0 - expected_half)) < 1e-6
    assert abs(ci_high - (12.0 + expected_half)) < 1e-6


def test_confidence_interval_small_sample_and_zero_variance():
    """Verifies robust handling of N=1, N=0, zero-variance, and NaN values."""
    # N = 1: standard deviation undefined/zero; interval half-width must be 0.0
    m1, s1, h1, l1, hi1 = ReportGenerator.calculate_confidence_interval([42.0])
    assert m1 == 42.0
    assert s1 == 0.0
    assert h1 == 0.0
    assert l1 == 42.0
    assert hi1 == 42.0

    # N = 0: empty input
    m0, s0, h0, l0, hi0 = ReportGenerator.calculate_confidence_interval([])
    assert m0 == 0.0
    assert s0 == 0.0
    assert h0 == 0.0

    # Zero variance (all elements identical)
    mz, sz, hz, lz, hiz = ReportGenerator.calculate_confidence_interval([5.0, 5.0, 5.0, 5.0])
    assert mz == 5.0
    assert sz == 0.0
    assert hz == 0.0
    assert lz == 5.0
    assert hiz == 5.0

    # NaN / Inf filtering
    mnan, snan, hnan, lnan, hinan = ReportGenerator.calculate_confidence_interval([10.0, np.nan, 14.0, np.inf, 12.0])
    assert mnan == 12.0
    assert snan == 2.0


def test_statistical_summary_computation():
    """Verifies compute_statistical_summary aggregates mean, std, CI, min, max across seeds."""
    mock_df = pd.DataFrame([
        {"workload": "w1", "baseline": "B1", "seed": 42, "completion_rate": 100.0, "throughput": 0.20},
        {"workload": "w1", "baseline": "B1", "seed": 101, "completion_rate": 100.0, "throughput": 0.22},
        {"workload": "w1", "baseline": "B1", "seed": 202, "completion_rate": 100.0, "throughput": 0.24},
        {"workload": "w1", "baseline": "B2", "seed": 42, "completion_rate": 50.0, "throughput": 0.10},
        {"workload": "w1", "baseline": "B2", "seed": 101, "completion_rate": 60.0, "throughput": 0.12},
        {"workload": "w1", "baseline": "B2", "seed": 202, "completion_rate": 70.0, "throughput": 0.14},
    ])

    summary = ReportGenerator.compute_statistical_summary(mock_df, group_cols=["workload", "baseline"])
    assert len(summary) == 2
    b1_row = summary[(summary["workload"] == "w1") & (summary["baseline"] == "B1")].iloc[0]

    assert b1_row["runs"] == 3
    assert b1_row["completion_rate_mean"] == 100.0
    assert b1_row["completion_rate_std"] == 0.0
    assert b1_row["completion_rate_ci95"] == 0.0
    assert b1_row["throughput_mean"] == 0.22
    assert b1_row["throughput_min"] == 0.20
    assert b1_row["throughput_max"] == 0.24


def test_paired_differences_matched_seeds():
    """Verifies paired differences on exactly matched seeds."""
    mock_df = pd.DataFrame([
        # Treatment
        {"workload": "steady", "baseline": "E_CompleteCoReOS", "seed": 42, "throughput": 0.25, "completion_rate": 100.0},
        {"workload": "steady", "baseline": "E_CompleteCoReOS", "seed": 101, "throughput": 0.20, "completion_rate": 100.0},
        {"workload": "steady", "baseline": "E_CompleteCoReOS", "seed": 202, "throughput": 0.18, "completion_rate": 100.0},
        # Control
        {"workload": "steady", "baseline": "A_Conventional", "seed": 42, "throughput": 0.20, "completion_rate": 100.0},
        {"workload": "steady", "baseline": "A_Conventional", "seed": 101, "throughput": 0.15, "completion_rate": 100.0},
        {"workload": "steady", "baseline": "A_Conventional", "seed": 202, "throughput": 0.10, "completion_rate": 100.0},
    ])

    paired = ReportGenerator.compute_paired_comparisons(
        mock_df,
        treatment="E_CompleteCoReOS",
        controls=["A_Conventional"],
        metric_cols=["throughput", "completion_rate"]
    )

    assert len(paired) == 2
    tp_row = paired[paired["metric"] == "throughput"].iloc[0]
    # Diffs: (0.25-0.20)=0.05, (0.20-0.15)=0.05, (0.18-0.10)=0.08 -> mean diff = 0.06
    assert tp_row["n_pairs"] == 3
    assert abs(tp_row["mean_difference"] - 0.06) < 1e-4
    assert tp_row["direction"] == "positive"
    assert tp_row["favorable_to"] == "CoReOS"


def test_paired_differences_missing_or_unmatched_seeds():
    """Verifies that unmatched seeds are safely isolated and do not skew comparisons."""
    mock_df = pd.DataFrame([
        # Treatment has seeds 42, 101, 999
        {"workload": "w", "baseline": "E_CompleteCoReOS", "seed": 42, "throughput": 0.20},
        {"workload": "w", "baseline": "E_CompleteCoReOS", "seed": 101, "throughput": 0.30},
        {"workload": "w", "baseline": "E_CompleteCoReOS", "seed": 999, "throughput": 0.99},
        # Control has seeds 42, 101, 888
        {"workload": "w", "baseline": "A_Conventional", "seed": 42, "throughput": 0.10},
        {"workload": "w", "baseline": "A_Conventional", "seed": 101, "throughput": 0.20},
        {"workload": "w", "baseline": "A_Conventional", "seed": 888, "throughput": 0.01},
    ])

    paired = ReportGenerator.compute_paired_comparisons(
        mock_df,
        treatment="E_CompleteCoReOS",
        controls=["A_Conventional"],
        metric_cols=["throughput"]
    )

    assert len(paired) == 1
    row = paired.iloc[0]
    # Should only pair on seeds 42 and 101 (N_pairs = 2)
    assert row["n_pairs"] == 2
    # Diffs: (0.20 - 0.10) = 0.10, (0.30 - 0.20) = 0.10 -> mean diff = 0.10
    assert abs(row["mean_difference"] - 0.10) < 1e-4

    # Completely disjoint seeds: Treatment on [1, 2], Control on [3, 4]
    disjoint_df = pd.DataFrame([
        {"workload": "w", "baseline": "E_CompleteCoReOS", "seed": 1, "throughput": 0.20},
        {"workload": "w", "baseline": "E_CompleteCoReOS", "seed": 2, "throughput": 0.30},
        {"workload": "w", "baseline": "A_Conventional", "seed": 3, "throughput": 0.10},
        {"workload": "w", "baseline": "A_Conventional", "seed": 4, "throughput": 0.20},
    ])

    paired_disjoint = ReportGenerator.compute_paired_comparisons(
        disjoint_df,
        treatment="E_CompleteCoReOS",
        controls=["A_Conventional"],
        metric_cols=["throughput"]
    )
    assert len(paired_disjoint) == 1
    assert paired_disjoint.iloc[0]["n_pairs"] == 0
    assert paired_disjoint.iloc[0]["favorable_to"] == "No Data"


def test_paired_differences_directionality_and_survivorship_caveat():
    """Verifies proper directionality and survivorship bias warning generation."""
    mock_df = pd.DataFrame([
        # CoReOS completed only 12 jobs (30%), turnaround = 60.0
        {"workload": "stress", "baseline": "E_CompleteCoReOS", "seed": 42, "completion_rate": 30.0, "avg_turnaround_time": 60.0},
        # Conventional completed 20 jobs (50%), turnaround = 120.0
        {"workload": "stress", "baseline": "A_Conventional", "seed": 42, "completion_rate": 50.0, "avg_turnaround_time": 120.0},
    ])

    paired = ReportGenerator.compute_paired_comparisons(
        mock_df,
        treatment="E_CompleteCoReOS",
        controls=["A_Conventional"],
        metric_cols=["completion_rate", "avg_turnaround_time"]
    )

    comp_row = paired[paired["metric"] == "completion_rate"].iloc[0]
    # Difference: 30 - 50 = -20.0 (Conventional completed more jobs)
    assert comp_row["mean_difference"] == -20.0
    assert comp_row["favorable_to"] == "A_Conventional"

    ta_row = paired[paired["metric"] == "avg_turnaround_time"].iloc[0]
    # Turnaround caveat must be present because completion rates diverge by 20%
    assert "Survivorship bias caveat" in ta_row["note"]
    assert "completed jobs only" in ta_row["note"]


def test_deterministic_report_generation_artifacts(tmp_path):
    """Verifies that generate_all_reports produces all 4 expected artifacts deterministically."""
    # Run generator targeting temporary output directory
    artifacts = ReportGenerator.generate_all_reports(output_dir=str(tmp_path))

    expected_keys = ["benchmark_summary", "ablation_summary", "paired_comparisons", "benchmark_analysis"]
    for key in expected_keys:
        assert key in artifacts
        file_path = artifacts[key]
        assert file_path.exists(), f"Expected artifact {file_path} to exist"
        assert file_path.stat().st_size > 0, f"Expected artifact {file_path} to be non-empty"

    # Verify Markdown report contains essential sections
    md_content = artifacts["benchmark_analysis"].read_text()
    assert "# CoReOS Benchmark & Statistical Analysis Report" in md_content
    assert "## 1. Executive Summary" in md_content
    assert "## 2. Statistical Methodology" in md_content
    assert "## 3. Workload Completion Rates" in md_content
    assert "## 4. Primary Paired Comparisons" in md_content
    assert "## 6. Honest Appraisal" in md_content
    assert "Survivorship Bias" in md_content


def test_bounded_confidence_intervals_clamping():
    """Verifies that confidence intervals for bounded metrics are clamped to valid ranges."""
    # High variance sample with N=3 that would produce negative and >100 intervals if unconstrained
    vals = [10.0, 50.0, 90.0]
    mean_val, std_val, ci_half, ci_low, ci_high = ReportGenerator.calculate_confidence_interval(
        vals, bounds=(0.0, 100.0)
    )
    assert ci_low == 0.0
    assert ci_high == 100.0
    assert ci_half > 50.0  # Raw half-width remains preserved

    # Fairness index bounded in [0.0, 1.0]
    fairness_vals = [0.1, 0.9, 0.5]
    m_f, s_f, ci_h_f, ci_l_f, ci_hi_f = ReportGenerator.calculate_confidence_interval(
        fairness_vals, bounds=(0.0, 1.0)
    )
    assert 0.0 <= ci_l_f <= m_f
    assert m_f <= ci_hi_f <= 1.0

    # compute_statistical_summary automatically clamps bounded metrics
    mock_df = pd.DataFrame([
        {"workload": "stress", "baseline": "B1", "seed": 1, "completion_rate": 10.0, "jains_fairness": 0.2},
        {"workload": "stress", "baseline": "B1", "seed": 2, "completion_rate": 80.0, "jains_fairness": 0.9},
        {"workload": "stress", "baseline": "B1", "seed": 3, "completion_rate": 20.0, "jains_fairness": 0.3},
    ])
    summary = ReportGenerator.compute_statistical_summary(mock_df, group_cols=["workload", "baseline"])
    row = summary.iloc[0]
    assert row["completion_rate_ci95_low"] >= 0.0
    assert row["completion_rate_ci95_high"] <= 100.0
    assert row["jains_fairness_ci95_low"] >= 0.0
    assert row["jains_fairness_ci95_high"] <= 1.0
