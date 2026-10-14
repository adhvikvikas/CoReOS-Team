"""
Chapter 6: Visualizations Interpretation Guide
"""

def get_chapter_6():
    return r'''
= Visualizations Interpretation Guide

CoReOS employs modern, interactive visualizations to translate complex multi-agent scheduling dynamics into clear, interpretable patterns. This chapter explains how to read every visual element, what questions they answer, what subtle patterns to look for, and which common interpretation pitfalls must be avoided.

== 6.1 Metric Cards & System Status Indicators
Metric cards appear at the top of every dashboard page to provide instant executive summaries.

=== Visual Elements & Anatomy
- *Primary Numerical Value*: Large bold font displaying the aggregate quantity (e.g. `10,000`, `0.12 ms`, `24.0% - 49.3%`).
- *Subtitle / Descriptor*: Small text indicating the operational meaning (e.g. `Verified records`, `Average arbitration time`, `Compared to conventional (stress)`).
- *Subsystem Color Accent*:
  - *Electric Blue (`#60A5FA`)*: Data plane, CPU subsystem, or general telemetry.
  - *Emerald Green (`#34D399`)*: Successful status, benchmark baselines, or self-healing completions.
  - *Cyan (`#2DD4BF` / `#34D3E9`)*: Coordination logic, memory subsystem, or arbitration speed.
  - *Amber (`#FBBF24`)*: Warnings, I/O storage saturation, or pending conflicts.
  - *Rose (`#F87171`)*: Critical hazards, thrashing collapse, or anomalies.
- *Status Indicator Dots*: Small circular badges (`Available`, `Completed`, `0 Unresolved`) providing immediate health validation.

=== Interpretation Guidance
- *What question does it answer?* "Is the system currently healthy, loaded, and operating within safe tolerances?"
- *What to look for*: A shift from green to amber or red in the health indicators, or sudden spikes in latency values.
- *Common interpretation mistake*: Confusing a static benchmark card with a live simulation metric. Stored benchmark improvements reflect historical multi-seed runs, not the active simulation run.

== 6.2 Time-Series Line Charts
Time-series charts appear on the Overview, Simulation Lab, Conflict Analysis, and Self-Healing pages.

=== 1. Real-Time Resource Utilization Chart
- *Axes*: Horizontal X-axis represents logical simulation time (0 to 250 ticks). Vertical Y-axis represents percentage saturation (0% to 105%).
- *Series & Colors*:
  - *CPU Utilization (Blue line, `#60A5FA`)*
  - *Memory Utilization (Cyan line, `#2DD4BF` / `#34D399`)*
  - *I/O Channel Saturation (Amber line, `#FBBF24`)*
- *What question does it answer?* "Which physical subsystem is currently the primary bottleneck, and are multiple resources saturating simultaneously?"
- *What to look for*:
  - *Decoupled Stress*: A single curve spikes while others remain low (e.g. CPU spike alone). The system handles this easily.
  - *Coupled Cross-Resource Collision*: Memory utilization climbs above 85% while I/O simultaneously surges. This indicates swap paging is saturating disk channels.
- *Meaning of a significant change*: If all three curves plateau above 80% simultaneously, the workload has triggered a `TRIPLE_CASCADE` hazard.
- *Common interpretation mistake*: Assuming 100% CPU utilization means great performance. If memory is simultaneously at 95%, the CPU is likely burning cycles in page-fault wait states.

=== 2. Process Queue Dynamics Chart
- *Axes*: X-axis = Simulation time (ticks). Y-axis = Queue backlog length (number of waiting jobs).
- *Series*: CPU Ready Queue (Blue) and I/O Request Queue (Amber/Cyan).
- *What question does it answer?* "Where are unfinished processes getting backed up in the operating system pipeline?"
- *What to look for*: A steady, climbing backlog in the I/O queue while the CPU queue drops to zero indicates processes are blocked on disk paging.
- *Common interpretation mistake*: Believing that an empty CPU queue means the computer is idle. The processes may simply all be blocked in memory swap sleep.

=== 3. Proposed vs. Coordinated Quantum Chart
- *Axes*: X-axis = Coordination step. Y-axis = Quantum length in milliseconds (1.0 to 16.0 ms).
- *Series*: Proposed Quantum (Dotted Purple, `#C084FC`) vs. Coordinated Quantum (Solid Emerald, `#34D399`).
- *What question does it answer?* "How aggressively is the central coordinator overriding the CPU Agent to preserve stability?"
- *What to look for*: Sudden upward divergence of the green line above the purple line. This visually marks the exact moment proactive conflict prevention intervened.

== 6.3 Donut and Distribution Proportional Charts
Donut charts appear in Conflict Analysis (Conflict Type Distribution) and Self-Healing (Strategy Usage).

=== Visual Elements
- *Hole & Center Text*: Displays the large total event count (`18 Conflicts`, `2 Actions`) with the category label below.
- *Color-Coded Slices*:
  - *CPU-Memory (`THRASHING_CPU_COLLAPSE`)*: Blue slice (`#60A5FA`).
  - *Memory-I/O (`IO_SWAP_SATURATION`)*: Cyan slice (`#34D3E9`).
  - *Triple Cascade*: Rose slice (`#F87171`).
  - *Cross-Resource*: Amber slice (`#FBBF24`).
- *Legend Grid*: Lists category labels with individual percentage breakdowns.

=== Interpretation Guidance
- *What question does it answer?* "What physical failure mode dominates this specific workload?"
- *What to look for*: A heavily dominant slice (e.g. 70% CPU-Memory) indicates that memory thrashing is the root vulnerability of that workload profile.
- *Common interpretation mistake*: Treating an empty donut chart as a broken visualization. Under `steady_state`, *zero conflicts occur*, which the page gracefully displays as a green "Zero Conflicts Detected" checkmark.

== 6.4 Comparative Bar Charts
Bar charts appear on the Benchmark Lab and Dataset Explorer pages.

=== 1. Benchmark Lab Multi-Baseline Comparison
- *Axes*: X-axis = Baselines A through F (`A_Conventional`, `B_IndependentAgents`, `C_CoordNoConflict`, `D_ConflictNoHealing`, `E_CompleteCoReOS`, `F_LearningRL`). Y-axis = Selected metric units (e.g. ticks, jobs/tick, %).
- *Value Annotations*: Exact values rendered directly above each bar for quick scanning.
- *Carbon Baseline Color Palette*:
  - *A_Conventional*: Cool Slate (`#64748B`)
  - *B_IndependentAgents*: Muted Blue (`#3B82F6`)
  - *C_CoordNoConflict*: Cyan (`#06B6D4`)
  - *D_ConflictNoHealing*: Amber (`#F59E0B`)
  - *E_CompleteCoReOS*: Vibrant Emerald Green (`#10B981`)
  - *F_LearningRL*: Royal Purple (`#8B5CF6`)
- *What question does it answer?* "Which architectural configuration wins on the selected metric, and by what margin?"
- *What to look for*: The height delta between Baseline A (Conventional) and Baseline E (Complete CoReOS) or F (Learning RL).
- *Common interpretation mistake*: Forgetting metric directionality! For Turnaround Time and Thrashing, *lower is better* (the shortest bar wins). For Throughput and Completion Rate, *higher is better* (the tallest bar wins).

== 6.5 Empirical Correlation Heatmap
The 12-Feature Correlation Heatmap appears on the Dataset Explorer page.

=== Visual Elements
- *Dimensions*: 12x12 symmetrical grid covering all telemetry features (`cpu_utilization`, `memory_usage`, `disk_io`, `network_latency`, `process_count`, `thread_count`, `context_switches`, `cache_miss_rate`, `temperature`, `power_consumption`, `uptime`, `status`).
- *Color Ramp*: *Viridis* palette ranging from deep dark purple (low/negative correlation) through teal to bright yellow (+1.0 perfect positive correlation).
- *Cell Labels*: Exact Pearson correlation coefficients printed inside each grid cell with contrasting white text.

=== Interpretation Guidance
- *What question does it answer?* "Which hardware metrics naturally couple together in real enterprise IT environments?"
- *What to look for*: Bright yellow/green clusters off the main diagonal. Observe that `memory_usage`, `cpu_utilization`, and `temperature` correlate positively with the failure `status` column.
- *Common interpretation mistake*: Confusing correlation with causation. A positive correlation between CPU usage and temperature does not mean high temperature caused the CPU usage; they are mutual consequences of high computation load.

== 6.6 Telemetry & Decision Audit Data Tables
Data tables appear in Agent Control, Conflict Analysis, Self-Healing, and Benchmark Lab.

=== Visual Elements & Status Badges
- *Sticky Header*: Dark slate background (`#101416`) with uppercase tracking labels.
- *Row Striping & Hover*: Alternating dark backgrounds with subtle hover highlights.
- *Status Badges*:
  - *Green Checkmark (`Yes`, `Resolved`, `Success`)*: Indicates successful arbitration or recovery.
  - *Red Crossmark (`No`, `Failed`, `Unresolved`)*: Indicates pass-through without intervention or unresolved state.
  - *Monospace Fonts*: Used for numeric parameters (e.g. `2.0`, `8.0`, `1024`) to ensure columnar alignment.
- *Tooltip Truncation*: Explanations truncate gracefully on smaller screens with full hover popovers.

=== Interpretation Guidance
- *What question does it answer?* "What was the exact parameter state, arbitration outcome, and scientific explanation at a specific logical tick?"
- *What to look for*: Correlating a sudden jump in `Coordinated Q` with the `Conflict Type` column and the human-readable `Explanation`.
- *Common interpretation mistake*: Overlooking the `Arbitration Applied` column. Just because an agent proposed an action does not mean it was executed; the coordinated parameter is the ground truth.

#pagebreak()
'''
