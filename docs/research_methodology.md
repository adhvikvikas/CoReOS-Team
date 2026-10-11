# CoReOS Research Methodology & Evaluation Design

## 1. Research Questions & Hypotheses

CoReOS investigates five central research questions (RQs):

- **RQ1 (Interaction Features)**: *Can joint resource-interaction features improve the prediction of harmful performance outcomes compared to univariate thresholding?*
  - **Hypothesis**: Coupled features (e.g., high RAM pressure combined with low CPU quantum) predict thrashing collapses significantly better than independent CPU or RAM metrics alone.
- **RQ2 (Coordinated vs Independent Agents)**: *Does conflict-aware coordination outperform independent, uncoordinated resource agents?*
  - **Hypothesis**: Independent agents suffer from localized optimization traps (e.g. Memory Agent aggressively paging out while CPU Agent frequently preempts), causing systemic degradation that a coordinator can mitigate.
- **RQ3 (Self-Healing Efficacy)**: *Does closed-loop self-healing reduce the duration and severity of performance regressions without causing policy thrashing?*
  - **Hypothesis**: Threshold-triggered corrective actions with cooling-off periods restore healthy throughput faster than static or unmanaged policies.
- **RQ4 (Computational Overhead)**: *What is the computational overhead of the proposed multi-agent and conflict-prediction components?*
  - **Hypothesis**: Lightweight rule and tree-based inference introduces $<0.2$ ms of decision latency per tick, proving real-time feasibility.
- **RQ5 (Workload Generalization)**: *Does the architecture remain effective under workload regimes differing from its calibration data?*
  - **Hypothesis**: Rule-based safeguards and deterministic fallbacks maintain stability across out-of-distribution shifts where black-box learners may fail.

---

## 2. Real Dataset vs. Simulated Trajectories

| Dimension | Empirical Kaggle Observations | Discrete-Event OS Simulation |
| :--- | :--- | :--- |
| **Origin** | Kaggle [IT System Performance and Resource Metrics](https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics/data) (`Big_data_dataset.csv`) | Python discrete-event simulation engine |
| **Contents** | 10,000 system-level snapshots across 12 metrics (CPU, RAM, Disk I/O, Context Switches, Status) | Process arrival events, CPU bursts, page tables, swap accesses, I/O queues |
| **Temporal Nature** | Near-zero autocorrelation ($[-0.0135, 0.0274]$); independently sampled system states | Continuous simulated time clock advancing monotonically |
| **Role in CoReOS** | Empirical calibration (distribution shape, means, variances, correlations, anomaly baseline) | Action execution, conflict generation, regression observation, dynamic reward signals |

---

## 3. Standardized Baselines

All baselines are evaluated on identical workloads, resource limits, and random seeds:

- **Baseline A (Conventional)**: Static Round Robin CPU scheduling (quantum = 4.0), FCFS memory allocation (no dynamic reclamation), and FCFS disk queueing.
- **Baseline B (Independent Agents)**: Autonomous CPU, Memory, and I/O agents making uncoordinated decisions applied directly to the simulator.
- **Baseline C (Coordinated, No Conflict Prediction)**: Central coordinator arbitrates basic safety constraints, but disables pre-execution conflict prediction.
- **Baseline D (Conflict-Aware, No Self-Healing)**: Central coordinator uses rule + ML conflict prediction to arbitrate decisions, but regression detection and self-healing overrides are disabled.
- **Baseline E (Complete CoReOS)**: Full architecture combining multi-agent proposals, conflict prediction, safety constraints, regression detection, recovery overrides, and feedback tuning.
- **Baseline F (Learning-Based / RL)**: Tabular/discretized Q-Learning coordination trained exclusively on dynamic simulation transitions.

---

## 4. Evaluation Metrics & Statistical Rigor

1. **Turnaround Time ($T_{turn}$)**: $T_{completion} - T_{arrival}$ for completed processes (Mean and 95th-percentile).
2. **Waiting Time ($T_{wait}$)**: Cumulative time spent waiting in the ready queue.
3. **Throughput ($\Theta$)**: Completed processes per unit of simulation time.
4. **Jain's Fairness Index ($\mathcal{J}$)**:
   $$\mathcal{J}(x_1, x_2, \dots, x_n) = \frac{\left( \sum_{i=1}^n x_i \right)^2}{n \sum_{i=1}^n x_i^2}$$
5. **Conflict Prediction Precision, Recall, and F1**:
   $$\text{Precision} = \frac{TP}{TP + FP}, \quad \text{Recall} = \frac{TP}{TP + FN}, \quad F_1 = \frac{2 \cdot P \cdot R}{P + R}$$
6. **Recovery Success Rate & Delay**: Fraction of regressions restored to baseline within 30 ticks, and mean ticks elapsed during recovery.
7. **Decision Overhead**: Mean CPU execution latency of agent and coordination logic in milliseconds per step.
8. **Confidence Intervals**: 95% confidence interval half-width calculated via Student's $t$-distribution across independent random seeds.
