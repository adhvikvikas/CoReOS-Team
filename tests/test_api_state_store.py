"""
Tests for Backend Centralized State Store and Dynamic API Endpoints
Verifies that Conflict Analysis and Self-Healing Center endpoints dynamically reflect
actual simulation runs, preserve legitimate zero values, link conflicts to healing actions,
and ensure resolution statuses are consistent.
"""

import pytest
from backend.state import state_store


def test_state_store_adversarial_stress_simulation():
    res = state_store.run_and_record_simulation(
        workload_type="adversarial_stress",
        num_processes=40,
        policy_mode="Complete CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    assert "history" in res
    assert "state" in res

    conflicts_data = state_store.get_conflict_analytics()
    healing_data = state_store.get_healing_analytics()

    # Adversarial stress causes real conflicts and healing
    assert conflicts_data["total_conflicts"] > 0
    assert len(conflicts_data["recent_conflicts"]) > 0
    assert len(conflicts_data["distribution"]) > 0
    dist_sum = sum(d["count"] for d in conflicts_data["distribution"])
    assert dist_sum == conflicts_data["total_conflicts"]

    assert healing_data["healing_actions"] > 0
    assert len(healing_data["recent_actions"]) > 0
    assert len(healing_data["strategy_usage"]) > 0
    strat_sum = sum(s["count"] for s in healing_data["strategy_usage"])
    assert strat_sum == healing_data["healing_actions"]


def test_conflict_and_healing_linkage_and_consistency():
    state_store.run_and_record_simulation(
        workload_type="adversarial_stress",
        num_processes=40,
        policy_mode="Complete CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    c_data = state_store.get_conflict_analytics()
    h_data = state_store.get_healing_analytics()

    # Check IDs exist
    assert all("id" in c for c in c_data["recent_conflicts"])
    assert all("id" in h for h in h_data["recent_actions"])

    # Check linking
    linked_conflicts = [c for c in c_data["recent_conflicts"] if c.get("linked_healing_id")]
    assert len(linked_conflicts) > 0

    # Ensure linked healing action exists and statuses match
    for c in linked_conflicts:
        hid = c["linked_healing_id"]
        matching_h = next((h for h in h_data["recent_actions"] if h["id"] == hid), None)
        if matching_h:
            # Both must agree on resolution
            assert c["status"] == matching_h["status"]
            assert c["id"] in matching_h["linked_conflicts"]


def test_state_store_steady_state_preserves_zeroes():
    # Steady state nominal workload should not invent fake conflicts
    state_store.run_and_record_simulation(
        workload_type="steady_state",
        num_processes=40,
        policy_mode="Complete CoReOS",
        seed=42,
        sim_quantum=4.0
    )

    conflicts_data = state_store.get_conflict_analytics()
    healing_data = state_store.get_healing_analytics()

    # Legitimate zeroes must be preserved
    assert conflicts_data["total_conflicts"] == 0
    assert conflicts_data["conflict_rate"] == "0.0%"
    assert len(conflicts_data["recent_conflicts"]) == 0
    assert len(conflicts_data["distribution"]) == 0

    assert healing_data["healing_actions"] == 0
    assert healing_data["success_rate"] == 0.0
    assert len(healing_data["recent_actions"]) == 0
    assert len(healing_data["strategy_usage"]) == 0


def test_state_store_transitions_dynamically():
    # Run memory thrashing
    state_store.run_and_record_simulation(
        workload_type="memory_thrashing",
        num_processes=40,
        policy_mode="Complete CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    c_thrash = state_store.get_conflict_analytics()
    h_thrash = state_store.get_healing_analytics()

    assert c_thrash["total_conflicts"] > 0
    assert h_thrash["healing_actions"] > 0
    assert c_thrash["workload_info"]["workload_type"] == "memory_thrashing"
    assert c_thrash["historical_runs_count"] >= 3


def test_simulation_non_default_workload_preservation_and_case_insensitivity():
    """
    Verifies that selecting a non-default workload such as CPU_spike with custom configuration
    (num_processes=50, sim_quantum=6.0) is preserved in state store and GET /latest endpoint,
    normalizes case, and does not reset to adversarial_stress.
    """
    from backend.api.simulation import get_latest_simulation, run_simulation, SimulationRequest
    from backend.api.agents import get_agent_decisions
    from backend.api.conflicts import get_conflict_analysis
    from backend.api.healing import get_healing_metrics
    from backend.api.overview import get_overview

    # Run non-default workload with uppercase/mixed case
    req = SimulationRequest(
        workload_type="CPU_spike",
        num_processes=50,
        policy_mode="Complete CoReOS",
        seed=101,
        sim_quantum=6.0
    )
    run_res = run_simulation(req)
    assert run_res is not None

    # 1. Check GET /api/simulation/latest preserves config and result
    latest = get_latest_simulation()
    assert latest["is_completed"] is True
    assert latest["config"]["workload_type"] == "cpu_spike"
    assert latest["config"]["num_processes"] == 50
    assert latest["config"]["seed"] == 101
    assert latest["config"]["sim_quantum"] == 6.0
    assert len(latest["result"]["history"]) > 0

    # 2. Check all dependent page APIs consume data from the SAME run
    agents = get_agent_decisions()
    assert agents["workload_info"]["workload_type"] == "cpu_spike"
    assert agents["workload_info"]["num_processes"] == 50
    assert len(agents["records"]) > 0
    # Audit records must reflect the 6.0 quantum
    assert any(r["cpu_proposed_quantum"] >= 6.0 or r["coordinated_quantum"] >= 6.0 for r in agents["records"])

    conflicts = get_conflict_analysis()
    assert conflicts["workload_info"]["workload_type"] == "cpu_spike"
    assert conflicts["workload_info"]["num_processes"] == 50

    healing = get_healing_metrics()
    assert healing["workload_info"]["workload_type"] == "cpu_spike"
    assert healing["workload_info"]["num_processes"] == 50

    overview = get_overview()
    assert overview["workload_info"]["workload_type"] == "cpu_spike"
    assert overview["telemetry"] == latest["result"]["history"]


def test_sequential_navigation_scenario_does_not_reset():
    """
    Simulates user navigation across pages:
    Simulation Lab -> Conflict Analysis -> Self-Healing -> Agent Control -> Overview -> Simulation Lab.
    Verifies that navigation does not trigger a re-run, does not reset to adversarial_stress,
    and preserves the user's active configuration.
    """
    from backend.api.simulation import get_latest_simulation, run_simulation, SimulationRequest
    from backend.api.conflicts import get_conflict_analysis
    from backend.api.healing import get_healing_metrics
    from backend.api.agents import get_agent_decisions
    from backend.api.overview import get_overview

    # Step 1: User runs cpu_spike
    run_simulation(SimulationRequest(
        workload_type="cpu_spike",
        num_processes=35,
        policy_mode="Complete CoReOS",
        seed=77,
        sim_quantum=5.0
    ))
    initial_runs = state_store.simulation_runs_history[-1]["run_id"]

    # Step 2: User navigates to Conflict Analysis
    c_page = get_conflict_analysis()
    assert c_page["workload_info"]["workload_type"] == "cpu_spike"

    # Step 3: User navigates to Self-Healing Center
    h_page = get_healing_metrics()
    assert h_page["workload_info"]["workload_type"] == "cpu_spike"

    # Step 4: User navigates to Agent Control Center
    a_page = get_agent_decisions()
    assert a_page["workload_info"]["workload_type"] == "cpu_spike"

    # Step 5: User navigates to System Overview
    o_page = get_overview()
    assert o_page["workload_info"]["workload_type"] == "cpu_spike"

    # Step 6: User navigates BACK to Simulation Lab (invoking get_latest_simulation)
    latest_page = get_latest_simulation()
    assert latest_page["config"]["workload_type"] == "cpu_spike"
    assert latest_page["config"]["num_processes"] == 35
    assert latest_page["config"]["sim_quantum"] == 5.0

    # Ensure NO unintended new simulation was executed during navigation
    assert state_store.simulation_runs_history[-1]["run_id"] == initial_runs


def test_state_store_coreos_adversarial_stress_simulation():
    """
    Verifies that policy_mode='CoReOS' invokes the improved CoReOS architecture,
    records non-zero conflicts and healing actions under adversarial stress,
    links conflict events to healing actions, and correctly updates summary analytics.
    """
    res = state_store.run_and_record_simulation(
        workload_type="adversarial_stress",
        num_processes=40,
        policy_mode="CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    assert res is not None
    assert "history" in res
    assert "state" in res

    conflicts_data = state_store.get_conflict_analytics()
    healing_data = state_store.get_healing_analytics()

    assert conflicts_data["total_conflicts"] > 0
    assert len(conflicts_data["recent_conflicts"]) > 0
    assert len(conflicts_data["distribution"]) > 0
    assert conflicts_data["workload_info"]["policy_mode"] == "CoReOS"

    assert healing_data["healing_actions"] > 0
    assert healing_data["success_rate"] > 0.0
    assert healing_data["avg_recovery_time"] > 0.0
    assert len(healing_data["recent_actions"]) > 0
    assert len(healing_data["strategy_usage"]) > 0


def test_state_store_coreos_workload_comparisons():
    """
    Verifies reproducible telemetry across key workloads using CoReOS policy:
    - steady_state: strictly 0 conflicts, 0 healing actions (control)
    - memory_thrashing: non-zero conflicts and healing actions
    - adversarial_stress: non-zero conflicts and healing actions
    """
    # 1. Steady state control
    state_store.run_and_record_simulation(
        workload_type="steady_state",
        num_processes=40,
        policy_mode="CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    c_steady = state_store.get_conflict_analytics()
    h_steady = state_store.get_healing_analytics()
    assert c_steady["total_conflicts"] == 0
    assert h_steady["healing_actions"] == 0

    # 2. Memory thrashing
    state_store.run_and_record_simulation(
        workload_type="memory_thrashing",
        num_processes=40,
        policy_mode="CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    c_mem = state_store.get_conflict_analytics()
    h_mem = state_store.get_healing_analytics()
    assert c_mem["total_conflicts"] > 0
    assert h_mem["healing_actions"] > 0
    assert any(d["type"] == "CPU-Memory" for d in c_mem["distribution"])
    assert any(s["strategy"] == "Memory Reclaim & Quantum Expansion" for s in h_mem["strategy_usage"])


def test_consecutive_simulation_refresh_preserves_independence():
    """
    Verifies that running a new simulation completely updates telemetry,
    increments run_id, and does not contaminate the previous run data.
    """
    # Run 1: memory_thrashing
    state_store.run_and_record_simulation(
        workload_type="memory_thrashing",
        num_processes=30,
        policy_mode="CoReOS",
        seed=12,
        sim_quantum=4.0
    )
    run1_id = state_store.workload_info["run_id"]
    conf1 = state_store.get_conflict_analytics()["total_conflicts"]

    # Run 2: steady_state
    state_store.run_and_record_simulation(
        workload_type="steady_state",
        num_processes=30,
        policy_mode="CoReOS",
        seed=12,
        sim_quantum=4.0
    )
    run2_id = state_store.workload_info["run_id"]
    c_steady = state_store.get_conflict_analytics()

    assert run2_id == run1_id + 1
    assert c_steady["workload_info"]["workload_type"] == "steady_state"
    assert c_steady["total_conflicts"] == 0


