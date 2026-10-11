"""
CoReOS Conflict Prediction Engine
Defines operational cross-resource conflicts and provides both interpretable
rule-based and machine-learning-based conflict prediction models.
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
from sklearn.ensemble import GradientBoostingClassifier
from src.agents.base_agent import AgentAction


@dataclass
class ConflictPredictionResult:
    is_conflict: bool
    conflict_type: str                  # "NONE", "THRASHING_CPU_COLLAPSE", "IO_SWAP_SATURATION", "PRIORITY_STARVATION", "TRIPLE_CASCADE"
    confidence: float                   # 0.0 to 1.0
    contributing_agents: List[str]      # e.g., ["CPU_AGENT", "MEMORY_AGENT"]
    severity: float                     # 0.0 to 1.0
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
    """
    Evaluates proposed action combinations from CPU, Memory, and I/O agents
    against current system state to predict harmful cross-resource interference.
    """

    def __init__(self, confidence_threshold: float = 0.65, use_ml: bool = True):
        self.confidence_threshold = confidence_threshold
        self.use_ml = use_ml
        
        # Performance tracking of predictions vs observed outcomes
        self.prediction_records: List[Dict[str, Any]] = []
        
        # Lightweight ML model initialized
        self.ml_model: Optional[GradientBoostingClassifier] = None
        self.feature_names = [
            "cpu_util", "mem_util", "io_sat", "ready_q", "io_q",
            "context_switches", "page_faults", "cpu_quantum",
            "is_emergency_reclaim", "is_io_throttle"
        ]
        self._init_ml_model()

    def _init_ml_model(self):
        """Initializes and pre-trains baseline ML conflict predictor on synthetic OS state transitions."""
        self.ml_model = GradientBoostingClassifier(n_estimators=40, max_depth=3, random_state=42)
        # Seed initial synthetic decision boundaries based on operating system dynamics
        rng = np.random.RandomState(42)
        X_dummy = []
        y_dummy = []
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
            
            # Ground truth conflict condition:
            # 1. High memory + short quantum -> thrashing conflict
            # 2. High IO + emergency reclaim -> swap collision
            # 3. Triple high saturation
            is_conf = (
                (mem_u > 85 and quantum <= 2.0) or
                (io_s > 75 and em_reclaim == 1) or
                (cpu_u > 85 and mem_u > 85 and io_s > 80)
            )
            X_dummy.append([cpu_u, mem_u, io_s, rq, iq, cs, pf, quantum, em_reclaim, io_throt])
            y_dummy.append(1 if is_conf else 0)

        self.ml_model.fit(np.array(X_dummy), np.array(y_dummy))

    def predict_conflict(
        self,
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> ConflictPredictionResult:
        """
        Evaluates candidate decisions from CPU, Memory, and I/O agents.
        Applies interpretable rule-based detection with ML probability fusion.
        """
        cpu_act = proposed_actions.get("CPU_AGENT")
        mem_act = proposed_actions.get("MEMORY_AGENT")
        io_act = proposed_actions.get("IO_AGENT")

        cpu_util = system_state.get("cpu_utilization", 0.0)
        mem_util = system_state.get("memory_utilization", 0.0)
        io_sat = system_state.get("io_saturation", 0.0)
        ready_q = system_state.get("ready_queue_length", 0)
        io_q = system_state.get("io_queue_length", 0)
        is_thrashing = system_state.get("is_thrashing", False)

        # Rule 1: Triple Saturation Cascade (Check first: all 3 subsystems saturated)
        if cpu_util >= 85.0 and mem_util >= 85.0 and io_sat >= 80.0:
            return ConflictPredictionResult(
                is_conflict=True,
                conflict_type="TRIPLE_CASCADE",
                confidence=0.95,
                contributing_agents=["CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"],
                severity=0.95,
                rationale="All core resources (CPU, RAM, I/O) simultaneously saturated; uncoordinated actions risk complete system deadlock.",
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

        # ML Model Secondary Check
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

        # No Conflict Predicted
        return ConflictPredictionResult(
            is_conflict=False,
            conflict_type="NONE",
            confidence=0.90,
            contributing_agents=[],
            severity=0.0,
            rationale="Candidate actions satisfy joint resource headroom constraints.",
            suggested_arbitration={}
        )

    def record_ground_truth_outcome(
        self,
        prediction: ConflictPredictionResult,
        was_regression_observed: bool
    ):
        """Records ground truth outcome to evaluate prediction Precision, Recall, F1."""
        self.prediction_records.append({
            "predicted_conflict": prediction.is_conflict,
            "conflict_type": prediction.conflict_type,
            "confidence": prediction.confidence,
            "actual_regression": was_regression_observed
        })

    def get_metrics(self) -> Dict[str, Any]:
        """Calculates Precision, Recall, F1, FPR, FNR of the conflict predictor."""
        if not self.prediction_records:
            return {"precision": 0.0, "recall": 0.0, "f1": 0.0, "fpr": 0.0, "fnr": 0.0, "total": 0, "total_evaluations": 0}

        tp = sum(1 for r in self.prediction_records if r["predicted_conflict"] and r["actual_regression"])
        fp = sum(1 for r in self.prediction_records if r["predicted_conflict"] and not r["actual_regression"])
        tn = sum(1 for r in self.prediction_records if not r["predicted_conflict"] and not r["actual_regression"])
        fn = sum(1 for r in self.prediction_records if not r["predicted_conflict"] and r["actual_regression"])

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
            "total_evaluations": len(self.prediction_records)
        }
