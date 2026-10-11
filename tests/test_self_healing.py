"""
Unit Tests for CoReOS Self-Healing & Recovery
Tests regression detection, cooling-off period enforcement, and feedback tuning.
"""

import pytest
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism
from src.coreos.conflict_prediction.predictor import ConflictEngine, ConflictPredictionResult


def test_regression_detector_thrashing():
    detector = PerformanceRegressionDetector()
    state = {
        "time": 5.0,
        "throughput": 0.05,
        "avg_waiting_time": 20.0,
        "memory_utilization": 96.0,
        "is_thrashing": True
    }
    event = detector.observe_and_detect(state)
    assert event is not None
    assert event.regression_type == "THRASHING_STALL"


def test_recovery_engine_cooling_off():
    recovery = RecoveryEngine()
    state = {"time": 10.0, "is_thrashing": True, "memory_utilization": 95.0}

    detector = PerformanceRegressionDetector()
    event = detector.observe_and_detect(state)

    # Step 1: Corrective action applied
    ov1 = recovery.select_corrective_action(event, current_step=1, system_state=state)
    assert ov1 is not None
    assert ov1["memory_reclaim_target"] > 0

    # Step 2 (immediately inside cooling-off window): should be blocked (None)
    ov2 = recovery.select_corrective_action(event, current_step=2, system_state=state)
    assert ov2 is None

    # Step 10 (after cooling-off window): allowed
    ov3 = recovery.select_corrective_action(event, current_step=10, system_state=state)
    assert ov3 is not None


def test_feedback_mechanism_adaptation():
    engine = ConflictEngine(use_ml=False)
    initial_thresh = engine.confidence_threshold
    feedback = FeedbackMechanism(engine)

    # False negative: unpredicted conflict where regression actually occurred
    unpredicted = ConflictPredictionResult(
        is_conflict=False, conflict_type="NONE", confidence=0.8,
        contributing_agents=[], severity=0.0, rationale="", suggested_arbitration={}
    )
    detector = PerformanceRegressionDetector()
    reg_event = detector.observe_and_detect({"time": 1.0, "is_thrashing": True, "memory_utilization": 95.0})

    feedback.process_feedback(unpredicted, reg_event, step=1)
    assert engine.confidence_threshold < initial_thresh
    assert feedback.sensitivity_adjustments == 1
