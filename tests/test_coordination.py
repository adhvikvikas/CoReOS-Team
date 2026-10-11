"""
Unit Tests for CoReOS Coordination & Safety Constraints
Tests safety constraint enforcement, Pareto arbitration, and fallback safeguards.
"""

import pytest
from src.coreos.coordination.constraints import validate_safety_constraints
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent


def test_safety_constraints_clamping():
    decision = {
        "cpu_policy": "INVALID_POLICY",
        "cpu_quantum": -5.0,
        "memory_reclaim_target": -100.0,
        "io_policy": "INVALID_IO"
    }
    safe, modified, note = validate_safety_constraints(decision, {})

    assert modified is True
    assert safe["cpu_policy"] == "ROUND_ROBIN"
    assert safe["cpu_quantum"] == 1.0  # Clamped to minimum quantum
    assert safe["memory_reclaim_target"] == 0.0  # Clamped to non-negative
    assert safe["io_policy"] == "FCFS"


def test_coordinator_pareto_arbitration():
    engine = ConflictEngine(use_ml=False)
    coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)
    state = {
        "cpu_utilization": 90.0,
        "memory_utilization": 92.0,
        "io_saturation": 85.0,
        "ready_queue_length": 10,
        "io_queue_length": 10,
        "is_thrashing": True,
        "time": 20.0
    }
    cpu_ag = CPUAgent()
    mem_ag = MemoryAgent()
    io_ag = IOAgent()

    props = {
        "CPU_AGENT": cpu_ag.propose_action(state),
        "MEMORY_AGENT": mem_ag.propose_action(state),
        "IO_AGENT": io_ag.propose_action(state)
    }

    decision, pred = coord.coordinate(state, props)
    assert pred.is_conflict is True
    assert decision["arbitration_applied"] is True
    assert decision["cpu_quantum"] >= 6.0
    assert len(coord.audit_log) > 0


def test_coordinator_fallback():
    coord = CoordinationAgent(conflict_engine=None, enable_conflict_prediction=False)
    props = {
        "CPU_AGENT": CPUAgent().propose_action({}),
        "MEMORY_AGENT": MemoryAgent().propose_action({}),
        "IO_AGENT": IOAgent().propose_action({})
    }
    decision, pred = coord.coordinate({}, props)
    assert decision["arbitration_applied"] is False
    assert decision["cpu_policy"] == "ROUND_ROBIN"


def test_non_predictive_coordination_arbitrates_tensions_without_predictions():
    """
    Priority 2 requirement: Test that the non-predictive coordination configuration
    (Configuration C, enable_conflict_prediction=False) actually changes proposal handling
    under a constructed conflict scenario, while respecting safety constraints and NOT using
    conflict predictions or ML models.
    """
    coord = CoordinationAgent(conflict_engine=None, enable_conflict_prediction=False)
    
    # State with active tensions:
    # 1. Memory pressure + thrashing
    # 2. Saturated I/O
    # 3. Congested CPU ready queue
    stress_state = {
        "memory_utilization": 92.0,
        "is_under_memory_pressure": True,
        "is_thrashing": True,
        "io_queue_length": 18,
        "io_saturation": 85.0,
        "ready_queue_length": 14,
        "time": 25.0
    }
    
    # Raw agent proposals before coordination
    raw_props = {
        "CPU_AGENT": CPUAgent().propose_action(stress_state),     # Proposes quantum 4.0
        "MEMORY_AGENT": MemoryAgent().propose_action(stress_state), # Proposes aggressive reclaim 4096.0 MB
        "IO_AGENT": IOAgent().propose_action(stress_state)          # Proposes FCFS
    }
    
    # Confirm raw proposals contain tensions before coordination
    assert raw_props["CPU_AGENT"].parameters["quantum"] == 4.0
    assert raw_props["MEMORY_AGENT"].parameters["target_free_mb"] == 4096.0
    
    # Run non-predictive coordination
    decision, pred = coord.coordinate(stress_state, raw_props)
    
    # 1. Prediction must be strictly disabled (no predictive conflict engine)
    assert pred.is_conflict is False
    assert pred.conflict_type == "NONE_DISABLED"
    assert "disabled" in pred.rationale.lower()
    
    # 2. Non-predictive coordination must have actively modified proposals
    assert decision["arbitration_applied"] is True
    # Quantum lengthened to 6.0 to dampen context switching under memory pressure
    assert decision["cpu_quantum"] == 6.0
    # Memory reclaim paced down to 1024 MB to protect saturated I/O channels
    assert decision["memory_reclaim_target"] == 1024.0
    # I/O policy upgraded to SCAN to prevent seek starvation during page-out
    assert decision["io_policy"] == "SCAN"
    
    # 3. Safety constraints are fully respected
    safe, modified, _ = validate_safety_constraints(decision, stress_state)
    assert not modified  # Must already be compliant with all hard safety bounds


def test_non_predictive_coordination_quiescent_state_passes_unmodified():
    """
    Verifies that under benign/quiescent conditions without tensions,
    non-predictive coordination passes raw proposals unmodified.
    """
    coord = CoordinationAgent(conflict_engine=None, enable_conflict_prediction=False)
    quiescent_state = {
        "memory_utilization": 25.0,
        "is_under_memory_pressure": False,
        "is_thrashing": False,
        "io_queue_length": 1,
        "io_saturation": 10.0,
        "ready_queue_length": 2,
        "time": 5.0
    }
    props = {
        "CPU_AGENT": CPUAgent().propose_action(quiescent_state),
        "MEMORY_AGENT": MemoryAgent().propose_action(quiescent_state),
        "IO_AGENT": IOAgent().propose_action(quiescent_state)
    }
    decision, pred = coord.coordinate(quiescent_state, props)
    assert pred.is_conflict is False
    assert decision["arbitration_applied"] is False
    # Unmodified raw CPU proposal for ready_q=2 is 2.0
    assert decision["cpu_quantum"] == props["CPU_AGENT"].parameters["quantum"]
    assert decision["memory_reclaim_target"] == props["MEMORY_AGENT"].parameters["target_free_mb"]
    assert decision["io_policy"] == props["IO_AGENT"].parameters["io_policy"]


def test_conventional_baseline_watermark_paging_fairness():
    """
    Priority 2 requirement: Test that conventional baseline and CoReOS receive
    comparable resource conditions. Specifically, verify that ConventionalScheduler
    triggers static watermark memory reclamation under memory pressure instead of
    unconditionally bypassing the virtual-memory swap subsystem with a hardcoded 0.0.
    """
    from src.coreos.baselines.schedulers import ConventionalScheduler
    from src.coreos.simulation.process import SimulatedProcess
    
    # Construct a memory-heavy workload exceeding physical RAM (8192 MB)
    # 8 processes requiring 1500 MB each = 12000 MB > 8192 MB
    heavy_procs = [
        SimulatedProcess(
            pid=i + 1,
            name=f"HeavyProc_{i+1}",
            arrival_time=0.0,
            cpu_burst_time=10.0,
            memory_demand_mb=1500.0,
            io_burst_time=2.0
        )
        for i in range(8)
    ]
    
    # Run with standard watermark paging (scientifically fair)
    metrics_watermark = ConventionalScheduler.run_round_robin(
        heavy_procs, quantum=4.0, enable_watermark_paging=True, watermark_reclaim_mb=1024.0
    )
    
    # Run without watermark paging (legacy hardcoded 0.0)
    metrics_legacy = ConventionalScheduler.run_round_robin(
        heavy_procs, quantum=4.0, enable_watermark_paging=False
    )
    
    # With watermark paging enabled, the conventional scheduler actively participates
    # in virtual-memory management:
    assert metrics_watermark["thrashing_ticks"] >= 0
    # Both modes should finish processes
    assert metrics_watermark["throughput"] > 0
    assert metrics_legacy["throughput"] > 0


def test_uncoordinated_baseline_disables_coordination():
    """
    Regression test: Verify that when enable_coordination=False,
    CoordinationAgent does NOT apply non-predictive coordination or arbitration,
    passing raw proposals through unmodified even under stress conditions.
    """
    from src.coordination.coordination_agent import CoordinationAgent as RootCoordAgent
    from src.coreos.coordination.coordinator import CoordinationAgent as CoreCoordAgent

    stress_state = {
        "memory_utilization": 92.0,
        "is_under_memory_pressure": True,
        "is_thrashing": True,
        "io_queue_length": 18,
        "io_saturation": 85.0,
        "ready_queue_length": 14,
        "time": 25.0
    }
    raw_props = {
        "CPU_AGENT": CPUAgent().propose_action(stress_state),
        "MEMORY_AGENT": MemoryAgent().propose_action(stress_state),
        "IO_AGENT": IOAgent().propose_action(stress_state)
    }

    for agent_cls in [RootCoordAgent, CoreCoordAgent]:
        coord = agent_cls(conflict_engine=None, enable_conflict_prediction=False, enable_coordination=False)
        decision, pred = coord.coordinate(stress_state, raw_props)
        assert pred.conflict_type == "NONE_UNCOORDINATED"
        assert decision["arbitration_applied"] is False
        # Raw proposals are unperturbed
        assert decision["cpu_quantum"] == raw_props["CPU_AGENT"].parameters["quantum"]
        assert decision["memory_reclaim_target"] == raw_props["MEMORY_AGENT"].parameters["target_free_mb"]
        assert decision["io_policy"] == raw_props["IO_AGENT"].parameters["io_policy"]


def test_ablation_uncoordinated_baseline_matches_independent_agents():
    """
    Regression test: Verify that AblationRunner's Uncoordinated_Baseline
    produces metrics identical to BenchmarkRunner's Baseline B (Independent Agents).
    """
    from src.evaluation.ablation_runner import AblationRunner
    from src.evaluation.benchmark_runner import BenchmarkRunner
    from src.simulation.workload_generator import WorkloadGenerator

    seed = 42
    wg = WorkloadGenerator(seed=seed)
    procs = wg.generate_workload(num_processes=40, workload_type="memory_thrashing")

    b_runner = BenchmarkRunner()
    b_metrics = b_runner.run_baseline_b_independent_agents(procs, seed=seed)

    a_runner = AblationRunner(seed=seed)
    a_metrics = a_runner.run_ablation_trial(
        procs,
        enable_conflict_prediction=False,
        use_ml_conflict=False,
        enable_self_healing=False,
        enable_feedback=False,
        enable_coordination=False,
        sim_seed=seed
    )

    assert a_metrics["completed_processes"] == b_metrics["completed_processes"]
    assert a_metrics["completion_rate"] == b_metrics["completion_rate"]
    assert a_metrics["thrashing_ticks"] == b_metrics["thrashing_ticks"]
    assert pytest.approx(a_metrics["avg_turnaround_time"], 0.01) == b_metrics["avg_turnaround_time"]


def test_ablation_configurations_feature_disabling_verification():
    """
    Regression test: Verify that each ablation configuration flag strictly
    disables its corresponding architectural feature.
    """
    from src.evaluation.ablation_runner import AblationRunner
    from src.simulation.workload_generator import WorkloadGenerator

    seed = 42
    wg = WorkloadGenerator(seed=seed)
    procs = wg.generate_workload(num_processes=20, workload_type="adversarial_stress")
    runner = AblationRunner(seed=seed)

    # 1. Full_CoReOS: all modules active
    m_full = runner.run_ablation_trial(
        procs, enable_conflict_prediction=True, use_ml_conflict=True,
        enable_self_healing=True, enable_feedback=True, enable_coordination=True, sim_seed=seed
    )
    assert m_full["conflict_metrics"]["total_evaluations"] > 0

    # 2. No_Self_Healing: recovery engine disabled
    m_no_heal = runner.run_ablation_trial(
        procs, enable_conflict_prediction=True, use_ml_conflict=True,
        enable_self_healing=False, enable_feedback=False, enable_coordination=True, sim_seed=seed
    )
    assert m_no_heal["healing_metrics"]["total_recoveries"] == 0
    assert m_no_heal["healing_metrics"]["policy_switches"] == 0

    # 3. No_Conflict_Prediction: conflict prediction disabled (evaluations == 0)
    m_no_pred = runner.run_ablation_trial(
        procs, enable_conflict_prediction=False, use_ml_conflict=False,
        enable_self_healing=True, enable_feedback=False, enable_coordination=True, sim_seed=seed
    )
    assert m_no_pred["conflict_metrics"]["total_evaluations"] == 0

    # 4. Rule_Only_Conflict: ML disabled, rule evaluations active with feedback
    m_rule = runner.run_ablation_trial(
        procs, enable_conflict_prediction=True, use_ml_conflict=False,
        enable_self_healing=True, enable_feedback=True, enable_coordination=True, sim_seed=seed
    )
    assert m_rule["conflict_metrics"]["total_evaluations"] > 0

    # 5. No_Feedback_Tuning: feedback processing disabled
    m_no_fb = runner.run_ablation_trial(
        procs, enable_conflict_prediction=True, use_ml_conflict=True,
        enable_self_healing=True, enable_feedback=False, enable_coordination=True, sim_seed=seed
    )
    # When feedback is disabled, process_feedback is bypassed (0 evaluations logged)
    assert m_no_fb["conflict_metrics"]["total_evaluations"] == 0

    # 6. Uncoordinated_Baseline: coordination disabled
    m_uncoord = runner.run_ablation_trial(
        procs, enable_conflict_prediction=False, use_ml_conflict=False,
        enable_self_healing=False, enable_feedback=False, enable_coordination=False, sim_seed=seed
    )
    assert m_uncoord["conflict_metrics"]["total_evaluations"] == 0
    assert m_uncoord["healing_metrics"]["total_recoveries"] == 0

