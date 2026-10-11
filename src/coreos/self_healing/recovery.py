"""
CoReOS Self-Healing: Recovery Engine & Feedback Mechanism
Applies forward corrective actions, prevents policy flapping, and tunes prediction sensitivity.
"""

from typing import Dict, Any, Optional, List
from src.coreos.config import SelfHealingConfig
from src.coreos.self_healing.regression_detector import RegressionEvent


class RecoveryEngine:
    def __init__(self, config: Optional[SelfHealingConfig] = None):
        self.config = config or SelfHealingConfig()
        self.last_recovery_step: int = -100
        self.active_recovery: Optional[RegressionEvent] = None
        self.active_recovery_start_time: float = 0.0
        self.recovery_records: List[Dict[str, Any]] = []
        self.policy_switches: int = 0

    def select_corrective_action(
        self,
        event: RegressionEvent,
        current_step: int,
        system_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        # Enforce cooling-off period to prevent repeated switching
        if (current_step - self.last_recovery_step) < self.config.cooling_off_period:
            return None

        self.last_recovery_step = current_step
        self.active_recovery = event
        self.active_recovery_start_time = system_state.get("time", 0.0)
        self.policy_switches += 1

        corrective = {}
        if event.regression_type == "THRASHING_STALL":
            corrective = {
                "memory_reclaim_target": 4096.0,
                "cpu_quantum": 8.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SCAN"
            }
        elif event.regression_type == "THROUGHPUT_COLLAPSE":
            corrective = {
                "cpu_quantum": 6.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SCAN"
            }
        elif event.regression_type == "LATENCY_SPIKE":
            corrective = {
                "cpu_quantum": 3.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SSTF",
                "memory_reclaim_target": 1024.0
            }

        return corrective

    def track_recovery_progress(self, current_step: int, system_state: Dict[str, Any]):
        if self.active_recovery is None:
            return

        current_time = system_state.get("time", 0.0)
        elapsed = current_time - self.active_recovery_start_time
        is_thrashing = system_state.get("is_thrashing", False)
        mem_util = system_state.get("memory_utilization", 0.0)

        recovered = (not is_thrashing) and (mem_util < 88.0)
        if recovered or elapsed >= 30.0:
            self.recovery_records.append({
                "regression_type": self.active_recovery.regression_type,
                "recovery_time": round(elapsed, 2),
                "success": recovered,
                "policy_switches_total": self.policy_switches
            })
            self.active_recovery = None

    def get_metrics(self) -> Dict[str, Any]:
        if not self.recovery_records:
            return {
                "total_recoveries": 0,
                "success_rate": 0.0,
                "avg_recovery_time": 0.0,
                "policy_switches": self.policy_switches
            }

        successes = sum(1 for r in self.recovery_records if r["success"])
        success_rate = successes / len(self.recovery_records)
        avg_time = float(sum(r["recovery_time"] for r in self.recovery_records) / len(self.recovery_records))

        return {
            "total_recoveries": len(self.recovery_records),
            "success_rate": round(success_rate, 4),
            "avg_recovery_time": round(avg_time, 2),
            "policy_switches": self.policy_switches
        }


class FeedbackMechanism:
    def __init__(self, conflict_engine: Any):
        self.conflict_engine = conflict_engine
        self.feedback_history: List[Dict[str, Any]] = []
        self.sensitivity_adjustments: int = 0

    def process_feedback(
        self,
        prediction: Any,
        regression_event: Optional[RegressionEvent],
        step: int
    ):
        was_predicted = prediction.is_conflict if prediction else False
        is_regression = regression_event is not None

        if self.conflict_engine is not None and hasattr(self.conflict_engine, "record_ground_truth_outcome"):
            self.conflict_engine.record_ground_truth_outcome(prediction, is_regression)

        if is_regression and not was_predicted and self.conflict_engine is not None:
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

    def get_summary(self) -> Dict[str, Any]:
        thresh = getattr(self.conflict_engine, "confidence_threshold", 0.65) if self.conflict_engine else 0.65
        return {
            "total_feedback_events": len(self.feedback_history),
            "sensitivity_adjustments": self.sensitivity_adjustments,
            "current_confidence_threshold": round(thresh, 3)
        }
