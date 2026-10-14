"""
Chapter 3: The Complete User Journey
"""

def get_chapter_3():
    return r'''
= The Complete User Journey

== Navigating CoReOS: Overview of User Actions
When a user, researcher, or evaluator opens CoReOS, they interact with an integrated research dashboard designed to explore, simulate, diagnose, and evaluate multi-agent operating system scheduling.

The user's journey follows eight logical phases:

#align(center)[
#table(
  columns: (0.8fr, 1.8fr, 2.8fr, 1.6fr),
  fill: (col, row) => if row == 0 { rgb("#0F172A") } else if calc.even(row) { rgb("#F8FAFC") } else { rgb("#FFFFFF") },
  stroke: 0.5pt + rgb("#CBD5E1"),
  inset: (x: 8pt, y: 7pt),
  [#text(fill: white, weight: "bold", size: 8.5pt)[Phase]],
  [#text(fill: white, weight: "bold", size: 8.5pt)[User Activity]],
  [#text(fill: white, weight: "bold", size: 8.5pt)[What the User Learns or Accomplishes]],
  [#text(fill: white, weight: "bold", size: 8.5pt)[Target Page]],

  [*Phase 1*], [System Inspection & State Verification], [Examines system health, active workload, dataset availability, and benchmark highlights.], [Overview (`/`)],
  [*Phase 2*], [Empirical Ground Truth Discovery], [Explores 10,000 real Kaggle IT records, distributions, correlation heatmaps, and supervised failure drivers.], [Dataset Explorer (`/dataset`)],
  [*Phase 3*], [Workload Configuration & Live Simulation], [Configures processes, quantum, workload regime, and executes 250-tick discrete-event simulation.], [Simulation Lab (`/simulation`)],
  [*Phase 4*], [Agent Proposal & Decision Audit], [Audits step-by-step proposals from CPU, Memory, and I/O agents against coordinator overrides.], [Agent Control Center (`/agents`)],
  [*Phase 5*], [Conflict Diagnostics & Taxonomy], [Analyzes detected hazard events, classification breakdowns, and ML prediction precision/recall.], [Conflict Analysis (`/conflicts`)],
  [*Phase 6*], [Self-Healing & Recovery Assessment], [Observes autonomous change-point detections, recovery overrides, latency, and cooldown periods.], [Self-Healing (`/healing`)],
  [*Phase 7*], [Comparative Benchmarking (A–F)], [Fairly evaluates Baselines A through F across 5 workloads using 95% confidence intervals.], [Benchmark Lab (`/benchmarks`)],
  [*Phase 8*], [Research Findings & Data Export], [Reads full research reports, reviews component ablations, and downloads verified CSV datasets.], [Research Reports (`/reports`)]
)
]

== Logical Relationships and Dependencies Between Activities
The user journey in CoReOS is not a random collection of isolated pages; it follows a strict dependency chain:

1. *Dataset Grounding Precedes Workload Generation*:
   Before running a simulation, the user should understand that CoReOS does not invent random numbers out of thin air. In Phase 2 (*Dataset Explorer*), the user inspects the 10,000 Kaggle IT performance records. The statistical distributions observed here (e.g. process counts, memory utilization, context switches) serve as empirical priors that calibrate the Workload Generator in Phase 3.
2. *Simulation Execution Drives Telemetry Pages*:
   When a user clicks "Run Simulation" in Phase 3 (*Simulation Lab*), the discrete-event engine steps through 250 ticks. This execution generates telemetry snapshots that *immediately populate* Phase 4 (*Agent Control Center*), Phase 5 (*Conflict Analysis*), and Phase 6 (*Self-Healing*). If no simulation has been run, these pages display the state of the default baseline run.
3. *Single Simulation vs. Benchmark Comparisons*:
   A live simulation run in Phase 3 represents a *single execution trajectory* for a specific random seed and workload. In contrast, Phase 7 (*Benchmark Lab*) presents aggregated results across *hundreds of randomized seeds and standardized baselines*. The user must not confuse their single active simulation run with the historical, multi-seed benchmark tables.
4. *Reports Synthesize All Prior Evidence*:
   Phase 8 (*Research Reports*) draws directly upon the data verified in Phase 2, the conflicts logged in Phase 5, the recoveries observed in Phase 6, and the baseline statistical distributions evaluated in Phase 7.

== Step-by-Step User Workflow Diagram

#align(center)[
#rect(
  fill: rgb("#F8FAFC"),
  stroke: 1pt + rgb("#CBD5E1"),
  radius: 8pt,
  inset: 12pt,
  width: 100%
)[
  #text(weight: "bold", size: 9.5pt, fill: rgb("#0F172A"))[CoReOS End-to-End Operational Workflow] \
  #v(8pt)

  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    align: center + horizon,
    gutter: 8pt,
    [
      #block(fill: rgb("#E0F2FE"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#0369A1"))[1. Overview] \
        #text(size: 7.5pt)[Verify system health & active workload status]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[→]],
    [
      #block(fill: rgb("#FEF3C7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#B45309"))[2. Dataset Explorer] \
        #text(size: 7.5pt)[Review empirical telemetry, correlations & anomaly baseline]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[→]],
    [
      #block(fill: rgb("#DCFCE7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#15803D"))[3. Simulation Lab] \
        #text(size: 7.5pt)[Configure stress profile & execute 250-tick run]
      ]
    ]
  )

  #v(8pt)
  #align(center)[#text(size: 14pt, fill: rgb("#94A3B8"))[↓]]
  #v(4pt)

  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    align: center + horizon,
    gutter: 8pt,
    [
      #block(fill: rgb("#FEE2E2"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#B91C1C"))[6. Benchmark Lab] \
        #text(size: 7.5pt)[Compare Baselines A–F across multiple seeds]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[←]],
    [
      #block(fill: rgb("#F3E8FF"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#7E22CE"))[5. Conflict & Healing] \
        #text(size: 7.5pt)[Inspect hazard classification & recovery duration]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[←]],
    [
      #block(fill: rgb("#F1F5F9"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#334155"))[4. Agent Control] \
        #text(size: 7.5pt)[Audit proposed vs coordinated quantum decisions]
      ]
    ]
  )

  #v(8pt)
  #align(center)[#text(size: 14pt, fill: rgb("#94A3B8"))[↓]]
  #v(4pt)

  #block(fill: rgb("#0F172A"), inset: 8pt, radius: 4pt, width: 60%)[
    #text(weight: "bold", size: 8.5pt, fill: rgb("#2DD4BF"))[7. Research Reports & Data Exports] \
    #text(size: 7.5pt, fill: rgb("#CBD5E1"))[Review executive findings, ablation metrics, and download raw CSV data]
  ]
]
]

== A Concise End-to-End Walkthrough Example
To see how a user typically operates CoReOS, consider the following real scenario:

- *Step 1*: The user launches the dashboard at `http://localhost:5173/` and checks the *Overview*. The health bar confirms: `Dataset: Available (10k Records)`, `Latest Sim: Completed (Run #1)`, and `Unresolved Conflicts: 0`.
- *Step 2*: The user navigates to *Dataset Explorer* and selects the "Empirical Correlations" tab. Looking at the 12x12 heatmap, they observe that `cpu_utilization`, `memory_usage`, and `temperature` exhibit moderate positive cross-correlations, confirming that heavy CPU bursts often coincide with high memory demand in real datacenters.
- *Step 3*: The user switches to *Simulation Lab*. They want to test how the system performs when resources are severely strained. They choose `adversarial_stress`, set process count to 40, leave the policy as `Complete CoReOS`, and click "Run Simulation (250 ticks)". Within approximately 1.5 seconds, the simulation completes, rendering utilization curves showing CPU at ~80% and Memory at ~90%.
- *Step 4*: The user moves to *Agent Control Center* to see what happened behind the scenes. In the decision table at Step 48, they spot that the CPU Agent proposed a quantum of 2.0 ms, but the Coordinated Quantum was expanded to 8.0 ms. The explanation reads: *"Hazard detected: Memory saturation; expanded quantum to suppress thrashing"*.
- *Step 5*: The user visits *Conflict Analysis*. The donut chart shows 18 total conflicts, with 60% categorized as `THRASHING_CPU_COLLAPSE` and 40% as `IO_SWAP_SATURATION`. All 18 conflicts are marked "Resolved".
- *Step 6*: The user checks *Self-Healing*. They see that 2 autonomous recoveries were triggered when throughput temporarily dipped, restoring nominal flow in an average of 4.5 ticks.
- *Step 7*: To see whether this performance actually beat traditional schedulers, the user opens *Benchmark Lab* and selects `adversarial_stress`. The bar chart shows that Conventional Round Robin (Baseline A) suffered a mean turnaround time of 118.11 ticks and 22.0 thrashing ticks, whereas Complete CoReOS (Baseline E) achieved 89.99 ticks and Reinforcement Learning (Baseline F) achieved 58.89 ticks.
- *Step 8*: Convinced by the empirical results, the user opens *Research Reports*, reads the executive summary, and clicks "Download Benchmark Results (CSV)" to export the numbers for their team presentation.

#pagebreak()
'''
