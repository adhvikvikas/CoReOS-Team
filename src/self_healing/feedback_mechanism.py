"""
CoReOS Self-Healing: Feedback Mechanism
Closes the loop between observed regressions, recovery efficacy,
and conflict-prediction sensitivity tuning.
"""

from typing import Dict, Any, List
from src.conflict_prediction.conflict_engine import ConflictEngine, ConflictPredictionResult
from src.self_healing.regression_detector import RegressionEvent


class FeedbackMechanism:
    def __init__(self, conflict_engine: ConflictEngine):
        self.conflict_engine = conflict_engine
        self.feedback_history: List[Dict[str, Any]] = []
        self.sensitivity_adjustments: int = 0

    def process_feedback(
        self,
        prediction: ConflictPredictionResult,
        regression_event: RegressionEvent,
        step: int
    ):
        """
        Adjusts system sensitivity when an unpredicted regression occurs (False Negative).
        """
        was_predicted = prediction.is_conflict
        is_regression = regression_event is not None

        # Record outcome for conflict predictor evaluation
        self.conflict_engine.record_ground_truth_outcome(prediction, is_regression)

        if is_regression and not was_predicted:
            # Unpredicted regression: tighten confidence threshold to increase recall
            old_thresh = self.conflict_engine.confidence_threshold
            new_thresh = max(0.40, old_thresh - 0.05)
            self.conflict_engine.confidence_threshold = new_thresh
            self.sensitivity_adjustments += 1
            
            self.feedback_history.append({
                "step": step,
                "event": "FALSE_NEGATIVE_ADJUSTMENT",
                "old_threshold": round(old_thresh, 2),
                "new_threshold": round(new_thresh, 2),
                "regression_type": regression_event.regression_type
            })

        elif not is_regression and was_predicted:
            self.feedback_history.append({
                "step": step,
                "event": "CONFLICT_AVERTED_OR_FALSE_POSITIVE",
                "conflict_type": prediction.conflict_type
            })

    def get_summary(self) -> Dict[str, Any]:
        return {
            "total_feedback_events": len(self.feedback_history),
            "sensitivity_adjustments": self.sensitivity_adjustments,
            "current_confidence_threshold": round(self.conflict_engine.confidence_threshold, 3)
        }
