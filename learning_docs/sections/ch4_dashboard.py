"""
Chapter 4: Detailed Analysis of Every Main Dashboard Section
"""

def get_chapter_4():
    return r'''
= Detailed Analysis of Every Main Dashboard Section

== 4.1 Overview Dashboard (`/`)

=== Purpose and High-Level Function
The *Overview* page serves as the executive cockpit of CoReOS. It synthesizes the operational health of the simulator, displays live telemetry from the most recent active simulation run, summarizes historical benchmark highlights across baselines, and outlines the system architecture pipeline.

#figure(
  image("screenshots/overview.png", width: 92%),
  caption: [CoReOS System Overview Dashboard showing active workload status, KPI cards, real-time resource utilization curves, and process queue dynamics.]
)

=== Section-by-Section Breakdown

*01 — System Overview Banner*:
- *Active Workload Pill*: Indicates which workload profile generated the current telemetry (e.g. `adversarial_stress`, `memory_thrashing`, `steady_state`). An active glowing pulse indicates an active in-memory run.
- *System Title & Core Subsystem Badges*: Highlights the three core tenets: *Conflict-aware scheduling*, *Resource coordination*, and *Self-healing*.

*02 — Current System Status & KPI Cards*:
- *Dataset Records (`10,000`)*: Confirms that the verified Kaggle IT performance dataset is loaded with 0 nulls and 0 duplicates.
- *Benchmark Baselines (`6`)*: Confirms that all six standardized architectural variants (A through F) are evaluated.
- *Decision Latency (`0.12 ms`)*: Measures the average CPU computation time required by the multi-agent coordination logic to arbitrate decisions during a simulation step.
- *Turnaround Improvement (`24.0% – 49.3%`)*: Displays the percentage reduction in average process turnaround time achieved by CoReOS compared to the conventional baseline under stress workloads.
- *Health Indicator Bar*: Displays live green/amber status indicators for Dataset Availability, Simulation Completion Status, and Unresolved Conflict Count.

*03 — System Performance Charts*:
- *Resource Utilization (Real-time)*: Plots three synchronous curves across 250 ticks: CPU Utilization (blue), Memory Utilization (cyan), and I/O Saturation (yellow).
- *Process Queue Length*: Plots the backlog dynamics across CPU Ready Queue (blue) and I/O Request Queue (cyan) over time.

*04 — Latest Benchmark Results Summary Table*:
- Displays stored multi-seed mean metrics across workloads and baselines: Completion Rate (%), Average Turnaround (ticks), Throughput (jobs/tick), and Thrashing (ticks).

*05 & 06 — Research Objective & System Architecture Pipeline*:
- Visualizes the 4-stage execution lifecycle: Data Plane → Agent Proposals → ML Arbitration → Self-Healing Recovery.

#info-box("What the User Should Learn from the Overview Page", [
  - Whether the system is healthy, loaded, and operating normally.
  - How severely resources were saturated during the latest simulation run.
  - The macroscopic performance delta between conventional scheduling and CoReOS.
])

#warning-box("What Conclusions Should NOT Be Drawn from Overview", [
  - *Do NOT assume the live utilization curves represent historical benchmarks*: The charts in Section 03 reflect *only the latest active simulation run*. The table in Section 04 reflects multi-seed benchmark averages.
  - *Do NOT interpret a high turnaround improvement as universal*: A 49% improvement occurs under high adversarial stress; under low steady-state loads, the improvement is modest (near parity), because uncoordinated schedulers do not trigger thrashing under light loads.
])

#pagebreak()

== 4.2 Agent Control Center (`/agents`)

=== Purpose and High-Level Function
The *Agent Control Center* provides a step-by-step audit trail into the autonomous decision-making process. It allows researchers and evaluators to peer inside the minds of the CPU, Memory, and I/O agents and verify exactly when and why the Coordination Agent arbitrated or overrode an agent's proposal.

#figure(
  image("screenshots/agents.png", width: 92%),
  caption: [Agent Control Center displaying the Proposed vs. Coordinated Quantum chart and the granular Decision Audit Log table.]
)

=== Section-by-Section Breakdown

*Proposed vs. Coordinated Quantum Chart*:
- *Proposed Quantum (Dotted Purple Curve)*: The time slice length (in milliseconds) dynamically proposed by the autonomous CPU Agent based purely on ready queue length.
- *Coordinated Quantum (Solid Emerald Green Curve)*: The actual time slice value approved and dispatched by the Coordination Agent after performing conflict prediction and Pareto safety arbitration.
- *Visual Interpretation*: Wherever the green line diverges upwards from the purple dotted line, the coordinator intervened to expand the quantum, actively suppressing thrashing and context-switch overhead.

*Decision Audit Log Table*:
The table logs every single coordination step with the following verified columns:
- *Step & Time*: The simulation step index and elapsed logical clock (in ticks).
- *CPU Proposed Q*: The time slice quantum requested by the CPU Agent (e.g. 2.0 ms).
- *Coordinated Q*: The final time slice approved by the coordinator (e.g. 8.0 ms).
- *Mem Target (MB)*: Target free physical RAM headroom enforced by the Memory Agent (e.g. 1024 MB).
- *I/O Policy*: The disk elevator algorithm selected (FCFS, SSTF, or SCAN).
- *Conflict Type*: Displays `None` under nominal conditions, or specific hazard tags such as `THRASHING_CPU_COLLAPSE` or `IO_SWAP_SATURATION`.
- *Arbitration Applied*: A green `Yes` checkmark if the coordinator altered parameters to protect system stability, or red `No` if proposals passed unaltered.
- *Explanation*: A human-readable scientific rationale justifying the decision (e.g. *"High memory pressure detected; quantum expanded to prevent page thrashing"*).

#info-box("Interpreting Conflict Outcomes", [
  When arbitration is marked `Yes`, the user is observing *proactive conflict prevention in action*. The CPU Agent was attempting to optimize ready queue latency, but the coordinator detected that doing so would trigger a fatal memory thrashing stall, safely overriding the parameter before execution.
])

#pagebreak()

== 4.3 Conflict Analysis & Diagnostics (`/conflicts`)

=== Purpose and High-Level Function
The *Conflict Analysis* section is the diagnostic heart of CoReOS. It exposes the frequency, severity, categories, and predictive accuracy of resource conflicts identified across simulation runs.

#figure(
  image("screenshots/conflicts.png", width: 92%),
  caption: [Conflict Analysis & Diagnostics featuring KPI cards, Conflict Type Distribution donut chart, temporal trend lines, and conflict taxonomy rules.]
)

=== Section-by-Section Breakdown

*4 Primary Metric Cards*:
- *Total Conflicts*: Total hazard events identified across the execution run (e.g. 18 events).
- *Conflict Rate*: The percentage of agent proposal cycles that resulted in a detected hazard.
- *Resolved by Self-Healing*: The count of severe conflicts mitigated via emergency closed-loop self-healing overrides.
- *Avg Resolution Time*: The average computational arbitration latency per conflict event (typically $< 0.1$ ms).

*Conflict Type Distribution (Donut Chart)*:
- Visualizes the proportion of conflicts across categories:
  - *CPU-Memory (`THRASHING_CPU_COLLAPSE`)*: Blue segment (~60% under stress).
  - *Memory-I/O (`IO_SWAP_SATURATION`)*: Cyan segment (~40% under stress).
  - *Triple Cascade / Cross-Resource*: Yellow and Rose segments.
- Center KPI annotation shows the exact total conflict count.

*Conflict Trend Over Time (Line Chart)*:
- Traces the temporal occurrence of conflicts across simulation ticks. Spikes indicate sudden bursts of resource pressure, while flatlines indicate stable execution.

*Recent Conflicts Audit Table*:
- Detailed event log recording: Conflict ID (`CONF-001`), Time, Participating Agents, Type, Resource Saturation, Severity (`High`, `Medium`, `Low`), Status (`Resolved`), and Resolution Link (`Coordinator Arbitration` or `Self-Healing`).

*Conflict Rule Taxonomy & Predictive Evaluation*:
- Displays empirical evaluation metrics for the Conflict Engine classifier:
  - *Precision*: 85.0% (proves that when a conflict is predicted, a real stall was imminent).
  - *Recall*: 88.0% (proves that the engine captures the vast majority of impending stalls).
  - *F1-Score*: 86.0% (harmonic mean of precision and recall).
  - *False Positive Rate*: 12.0% (acceptable false alarm rate preventing unnecessary overrides).
- *Taxonomy Rules Table*: Details interacting subsystems and underlying physical mechanisms.

#warning-box("Distinguishing Conflict Count from System Performance", [
  *A high conflict count does NOT mean the system is failing*. On the contrary: under an adversarial workload, a high conflict count coupled with 100% "Resolved" status indicates that the multi-agent operating system successfully *detected and neutralized* hazards that would have completely collapsed a conventional uncoordinated scheduler.
])

#pagebreak()

== 4.4 Dataset Explorer (`/dataset`)

=== Purpose and High-Level Function
The *Dataset Explorer* provides absolute empirical transparency. It proves that CoReOS is calibrated against real-world datacenter telemetry rather than fabricated numbers, and demonstrates the scientific separation between real empirical data and simulated process trajectories.

#figure(
  image("screenshots/dataset.png", width: 92%),
  caption: [Dataset Explorer showing the 12-feature empirical correlation heatmap and Kaggle dataset metadata cards.]
)

=== Section-by-Section Breakdown

*4 Dataset Integrity Cards*:
- *Total Rows (`10,000`)*: Confirmed verified observations from the Kaggle IT System Performance dataset.
- *Total Columns (`12`)*: Verified schema covering CPU, memory, disk, network, process counts, temperature, and status.
- *Duplicate Rows (`0`)*: Clean dataset with zero duplicates.
- *Status Anomalies (`97 / 0.97%`)*: Ground truth labeled operational system failure anomalies.

*Four Interactive Analysis Tabs*:

1. *Tab 1: Data Table & Schema*:
   - Displays the raw first 100 observations and comprehensive statistical descriptive summaries (count, mean, standard deviation, min, quartiles, max) across all 12 columns.
2. *Tab 2: Feature Distributions*:
   - Allows the user to select any feature (e.g. `cpu_utilization`, `memory_usage`, `disk_io`) and renders grouped histograms comparing normal operation (status 0) against anomaly states (status 1).
3. *Tab 3: Empirical Correlations (12-Feature Viridis Heatmap)*:
   - Displays the Pearson correlation matrix across all 12 features. Shows that `memory_usage` and `cpu_utilization` exhibit positive correlations with operational failure.
4. *Tab 4: Supervised Anomaly Baseline*:
   - An interactive machine learning lab. The user can click "Train Real Data Classifier" to train a Random Forest model on the real empirical status labels. The model achieves an *ROC-AUC of 1.0000* and *Anomaly F1 of 0.9730*, rendering a horizontal bar chart of feature importances that confirms memory and CPU saturation drive system failures.

#info-box("What Empirical Correlations Can and Cannot Prove", [
  - *What they prove*: High memory and CPU utilization frequently co-occur during datacenter operational failures.
  - *What they CANNOT prove*: Because lag-1 autocorrelation is near zero, rows represent independent snapshots from different servers, *not a continuous time series*. The dataset cannot prove per-process microsecond execution dynamics—which is precisely why a calibrated discrete-event simulation is required.
])

#pagebreak()

== 4.5 Simulation Lab & System Monitor (`/simulation`)

=== Purpose and High-Level Function
The *Simulation Lab* is the active operational testbed. It allows users to configure workload profiles, select target scheduling policies, launch real-time 250-tick simulation runs, and observe live subsystem utilization and queue dynamics.

#figure(
  image("screenshots/simulation.png", width: 92%),
  caption: [Simulation Lab with interactive parameter controls, performance metric KPI cards, and live system resource saturation curves.]
)

=== Configurable Simulation Settings
The user can modify the following parameters:
- *Workload Profile*:
  - `adversarial_stress`: Simultaneous CPU, memory, and I/O overload designed to induce cross-resource thrashing.
  - `steady_state`: Balanced job arrivals with nominal resource demands.
  - `cpu_spike`: Clusters of long-burst, compute-heavy tasks.
  - `memory_thrashing`: High working-set jobs (2–6 GB each) exceeding physical RAM capacity.
  - `io_bottleneck`: Frequent storage requests with long device service times.
  - `mixed`: Heterogeneous distribution of compute, memory, and disk tasks.
- *Target Policy / Baseline*:
  - `Complete CoReOS`: Full architecture with agents, conflict prediction, and self-healing.
  - `Conventional (Static RR)`: Static Round Robin (quantum=4.0 ms) + FCFS memory + FCFS I/O.
  - `Independent Agents`: Autonomous agents without coordination.
  - `Coordinated (No Conflict)`: Central coordinator without pre-execution conflict prediction.
- *Number of Processes*: Slider between 10 and 80 processes (default: 40).
- *Base CPU Quantum*: Slider between 1.0 ms and 16.0 ms (default: 4.0 ms).
- *Random Seed*: Integer setting for repeatable, deterministic random task generation.

=== Live Simulation Output Metrics
- *Turnaround Time*: Mean time from process arrival to completion (in ticks).
- *Waiting Time*: Mean cumulative time spent by processes waiting in the CPU ready queue.
- *Throughput*: Completed processes divided by elapsed simulation time (jobs/tick).
- *Context Switches*: Total processor core context switches executed during the run.
- *System Resource Usage Curves*: Synchronous live time-series tracking CPU, Memory, and I/O saturation.
- *Process Queue Dynamics*: Real-time tracking of CPU Ready Queue length and I/O Queue length.

#pagebreak()

== 4.6 Self-Healing Center (`/healing`)

=== Purpose and High-Level Function
The *Self-Healing Center* evaluates the closed-loop recovery mechanisms of CoReOS. It records when and how the system intervened autonomously to arrest performance regressions, restore degraded throughput, and eliminate policy flapping.

#figure(
  image("screenshots/healing.png", width: 92%),
  caption: [Self-Healing Center displaying autonomous recovery KPI cards, strategy usage distribution, and the recent interventions log.]
)

=== Section-by-Section Breakdown

*4 Primary Recovery Cards*:
- *Healing Actions*: Total autonomous corrective interventions triggered during the run.
- *Success Rate*: Percentage of regressions successfully stabilized within 30 ticks (verified 100% across test seeds).
- *Avg Healing Time*: Average duration (in simulation ticks) required to restore nominal metrics (averages 1.0 to 4.5 ticks).
- *Active Strategies*: Count of distinct recovery heuristics deployed by the engine.

*Self-Healing Strategy Usage (Donut Chart)*:
- Visualizes the breakdown of applied recovery interventions:
  - *Memory Reclaim & Quantum Expansion*: Deployed against `THRASHING_STALL` conditions.
  - *CPU Quantum Expansion*: Deployed against `THROUGHPUT_COLLAPSE` conditions.
  - *I/O Elevating SSTF*: Deployed against storage starvation deadlocks.

*Healing Success Rate Over Time (Line Chart)*:
- Plots the cumulative recovery success percentage (emerald green curve) against failed attempts (rose curve). Under nominal and calibrated stress runs, failed attempts remain flat at zero.

*Recent Self-Healing Actions Audit Table*:
- Detailed record of every intervention: ID (`HEAL-001`), Time, Issue Detected (`Thrashing Stall`, `Throughput Collapse`), Strategy, Target Subsystem, Result (`Success`), Latency, and Linked Conflict IDs (`CONF-003`).

*Subsystem Architecture Documentation*:
- Explains the two underlying modules:
  - *Performance Regression Detector*: Uses rolling statistical change-point analysis with a 3-step patience threshold to prevent false alarms.
  - *Pareto-Optimal Recovery Engine*: Applies targeted parameter overrides and enforces a mandatory 5-step cooling-off interval to eliminate policy flapping.

#pagebreak()

== 4.7 Benchmark Lab (`/benchmarks`)

=== Purpose and High-Level Function
The *Benchmark Lab* is the scientific comparison engine of CoReOS. It presents rigorous, reproducible evaluations comparing all six architectural baselines across workloads using standardized metrics and 95% confidence intervals.

#figure(
  image("screenshots/benchmarks.png", width: 92%),
  caption: [Benchmark Lab with interactive workload and metric selectors, color-coded baseline bar chart, and detailed comparative performance table.]
)

=== The Six Evaluated Baselines
- *Baseline A (Conventional)*: Static Round Robin (quantum=4.0 ms) + FCFS memory + FCFS I/O.
- *Baseline B (Independent Agents)*: Autonomous CPU, Memory, and I/O agents running without coordination.
- *Baseline C (Coord, No Conflict)*: Central coordinator without pre-execution conflict prediction checks.
- *Baseline D (Conflict, No Heal)*: Conflict-aware coordinator, but regression detection disabled.
- *Baseline E (Complete CoReOS)*: Full architecture combining multi-agent coordination, conflict prediction, and self-healing.
- *Baseline F (Learning RL)*: Q-learning multi-agent coordinator trained on dynamic simulation transitions.

=== Interactive Controls & Visualizations
- *Workload Selector*: Dropdown covering `adversarial_stress`, `steady_state`, `cpu_spike`, `memory_thrashing`, and `io_bottleneck`.
- *Metric Selector*: Dropdown toggling between:
  - *Average Turnaround Time* (ticks, lower is better)
  - *Throughput* (jobs/tick, higher is better)
  - *Completion Rate* (%, higher is better)
  - *Thrashing Ticks* (ticks, lower is better)
  - *Decision Overhead* (ms, lower is better)
- *Main Comparison Bar Chart*: Displays color-coded bars across Baselines A through F with exact values printed above each bar.
- *Detailed Baseline Comparison Table*: Tabulates all baselines side-by-side with automatic emerald green highlighting for the winning variant in each metric column.

#info-box("Interpreting Benchmark Results Fairly", [
  - *Complete CoReOS (Baseline E)* achieves its strongest advantage under high stress: a *65.0% turnaround reduction* under memory thrashing and a *36.7% improvement* under adversarial stress compared to Conventional.
  - *Learning RL (Baseline F)* achieves the absolute lowest turnaround under familiar regimes (58.89 ms vs 118.11 ms), but shows higher variance under radical out-of-distribution shifts.
  - *Under Steady State*, all baselines achieve 100% completion rate with turnaround times within 1-2 ticks of each other, confirming that advanced coordination adds no penalty when resources are unconstrained.
])

#pagebreak()

== 4.8 Research Reports & Exports (`/reports`)

=== Purpose and High-Level Function
The *Research Reports* page serves as the publication and archival portal. It provides access to full scientific papers, component ablation summaries, and downloadable datasets for academic reproduction.

#figure(
  image("screenshots/reports.png", width: 92%),
  caption: [Research Reports portal showing the Executive Summary tab, statistical ablation tables, and one-click data download buttons.]
)

=== Section-by-Section Breakdown

*Document Navigation Tabs*:
- *Executive Summary*: High-level core takeaways, research question evaluation framework (RQ1–RQ4), and empirical findings summary.
- *Detailed Analysis*: Renders the full `benchmark_analysis.md` research paper, providing deep theoretical justifications and experimental methodology.
- *Statistical Results*: Displays the *Component Ablation Summary Table*, showing exact performance changes when individual modules (conflict prediction, self-healing, ML models) are systematically disabled.
- *Discussion & Conclusions*: Renders the master `research_report.md` scientific manuscript, discussing threats to validity and architectural trade-offs.

*Download Cards & Artifact Exports*:
- *Full Research Report (PDF/MD)*: One-click export of the full paper.
- *Benchmark Results (CSV)*: Downloads `benchmark_results.csv` containing raw per-seed trial numbers.
- *Simulation Logs (ZIP)*: Downloads detailed telemetry traces.
- *Figures & Charts (ZIP)*: Downloads vector figures and paired comparison datasets (`paired_comparisons.csv`).

*Report Metadata Box*:
- Confirms the report timestamp (October 2026), document version (`v1.0`), evaluated workloads (6), and tested baselines (6).

#pagebreak()
'''
