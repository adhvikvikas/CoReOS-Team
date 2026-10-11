"""
CoReOS Conflict Prediction Engine
Predicts harmful cross-resource interactions between candidate decisions before execution.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from src.coreos.agents.base import AgentAction
from src.coreos.conflict_prediction.conflict_log import ConflictLog


@dataclass
class ConflictPredictionResult:
    is_conflict: bool
    conflict_type: str
    confidence: float
    contributing_agents: List[str]
    severity: float
    rationale: str
    suggested_arbitration: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_conflict": self.is_conflict,
            "conflict_type": self.conflict_type,
            "confidence": round(self.confidence, 3),
            "contributing_agents": self.contributing_agents,
            "severity": round(self.severity, 3),
            "rationale": self.rationale,
            "suggested_arbitration": self.suggested_arbitration
        }


class ConflictEngine:
    def __init__(self, confidence_threshold: float = 0.65, use_ml: bool = True):
        self.confidence_threshold = confidence_threshold
        self.use_ml = use_ml
        self.log = ConflictLog()
        self.ml_model: Optional[GradientBoostingClassifier] = None
        self._init_ml_model()

    def _init_ml_model(self):
        """Initializes and trains baseline ML predictor on synthesized OS state transitions."""
        self.ml_model = GradientBoostingClassifier(n_estimators=40, max_depth=3, random_state=42)
        rng = np.random.RandomState(42)
        X = []
        y = []
        for _ in range(500):
            cpu_u = rng.uniform(10, 100)
            mem_u = rng.uniform(20, 100)
            io_s = rng.uniform(5, 100)
            rq = rng.randint(0, 30)
            iq = rng.randint(0, 40)
            cs = rng.randint(50, 2000)
            pf = rng.randint(0, 50)
            quantum = rng.choice([2.0, 4.0, 8.0])
            em_reclaim = rng.choice([0, 1])
            io_throt = rng.choice([0, 1])

            is_conf = (
                (mem_u > 85 and quantum <= 4.0) or
                (io_s > 75 and em_reclaim == 1) or
                (cpu_u > 85 and mem_u > 85 and io_s > 80)
            )
            X.append([cpu_u, mem_u, io_s, rq, iq, cs, pf, quantum, em_reclaim, io_throt])
            y.append(1 if is_conf else 0)

        self.ml_model.fit(np.array(X), np.array(y))

    def predict_conflict(
        self,
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> ConflictPredictionResult:
        cpu_act = proposed_actions.get("CPU_AGENT")
        mem_act = proposed_actions.get("MEMORY_AGENT")
        io_act = proposed_actions.get("IO_AGENT")

        cpu_util = system_state.get("cpu_utilization", 0.0)
        mem_util = system_state.get("memory_utilization", 0.0)
        io_sat = system_state.get("io_saturation", 0.0)
        ready_q = system_state.get("ready_queue_length", 0)
        io_q = system_state.get("io_queue_length", 0)
        is_thrashing = system_state.get("is_thrashing", False)

        # Rule 1: Triple Saturation Cascade (Check first)
        if cpu_util >= 85.0 and mem_util >= 85.0 and io_sat >= 80.0:
            return ConflictPredictionResult(
                is_conflict=True,
                conflict_type="TRIPLE_CASCADE",
                confidence=0.95,
                contributing_agents=["CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"],
                severity=0.95,
                rationale="All core resources (CPU, RAM, I/O) simultaneously saturated; uncoordinated actions risk complete deadlock.",
                suggested_arbitration={
                    "CPU_AGENT": {"quantum": 6.0, "policy": "ROUND_ROBIN"},
                    "MEMORY_AGENT": {"target_free_mb": 2048.0},
                    "IO_AGENT": {"io_policy": "SCAN", "throttle_low_priority": True}
                }
            )

        # Rule 2: Thrashing-Induced CPU Collapse (Memory-CPU Conflict)
        quantum = cpu_act.parameters.get("quantum", 4.0) if cpu_act else 4.0
        if (mem_util >= 88.0 or is_thrashing) and quantum <= 4.0:
            return ConflictPredictionResult(
                is_conflict=True,
                conflict_type="THRASHING_CPU_COLLAPSE",
                confidence=0.92,
                contributing_agents=["CPU_AGENT", "MEMORY_AGENT"],
                severity=0.85,
                rationale="Under high memory pressure, short/standard CPU quantum increases context switches and triggers cascade page faults.",
                suggested_arbitration={
                    "CPU_AGENT": {"quantum": 8.0, "policy": "ROUND_ROBIN"},
                    "MEMORY_AGENT": {"target_free_mb": 2048.0}
                }
            )

        # Rule 3: I/O Channel Collision with Memory Swapping (Memory-IO Conflict)
        is_em_reclaim = (mem_act and mem_act.action_type == "EMERGENCY_RECLAIM")
        if (io_sat >= 75.0 or io_q >= 20) and is_em_reclaim:
            return ConflictPredictionResult(
                is_conflict=True,
                conflict_type="IO_SWAP_SATURATION",
                confidence=0.88,
                contributing_agents=["MEMORY_AGENT", "IO_AGENT"],
                severity=0.80,
                rationale="Emergency memory reclamation writes pages to swap, saturating already congested I/O channels.",
                suggested_arbitration={
                    "MEMORY_AGENT": {"target_free_mb": 1024.0, "pace_reclamation": True},
                    "IO_AGENT": {"io_policy": "SCAN", "throttle_low_priority": True}
                }
            )

        # ML Model Secondary Verification
        if self.use_ml and self.ml_model is not None:
            feat_vec = np.array([[
                cpu_util, mem_util, io_sat, ready_q, io_q,
                system_state.get("total_context_switches", 0),
                system_state.get("total_page_faults", 0),
                quantum,
                1 if is_em_reclaim else 0,
                1 if (io_act and io_act.parameters.get("throttle_low_priority", False)) else 0
            ]])
            prob = float(self.ml_model.predict_proba(feat_vec)[0, 1])
            if prob >= self.confidence_threshold:
                return ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="STATISTICAL_CROSS_RESOURCE_CONFLICT",
                    confidence=prob,
                    contributing_agents=["CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"],
                    severity=prob,
                    rationale=f"ML conflict predictor identified high probability ({prob:.2f}) of cross-resource degradation.",
                    suggested_arbitration={
                        "CPU_AGENT": {"quantum": 6.0},
                        "MEMORY_AGENT": {"target_free_mb": 1024.0}
                    }
                )

        return ConflictPredictionResult(
            is_conflict=False,
            conflict_type="NONE",
            confidence=0.90,
            contributing_agents=[],
            severity=0.0,
            rationale="Candidate actions satisfy joint resource headroom constraints.",
            suggested_arbitration={}
        )

    def record_ground_truth_outcome(self, prediction: ConflictPredictionResult, was_regression_observed: bool):
        self.log.log_prediction(
            step=0,
            candidate_actions={},
            is_conflict=prediction.is_conflict,
            conflict_type=prediction.conflict_type,
            severity=prediction.severity,
            confidence=prediction.confidence,
            coordinator_response=prediction.suggested_arbitration
        )
        self.log.record_outcome(len(self.log.records) - 1, was_regression_observed)

    def get_metrics(self) -> Dict[str, Any]:
        return self.log.compute_metrics()
