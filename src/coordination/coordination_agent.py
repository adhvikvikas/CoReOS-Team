"""
CoReOS Coordination Agent
Aggregates candidate actions from resource agents, runs conflict checks,
arbitrates conflicting proposals, and provides a deterministic fallback.
"""

from typing import Dict, Any, Tuple
from src.agents.base_agent import AgentAction
from src.conflict_prediction.conflict_engine import ConflictEngine, ConflictPredictionResult


class CoordinationAgent:
    def __init__(
        self,
        conflict_engine: ConflictEngine,
        enable_conflict_prediction: bool = True,
        enable_coordination: bool = True
    ):
        self.conflict_engine = conflict_engine
        self.enable_conflict_prediction = enable_conflict_prediction
        self.enable_coordination = enable_coordination
        self.audit_log: list = []

    def _apply_non_predictive_coordination(
        self,
        cpu_policy: str,
        cpu_quantum: float,
        mem_reclaim: float,
        io_policy: str,
        system_state: Dict[str, Any]
    ) -> Tuple[str, float, float, str, bool]:
        arbitrated = False
        mem_util = system_state.get("memory_utilization", 0.0)
        is_pressure = system_state.get("is_under_memory_pressure", False)
        is_thrashing = system_state.get("is_thrashing", False)
        io_q = system_state.get("io_queue_length", 0)
        io_sat = system_state.get("io_saturation", 0.0)
        ready_q = system_state.get("ready_queue_length", 0)

        if (is_pressure or is_thrashing or mem_util >= 85.0) and cpu_quantum < 6.0:
            cpu_quantum = 6.0
            arbitrated = True

        if mem_reclaim > 1024.0 and (io_sat >= 75.0 or io_q >= 15):
            mem_reclaim = 1024.0
            io_policy = "SCAN"
            arbitrated = True

        if ready_q > 10 and io_q >= 5 and io_policy == "FCFS":
            io_policy = "SSTF"
            arbitrated = True

        return cpu_policy, cpu_quantum, mem_reclaim, io_policy, arbitrated

    def coordinate(
        self,
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> Tuple[Dict[str, Any], ConflictPredictionResult]:
        """
        Coordinates candidate actions from CPU, Memory, and I/O agents.
        Returns:
            coordinated_decision: Execution parameters for the simulator.
            prediction_result: Conflict prediction diagnostic object.
        """
        cpu_act = proposed_actions.get("CPU_AGENT")
        mem_act = proposed_actions.get("MEMORY_AGENT")
        io_act = proposed_actions.get("IO_AGENT")

        # Default parameters from raw proposals
        cpu_policy = cpu_act.parameters.get("policy", "ROUND_ROBIN") if cpu_act else "ROUND_ROBIN"
        cpu_quantum = cpu_act.parameters.get("quantum", 4.0) if cpu_act else 4.0
        mem_reclaim = mem_act.parameters.get("target_free_mb", 0.0) if mem_act else 0.0
        io_policy = io_act.parameters.get("io_policy", "FCFS") if io_act else "FCFS"
        arbitration_applied = False

        if not self.enable_coordination:
            # Baseline B / Uncoordinated: proposals pass through directly without coordination
            prediction = ConflictPredictionResult(
                is_conflict=False,
                conflict_type="NONE_UNCOORDINATED",
                confidence=1.0,
                contributing_agents=[],
                severity=0.0,
                rationale="Coordination disabled in uncoordinated baseline.",
                suggested_arbitration={}
            )
        elif not self.enable_conflict_prediction:
            # Baseline C: Coordinated without conflict prediction (Reactive non-predictive coordination)
            prediction = ConflictPredictionResult(
                is_conflict=False,
                conflict_type="NONE_DISABLED",
                confidence=1.0,
                contributing_agents=[],
                severity=0.0,
                rationale="Conflict prediction disabled in ablation baseline (reactive non-predictive coordination active).",
                suggested_arbitration={}
            )
            cpu_policy, cpu_quantum, mem_reclaim, io_policy, arbitration_applied = self._apply_non_predictive_coordination(
                cpu_policy, cpu_quantum, mem_reclaim, io_policy, system_state
            )
        else:
            # Full Conflict Prediction
            prediction = self.conflict_engine.predict_conflict(system_state, proposed_actions)

            if prediction.is_conflict:
                arbitration_applied = True
                sug = prediction.suggested_arbitration

                # Apply negotiated arbitration modifications
                if "CPU_AGENT" in sug:
                    cpu_quantum = sug["CPU_AGENT"].get("quantum", cpu_quantum)
                    cpu_policy = sug["CPU_AGENT"].get("policy", cpu_policy)

                if "MEMORY_AGENT" in sug:
                    mem_reclaim = sug["MEMORY_AGENT"].get("target_free_mb", mem_reclaim)

                if "IO_AGENT" in sug:
                    io_policy = sug["IO_AGENT"].get("io_policy", io_policy)

        coordinated_decision = {
            "cpu_policy": cpu_policy,
            "cpu_quantum": cpu_quantum,
            "memory_reclaim_target": mem_reclaim,
            "io_policy": io_policy,
            "conflict_predicted": prediction.is_conflict,
            "conflict_type": prediction.conflict_type,
            "arbitration_applied": arbitration_applied
        }

        self.audit_log.append({
            "time": system_state.get("time", 0.0),
            "decision": coordinated_decision,
            "prediction": prediction.to_dict()
        })

        return coordinated_decision, prediction
