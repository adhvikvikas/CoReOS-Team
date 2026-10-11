"""
CoReOS Coordination Agent
Arbitrates cross-agent proposals, invokes conflict prediction, applies Pareto safeguards,
enforces hard constraints, and provides deterministic fallback.
"""

from typing import Dict, Any, Tuple, Optional, List
from src.coreos.agents.base import AgentAction
from src.coreos.coordination.constraints import validate_safety_constraints


class CoordinationAgent:
    def __init__(
        self,
        conflict_engine: Any,
        enable_conflict_prediction: bool = True,
        confidence_threshold: float = 0.65,
        enable_coordination: bool = True
    ):
        self.conflict_engine = conflict_engine
        self.enable_conflict_prediction = enable_conflict_prediction
        self.confidence_threshold = confidence_threshold
        self.enable_coordination = enable_coordination
        self.audit_log: List[Dict[str, Any]] = []

    def _apply_non_predictive_coordination(
        self,
        raw_decision: Dict[str, Any],
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> Tuple[Dict[str, Any], bool, List[str]]:
        """
        Non-predictive reactive coordination policy (Configuration C).
        Arbitrates conflicting inter-agent proposals based strictly on CURRENT
        observed state metrics without statistical or machine-learning conflict models,
        future cascade projections, or predictive risk scoring.
        """
        coordinated = dict(raw_decision)
        arbitrated = False
        notes = []

        mem_util = system_state.get("memory_utilization", 0.0)
        is_pressure = system_state.get("is_under_memory_pressure", False)
        is_thrashing = system_state.get("is_thrashing", False)
        io_q = system_state.get("io_queue_length", 0)
        io_sat = system_state.get("io_saturation", 0.0)
        ready_q = system_state.get("ready_queue_length", 0)

        # 1. Memory-CPU Tension:
        # Under current memory pressure or thrashing, CPU agent's tight quantum (<6.0) causes
        # excessive context-switching and page-fault churn. Reactive coordinator balances
        # CPU quantum to 6.0 to amortize scheduling overhead under current memory pressure.
        if (is_pressure or is_thrashing or mem_util >= 85.0) and coordinated.get("cpu_quantum", 4.0) < 6.0:
            coordinated["cpu_quantum"] = 6.0
            arbitrated = True
            notes.append("Non-predictive coordination: Lengthened CPU quantum to 6.0 to dampen context-switching under memory pressure")

        # 2. Memory-I/O Tension:
        # If Memory agent requests aggressive reclamation (>1024 MB) while current I/O queue
        # or saturation is high (io_sat >= 75% or io_q >= 15), writing pages to swap overloads
        # storage channels. Reactive coordinator paces reclamation and enforces elevator SCAN.
        if coordinated.get("memory_reclaim_target", 0.0) > 1024.0 and (io_sat >= 75.0 or io_q >= 15):
            coordinated["memory_reclaim_target"] = 1024.0
            coordinated["io_policy"] = "SCAN"
            arbitrated = True
            notes.append("Non-predictive coordination: Paced memory reclaim to 1024 MB and engaged SCAN to prevent I/O channel saturation")

        # 3. CPU-I/O Tension:
        # If ready queue is congested (ready_q > 10) and I/O traffic is present (io_q >= 5),
        # coordinator upgrades I/O policy from FCFS to SSTF to accelerate seek times and
        # return waiting processes to the ready queue faster.
        if ready_q > 10 and io_q >= 5 and coordinated.get("io_policy") == "FCFS":
            coordinated["io_policy"] = "SSTF"
            arbitrated = True
            notes.append("Non-predictive coordination: Upgraded I/O policy to SSTF to relieve ready queue congestion")

        return coordinated, arbitrated, notes

    def coordinate(
        self,
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> Tuple[Dict[str, Any], Any]:
        """
        Coordinates candidate actions from CPU, Memory, and I/O agents.
        Returns: (coordinated_decision, prediction_result)
        """
        cpu_act = proposed_actions.get("CPU_AGENT")
        mem_act = proposed_actions.get("MEMORY_AGENT")
        io_act = proposed_actions.get("IO_AGENT")

        # Initial raw proposals
        raw_decision = {
            "cpu_policy": cpu_act.parameters.get("policy", "ROUND_ROBIN") if cpu_act else "ROUND_ROBIN",
            "cpu_quantum": cpu_act.parameters.get("quantum", 4.0) if cpu_act else 4.0,
            "memory_reclaim_target": mem_act.parameters.get("target_free_mb", 0.0) if mem_act else 0.0,
            "io_policy": io_act.parameters.get("io_policy", "FCFS") if io_act else "FCFS"
        }

        # 1. Hard Safety Constraints Validation
        safe_decision, safety_modified, safety_note = validate_safety_constraints(raw_decision, system_state)
        arbitration_applied = safety_modified
        explanation = [safety_note] if safety_modified else []

        if not self.enable_coordination:
            from src.coreos.conflict_prediction.predictor import ConflictPredictionResult
            prediction = ConflictPredictionResult(
                is_conflict=False,
                conflict_type="NONE_UNCOORDINATED",
                confidence=1.0,
                contributing_agents=[],
                severity=0.0,
                rationale="Coordination disabled in uncoordinated baseline.",
                suggested_arbitration={}
            )
            coordinated_decision = dict(raw_decision)
            coordinated_decision.update({
                "conflict_predicted": False,
                "conflict_type": "NONE_UNCOORDINATED",
                "arbitration_applied": False,
                "explanation": ["Uncoordinated baseline: Raw agent proposals executed directly"]
            })
            self.audit_log.append({
                "time": system_state.get("time", 0.0),
                "decision": coordinated_decision,
                "prediction": prediction.to_dict()
            })
            return coordinated_decision, prediction

        prediction = None
        if not self.enable_conflict_prediction or self.conflict_engine is None:
            # Baseline C: Coordinated without conflict prediction (Reactive non-predictive coordination)
            from src.coreos.conflict_prediction.predictor import ConflictPredictionResult
            prediction = ConflictPredictionResult(
                is_conflict=False,
                conflict_type="NONE_DISABLED",
                confidence=1.0,
                contributing_agents=[],
                severity=0.0,
                rationale="Conflict prediction disabled in ablation baseline (reactive non-predictive coordination active).",
                suggested_arbitration={}
            )
            # Apply reactive non-predictive coordination across candidate proposals
            safe_decision, coord_applied, coord_notes = self._apply_non_predictive_coordination(
                safe_decision, system_state, proposed_actions
            )
            if coord_applied:
                arbitration_applied = True
                explanation.extend(coord_notes)
        else:
            # 2. Conflict Prediction
            prediction = self.conflict_engine.predict_conflict(system_state, proposed_actions)

            # 3. Deterministic Fallback if model confidence is low or invalid
            if prediction.confidence < 0.40:
                safe_decision = {
                    "cpu_policy": "ROUND_ROBIN",
                    "cpu_quantum": 4.0,
                    "memory_reclaim_target": 1024.0,
                    "io_policy": "SCAN"
                }
                arbitration_applied = True
                explanation.append("Low prediction confidence: Reverted to deterministic conservative fallback")

            elif prediction.is_conflict:
                arbitration_applied = True
                sug = prediction.suggested_arbitration

                if "CPU_AGENT" in sug:
                    safe_decision["cpu_quantum"] = sug["CPU_AGENT"].get("quantum", safe_decision["cpu_quantum"])
                    safe_decision["cpu_policy"] = sug["CPU_AGENT"].get("policy", safe_decision["cpu_policy"])
                    explanation.append(f"Adjusted CPU quantum to {safe_decision['cpu_quantum']}")

                if "MEMORY_AGENT" in sug:
                    safe_decision["memory_reclaim_target"] = sug["MEMORY_AGENT"].get("target_free_mb", safe_decision["memory_reclaim_target"])
                    explanation.append(f"Adjusted memory reclaim to {safe_decision['memory_reclaim_target']} MB")

                if "IO_AGENT" in sug:
                    safe_decision["io_policy"] = sug["IO_AGENT"].get("io_policy", safe_decision["io_policy"])
                    explanation.append(f"Adjusted I/O policy to {safe_decision['io_policy']}")

        # Final pass safety constraint check
        final_decision, _, _ = validate_safety_constraints(safe_decision, system_state)
        final_decision["conflict_predicted"] = prediction.is_conflict
        final_decision["conflict_type"] = prediction.conflict_type
        final_decision["arbitration_applied"] = arbitration_applied
        final_decision["explanation"] = "; ".join(explanation) if explanation else "Proposals accepted without conflict"

        self.audit_log.append({
            "time": system_state.get("time", 0.0),
            "decision": dict(final_decision),
            "prediction": prediction.to_dict() if prediction else {}
        })

        return final_decision, prediction
