"""
Unit Tests for CoReOS Conflict Prediction Engine
Tests hazard classification rules, ML inference, and conflict logging metrics.
"""

import pytest
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.conflict_prediction.conflict_log import ConflictLog
from src.coreos.agents.base import AgentAction


def test_conflict_engine_rules():
    engine = ConflictEngine(use_ml=False)

    # 1. Triple cascade
    state_triple = {"cpu_utilization": 88.0, "memory_utilization": 88.0, "io_saturation": 82.0}
    actions = {
        "CPU_AGENT": AgentAction("CPU_AGENT", "SET_CPU_SCHEDULE", {"quantum": 4.0}),
        "MEMORY_AGENT": AgentAction("MEMORY_AGENT", "MONITOR_HEALTHY"),
        "IO_AGENT": AgentAction("IO_AGENT", "DIRECT_DISPATCH")
    }
    pred = engine.predict_conflict(state_triple, actions)
    assert pred.is_conflict is True
    assert pred.conflict_type == "TRIPLE_CASCADE"

    # 2. Thrashing CPU collapse
    state_thrash = {"cpu_utilization": 50.0, "memory_utilization": 90.0, "is_thrashing": True}
    actions["CPU_AGENT"].parameters["quantum"] = 2.0
    pred2 = engine.predict_conflict(state_thrash, actions)
    assert pred2.is_conflict is True
    assert pred2.conflict_type == "THRASHING_CPU_COLLAPSE"


def test_conflict_log_confusion_metrics():
    log = ConflictLog()

    idx1 = log.log_prediction(step=1, candidate_actions={}, is_conflict=True, conflict_type="TEST", severity=0.8, confidence=0.9, coordinator_response={})
    idx2 = log.log_prediction(step=2, candidate_actions={}, is_conflict=False, conflict_type="NONE", severity=0.0, confidence=0.9, coordinator_response={})

    # Ground truth: idx1 was true positive, idx2 was true negative
    log.record_outcome(idx1, was_regression_observed=True)
    log.record_outcome(idx2, was_regression_observed=False)

    metrics = log.compute_metrics()
    assert metrics["precision"] == 1.0
    assert metrics["recall"] == 1.0
    assert metrics["f1"] == 1.0
    assert metrics["tp"] == 1
    assert metrics["tn"] == 1
