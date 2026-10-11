"""
CoReOS Self-Healing: Performance Regression Detector
Detects performance regressions using rolling statistics, patience thresholds, and thrashing indicators.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from src.coreos.config import SelfHealingConfig


@dataclass
class RegressionEvent:
    timestamp: float
    regression_type: str              # "THROUGHPUT_COLLAPSE", "LATENCY_SPIKE", "THRASHING_STALL"
    severity: float                   # 0.0 to 1.0
    current_value: float
    baseline_value: float
    consecutive_violations: int
    candidate_decisions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": round(self.timestamp, 2),
            "regression_type": self.regression_type,
            "severity": round(self.severity, 3),
            "current_value": round(self.current_value, 2),
            "baseline_value": round(self.baseline_value, 2),
            "consecutive_violations": self.consecutive_violations,
            "candidate_decisions_count": len(self.candidate_decisions)
        }


class PerformanceRegressionDetector:
    def __init__(self, config: Optional[SelfHealingConfig] = None):
        self.config = config or SelfHealingConfig()
        self.throughput_window: List[float] = []
        self.wait_time_window: List[float] = []
        self.decision_window: List[Dict[str, Any]] = []
        self.consecutive_drops: int = 0
        self.detected_regressions: List[RegressionEvent] = []

    def record_decision(self, decision: Dict[str, Any]):
        self.decision_window.append(decision)
        if len(self.decision_window) > self.config.regression_window_size:
            self.decision_window.pop(0)

    def observe_and_detect(self, state: Dict[str, Any]) -> Optional[RegressionEvent]:
        current_time = state.get("time", 0.0)
        throughput = state.get("throughput", 0.0)
        avg_wait = state.get("avg_waiting_time", 0.0)
        is_thrashing = state.get("is_thrashing", False)

        self.throughput_window.append(throughput)
        self.wait_time_window.append(avg_wait)
        if len(self.throughput_window) > self.config.regression_window_size:
            self.throughput_window.pop(0)
            self.wait_time_window.pop(0)

        # Condition 1: Thrashing Stall (evaluated immediately)
        if is_thrashing:
            event = RegressionEvent(
                timestamp=current_time,
                regression_type="THRASHING_STALL",
                severity=0.90,
                current_value=state.get("memory_utilization", 0.0),
                baseline_value=85.0,
                consecutive_violations=1,
                candidate_decisions=list(self.decision_window)
            )
            self.detected_regressions.append(event)
            return event

        if len(self.throughput_window) < 8:
            return None

        baseline_tp = float(np.mean(self.throughput_window[:-1]))
        baseline_wait = float(np.mean(self.wait_time_window[:-1]))

        # Condition 2: Throughput Collapse
        if baseline_tp > 0.05 and throughput < baseline_tp * (1.0 - self.config.throughput_drop_threshold):
            self.consecutive_drops += 1
            if self.consecutive_drops >= self.config.patience_steps:
                severity = min(1.0, (baseline_tp - throughput) / baseline_tp)
                event = RegressionEvent(
                    timestamp=current_time,
                    regression_type="THROUGHPUT_COLLAPSE",
                    severity=severity,
                    current_value=throughput,
                    baseline_value=baseline_tp,
                    consecutive_violations=self.consecutive_drops,
                    candidate_decisions=list(self.decision_window)
                )
                self.detected_regressions.append(event)
                self.consecutive_drops = 0
                return event
        else:
            self.consecutive_drops = max(0, self.consecutive_drops - 1)

        # Condition 3: Latency / Wait Time Spike
        if baseline_wait > 5.0 and avg_wait > baseline_wait * (1.0 + self.config.turnaround_spike_threshold):
            severity = min(1.0, (avg_wait - baseline_wait) / (baseline_wait * 2.0))
            event = RegressionEvent(
                timestamp=current_time,
                regression_type="LATENCY_SPIKE",
                severity=severity,
                current_value=avg_wait,
                baseline_value=baseline_wait,
                consecutive_violations=1,
                candidate_decisions=list(self.decision_window)
            )
            self.detected_regressions.append(event)
            return event

        return None
