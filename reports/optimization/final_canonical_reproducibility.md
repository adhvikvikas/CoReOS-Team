# CoReOS Master Reproducibility Record
**Phase 10: Final Benchmark Evaluation**
**Date**: October 2026 | **Repository**: `CoReOS-Team` | **Status**: Verified

---

## 1. System & Environment Specifications

- **Repository Root**: `/Users/adhvikvikas/Documents/GitHub/CoReOS-Team`
- **Git Branch**: `main`
- **Python Version**: `Python 3.11.4`
- **Virtual Environment**: `.venv`
- **Key Dependencies**:
  - `numpy >= 1.24.0`
  - `pandas >= 2.0.0`
  - `scipy >= 1.10.0`
  - `scikit-learn >= 1.2.0`
  - `fastapi >= 0.100.0`
  - `uvicorn >= 0.22.0`
  - `pytest >= 7.4.0`
- **Frontend Stack**: React 18, TypeScript 5, Vite, Lucide Icons, Recharts

---

## 2. Benchmark Protocol & Configuration

- **Simulation Engine**: `src/coreos/simulation/environment.py` (`SystemSimulator`)
- **Evaluation Horizon**: 300 ticks per trial across all candidates and workloads
- **Number of Candidates**: 8
  - `A_Conventional`: Static Round Robin ($q=4.0$), FCFS I/O
  - `B_IndependentAgents`: Uncoordinated CPU, Memory, and I/O agents
  - `C_CoordNoConflict`: Coordination without conflict prediction
  - `D_ConflictNoHealing`: Conflict prediction without self-healing
  - `E_CompleteCoReOS`: Complete CoReOS architecture (Baseline E)
  - `F_ImprovedRL`: Curriculum-trained Adaptive RL with nearest-neighbor generalization
  - `G_ChampionCoReOS`: Hybrid CoReOS with progress-aware scheduling and calibrated healing
  - `H_OriginalRL`: Pre-trained tabular Q-learning baseline (15 episodes steady-state)
- **Workloads Evaluated**: 6
  - `steady_state`: Baseline nominal workload
  - `cpu_spike`: Compute saturation with deep CPU queue bursts
  - `memory_thrashing`: Memory overcommit and page-thrashing stress
  - `io_bottleneck`: High-frequency I/O access across heterogeneous cylinders
  - `mixed`: Dynamic multi-resource transitions
  - `adversarial_stress`: Simultaneous CPU, RAM, and disk channel saturation
- **Held-Out Test Seeds**: 30 seeds (`5001` through `5030`, inclusive)
  - Completely disjoint from training seeds (`1000..1060`, `4000..4120`) and development seeds (`42`, `4001..4003`).
- **Total Executed Trials**: $8 \text{ candidates} \times 6 \text{ workloads} \times 30 \text{ seeds} = 1,440 \text{ trials}$.

---

## 3. Scoring Formula

Frozen canonical composite score formula:
$$S = 100 \times \left[ 0.30 \cdot \frac{\text{comp}}{100} + 0.25 \cdot \min\left(1, \frac{\text{tp}}{0.25}\right) + 0.20 \cdot \max\left(0, 1 - \frac{\text{pt} - 5}{295}\right) + 0.15 \cdot \max\left(0, 1 - \frac{\text{thrash}}{150}\right) + 0.10 \cdot \text{clamp}(\text{fair}, 0, 1) \right]$$

---

## 4. Execution Commands

To reproduce the full evaluation from scratch:

```bash
# 1. Activate dedicated repository virtual environment
source .venv/bin/activate

# 2. Run test suite to verify baseline integrity (102 tests)
pytest tests/

# 3. Execute final canonical benchmark competition (1,440 trials)
python scripts/run_final_canonical_benchmark.py

# 4. Verify that generated CSV files match the summary
python -c '
import pandas as pd
raw = pd.read_csv("reports/optimization/final_canonical_benchmark_results.csv")
summary = pd.read_csv("reports/optimization/final_canonical_ranking_summary.csv")
assert len(raw) == 1440
assert len(summary) == 8
'
```

---

## 5. Artifact Verification Hash & Manifest

The canonical dataset is cataloged in `reports/optimization/canonical_manifest.json`:
- `final_canonical_benchmark_results.csv`: Exactly 1,440 rows, 17 columns, zero null values.
- `final_canonical_ranking_summary.csv`: Exactly 8 rows, ranks 1 to 8.
- `final_canonical_per_workload_summary.csv`: Exactly 48 rows (8 candidates $\times$ 6 workloads).
- `final_canonical_statistical_comparisons.csv`: Exactly 28 pairwise comparisons with Holm-Bonferroni corrections.
- `final_canonical_guardrail_compliance.csv`: Exactly 48 workload-candidate guardrail audit rows.
