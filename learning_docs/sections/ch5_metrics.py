"""
Chapter 5: Comprehensive Reference of System Outputs and Metrics
"""

def get_chapter_5():
    return r'''
= Comprehensive Reference of System Outputs and Metrics

This chapter provides a definitive reference manual for every significant metric, status, indicator, and telemetry output displayed across the CoReOS dashboard.

== Detailed Metric Profiles

=== 1. Average Turnaround Time ($T_"turn"$)
- *What it is*: The mean duration that processes spend in the operating system from initial submission to final termination.
- *What it measures*: System-wide latency and execution efficiency under a given scheduling policy.
- *How to interpret it*: Lower values indicate superior scheduling efficiency. A sharp increase indicates severe queuing delays, context-switch thrashing, or swap bottlenecks.
- *Why it matters*: Turnaround time is the primary benchmark metric in CoReOS; reducing turnaround time under adversarial stress proves the efficacy of multi-agent coordination.
- *Limitations*: It does not measure user-perceived interactive response time for real-time tasks; a low average turnaround can mask significant starvation for an isolated long-running process unless paired with fairness metrics.

=== 2. Average Waiting Time ($T_"wait"$)
- *What it is*: The average cumulative time units that processes spend waiting in the CPU ready queue before acquiring a core.
- *What it measures*: Processor scheduling friction and queue backlog.
- *How to interpret it*: Lower values indicate that processes transition rapidly from ready to running. High values signify insufficient CPU capacity or excessive quantum times that monopolize cores.
- *Why it matters*: Validates whether expanding time quanta to suppress thrashing creates unacceptable ready queue starvation for competing tasks.
- *Limitations*: Does not include time spent blocked waiting for memory pages or storage I/O transfers.

=== 3. System Throughput ($Theta$)
- *What it is*: The total number of completed processes divided by the total elapsed simulation time (jobs per tick).
- *What it measures*: The macroscopic completion velocity of the entire operating system.
- *How to interpret it*: Higher values indicate greater productivity. A sudden collapse towards zero signifies live-lock, dead-lock, or severe memory thrashing.
- *Why it matters*: Used directly by the `PerformanceRegressionDetector` to trigger emergency closed-loop self-healing overrides.
- *Limitations*: Throughput treats all processes equally; completing 10 tiny synthetic tasks yields the same throughput as completing 10 massive data-processing jobs.

=== 4. Process Completion Rate (%)
- *What it is*: The percentage of submitted processes that successfully completed execution before the simulation horizon (250 ticks).
- *What it measures*: System survivability and job completion integrity under heavy load.
- *How to interpret it*: Nominal workloads achieve 100.0%. Under severe adversarial stress, uncoordinated baselines drop to 25.0%–46.7%, whereas CoReOS maintains high completion rates.
- *Why it matters*: Directly proves whether a scheduling algorithm can complete tasks or whether it leaves processes abandoned in perpetual thrashing states.
- *Limitations*: Does not reflect the speed of completion; two systems can both achieve 100% completion while one took three times longer to finish.

=== 5. Completed vs. Unfinished Processes
- *What it is*: The exact count of processes that terminated normally versus those still trapped in ready, blocked, or waiting queues when time expired.
- *What it measures*: Absolute task accounting for scientific transparency.
- *How to interpret it*: Unfinished process counts $> 0$ indicate that the workload overwhelmed system capacity within the evaluated window.
- *Why it matters*: Essential for scientific integrity; reporting turnaround time only for completed processes creates survivorship bias unless unfinished tasks are tracked.
- *Limitations*: Does not describe how close unfinished jobs were to completion (e.g. 99% done vs. 1% done).

=== 6. Context Switches Count
- *What it is*: The cumulative number of times CPU cores saved the state of one process and loaded another.
- *What it measures*: Processor scheduling churn and dispatch frequency.
- *How to interpret it*: Excessively high context switches under memory pressure accelerate page thrashing. Moderate context switches provide fair interactive responsiveness.
- *Why it matters*: The CPU Agent dynamically adjusts time quanta specifically to control and balance this metric.
- *Limitations*: A low context switch count does not guarantee efficiency if a single monopolizing process is blocking other urgent jobs.

=== 7. Thrashing Ticks
- *What it is*: The cumulative simulation ticks during which physical RAM was saturated and CPU cores were trapped waiting for memory-disk swap operations.
- *What it measures*: Subsystem paralysis caused by cross-resource memory-CPU interference.
- *How to interpret it*: Zero thrashing ticks indicates healthy execution. High values (e.g. 85 to 121 ticks) indicate catastrophic failure where the machine wasted significant cycles swapping pages.
- *Why it matters*: Proves the core hypothesis: Complete CoReOS reduces thrashing ticks from 121.0 down to near zero under heavy memory pressure.
- *Limitations*: Does not differentiate between read-heavy paging vs. write-heavy swap flushes.

=== 8. Decision Latency / Overhead (ms)
- *What it is*: The wall-clock execution time (in milliseconds) consumed by the multi-agent coordination logic per simulation step.
- *What it measures*: The computational cost of running AI agents, conflict prediction models, and arbitration rules.
- *How to interpret it*: Values below 0.10 ms (100 microseconds) prove real-time operating system feasibility. Values exceeding 1.0 ms would make real-time OS deployment impractical.
- *Why it matters*: Answers Research Question 4 (computational overhead), confirming CoReOS adds negligible overhead (0.085–0.092 ms).
- *Limitations*: Measured in user-space Python on standard multi-core hardware; production kernel C/eBPF implementations would execute even faster.

=== 9. Turnaround Improvement (%)
- *What it is*: The percentage reduction in average turnaround time achieved by CoReOS compared to the Conventional baseline: $((T_"conv" - T_"core") / T_"conv" times 100)$.
- *What it measures*: Relative performance advantage over traditional static scheduling.
- *How to interpret it*: Positive values indicate superiority. Higher percentages (e.g. 24.0% to 49.3%) demonstrate strong resilience under stress.
- *Why it matters*: Synthesizes project success into an easily communicable executive metric.
- *Limitations*: Percentage improvement is highly workload-dependent; under steady state with zero contention, improvement is close to 0%.

=== 10. Total Conflicts & Conflict Rate (%)
- *What it is*: The absolute count and percentage of coordination cycles where proposed agent actions triggered a pre-execution hazard classification.
- *What it measures*: Cross-subsystem contention frequency.
- *How to interpret it*: A high conflict rate indicates severe resource competition. If paired with high completion rates, it indicates successful predictive mediation.
- *Why it matters*: Quantifies how frequently agents disagree or make proposals that would harm shared headroom.
- *Limitations*: A high conflict count does not prove system failure; it proves the detector is actively identifying contention.

=== 11. Conflicts Resolved by Self-Healing
- *What it is*: The count of detected conflicts that were subsequently stabilized via closed-loop emergency self-healing overrides.
- *What it measures*: The degree of cooperation between predictive arbitration and emergency recovery.
- *How to interpret it*: High numbers indicate that pre-execution arbitration alone was insufficient to prevent degradation, requiring closed-loop overrides.
- *Why it matters*: Demonstrates the complementary necessity of self-healing alongside prediction.
- *Limitations*: Does not indicate the severity of the initial stall.

=== 12. Conflict Resolution Latency (ms)
- *What it is*: Time required by the Pareto arbitration algorithm to evaluate and override conflicting proposal tuples.
- *What it measures*: Coordination agility.
- *How to interpret it*: Lower values ensure minimal delay between agent proposals and core execution dispatch.
- *Why it matters*: Confirms arbitration does not introduce scheduling jitter.
- *Limitations*: Does not include communication serialization overhead in distributed systems.

=== 13. Conflict Prediction Precision, Recall & F1-Score
- *What it is*: Standard statistical classification metrics evaluating the accuracy of the Conflict Engine against ground-truth system stall events.
  - *Precision (85.0%)*: Proportion of predicted conflicts that truly represented impending stalls.
  - *Recall (88.0%)*: Proportion of actual system stalls that were successfully predicted in advance.
  - *F1-Score (86.0%)*: Harmonic mean balancing precision and recall.
  - *False Positive Rate (12.0%)*: Frequency of false alarms that triggered unnecessary arbitration.
- *What it measures*: The mathematical validity of the machine learning and rule-based conflict prediction engine.
- *How to interpret it*: High precision and recall confirm that the engine is neither blind to real hazards nor constantly triggering false alarms.
- *Why it matters*: Validates Research Question 1 (predictive efficacy).
- *Limitations*: Evaluated against discrete-event simulation hazard definitions; real physical systems contain additional microarchitectural noise.

=== 14. Healing Actions / Total Recoveries
- *What it is*: The count of autonomous corrective overrides executed by the `RecoveryEngine`.
- *What it measures*: The invocation frequency of the closed-loop recovery mechanism.
- *How to interpret it*: Zero in nominal workloads; positive integers (e.g. 2 to 5) during severe adversarial stress.
- *Why it matters*: Proves that the self-healing subsystem remains dormant until genuine regressions occur.
- *Limitations*: Does not measure the magnitude of the override applied.

=== 15. Self-Healing Success Rate (%)
- *What it is*: The percentage of regression events where system throughput was restored to baseline within 30 simulation ticks.
- *What it measures*: Recovery effectiveness and policy stability.
- *How to interpret it*: Verified at 100.0% across test seeds, confirming that recovery overrides reliably break resource deadlocks.
- *Why it matters*: Answers Research Question 3, proving self-healing reliability.
- *Limitations*: Measured within the simulator's 30-tick evaluation horizon.

=== 16. Average Healing Time (ticks)
- *What it is*: The mean duration (in simulation ticks) from regression detection to verified throughput restoration.
- *What it measures*: Recovery agility.
- *How to interpret it*: Lower values (e.g. 1.0 to 4.5 ticks) indicate swift stabilization.
- *Why it matters*: Proves that regressions are arrested before causing cumulative application timeouts.
- *Limitations*: In a tick-based discrete simulator, one tick represents one scheduling quantum epoch.

=== 17. Active Healing Strategies Count
- *What it is*: The number of distinct recovery heuristics currently configured and active in the system (e.g. 5 registered strategies).
- *What it measures*: Diversity of available corrective actions.
- *How to interpret it*: Indicates that the system possesses multiple specialized responses rather than a crude one-size-fits-all restart.
- *Why it matters*: Different failure modes require different interventions (e.g. expanding quantum vs. elevating I/O).
- *Limitations*: Having many strategies is only valuable if the change-point detector accurately pairs each failure mode with the correct strategy.

=== 18. Jain's Fairness Index ($cal(J)$)
- *What it is*: A mathematical index in [0.0, 1.0] measuring the equality of service allocation across all processes ($cal(J) = (sum T_i)^2 / [N sum T_i^2]$).
- *What it measures*: Starvation prevention and egalitarian service distribution.
- *How to interpret it*: A value of 1.0 indicates perfect equality. Values below 0.70 indicate that some processes are being severely starved to boost overall averages.
- *Why it matters*: Ensures that CoReOS does not achieve low turnaround times by unfairly abandoning slow jobs. Verified at > 0.84 under stress.
- *Limitations*: Strict mathematical fairness can sometimes conflict with maximizing overall system throughput.

=== 19. CPU Utilization (%)
- *What it is*: The percentage of time processor cores spent actively executing process instructions versus idling or waiting.
- *What it measures*: Core saturation.
- *How to interpret it*: High utilization is desirable *only if* cores are doing useful compute. 100% utilization during thrashing represents wasted swap wait cycles.
- *Why it matters*: Helps distinguish healthy compute saturation from pathological thrashing stalls.
- *Limitations*: Does not distinguish between user-space application execution and kernel coordination overhead.

=== 20. Memory Utilization / Pressure (%)
- *What it is*: The percentage of physical RAM currently allocated to active processes (out of 16 GB).
- *What it measures*: Physical memory exhaustion.
- *How to interpret it*: Above 85% triggers memory agent reclamation; above 90% triggers emergency swap paging.
- *Why it matters*: Memory pressure is the primary trigger for cross-resource interference.
- *Limitations*: High memory utilization is normal in modern OS caching; it only becomes dangerous when working sets exceed capacity.

=== 21. I/O Channel Saturation (%)
- *What it is*: The proportion of storage channel bandwidth consumed by disk read and write requests across the dual channels.
- *What it measures*: Storage subsystem bottlenecking.
- *How to interpret it*: Approaching 100% indicates that disk requests are backing up in the elevator queue.
- *Why it matters*: Indicates when memory page flushes are starving application read operations.
- *Limitations*: Does not reveal disk head seek distance or mechanical latency.

=== 22. CPU Ready Queue vs. I/O Queue Length
- *What it is*: The count of jobs waiting for processor assignment versus jobs waiting for disk service.
- *What it measures*: Subsystem backlog distribution.
- *How to interpret it*: A surging I/O queue while CPU queue drops indicates processes are blocked on disk paging.
- *Why it matters*: Visualizes cross-subsystem pipeline balance in real time.
- *Limitations*: Queue count does not reflect the burst size of individual requests.

=== 23. Dataset Status Anomalies Count & Percentage
- *What it is*: Exactly 97 records out of 10,000 (0.97%) in the Kaggle dataset labeled with status = 1.
- *What it measures*: Ground-truth operational failure frequency in real datacenter telemetry.
- *How to interpret it*: Reflects real-world class imbalance; failures are rare but catastrophic.
- *Why it matters*: Provides empirical ground truth for training the supervised anomaly baseline.
- *Limitations*: Labeled at the system level, not per individual thread or process.

=== 24. Supervised Anomaly Classifier ROC-AUC & F1-Score
- *What it is*: Machine learning performance scores (ROC-AUC = 1.0000, F1 = 0.9730) of a Random Forest trained on real Kaggle status labels.
- *What it measures*: Predictability of datacenter failure from telemetry features.
- *How to interpret it*: Near-perfect scores confirm that operational failures exhibit clear mathematical signatures (specifically joint memory and CPU saturation).
- *Why it matters*: Scientifically justifies building a conflict-prediction engine on coupled resource features.
- *Limitations*: Trained on snapshot data; does not model temporal state sequences.

=== 25. Proposed vs. Coordinated CPU Quantum (ms)
- *What it is*: The numerical gap between the CPU Agent's desired time slice and the Coordinator's approved time slice.
- *What it measures*: The degree of arbitration intervention applied.
- *How to interpret it*: Zero gap indicates proposals were deemed safe. Positive gap indicates the coordinator expanded the quantum to suppress context-switch thrashing.
- *Why it matters*: The primary control knob arbitrated during multi-agent scheduling.
- *Limitations*: Clamped between 1.0 ms and 32.0 ms by hard safety constraints.

#pagebreak()

== Master Metric Reference Table

#align(center)[
#table(
  columns: (1.5fr, 2.2fr, 2.3fr, 1.5fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { rgb("#FFFFFF") },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: (x: 6pt, y: 5.5pt),
  [#text(fill: white, weight: "bold", size: 8pt)[Metric / Output]],
  [#text(fill: white, weight: "bold", size: 8pt)[Meaning & Quantity]],
  [#text(fill: white, weight: "bold", size: 8pt)[How to Interpret It]],
  [#text(fill: white, weight: "bold", size: 8pt)[Where it Appears]],

  [*Avg Turnaround ($T_"turn"$)*], [Mean submission-to-completion time.], [Lower is better; measures system latency.], [Overview, Sim Lab, Benchmarks, Reports],
  [*Avg Waiting Time ($T_"wait"$)*], [Mean time spent in ready queue.], [Lower is better; measures scheduling friction.], [Sim Lab, Benchmarks, Reports],
  [*Throughput ($Theta$)*], [Completed jobs per simulation tick.], [Higher is better; drop triggers self-healing.], [Overview, Sim Lab, Benchmarks],
  [*Completion Rate (%)*], [Percentage of jobs completed in 250 ticks.], [100% nominal; drops under thrashing.], [Overview, Benchmarks, Reports],
  [*Completed / Unfinished*], [Exact process completion count.], [Unfinished $> 0$ indicates capacity overload.], [Benchmarks, Reports],
  [*Context Switches*], [Total core process state saves.], [High values accelerate paging thrashing.], [Sim Lab, Reports],
  [*Thrashing Ticks*], [Ticks lost to memory-disk swap wait.], [Zero is healthy; high indicates collapse.], [Overview, Benchmarks, Reports],
  [*Decision Overhead (ms)*], [Coordination CPU time per tick.], [Sub-0.1 ms establishes real-time feasibility.], [Overview, Benchmarks, Reports],
  [*Turnaround Improvement*], [Percentage delta vs Conventional baseline.], [24%–49% improvement proves efficacy under stress.], [Overview, Reports],
  [*Total Conflicts*], [Detected hazard events across run.], [High count with resolution proves protection.], [Conflict Analysis],
  [*Conflict Rate (%)*], [Percentage of cycles triggering hazards.], [Measures cross-subsystem contention rate.], [Conflict Analysis],
  [*Resolved by Self-Healing*], [Conflicts stabilized via emergency overrides.], [Demonstrates closed-loop backup necessity.], [Conflict Analysis],
  [*Resolution Latency (ms)*], [Arbitration evaluation computation time.], [Sub-0.1 ms confirms no scheduling jitter.], [Conflict Analysis],
  [*Precision, Recall, F1*], [Conflict classifier predictive accuracy.], [F1 > 85% validates predictive reliability.], [Conflict Analysis],
  [*False Positive Rate*], [Frequency of false alarm arbitrations.], [12% FPR is within acceptable limits.], [Conflict Analysis],
  [*Healing Actions*], [Autonomous corrective interventions.], [Zero in nominal; positive under severe stress.], [Self-Healing Center],
  [*Healing Success Rate*], [Regressions restored within 30 ticks.], [100% verified confirms recovery reliability.], [Self-Healing Center],
  [*Avg Healing Time*], [Ticks required to restore throughput.], [1.0–4.5 ticks confirms swift stabilization.], [Self-Healing Center],
  [*Active Strategies*], [Count of configured recovery heuristics.], [Diversity of specialized response rules.], [Self-Healing Center],
  [*Jain's Fairness ($cal(J)$)*], [Equality of service across processes.], [Values > 0.84 confirm no job starvation.], [Benchmarks, Reports],
  [*CPU Utilization (%)*], [Processor core active busy time.], [High is good unless trapped in swap wait.], [Overview, Sim Lab],
  [*Memory Utilization (%)*], [Physical RAM allocated out of 16 GB.], [> 85% triggers reclamation; > 90% thrashing.], [Overview, Sim Lab],
  [*I/O Saturation (%)*], [Dual storage channel bandwidth usage.], [High saturation starves interactive reads.], [Overview, Sim Lab],
  [*Queue Lengths*], [Ready queue vs. I/O queue depths.], [Identifies pipeline backlog location.], [Overview, Sim Lab],
  [*Dataset Anomalies*], [97 ground-truth failures out of 10k rows.], [Real datacenter operational failure rate (0.97%).], [Dataset Explorer],
  [*ROC-AUC & F1-Score*], [Random Forest empirical classifier score.], [1.0000 AUC proves failure signatures exist.], [Dataset Explorer],
  [*Coordinated Quantum*], [Final approved CPU time slice (ms).], [Expands under pressure to suppress thrashing.], [Agent Control Center]
)
]

#pagebreak()
'''
