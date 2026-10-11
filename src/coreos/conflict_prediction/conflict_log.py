"""
CoReOS Conflict Logging & Evaluation
Tracks pre-decision conflict predictions and matches them against eventual simulation outcomes.
"""

from typing import List, Dict, Any, Optional


class ConflictLog:
    """
    Maintains rigorous temporal separation between prediction and outcome observation.
    Logs simulation step, candidate actions, conflict prediction, coordinator response,
    and ground-truth outcomes to evaluate Precision, Recall, F1, FPR, FNR.
    """

    def __init__(self):
        self.records: List[Dict[str, Any]] = []

    def log_prediction(
        self,
        step: int,
        candidate_actions: Dict[str, Any],
        is_conflict: bool,
        conflict_type: str,
        severity: float,
        confidence: float,
        coordinator_response: Dict[str, Any]
    ) -> int:
        record_idx = len(self.records)
        self.records.append({
            "step": step,
            "candidate_actions": candidate_actions,
            "predicted_conflict": is_conflict,
            "conflict_type": conflict_type,
            "severity": round(severity, 3),
            "confidence": round(confidence, 3),
            "coordinator_response": coordinator_response,
            "observed_regression": None,
            "is_correct": None
        })
        return record_idx

    def record_outcome(self, record_idx: int, was_regression_observed: bool):
        if 0 <= record_idx < len(self.records):
            rec = self.records[record_idx]
            rec["observed_regression"] = was_regression_observed
            rec["is_correct"] = (rec["predicted_conflict"] == was_regression_observed)

    def compute_metrics(self) -> Dict[str, Any]:
        """Calculates Precision, Recall, F1-score, False-Positive and False-Negative Rates."""
        evaluated = [r for r in self.records if r["observed_regression"] is not None]
        if not evaluated:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "fpr": 0.0, "fnr": 0.0, "total": 0}

        tp = sum(1 for r in evaluated if r["predicted_conflict"] and r["observed_regression"])
        fp = sum(1 for r in evaluated if r["predicted_conflict"] and not r["observed_regression"])
        tn = sum(1 for r in evaluated if not r["predicted_conflict"] and not r["observed_regression"])
        fn = sum(1 for r in evaluated if not r["predicted_conflict"] and r["observed_regression"])

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0
        fnr = fn / (fn + tp) if (fn + tp) > 0 else 0.0

        return {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "fpr": round(fpr, 4),
            "fnr": round(fnr, 4),
            "tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "total_evaluations": len(evaluated)
        }
