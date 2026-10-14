# CoReOS Phase 2: Competition Objective & Experimental Protocol

**Author**: CoReOS Optimization Team  
**Date**: 2026-10-13  
**Status**: Approved & Frozen for Candidate Optimization  

---

## 1. Primary Ranking Objective

To prevent single-metric gaming and ensure balanced system performance across all operating conditions, all baselines and CoReOS candidates are evaluated against a predefined **Composite Optimization Score ($S \in [0.0, 100.0]$)**.

### 1.1 Normalized Component Metric Formulations
Each component metric is mapped to a strictly bounded $[0.0, 1.0]$ interval using fixed, documented reference parameters:

1. **Completion Rate Score ($S_{\text{comp}}$)**:
   $$S_{\text{comp}} = \frac{\text{Completion Rate (\%)}}{100.0} \in [0.0, 1.0]$$
   - Direction: Higher is better.
   - Reference: 0% = 0.0, 100% = 1.0.

2. **Throughput Score ($S_{\text{thru}}$)**:
   $$S_{\text{thru}} = \min\left(1.0, \frac{\text{Throughput}}{0.25}\right) \in [0.0, 1.0]$$
   - Direction: Higher is better.
   - Reference: Normalized against $T_{\text{ref}} = 0.25$ processes/tick (the theoretical saturation bound for 40 processes completing within a 150–160 tick window).

3. **Penalized Turnaround Score ($S_{\text{turn}}$)**:
   $$S_{\text{turn}} = \max\left(0.0, 1.0 - \frac{\text{Penalized Turnaround} - 5.0}{300.0 - 5.0}\right) \in [0.0, 1.0]$$
   - Direction: Lower penalized turnaround produces higher score.
   - Reference: Minimum turnaround baseline = 5.0 ticks; maximum penalty cutoff = 300.0 ticks.

4. **Thrashing Control Score ($S_{\text{thrash}}$)**:
   $$S_{\text{thrash}} = \max\left(0.0, 1.0 - \frac{\text{Thrashing Ticks}}{150.0}\right) \in [0.0, 1.0]$$
   - Direction: Lower thrashing produces higher score.
   - Reference: $H_{\text{ref}} = 150.0$ ticks (zero thrashing = 1.0; 150+ thrashing ticks = 0.0).

5. **Jain's Fairness Score ($S_{\text{fair}}$)**:
   $$S_{\text{fair}} = \max(0.0, \min(1.0, \text{Jain's Fairness Index})) \in [0.0, 1.0]$$
   - Direction: Higher fairness is better.
   - Reference: Naturally bounded in $[0.0, 1.0]$ by mathematical formulation.

### 1.2 Composite Score Equation
The composite score is computed per trial and averaged across matched seeds:
$$\text{Composite Score} = 100.0 \times \left(0.30 \cdot S_{\text{comp}} + 0.25 \cdot S_{\text{thru}} + 0.20 \cdot S_{\text{turn}} + 0.15 \cdot S_{\text{thrash}} + 0.10 \cdot S_{\text{fair}}\right)$$

### 1.3 Historical Baseline Reference Scores (15 Seeds, 6 Workloads)
Under this formula, the historical Phase 3 baselines achieve:
- **Baseline F (Learning/RL)**: **82.14** (Rank 1)
- **Baseline C (Coordination without Conflict Prediction)**: **74.97** (Rank 2)
- **Baseline E (Complete CoReOS)**: **74.95** (Rank 3)
- **Baseline D (Conflict Prediction without Self-Healing)**: **74.68** (Rank 4)
- **Baseline A (Conventional Round Robin)**: **73.89** (Rank 5)
- **Baseline B (Independent Agents)**: **73.77** (Rank 6)

The competition goal is for an optimized CoReOS candidate to achieve **$\ge 82.50$**, surpassing or matching Baseline F and decisively outperforming Baselines A through E across all workloads.

---

## 2. Competition Guardrails

A candidate will be disqualified or rejected if it violates any of the following guardrails:
1. **Starvation & Deadlock Guardrail**: Jain's Fairness Index must not fall below 0.60 on any workload where processes remain runnable.
2. **Workload Robustness Guardrail**: Steady-state and mixed workloads must maintain 100.0% completion rate without regression in turnaround ($\le 16.0$ ticks).
3. **Thrashing Boundary Guardrail**: Memory thrashing ticks must not exceed 25.0 ticks on any non-adversarial workload and $\le 15.0$ ticks under adversarial stress.
4. **Decision Overhead Guardrail**: Decision overhead must remain strictly bounded ($\le 1.0$ ms per step) to ensure real-time feasibility.
5. **No Benchmark Hardcoding**: Schedulers must not inspect process count, seed values, or workload name strings. Adaptation must rely exclusively on dynamic system telemetry.

---

## 3. Seed Separation Protocol

To strictly prevent benchmark overfitting, evaluation is partitioned into four independent, non-overlapping seed cohorts:

| Cohort | Seed Range | Size | Purpose |
|---|---|---:|---|
| **Diagnostic Set** | Historical Seeds: `[42, 101, 202, 303, 404, 505, 606, 707, 808, 909, 1001, 1111, 1222, 1333, 1444]` | 15 | Root cause verification and diagnostic checks |
| **Tuning Set** | Seeds: `[2001..2015]` | 15 | Hyperparameter tuning and parameter search |
| **Validation / Ablation Set** | Seeds: `[2101..2115]` | 15 | Component ablation and candidate selection |
| **Held-Out Competition Set** | Seeds: `[3001..3030]` | 30 | Final held-out evaluation across all baselines |

**Rule**: Held-out seeds `[3001..3030]` will NOT be run or inspected until Phase 5.

---

## 4. Evaluation Workloads & Baselines

All evaluations encompass all 6 standard workloads:
1. `steady_state`: Normal baseline load
2. `cpu_spike`: High CPU burst demand exceeding core capacity
3. `memory_thrashing`: Severe RAM demand (overcommit)
4. `io_bottleneck`: High I/O frequency and queue congestion
5. `mixed`: Heterogeneous multi-modal demand
6. `adversarial_stress`: Compound CPU, memory, and I/O pressure

All evaluations compare:
- `A_Conventional`: Round Robin (quantum=4.0, FCFS disk)
- `B_IndependentAgents`: Uncoordinated CPU, Memory, IO agents
- `C_CoordNoConflict`: Coordination without conflict prediction
- `D_ConflictNoHealing`: Coordinated with ML conflict prediction, no healing
- `E_CompleteCoReOS`: Original complete CoReOS
- `F_LearningRL`: Tabular Q-learning agent
- `G_ChampionCoReOS`: New optimized CoReOS candidate
