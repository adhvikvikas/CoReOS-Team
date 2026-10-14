# CoReOS Phase 8: Reproducibility Protocol and Environment Specification

---

## 1. System and Software Environment

- **Operating System**: macOS (Darwin 24.6.0)
- **Repository Root**: `/Users/adhvikvikas/Documents/GitHub/CoReOS-Team`
- **Python Runtime**: Python 3.11.4 (via dedicated virtual environment `.venv/bin/python`)
- **Key Python Dependencies**:
  - `numpy >= 1.24.0` (active: `2.4.4`)
  - `pandas >= 2.0.0` (active: `3.0.1`)
  - `scipy >= 1.10.0` (active: `1.17.1`)
  - `pytest >= 8.0.0` (active: `9.1.1`)
  - `fastapi >= 0.100.0`, `pydantic >= 2.0.0`, `uvicorn >= 0.22.0`
- **Frontend Runtime**:
  - Node.js v20+ / npm v10+
  - Vite v8.3.4, React v19.2.8, Tailwind CSS v4.3.3

---

## 2. Seed Cohort Partitioning

To ensure strict experimental integrity and prevent data contamination, random seeds are strictly partitioned across all project phases:

| Phase | Purpose | Random Seed Cohort | Total Seeds | Contamination Status |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1–2** | Initial Baseline Tuning | `[42, 102, 202]` | 3 | Disjoint from evaluation |
| **Phase 3** | Benchmark Reporting | `[42, 142, ..., 1442]` | 15 | Disjoint from evaluation |
| **Phase 3** | Candidate Tuning | `[2001..2015]` | 15 | Disjoint from evaluation |
| **Phase 3** | Ablation Experiments | `[2101..2115]` | 15 | Disjoint from evaluation |
| **Phase 5** | Historical Held-Out Competition | `[3001..3030]` | 30 | Disjoint from Phase 8 |
| **Phase 7** | RL Multi-Workload Curriculum Training | `[4001..4120]` | 120 | Training set only |
| **Phase 7** | Diagnostic RL Verification | `[42..46]` | 5 | Diagnostic only |
| **Phase 8** | **Final Competition Evaluation** | **`[5001..5030]`** | **30** | **Virgin Held-Out Cohort** |

---

## 3. Candidate Mappings and Implementation Files

| Candidate | Name | Source Code Location |
| :--- | :--- | :--- |
| `A_Conventional` | Conventional Round Robin ($q=4.0$) | [`src/coreos/baselines/schedulers.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/baselines/schedulers.py) |
| `B_IndependentAgents` | Independent Agent Coordination | [`src/coreos/baselines/schedulers.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/baselines/schedulers.py) |
| `C_CoordNoConflict` | Coordination w/o Conflict Prediction | [`src/coreos/evaluation/experiments.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/evaluation/experiments.py) |
| `D_ConflictNoHealing` | Conflict Prediction w/o Healing | [`src/coreos/evaluation/experiments.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/evaluation/experiments.py) |
| `E_CompleteCoReOS` | Baseline Complete CoReOS | [`src/coreos/evaluation/experiments.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/evaluation/experiments.py) |
| `F_ImprovedRL` | Improved Adaptive RL Candidate | [`src/coreos/learning/adaptive_rl.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/learning/adaptive_rl.py) |
| `G_ChampionCoReOS` | Hybrid Champion CoReOS | [`src/coreos/optimization/candidates.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/optimization/candidates.py) |
| `H_OriginalRL` | Original Tabular RL Baseline | [`src/coreos/learning/train.py`](file:///Users/adhvikvikas/Documents/GitHub/CoReOS-Team/src/coreos/learning/train.py) |

---

## 4. Frozen Composite Scoring Formula

$$S = 100 \times \left[ 0.30 \times \frac{\text{comp}}{100} + 0.25 \times \min\left(1.0, \frac{\text{thru}}{0.25}\right) + 0.20 \times \max\left(0, 1 - \frac{\text{pt} - 5}{295}\right) + 0.15 \times \max\left(0, 1 - \frac{\text{thrash}}{150}\right) + 0.10 \times \text{clamp}(\text{fair}, 0, 1) \right]$$

---

## 5. Execution Commands

### 1. Execute Regression Test Suite (96 Tests)
```bash
cd /Users/adhvikvikas/Documents/GitHub/CoReOS-Team
.venv/bin/pytest tests/
```

### 2. Verify Frontend Production Build
```bash
cd /Users/adhvikvikas/Documents/GitHub/CoReOS-Team
npm --prefix frontend run build
```

### 3. Run Phase 8 Benchmark Competition (1,440 Trials)
```bash
cd /Users/adhvikvikas/Documents/GitHub/CoReOS-Team
.venv/bin/python scripts/run_phase8_final_competition.py
```

### 4. Generated Output CSV Files
- Raw trial results: `reports/optimization/phase8_final_benchmark_results.csv`
- Aggregate ranking: `reports/optimization/phase8_final_ranking_summary.csv`
- Per-workload results: `reports/optimization/phase8_per_workload_summary.csv`
- Statistical comparisons: `reports/optimization/phase8_statistical_comparisons.csv`
- Final competition report: `reports/optimization/phase8_final_competition_report.md`
- Final audit and research sign-off: `reports/optimization/phase9_final_audit_report.md`
