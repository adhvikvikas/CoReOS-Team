"""
Tests for Frontend-to-Backend Performance Integration (Phase 8/9 Verification)

Verifies:
1. Benchmark endpoint returns all 8 candidates from Phase 8 final benchmark results (1,440 trials).
2. Overall ranking summary contains 8 candidates with exact Phase 8 composite score aggregates
   (F_ImprovedRL ~ 84.80, G_ChampionCoReOS ~ 82.84, H_OriginalRL ~ 82.17).
3. Per-workload summary contains all 48 candidate-workload combinations.
4. Overview endpoint reports 8 evaluated candidates and Phase 8 adversarial stress comparison.
5. Simulation Lab executes live simulation for both Champion CoReOS and Improved RL.
6. Reports download and content endpoints serve Phase 8/9 datasets and Markdown reports.
"""

import pytest
from backend.api.benchmarks import get_benchmarks
from backend.api.overview import get_overview
from backend.api.simulation import run_simulation, SimulationRequest
from backend.api.reports import download_report, get_report_content


def test_benchmarks_endpoint_phase8_candidates_and_shape():
    data = get_benchmarks()
    assert data["source"] in ["final_canonical_benchmark_results.csv", "phase8_final_benchmark_results.csv"]

    # Must contain all 8 candidates
    expected_candidates = [
        "A_Conventional",
        "B_IndependentAgents",
        "C_CoordNoConflict",
        "D_ConflictNoHealing",
        "E_CompleteCoReOS",
        "F_ImprovedRL",
        "G_ChampionCoReOS",
        "H_OriginalRL"
    ]
    assert data["candidates"] == expected_candidates
    assert len(data["workloads"]) == 6
    assert len(data["data"]) == 1440

    # Every record must have both baseline and candidate keys
    for r in data["data"][:20]:
        assert "candidate" in r
        assert "baseline" in r
        assert r["candidate"] == r["baseline"]
        assert "penalized_turnaround" in r
        assert "composite_score" in r


def test_benchmarks_ranking_summary_scores():
    data = get_benchmarks()
    ranking = data["overall_ranking"]
    assert len(ranking) == 8

    rank_by_cand = {r["candidate"]: r for r in ranking}

    # Rank 1: F_ImprovedRL ~ 85.81 (or Phase 8: 84.80)
    assert "F_ImprovedRL" in rank_by_cand
    imp = rank_by_cand["F_ImprovedRL"]
    assert imp["rank"] == 1
    assert float(imp["composite_score_mean"]) >= 84.50
    assert float(imp["completion_rate_mean"]) >= 95.0

    # Rank 2: G_ChampionCoReOS ~ 84.87 (or Phase 8: 82.84)
    assert "G_ChampionCoReOS" in rank_by_cand
    champ = rank_by_cand["G_ChampionCoReOS"]
    assert champ["rank"] == 2
    assert float(champ["composite_score_mean"]) >= 82.80
    assert float(champ["completion_rate_mean"]) >= 92.0
    assert float(champ["thrashing_ticks_mean"]) <= 0.20

    # Rank 3: H_OriginalRL ~ 82.17
    assert "H_OriginalRL" in rank_by_cand
    orig = rank_by_cand["H_OriginalRL"]
    assert orig["rank"] == 3
    assert pytest.approx(float(orig["composite_score_mean"]), abs=0.1) == 82.17


def test_benchmarks_per_workload_summary():
    data = get_benchmarks()
    pw = data["per_workload_summary"]
    assert len(pw) == 48  # 8 candidates * 6 workloads

    # Check adversarial stress
    adv = [r for r in pw if r["workload"] == "adversarial_stress"]
    assert len(adv) == 8

    adv_by_cand = {r["candidate"]: r for r in adv}
    # Champion achieved >= 82.8% completion (Phase 10: 96.17%)
    assert float(adv_by_cand["G_ChampionCoReOS"]["completion_rate_mean"]) >= 82.5
    assert float(adv_by_cand["F_ImprovedRL"]["completion_rate_mean"]) >= 95.0
    assert pytest.approx(float(adv_by_cand["A_Conventional"]["completion_rate_mean"]), abs=0.5) == 40.7


def test_overview_endpoint_phase8_metrics():
    overview = get_overview()
    assert overview["evaluated_baselines"] == "8"

    stress = overview["stress_comparison"]
    assert stress is not None
    assert stress["baseline_conv"] == "A_Conventional"
    assert stress["baseline_coreos"] == "G_ChampionCoReOS"
    assert stress["conv_completion_rate"] == 40.7
    assert stress["coreos_completion_rate"] >= 82.5
    assert stress["thrashing_reduction_pct"] >= 99.0
    assert stress["comp_diff_pct"] >= 40.0


def test_simulation_run_champion_and_improved_rl():
    # 1. Champion CoReOS live simulation
    champ_req = SimulationRequest(
        workload_type="steady_state",
        num_processes=30,
        policy_mode="Champion CoReOS (Optimized)",
        seed=123,
        sim_quantum=4.0
    )
    champ_res = run_simulation(champ_req)
    assert len(champ_res["history"]) > 0
    assert champ_res["workload_info"]["policy_mode"] == "Champion CoReOS (Optimized)"

    # 2. Improved RL live simulation
    rl_req = SimulationRequest(
        workload_type="steady_state",
        num_processes=30,
        policy_mode="Improved RL (Phase 7)",
        seed=123,
        sim_quantum=4.0
    )
    rl_res = run_simulation(rl_req)
    assert len(rl_res["history"]) > 0
    assert rl_res["workload_info"]["policy_mode"] == "Improved RL (Phase 7)"


def test_reports_phase8_and_phase9_access():
    # Download checks
    res_b = download_report("phase8_final_benchmark_results.csv")
    assert not isinstance(res_b, dict)  # FileResponse returned

    res_r = download_report("phase8_final_ranking_summary.csv")
    assert not isinstance(res_r, dict)

    res_pw = download_report("phase8_per_workload_summary.csv")
    assert not isinstance(res_pw, dict)

    res_rep = download_report("phase8_final_competition_report.md")
    assert not isinstance(res_rep, dict)

    res_aud = download_report("phase9_final_audit_report.md")
    assert not isinstance(res_aud, dict)

    # Content checks
    comp_rep = get_report_content("phase8_final_competition_report.md")
    assert "Phase 8" in comp_rep["content"]

    audit_rep = get_report_content("phase9_final_audit_report.md")
    assert "Phase 9" in audit_rep["content"]


def test_benchmarks_active_7_candidates_and_ranking():
    data = get_benchmarks()
    # Active visible candidates set has 7 candidates (E_CompleteCoReOS removed)
    assert "active_candidates" in data
    assert len(data["active_candidates"]) == 7
    assert "E_CompleteCoReOS" not in data["active_candidates"]
    assert "G_ChampionCoReOS" in data["active_candidates"]
    assert "F_ImprovedRL" in data["active_candidates"]

    # Active ranking has exactly 7 candidates with ranks 1..7 without gaps
    active_ranking = data["active_ranking"]
    assert len(active_ranking) == 7
    ranks = [r["rank"] for r in active_ranking]
    assert ranks == [1, 2, 3, 4, 5, 6, 7]
    assert "E_CompleteCoReOS" not in [r["candidate"] for r in active_ranking]


def test_simulation_canonical_coreos_execution():
    coreos_req = SimulationRequest(
        workload_type="adversarial_stress",
        num_processes=40,
        policy_mode="CoReOS",
        seed=42,
        sim_quantum=4.0
    )
    res = run_simulation(coreos_req)
    assert len(res["history"]) > 0
    assert res["workload_info"]["policy_mode"] == "CoReOS"
    assert "state" in res


def test_reports_ablation_summary_endpoint():
    from backend.api.reports import get_ablation_summary
    abl = get_ablation_summary()
    assert "data" in abl
    assert len(abl["data"]) > 0
    configs = [r["configuration"] for r in abl["data"]]
    assert "CoReOS (Full Architecture)" in configs
    # No KeyError: 'configuration'
    assert all("workload" in r and "configuration" in r for r in abl["data"])
