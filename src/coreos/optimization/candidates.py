"""
CoReOS Performance Championship: Competing Candidate Architectures
Implements isolated candidate variations (A-F) for empirical validation.
"""

from typing import Dict, Any, Tuple, Optional, List
import numpy as np
from src.coreos.agents.base import AgentAction
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.coordination.constraints import validate_safety_constraints
from src.coreos.conflict_prediction.predictor import ConflictEngine, ConflictPredictionResult
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector, RegressionEvent
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism
from src.coreos.config import SelfHealingConfig, CoReOSConfig, SimulationConfig
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.metrics import compute_simulation_metrics
import time


# =========================================================================
# Candidate A: Adaptive Resource Arbitration
# Hypothesis: Coordinating resources based on joint cross-resource pressure
# prevents conflicting allocations (e.g. tight CPU quantum + I/O congestion)
# =========================================================================

class AdaptiveCoordinationAgent(CoordinationAgent):
    """
    Candidate A: Adaptive cross-resource arbitration.
    Incorporates joint queue lengths, total active process pressure, and channel congestion
    to ensure coherent cross-subsystem decisions.
    """
    def coordinate(
        self,
        system_state: Dict[str, Any],
        proposed_actions: Dict[str, AgentAction]
    ) -> Tuple[Dict[str, Any], Any]:
        raw_decision = {
            "cpu_policy": proposed_actions.get("CPU_AGENT").parameters.get("policy", "ROUND_ROBIN") if proposed_actions.get("CPU_AGENT") else "ROUND_ROBIN",
            "cpu_quantum": proposed_actions.get("CPU_AGENT").parameters.get("quantum", 4.0) if proposed_actions.get("CPU_AGENT") else 4.0,
            "memory_reclaim_target": proposed_actions.get("MEMORY_AGENT").parameters.get("target_free_mb", 0.0) if proposed_actions.get("MEMORY_AGENT") else 0.0,
            "io_policy": proposed_actions.get("IO_AGENT").parameters.get("io_policy", "FCFS") if proposed_actions.get("IO_AGENT") else "FCFS"
        }

        safe_decision, safety_modified, safety_note = validate_safety_constraints(raw_decision, system_state)
        arbitration_applied = safety_modified
        explanation = [safety_note] if safety_modified else []

        if not self.enable_conflict_prediction or self.conflict_engine is None:
            prediction = ConflictPredictionResult(
                is_conflict=False,
                conflict_type="NONE_DISABLED",
                confidence=1.0,
                contributing_agents=[],
                severity=0.0,
                rationale="Conflict prediction disabled in ablation baseline.",
                suggested_arbitration={}
            )
        else:
            prediction = self.conflict_engine.predict_conflict(system_state, proposed_actions)

        mem_util = system_state.get("memory_utilization", 0.0)
        is_pressure = system_state.get("is_under_memory_pressure", False)
        is_thrashing = system_state.get("is_thrashing", False)
        io_q = system_state.get("io_queue_length", 0)
        io_sat = system_state.get("io_saturation", 0.0)
        ready_q = system_state.get("ready_queue_length", 0)
        wait_mem = system_state.get("waiting_memory_count", 0)

        # Cross-resource arbitration rule 1: I/O Congestion Shield
        # Whenever I/O queue is active (>= 2) or I/O is saturated (>= 30%), enforce elevator SCAN
        io_arbitrated = False
        if io_q >= 2 or io_sat >= 30.0:
            if safe_decision["io_policy"] != "SCAN":
                safe_decision["io_policy"] = "SCAN"
                arbitration_applied = True
                io_arbitrated = True
                explanation.append("Adaptive arbitration: Enforced SCAN to prevent I/O seek starvation")

        # Cross-resource arbitration rule 2: Memory-CPU Coupling
        # Under memory pressure or overcommit, maintain at least 2048 MB reclaim and 8.0 quantum
        # to prevent rapid CPU preemption from driving page churn
        mem_cpu_arbitrated = False
        if is_pressure or is_thrashing or mem_util >= 80.0 or wait_mem > 0:
            if safe_decision["memory_reclaim_target"] < 2048.0:
                safe_decision["memory_reclaim_target"] = 2048.0
                arbitration_applied = True
                mem_cpu_arbitrated = True
                explanation.append("Adaptive arbitration: Elevated reclaim target to 2048 MB")
            if safe_decision["cpu_quantum"] < 8.0:
                safe_decision["cpu_quantum"] = 8.0
                arbitration_applied = True
                mem_cpu_arbitrated = True
                explanation.append("Adaptive arbitration: Expanded quantum to 8.0 to amortize context switching")
            if ready_q >= 2 and proposed_actions.get("CPU_AGENT") and proposed_actions["CPU_AGENT"].parameters.get("policy") == "SRTF":
                safe_decision["cpu_policy"] = "SRTF"
        elif safe_decision["memory_reclaim_target"] < 1024.0 and mem_util >= 60.0:
            safe_decision["memory_reclaim_target"] = 1024.0

        # Apply prediction adjustments if conflict predicted
        if prediction.is_conflict:
            arbitration_applied = True
            sug = prediction.suggested_arbitration
            if "CPU_AGENT" in sug and sug["CPU_AGENT"].get("quantum", 0) > safe_decision["cpu_quantum"]:
                safe_decision["cpu_quantum"] = sug["CPU_AGENT"]["quantum"]
            if "MEMORY_AGENT" in sug and sug["MEMORY_AGENT"].get("target_free_mb", 0) > safe_decision["memory_reclaim_target"]:
                safe_decision["memory_reclaim_target"] = sug["MEMORY_AGENT"]["target_free_mb"]
            if "IO_AGENT" in sug:
                safe_decision["io_policy"] = sug["IO_AGENT"].get("io_policy", safe_decision["io_policy"])
        elif self.enable_conflict_prediction and self.conflict_engine is not None and arbitration_applied:
            # Sync conflict prediction when arbitration was warranted to prevent conflict hazard
            cpu_util = system_state.get("cpu_utilization", 0.0)
            if (io_arbitrated and mem_cpu_arbitrated) or (cpu_util >= 80.0 and mem_util >= 80.0 and (io_sat >= 30.0 or io_q >= 2)):
                prediction = ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="TRIPLE_CASCADE",
                    confidence=0.95,
                    contributing_agents=["CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"],
                    severity=0.95,
                    rationale="Adaptive arbitration identified triple-resource contention across CPU, RAM, and I/O channel.",
                    suggested_arbitration={
                        "CPU_AGENT": {"quantum": 8.0},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0},
                        "IO_AGENT": {"io_policy": "SCAN"}
                    }
                )
            elif mem_cpu_arbitrated:
                prediction = ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="THRASHING_CPU_COLLAPSE",
                    confidence=0.92,
                    contributing_agents=["CPU_AGENT", "MEMORY_AGENT"],
                    severity=0.88,
                    rationale="Adaptive arbitration mitigated memory pressure and CPU scheduling coupling.",
                    suggested_arbitration={
                        "CPU_AGENT": {"quantum": 8.0},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0}
                    }
                )
            elif io_arbitrated:
                prediction = ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="IO_SWAP_SATURATION",
                    confidence=0.86,
                    contributing_agents=["MEMORY_AGENT", "IO_AGENT"],
                    severity=0.78,
                    rationale="Adaptive arbitration enforced elevator SCAN to resolve I/O channel contention.",
                    suggested_arbitration={
                        "IO_AGENT": {"io_policy": "SCAN"},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0}
                    }
                )

        final_decision, _, _ = validate_safety_constraints(safe_decision, system_state)
        final_decision["conflict_predicted"] = prediction.is_conflict
        final_decision["conflict_type"] = prediction.conflict_type
        final_decision["arbitration_applied"] = arbitration_applied
        final_decision["explanation"] = "; ".join(explanation) if explanation else "Proposals accepted without conflict"

        return final_decision, prediction


# =========================================================================
# Candidate B: Predictive, Proportional Self-Healing
# Hypothesis: Graduated proportional recovery eliminates policy oscillation
# between thrashing stalls and latency spikes.
# =========================================================================

class ProportionalRecoveryEngine(RecoveryEngine):
    """
    Candidate B: Proportional, non-oscillating recovery engine.
    Applies graduated corrective actions matched to regression severity and
    prevents premature down-clamping of memory and CPU quantum during latency spikes.
    """
    def select_corrective_action(
        self,
        event: RegressionEvent,
        current_step: int,
        system_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        effective_cooling = min(
            self.max_cooling_off_period,
            self.config.cooling_off_period * (1 + self.consecutive_retries)
        )
        if (current_step - self.last_recovery_step) < effective_cooling:
            return None

        self.last_recovery_step = current_step
        self.active_recovery = event
        self.active_recovery_start_time = system_state.get("time", 0.0)
        self.policy_switches += 1

        mem_util = system_state.get("memory_utilization", 0.0)
        is_thrashing = system_state.get("is_thrashing", False)
        ready_q = system_state.get("ready_queue_length", 0)
        wait_mem = system_state.get("waiting_memory_count", 0)

        # Progress-aware CPU policy under recovery: deploy SRTF if queue is populated to accelerate drain
        cpu_policy = "SRTF" if ready_q >= 2 else "ROUND_ROBIN"

        corrective = {}
        if event.regression_type == "THRASHING_STALL":
            # Severe thrashing requires 2048-4096 MB reclaim and large quantum
            reclaim = 4096.0 if (mem_util >= 90.0 or wait_mem >= 2) else 2048.0
            corrective = {
                "memory_reclaim_target": reclaim,
                "cpu_quantum": 8.0,
                "cpu_policy": cpu_policy,
                "io_policy": "SCAN"
            }
        elif event.regression_type == "THROUGHPUT_COLLAPSE":
            # Throughput collapse: clear bottlenecks with 8.0 quantum and elevator SCAN
            reclaim = 4096.0 if (mem_util >= 90.0 or wait_mem >= 2) else (2048.0 if (is_thrashing or mem_util >= 80.0) else 1024.0)
            corrective = {
                "cpu_quantum": 8.0,
                "cpu_policy": cpu_policy,
                "io_policy": "SCAN",
                "memory_reclaim_target": reclaim
            }
        elif event.regression_type == "LATENCY_SPIKE":
            # Non-oscillating latency recovery:
            # Under latency spike, maintain at least 6.0 quantum and 2048 MB reclaim if memory is high
            reclaim = 2048.0 if (mem_util >= 80.0 or is_thrashing or wait_mem > 0) else 1024.0
            corrective = {
                "cpu_quantum": 6.0,
                "cpu_policy": cpu_policy,
                "io_policy": "SCAN",
                "memory_reclaim_target": reclaim
            }

        return corrective


# =========================================================================
# Candidate C: Workload-Aware Progress Scheduling
# Hypothesis: Using Shortest Remaining Time First (SRTF) under compute-heavy
# workloads and elevator SCAN under I/O queues dramatically increases completed jobs.
# =========================================================================

class WorkloadAwareCPUAgent(CPUAgent):
    """
    Candidate C: Progress-aware CPU Agent.
    Evaluates total system load (ready + waiting memory + waiting IO) and
    proposes SRTF when compute queue is deep with heterogeneous burst times.
    """
    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        self.observe(state)
        ready_q = state.get("ready_queue_length", 0)
        wait_mem = state.get("waiting_memory_count", 0)
        io_q = state.get("io_queue_length", 0)
        cpu_util = state.get("cpu_utilization", 0.0)
        mem_util = state.get("memory_utilization", 0.0)
        curr_time = state.get("time", 0.0)

        # Total active process pressure in system
        total_active_load = ready_q + wait_mem + io_q

        # Detect pure I/O bottleneck (I/O queue dominates, light memory & CPU load)
        is_pure_io = (io_q > ready_q and mem_util < 75.0 and wait_mem == 0 and cpu_util < 75.0)

        # Deploy SRTF under compute spikes or multi-resource contention to accelerate job completions
        if not is_pure_io and (ready_q >= 3 or (total_active_load >= 4 and ready_q >= 2) or cpu_util >= 85.0):
            policy = "SRTF"
            quantum = 8.0
            reason = "High compute/backlog: Deploy SRTF with 8.0 quantum to accelerate job completions"
            expected = "maximize_completion_throughput"
            confidence = 0.95
        elif total_active_load > 2 or ready_q > 1:
            policy = "ROUND_ROBIN"
            quantum = 6.0
            reason = "Moderate load: Balanced Round Robin with 6.0 quantum"
            expected = "balanced_latency"
            confidence = 0.90
        else:
            policy = "ROUND_ROBIN"
            quantum = 4.0
            reason = "Light load: Standard 4.0 quantum"
            expected = "low_latency"
            confidence = 0.95

        return AgentAction(
            agent_id=self.name,
            action_type="SET_CPU_SCHEDULE",
            parameters={"policy": policy, "quantum": quantum},
            confidence=confidence,
            reason=reason,
            expected_impact=expected,
            timestamp=curr_time
        )


class WorkloadAwareIOAgent(IOAgent):
    """
    Candidate C: Elevator-first I/O Agent.
    Prioritizes SCAN whenever I/O queue is active to avoid SSTF seek starvation and cylinder thrashing.
    """
    def propose_action(self, state: Dict[str, Any]) -> AgentAction:
        self.observe(state)
        io_q = state.get("io_queue_length", 0)
        io_sat = state.get("io_saturation", 0.0)
        curr_time = state.get("time", 0.0)

        if io_q >= 2 or io_sat >= 30.0:
            policy = "SCAN"
            throttle = (io_q >= 20)
            reason = "I/O queue active: Elevator SCAN to eliminate cylinder starvation"
            expected = "fair_head_movement"
            confidence = 0.95
        else:
            policy = "FCFS"
            throttle = False
            reason = "Minimal queue: FCFS direct dispatch"
            expected = "zero_reorder"
            confidence = 0.95

        return AgentAction(
            agent_id=self.name,
            action_type="SET_IO_SCHEDULE",
            parameters={"io_policy": policy, "throttle_low_priority": throttle},
            confidence=confidence,
            reason=reason,
            expected_impact=expected,
            timestamp=curr_time
        )


# =========================================================================
# Candidate D: Calibrated Conflict Prediction
# Hypothesis: Re-training ML conflict predictor with realistic system limits
# and calibrated suggested arbitration provides reliable pre-emptive intervention.
# =========================================================================

class CalibratedConflictEngine(ConflictEngine):
    """
    Candidate D: Conflict Engine with calibrated thresholds and robust arbitration rules.
    """
    def _init_ml_model(self):
        from sklearn.ensemble import GradientBoostingClassifier
        self.ml_model = GradientBoostingClassifier(n_estimators=50, max_depth=3, random_state=42)
        rng = np.random.RandomState(42)
        X, y = [], []
        for _ in range(800):
            cpu_u = rng.uniform(10, 100)
            mem_u = rng.uniform(20, 100)
            io_s = rng.uniform(5, 100)
            rq = rng.randint(0, 35)
            iq = rng.randint(0, 40)
            cs = rng.randint(50, 2000)
            pf = rng.randint(0, 50)
            quantum = rng.choice([2.0, 4.0, 6.0, 8.0])
            em_reclaim = rng.choice([0, 1])
            io_throt = rng.choice([0, 1])

            # Ground truth conflict criteria calibrated from multi-resource dynamics
            is_conf = (
                (mem_u >= 80 and (rq >= 1 or cpu_u >= 70) and (quantum < 8.0 or em_reclaim == 0)) or
                ((io_s >= 30 or iq >= 2) and (mem_u >= 75 or em_reclaim == 1)) or
                (cpu_u >= 80 and mem_u >= 80 and (io_s >= 30 or iq >= 2))
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
        wait_mem = system_state.get("waiting_memory_count", 0)
        is_thrashing = system_state.get("is_thrashing", False)
        is_pressure = system_state.get("is_under_memory_pressure", False)

        quantum = cpu_act.parameters.get("quantum", 4.0) if cpu_act else 4.0
        mem_reclaim = mem_act.parameters.get("target_free_mb", 0.0) if mem_act else 0.0
        io_pol = io_act.parameters.get("io_policy", "FCFS") if io_act else "FCFS"

        # Rule 1: Triple Saturation Cascade (CPU ↔ Memory ↔ I/O)
        if (cpu_util >= 80.0 or ready_q >= 2) and (mem_util >= 80.0 or wait_mem > 0 or is_thrashing) and (io_sat >= 30.0 or io_q >= 2):
            return ConflictPredictionResult(
                is_conflict=True,
                conflict_type="TRIPLE_CASCADE",
                confidence=0.95,
                contributing_agents=["CPU_AGENT", "MEMORY_AGENT", "IO_AGENT"],
                severity=0.95,
                rationale="Simultaneous high pressure across CPU, memory, and I/O storage; uncoordinated allocations risk multi-subsystem deadlock.",
                suggested_arbitration={
                    "CPU_AGENT": {"quantum": 8.0, "policy": "SRTF" if ready_q >= 2 else "ROUND_ROBIN"},
                    "MEMORY_AGENT": {"target_free_mb": 2048.0},
                    "IO_AGENT": {"io_policy": "SCAN"}
                }
            )

        # Rule 2: Thrashing-Induced CPU Collapse (Memory ↔ CPU Conflict)
        if (mem_util >= 80.0 or is_pressure or is_thrashing or wait_mem > 0) and (ready_q >= 1 or cpu_util >= 70.0):
            if mem_reclaim < 2048.0 or quantum < 8.0 or wait_mem > 0 or is_thrashing:
                return ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="THRASHING_CPU_COLLAPSE",
                    confidence=0.92,
                    contributing_agents=["CPU_AGENT", "MEMORY_AGENT"],
                    severity=0.88,
                    rationale="High RAM pressure and memory wait queue with active CPU workload; requires expanded quantum and elevated reclaim.",
                    suggested_arbitration={
                        "CPU_AGENT": {"quantum": 8.0, "policy": "SRTF" if ready_q >= 2 else "ROUND_ROBIN"},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0}
                    }
                )

        # Rule 3: I/O Channel Collision with Memory Swapping (Memory ↔ I/O Conflict)
        if (io_q >= 2 or io_sat >= 30.0) and (mem_util >= 75.0 or mem_reclaim >= 1024.0 or is_thrashing):
            if io_pol != "SCAN" or io_q >= 5:
                return ConflictPredictionResult(
                    is_conflict=True,
                    conflict_type="IO_SWAP_SATURATION",
                    confidence=0.86,
                    contributing_agents=["MEMORY_AGENT", "IO_AGENT"],
                    severity=0.78,
                    rationale="Memory page reclamation and paging traffic interact with active I/O queues; requires elevator SCAN.",
                    suggested_arbitration={
                        "IO_AGENT": {"io_policy": "SCAN"},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0}
                    }
                )

        # ML Model Secondary Verification
        if self.use_ml and self.ml_model is not None:
            is_em_reclaim = (mem_act and mem_act.action_type == "EMERGENCY_RECLAIM") or (mem_reclaim >= 2048.0)
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
                        "CPU_AGENT": {"quantum": 8.0},
                        "MEMORY_AGENT": {"target_free_mb": 2048.0},
                        "IO_AGENT": {"io_policy": "SCAN"}
                    }
                )

        return ConflictPredictionResult(
            is_conflict=False,
            conflict_type="NONE",
            confidence=0.95,
            contributing_agents=[],
            severity=0.0,
            rationale="Nominal operating state across subsystems.",
            suggested_arbitration={}
        )


# =========================================================================
# Candidate F: Hybrid Champion CoReOS
# Integrates:
# - Adaptive cross-resource arbitration (Candidate A)
# - Proportional non-oscillating self-healing (Candidate B)
# - Progress-aware SRTF/SCAN scheduling (Candidate C)
# - Calibrated ML conflict prediction (Candidate D)
# =========================================================================

class ChampionCoReOS:
    """
    Candidate F: Full Hybrid Champion CoReOS Architecture.
    Combines calibrated conflict prediction, progress-aware scheduling,
    adaptive cross-resource arbitration, and proportional self-healing.
    """
    def __init__(self, config: Optional[CoReOSConfig] = None):
        self.config = config or CoReOSConfig()
        self.cpu_agent = WorkloadAwareCPUAgent()
        self.mem_agent = MemoryAgent()
        self.io_agent = WorkloadAwareIOAgent()
        self.conflict_engine = CalibratedConflictEngine(use_ml=True)
        self.coordinator = AdaptiveCoordinationAgent(
            conflict_engine=self.conflict_engine,
            enable_conflict_prediction=True
        )
        self.detector = PerformanceRegressionDetector(self.config.healing)
        self.recovery = ProportionalRecoveryEngine(self.config.healing)
        self.feedback = FeedbackMechanism(self.conflict_engine)

    def run_simulation(
        self,
        processes: List[Any],
        seed: Optional[int] = None,
        max_steps: int = 300
    ) -> Dict[str, Any]:
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.config.simulation
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        decision_time = 0.0
        step_i = 0
        while not sim.is_done() and step_i < max_steps:
            state = sim.get_system_state()
            t0 = time.perf_counter()

            props = {
                "CPU_AGENT": self.cpu_agent.propose_action(state),
                "MEMORY_AGENT": self.mem_agent.propose_action(state),
                "IO_AGENT": self.io_agent.propose_action(state)
            }
            decision, prediction = self.coordinator.coordinate(state, props)

            reg_event = self.detector.observe_and_detect(state)
            self.detector.record_decision(decision)

            if reg_event is not None:
                overrides = self.recovery.select_corrective_action(reg_event, step_i, state)
                if overrides:
                    decision.update(overrides)

            self.feedback.process_feedback(prediction, reg_event, step_i)
            self.recovery.track_recovery_progress(step_i, state)

            decision_time += (time.perf_counter() - t0)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(
            sim.completed_processes,
            sim.history,
            overhead_ms,
            conflict_metrics=self.conflict_engine.get_metrics(),
            healing_metrics=self.recovery.get_metrics(),
            total_processes=len(workload)
        )
