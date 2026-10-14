# CoReOS Research Paper — Comprehensive Verification & Audit Report

**Document Date:** October 2026  
**Target Repository:** `/Users/adhvikvikas/Documents/GitHub/CoReOS-Team`  
**Paper Output Directory:** `research_paper/`  
**Artifact Deliverables:** `main.tex`, `references.bib`, `figures/`, `scripts/`, `paper.pdf`, `paper.docx`, `Verification_Report.md`

---

## 1. Repository Components Inspected

A comprehensive, ground-truth inspection of the CoReOS codebase was executed across the following modules:

- **Core Simulation Subsystems:**
  - `src/coreos/simulation/environment.py`: Implements `CPUSubsystem` (4 cores, context-switch penalty $\delta_{cs}=0.5$, Round-Robin, SRTF, Priority, FCFS), `MemorySubsystem` (16,384\,MB physical RAM, 8,192\,MB swap, $\theta_{press}=0.85$, $\delta_{pf}=5.0$, thrashing threshold), `IOSubsystem` (2 channels, base latency $3.0$, queue capacity $50$, elevator SCAN, SSTF, FCFS), and master `SystemSimulator`.
  - `src/coreos/simulation/process.py`: Process state transitions across `PENDING`, `WAITING_MEMORY`, `READY`, `RUNNING`, `WAITING_IO`, and `TERMINATED`.
  - `src/coreos/simulation/metrics.py` \& `src/evaluation/metrics.py`: Metrics calculations for throughput, completed-job turnaround, penalized turnaround ($T_{pen}$ with 300-tick cutoff penalty), thrashing ticks, and Jain's Fairness Index.
- **Agent and Coordination Architecture:**
  - `src/coreos/agents/cpu_agent.py`, `memory_agent.py`, `io_agent.py`: Specialized localized proposal agents.
  - `src/coreos/coordination/coordinator.py` \& `constraints.py`: Base coordination and safety constraints.
  - `src/coreos/optimization/candidates.py`: Candidate architectures A through F, including `WorkloadAwareCPUAgent`, `WorkloadAwareIOAgent`, `AdaptiveCoordinationAgent`, `CalibratedConflictEngine`, and `ChampionCoReOS` (the official CoReOS implementation, internally identified as `G_ChampionCoReOS`).
- **Conflict Prediction and Self-Healing:**
  - `src/coreos/conflict_prediction/predictor.py`: Rule-based and GradientBoosting ML conflict detection.
  - `src/coreos/self_healing/regression_detector.py`: Sliding-window anomaly detector (`THRASHING_STALL`, `THROUGHPUT_COLLAPSE`, `LATENCY_SPIKE`).
  - `src/coreos/self_healing/recovery.py`: `RecoveryEngine`, `ProportionalRecoveryEngine`, and `FeedbackMechanism`.
- **Adaptive Reinforcement Learning:**
  - `src/coreos/learning/adaptive_rl.py`: `AdaptiveCoReOSGymEnv`, 54-state physical discretization, multi-workload curriculum trainer, tabular Q-learning, and Manhattan nearest-neighbor generalization.
- **Evaluation and Reproducibility:**
  - `scripts/run_final_canonical_benchmark.py`: Benchmark runner evaluating 1,440 matched trials on held-out seeds [5001..5030].
  - `scripts/run_candidate_experiments.py` \& `run_ablation_experiments.py`: Controlled candidate and ablation runners.
- **Canonical Reports and Data Artifacts:**
  - `reports/optimization/final_canonical_benchmark_results.csv`: Authoritative trial dataset (1,440 rows).
  - `reports/optimization/final_canonical_per_workload_summary.csv`: Per-workload aggregates across 6 workloads.
  - `reports/optimization/final_canonical_ranking_summary.csv`: Overall candidate leaderboard.
  - `reports/optimization/final_canonical_guardrail_compliance.csv`: Granular guardrail compliance records.
  - `reports/optimization/final_canonical_statistical_comparisons.csv`: Paired parametric hypothesis testing.
- **Full-Stack Application:**
  - FastAPI backend (`backend/main.py`, `backend/api/benchmarks.py`, `overview.py`, `simulation.py`, `conflicts.py`, `healing.py`).
  - React/TypeScript frontend (`frontend/src/pages/BenchmarkLab.tsx`, `SimulationLab.tsx`, `ConflictAnalysis.tsx`, `SelfHealing.tsx`, `Overview.tsx`).

---

## 2. Actual Implemented Algorithms and Source Locations

| Algorithm | Role in CoReOS | Primary Source Location |
| :--- | :--- | :--- |
| **CoReOS Discrete-Event Simulation Loop** | Master orchestration clock, queue stepping, context-switch accounting, and paging simulation | `src/coreos/simulation/environment.py:301-514` |
| **Workload-Aware Progress Scheduling** | SRTF ($q=8.0$) queue drain under compute backlog; pure I/O disentanglement | `src/coreos/optimization/candidates.py:242-292` |
| **Elevator SCAN I/O Dispatch** | Elimination of cylinder seek starvation and head clustering for queues $\ge 2$ | `src/coreos/optimization/candidates.py:294-327` |
| **Adaptive Cross-Resource Arbitration** | I/O Congestion Shield, Memory-CPU Coupling ($q \ge 8.0, R \ge 2048$), SRTF preservation | `src/coreos/optimization/candidates.py:29-163` |
| **Calibrated Conflict Prediction** | Rule-based cascade identification (`TRIPLE_CASCADE`, etc.) and GradientBoosting classifier | `src/coreos/optimization/candidates.py:335-473` |
| **Graduated Proportional Self-Healing** | Moving-average regression detection and graduated, non-oscillating recovery overrides | `src/coreos/optimization/candidates.py:171-234` |
| **Closed-Loop Feedback Mechanism** | Dynamic adjustment of conflict prediction confidence based on regression outcomes | `src/coreos/self_healing/recovery.py:115-165` |
| **Curriculum Adaptive Q-Learning** | 54-state physical discretization, curriculum training across 6 workloads, Manhattan NN fallback | `src/coreos/learning/adaptive_rl.py:35-265` |
| **Penalized Turnaround Calculation** | Cutoff penalty integration ($\Pi=300$) to eliminate survivorship bias | `src/coreos/simulation/metrics.py:44-77` |
| **Jain's Fairness Index** | Axiomatic fairness evaluation bounded in $[1/n, 1.0]$ | `src/coreos/simulation/metrics.py:12-25` |

---

## 3. Canonical Data Files and Verification

The canonical benchmark dataset was verified directly against the underlying CSV files:

- **Canonical Raw Dataset:** `reports/optimization/final_canonical_benchmark_results.csv`
  - Total records: **1,440 trials**
  - Scope: 8 candidates $\times$ 6 workloads $\times$ 30 held-out pseudo-random seeds ($5001$ to $5030$).
  - Active comparison candidate count: **7 candidates** (1,260 trials, excluding historical `E_CompleteCoReOS`).
  - Columns: `candidate`, `workload`, `seed`, `composite_score`, `completion_rate`, `completed_processes`, `unfinished_processes`, `throughput`, `penalized_turnaround`, `avg_turnaround_time`, `thrashing_ticks`, `jains_fairness`, `decision_overhead_ms`, `total_recoveries`, `recovery_success_rate`, `guardrail_compliant`, `guardrail_violations`.
- **Per-Workload Summary:** `reports/optimization/final_canonical_per_workload_summary.csv` (48 rows, 8 candidates $\times$ 6 workloads).
- **Ranking Summary:** `reports/optimization/final_canonical_ranking_summary.csv` (8 rows).
- **Guardrail Compliance Table:** `reports/optimization/final_canonical_guardrail_compliance.csv` (48 rows).

---

## 4. Verified Candidate Rankings and Metrics

All numerical claims reported in the paper have been independently recalculated from the raw trial records and cross-referenced against the canonical summaries down to $10^{-4}$ precision:

| Candidate | Composite Score (Mean $\pm$ 95\% CI) | Completion Rate | Penalized Turnaround | Throughput | Thrashing Ticks | Jain Fairness | Decision Overhead |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **F\_ImprovedRL** | $85.81 \pm 1.53$ (std $10.40$) | $95.28\%$ | $39.84$ ticks | $0.1834$ | $0.01$ ticks | $0.6510$ | $0.0030$ ms |
| **CoReOS (G\_ChampionCoReOS)** | $\mathbf{84.87 \pm 1.35}$ (std $\mathbf{9.15}$) | $\mathbf{95.86\%}$ | $\mathbf{40.79}$ ticks | $\mathbf{0.1771}$ | $\mathbf{0.02}$ ticks | $\mathbf{0.5934}$ | $\mathbf{0.1517}$ ms |
| **H\_OriginalRL** | $82.17 \pm 2.29$ (std $15.55$) | $90.76\%$ | $58.36$ ticks | $0.1743$ | $0.06$ ticks | $0.6329$ | $0.0316$ ms |
| **D\_ConflictNoHealing** | $75.47 \pm 3.06$ (std $20.80$) | $81.35\%$ | $82.40$ ticks | $0.1549$ | $4.32$ ticks | $0.6321$ | $0.1346$ ms |
| **E\_CompleteCoReOS** (Hist.) | $75.46 \pm 3.07$ (std $20.87$) | $81.32\%$ | $82.23$ ticks | $0.1549$ | $4.08$ ticks | $0.6288$ | $0.1497$ ms |
| **C\_CoordNoConflict** | $75.18 \pm 3.13$ (std $21.26$) | $81.76\%$ | $81.78$ ticks | $0.1554$ | $9.67$ ticks | $0.6346$ | $0.0051$ ms |
| **A\_Conventional** | $74.29 \pm 3.45$ (std $23.44$) | $81.35\%$ | $81.73$ ticks | $0.1573$ | $19.81$ ticks | $0.6393$ | $0.0341$ ms |
| **B\_IndependentAgents** | $74.29 \pm 3.30$ (std $22.46$) | $79.46\%$ | $86.46$ ticks | $0.1521$ | $4.61$ ticks | $0.6288$ | $0.0020$ ms |

### Key Audit Findings
1. **Rankings:** `F_ImprovedRL` ranks \#1 ($85.81$) and `G_ChampionCoReOS` ranks \#2 ($84.87$). CoReOS does not rank \#1 on the aggregate score, but achieves the highest completion rate ($95.86\%$), the lowest standard deviation ($9.15$), and dominates `cpu_spike` ($68.13$ vs. $64.87$).
2. **Statistical Significance:** CoReOS beats Conventional by $+10.58$ points ($t=8.589, p=4.20 \times 10^{-15}$, Cohen's $d=0.640$) and Complete CoReOS by $+9.41$ points ($t=9.452, p=1.87 \times 10^{-17}$, $d=0.704$).
3. **Overhead Compliance:** CoReOS satisfies the $\le 1.0$\,ms overhead guardrail in $100\%$ of trials ($180/180$), averaging $0.1517$\,ms ($85\%$ safety margin).
4. **Fairness Weakness:** CoReOS achieves an overall guardrail compliance rate of $58.9\%$ due to fairness failures on `io_bottleneck` ($0.3934$) and `mixed` ($0.5045$). This is transparently reported without obfuscation.

---

## 5. Figure and Table Inventory

### Figures
1. **Fig. 1 (`fig1_architecture.pdf`/`.png`):** CoReOS system architecture diagram showing discrete-event engine, domain agents, adaptive coordinator, conflict predictor, and proportional recovery engine. (Source: architectural implementation in `src/coreos/`).
2. **Fig. 2 (`fig2_workflow.pdf`/`.png`):** End-to-end discrete-event execution and arbitration workflow diagram. (Source: discrete step lifecycle in `src/coreos/simulation/environment.py`).
3. **Fig. 3 (`fig3_rank_composite.pdf`/`.png`):** Overall candidate ranking bar chart with 95\% CI error bars. (Source: `final_canonical_ranking_summary.csv`).
4. **Fig. 4 (`fig4_per_workload_composite.pdf`/`.png`):** Grouped bar chart of composite scores across all 6 workloads. (Source: `final_canonical_per_workload_summary.csv`).
5. **Fig. 5 (`fig5_completion_rate.pdf`/`.png`):** Task completion rate comparison across workloads. (Source: `final_canonical_per_workload_summary.csv`).
6. **Fig. 6 (`fig6_turnaround_comparison.pdf`/`.png`):** Penalized turnaround vs completed-job turnaround under adversarial stress. (Source: raw trial calculations in `final_canonical_benchmark_results.csv`).
7. **Fig. 7 (`fig7_throughput.pdf`/`.png`):** Throughput across workloads and candidates. (Source: `final_canonical_per_workload_summary.csv`).
8. **Fig. 8 (`fig8_thrashing.pdf`/`.png`):** Thrashing ticks comparison across workloads. (Source: `final_canonical_per_workload_summary.csv`).
9. **Fig. 9 (`fig9_fairness.pdf`/`.png`):** Jain's Fairness Index across workloads with $0.60$ floor reference line. (Source: `final_canonical_per_workload_summary.csv`).
10. **Fig. 10 (`fig10_decision_overhead.pdf`/`.png`):** Decision overhead per step vs. $1.0$\,ms guardrail ceiling. (Source: `final_canonical_ranking_summary.csv`).
11. **Fig. 11 (`fig11_guardrail_breakdown.pdf`/`.png`):** Granular guardrail compliance breakdown across Overhead, Thrashing, Robustness, and Fairness criteria. (Source: `final_canonical_guardrail_compliance.csv`).
12. **Fig. 12 (`fig12_workload_heatmap.pdf`/`.png`):** 2D performance heatmap across candidates and workloads. (Source: `final_canonical_per_workload_summary.csv`).
13. **Fig. 13 (`fig13_radar_comparison.pdf`/`.png`):** Multi-criteria radar chart across normalized dimensions. (Source: normalized canonical summary values).
14. **Fig. 14 (`screenshot_benchmarks.png`):** Application Benchmark Lab interface showing live leaderboard and Plotly charts. (Source: `learning_docs/screenshots/benchmarks.png`).
15. **Fig. 15 (`screenshot_simulation.png`):** Application Simulation Lab interface showing real-time resource gauges. (Source: `learning_docs/screenshots/simulation.png`).
16. **Fig. 16 (`screenshot_conflicts.png`):** Application Conflict Analysis interface showing detected hazards and feature inputs. (Source: `learning_docs/screenshots/conflicts.png`).
17. **Fig. 17 (`screenshot_healing.png`):** Application Self-Healing Center interface showing regression telemetry. (Source: `learning_docs/screenshots/healing.png`).

### Tables
1. **Table I:** Taxonomic comparison of related resource-management systems and positioning of CoReOS.
2. **Table II:** Discrete-event simulation parameters (cores, memory, swap, channels, penalties).
3. **Table III:** Evaluated candidate architectures and baseline descriptions.
4. **Table IV:** Overall benchmark leaderboard across 1,440 matched trials.
5. **Table V:** Pairwise statistical hypothesis testing (t-stats, p-values, Holm-Bonferroni, Cohen's d).
6. **Table VI:** Detailed per-workload performance matrix across candidates and workloads.
7. **Table VII (Appendix):** Mathematical notational glossary.
8. **Table VIII (Appendix):** Extended statistical quantiles for CoReOS across seeds.

---

## 6. References Verification Audit

All 36 references in `references.bib` have been verified for publication venue, authorship, publication year, and digital object identifier (DOI) or stable archival URL:

1. `jain1984quantitative`: Digital Equipment Corporation TR-301 (1984), arXiv:cs/9809099. [Verified]
2. `jain1991art`: John Wiley \& Sons (1991), ISBN 0-471-50336-3. [Verified]
3. `delimitrou2013paragon`: ASPLOS 2013, DOI: `10.1145/2451116.2451125`. [Verified]
4. `delimitrou2014quasar`: ASPLOS 2014, DOI: `10.1145/2541940.2541941`. [Verified]
5. `lo2015heracles`: ISCA 2015, DOI: `10.1145/2749469.2749475`. [Verified]
6. `mars2011bubble`: MICRO 2011, DOI: `10.1145/2155620.2155650`. [Verified]
7. `tang2011compiling`: ISCA 2011, DOI: `10.1145/2000064.2000098`. [Verified]
8. `kephart2003vision`: IEEE Computer, Vol. 36, No. 1, 2003, DOI: `10.1109/MC.2003.1160055`. [Verified]
9. `candea2004microreboot`: OSDI 2004, USENIX. [Verified]
10. `qin2005rx`: SOSP 2005, DOI: `10.1145/1095810.1095833`. [Verified]
11. `kramer2007self`: IEEE FOSE 2007, DOI: `10.1109/FOSE.2007.19`. [Verified]
12. `salehie2009self`: ACM TAAS, Vol. 4, No. 2, 2009, DOI: `10.1145/1516533.1516538`. [Verified]
13. `waldspurger1994lottery`: OSDI 1994, USENIX. [Verified]
14. `watkins1992q`: Machine Learning, Vol. 8, 1992, DOI: `10.1007/BF00992698`. [Verified]
15. `sutton2018reinforcement`: MIT Press, 2nd Edition, 2018. [Verified]
16. `mao2016resource`: ACM HotNets 2016, DOI: `10.1145/3005745.3005750`. [Verified]
17. `mao2019learning`: ACM SIGCOMM 2019, DOI: `10.1145/3341302.3342080`. [Verified]
18. `wooldridge2009introduction`: John Wiley \& Sons, 2nd Edition, 2009. [Verified]
19. `stone2000multiagent`: Autonomous Robots, Vol. 8, No. 3, 2000, DOI: `10.1023/A:1008942012299`. [Verified]
20. `panait2005cooperative`: Autonomous Agents and Multi-Agent Systems, 2005, DOI: `10.1007/s10458-005-2631-2`. [Verified]
21. `shoham2008multiagent`: Cambridge University Press, 2008. [Verified]
22. `zhang2021multi`: Springer Handbook of RL and Control, 2021, DOI: `10.1007/978-3-030-60990-0_12`. [Verified]
23. `law2015simulation`: McGraw-Hill Education, 5th Edition, 2015. [Verified]
24. `banks2010discrete`: Pearson, 5th Edition, 2010. [Verified]
25. `silberschatz2018operating`: Operating System Concepts, 10th Edition, Wiley, 2018. [Verified]
26. `tanenbaum2015modern`: Modern Operating Systems, 4th Edition, Pearson, 2015. [Verified]
27. `arpacidusseau2018operating`: Operating Systems: Three Easy Pieces, Version 1.00, 2018. [Verified]
28. `deb2001multi`: Multi-Objective Optimization Using Evolutionary Algorithms, Wiley, 2001. [Verified]
29. `marler2004survey`: Structural and Multidisciplinary Optimization, 2004, DOI: `10.1007/s00158-003-0368-6`. [Verified]
30. `lan2010axiomatic`: IEEE INFOCOM 2010, DOI: `10.1109/INFCOM.2010.5461957`. [Verified]
31. `mei2024aios`: COLM 2024 / arXiv:2403.16971. [Verified]
32. `wu2023autogen`: arXiv:2308.08155, 2023. [Verified]
33. `sun2024cooperative`: IEEE ICPADS 2024, DOI: `10.1109/ICPADS63028.2024.00140`. [Verified]
34. `agentrm2026`: arXiv:2602.04189, 2026. [Verified]
35. `kasture2014ubik`: ASPLOS 2014, DOI: `10.1145/2541940.2541968`. [Verified]
36. `cohen1988statistical`: Statistical Power Analysis for the Behavioral Sciences, 1988. [Verified]

*Zero references were marked `[VERIFY]` or omitted; all citations are verified authentic entries.*

---

## 7. Data Discrepancy & Ambiguity Disclosures

1. **Reconciliation of Legacy Documentation Screenshot:**
   - As audited in Phase 10, the static image `learning_docs/screenshots/benchmarks.png` originated from an exploratory Phase 1 test run (`reports/benchmark_results.csv`, 6 candidates, 3 seeds) that exhibited an early formatting artifact (completion rate displayed as $4666.7\%$).
   - The active canonical dataset (`final_canonical_benchmark_results.csv`) reflects the authoritative 1,440-trial evaluation. The paper exclusively reports and plots values from the canonical dataset.
2. **Workload-Dependent Throughput vs. Aggregate Throughput:**
   - In Benchmark Lab, the Detailed Table filters metrics by individual workload (e.g., CoReOS throughput on `adversarial_stress` is $0.1297$), whereas the Leaderboard displays the mean across all six workloads ($0.1771$). The paper clearly differentiates between per-workload and cross-workload aggregations in all text and tables.
3. **Survivor Bias in Fairness Index:**
   - Schedulers that starve tasks (e.g., Conventional starving $52.5\%$ on `cpu_spike`) artificially receive high unpenalized fairness scores ($0.8230$) because unfinished tasks are excluded from the calculation. The paper explains this phenomenon in Section VI-D and contrasts it with penalized turnaround.

---

## 8. LaTeX Compilation and Deliverables Audit

- **Compilation Tool:** `Tectonic 0.17.0` (XeTeX engine).
- **Target Source:** `research_paper/main.tex`
- **Bibliography:** `research_paper/references.bib`
- **Class File:** `research_paper/IEEEtran.cls` (official IEEE conference class, 2015/08/26 V1.8b).
- **BibTeX Style:** `research_paper/IEEEtran.bst` (Version 1.14).
- **Compilation Status:** **SUCCESS (Exit Code 0)**.
- **Output File:** `research_paper/paper.pdf` (and `main.pdf`, 964\,KB).
- **Compiled Page Count:** **21 pages** (within the requested 20–25 page range).
- **Editable Word Deliverable:** `research_paper/paper.docx` (789\,KB, generated via pandoc).
- **Automated Test Suite Status:** `pytest` passed **108/108 tests** in 6.53s.
- **Frontend Build Status:** `npm run build` (`tsc -b && vite build`) passed with **0 errors**.

---

## 9. Reproduction Instructions

To regenerate all experimental figures, run the automated test suite, and recompile the research paper:

```bash
# 1. Activate virtual environment
source .venv/bin/activate

# 2. Run backend regression and optimization tests (108 passed)
pytest

# 3. Regenerate all 13 analytical publication figures
python research_paper/scripts/generate_figures.py

# 4. Compile LaTeX paper to PDF via tectonic
cd research_paper && tectonic main.tex && cp main.pdf paper.pdf
```
