"""
Chapter 2: Overall System Architecture
"""

def get_chapter_2():
    return r'''
= Overall System Architecture

== Conceptual Multi-Plane Architecture
CoReOS is structured into five distinct, interacting architectural planes. This separation ensures that raw data, simulation dynamics, agent proposals, safety arbitrations, and closed-loop healing operate with clean boundaries:

#align(center)[
#rect(
  fill: rgb("#F8FAFC"),
  stroke: 1pt + rgb("#CBD5E1"),
  radius: 8pt,
  inset: 14pt,
  width: 100%
)[
  #grid(
    columns: (1fr, 1fr, 1fr),
    gutter: 10pt,
    [
      #block(fill: rgb("#E0F2FE"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(fill: rgb("#0369A1"), weight: "bold", size: 9pt)[1. Data Plane] \
        #text(size: 8pt, fill: rgb("#0F172A"))[Kaggle IT Dataset (10,000 rows) • Empirical Priors • Anomaly Ground Truth]
      ]
    ],
    [
      #block(fill: rgb("#DCFCE7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(fill: rgb("#15803D"), weight: "bold", size: 9pt)[2. Simulation Plane] \
        #text(size: 8pt, fill: rgb("#0F172A"))[Discrete-Event Engine • 4 CPU Cores • 16GB RAM with Swap • 2 I/O Channels]
      ]
    ],
    [
      #block(fill: rgb("#FEF3C7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(fill: rgb("#B45309"), weight: "bold", size: 9pt)[3. Agent Control Plane] \
        #text(size: 8pt, fill: rgb("#0F172A"))[CPU Agent • Memory Agent • I/O Agent (Proposals & Confidence Scores)]
      ]
    ]
  )
  #v(8pt)
  #grid(
    columns: (1fr, 1fr),
    gutter: 10pt,
    [
      #block(fill: rgb("#FEE2E2"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(fill: rgb("#B91C1C"), weight: "bold", size: 9pt)[4. Conflict & Coordination Plane] \
        #text(size: 8pt, fill: rgb("#0F172A"))[Conflict Engine (Rules + ML) • Pareto Arbitration • Hard Safety Constraints Gate]
      ]
    ],
    [
      #block(fill: rgb("#F3E8FF"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(fill: rgb("#7E22CE"), weight: "bold", size: 9pt)[5. Self-Healing & Closed-Loop Plane] \
        #text(size: 8pt, fill: rgb("#0F172A"))[Rolling Change-Point Regression Detector • Recovery Overrides • Cooldown Enforcer]
      ]
    ]
  )
]
]

== The Role of Autonomous AI Agents
Rather than relying on hardcoded static rules, CoReOS assigns specialized autonomous agents to oversee individual physical resources:

=== 1. The CPU Agent (`CPUAgent`)
- *Role*: Evaluates the CPU ready queue length, process priorities, and recent context-switch frequency.
- *Proposed Actions*: Dynamically proposes the CPU time quantum (between 1.0 ms and 16.0 ms, nominal 4.0 ms) and the dispatch policy (Round Robin vs Priority-based).
- *Reasoning*: Under heavy ready queue pressure, it attempts to expand quanta to amortize context-switching overhead; under interactive, low-load regimes, it shortens quanta to improve responsiveness.

=== 2. The Memory Agent (`MemoryAgent`)
- *Role*: Monitors physical RAM utilization (out of 16 GB), free headroom, page fault counts, and thrashing indicators.
- *Proposed Actions*: Proposes the target free RAM headroom (e.g. 512 MB to 2048 MB) and triggers preemptive or emergency page reclamation.
- *Reasoning*: As utilization approaches 85%, it requests background page reclamation to prevent processes from triggering emergency synchronous page faults.

=== 3. The I/O Agent (`IOAgent`)
- *Role*: Observes disk queue depth, channel latency, and device saturation across the dual storage channels.
- *Proposed Actions*: Proposes disk elevator dispatching policies (FCFS, SSTF, or SCAN) and throttling levels for background tasks.
- *Reasoning*: Switches to Shortest Seek Time First (SSTF) or SCAN when queue depth rises to maximize disk arm mechanical efficiency.

== How Agents Interact with the Overall System
To prevent rogue agents from corrupting the operating system, *no agent is ever permitted to directly modify hardware state or simulation variables*.

Instead, agents submit structured *proposals* to the central coordinator at every simulation step. Each proposal encapsulates:
- *Agent Identifier*: Identifying the source (`CPU_AGENT`, `MEMORY_AGENT`, `IO_AGENT`).
- *Proposed Operation & Parameters*: E.g., target quantum = 2.0 ms, target free RAM = 1024 MB, disk policy = SSTF.
- *Confidence Score*: A mathematical confidence level in [0.0, 1.0].
- *Human-Readable Justification*: A natural-language explanation of why the agent desires this configuration (e.g., *"Ready queue depth > 15; expanding quantum to reduce thrashing"*).

== How Conflicts Arise Between Agents
Conflicts in CoReOS do not stem from software programming bugs; they emerge naturally from *competing physical resource demands*. 

When multiple agents pursue localized optimizations simultaneously, their joint parameter combination can create a systemic hazard:
- *CPU-Memory Clash*: When RAM is at 90% utilization, the CPU Agent may observe a long ready queue and propose a very short quantum (e.g. 2.0 ms) to serve all waiting jobs. However, rapid context switching between jobs with large working sets causes immediate page faults. The CPU cores become paralyzed in swap wait.
- *Memory-I/O Clash*: As RAM hits 95%, the Memory Agent panics and orders 2 GB of memory flushed to disk swap. Simultaneously, the I/O Agent is attempting to serve critical file-read requests. The sudden flood of swap writes blocks the storage channel, freezing application reads.
- *Triple Cascade Deadlock*: Under adversarial load, the CPU, Memory, and I/O subsystems simultaneously saturate, causing mutual deadlock across all three channels.

== Conflict Prediction and Pareto Arbitration
Before any proposal tuple `[A_CPU, A_Mem, A_IO]` can be executed, it passes through the *Conflict Prediction & Coordination Plane*:

1. *Pre-Execution Evaluation*: The *Conflict Engine* evaluates the joint proposal tuple against current system headroom using a hybrid model:
   - *Deterministic Domain Rules*: Rapidly identify known dangerous thresholds (e.g., Memory > 85% AND Quantum < 3.0 ms).
   - *Gradient Boosting ML Classifier*: Evaluates subtle multi-feature interactions trained on historical execution patterns.
2. *Hazard Classification*: If a hazard is predicted, it is classified into one of three taxonomies:
   - `THRASHING_CPU_COLLAPSE` (CPU-Memory hazard)
   - `IO_SWAP_SATURATION` (Memory-I/O hazard)
   - `TRIPLE_CASCADE` (All-resource mutual saturation)
3. *Pareto Arbitration*: If a conflict is predicted with confidence $>= 0.40$, the *Coordination Agent* modifies the proposed parameters to find a *Pareto-improving* compromise. For example, it overrides the CPU Agent's requested 2.0 ms quantum to 8.0 ms, thereby amortizing context switches and suppressing page thrashing while still servicing the processes.
4. *Deterministic Safety Fallback*: If prediction confidence drops below $0.40$ or an unexpected input is encountered, the coordinator engages a deterministic fallback policy (standard Round Robin quantum 4.0 ms, SCAN I/O, 1024 MB headroom).
5. *Hard Safety Constraints Gate*: As a final safeguard, all parameters pass through a hard constraint validator. Quanta are strictly clamped between $1.0$ and $32.0$ ms, memory targets cannot exceed physical RAM (16 GB), and only registered policies are permitted. Illegal states are physically incapable of reaching execution.

== Closed-Loop Self-Healing
Predictive coordination is proactive, but what happens if an extreme, unmodeled burst bypasses the predictor? CoReOS incorporates closed-loop *Self-Healing*:

- *Regression Detection*: The `PerformanceRegressionDetector` continuously watches system throughput and queue dynamics over rolling time windows. It uses statistical change-point analysis with a 3-step patience threshold to verify that a performance drop is genuine and not just transient noise.
- *Autonomous Recovery*: When a regression is confirmed, the `RecoveryEngine` executes targeted overrides:
  - *Thrashing Stall*: Triggers emergency memory reclamation and doubles CPU quantum.
  - *Throughput Collapse*: Expands CPU quantum to clear ready queue backlog.
  - *I/O Starvation*: Elevates I/O scheduling to SSTF and deprioritizes background traffic.
- *Cooling-Off Period*: To prevent *policy flapping* (where the system rapidly oscillates back and forth between normal and recovery policies), the engine enforces a mandatory 5-step cooling-off period during which recovery overrides remain locked until stability is verified.
- *Feedback Tuning*: The `FeedbackMechanism` reports unpredicted regressions back to the Conflict Engine, automatically tightening prediction sensitivity thresholds.

== Conceptual System Execution Flow
The readable diagram below traces how a workload moves through CoReOS during execution:

#align(center)[
#rect(
  fill: rgb("#F8FAFC"),
  stroke: 1pt + rgb("#CBD5E1"),
  radius: 8pt,
  inset: 12pt,
  width: 100%
)[
  #text(weight: "bold", size: 10pt, fill: rgb("#0F172A"))[Conceptual System Execution Flowchart] \
  #v(8pt)

  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    align: center + horizon,
    gutter: 6pt,
    [
      #block(fill: rgb("#E0F2FE"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#0369A1"))[1. Workload Task Arrival] \
        #text(size: 7.5pt)[Process arrivals calibrated by Kaggle dataset empirical priors]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[→]],
    [
      #block(fill: rgb("#FEF3C7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#B45309"))[2. Agent Proposal Tuple] \
        #text(size: 7.5pt)[CPU, Memory & I/O agents generate structured actions]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[→]],
    [
      #block(fill: rgb("#FEE2E2"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#B91C1C"))[3. Conflict Prediction Engine] \
        #text(size: 7.5pt)[Evaluates joint actions [A_CPU, A_Mem, A_IO] for hazards]
      ]
    ]
  )

  #v(8pt)
  #align(center)[#text(size: 14pt, fill: rgb("#94A3B8"))[↓]]
  #v(4pt)

  #grid(
    columns: (1fr, auto, 1fr, auto, 1fr),
    align: center + horizon,
    gutter: 6pt,
    [
      #block(fill: rgb("#F1F5F9"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#334155"))[6. Telemetry & Benchmark Evaluation] \
        #text(size: 7.5pt)[Turnaround, waiting time, throughput & fairness logged]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[←]],
    [
      #block(fill: rgb("#F3E8FF"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#7E22CE"))[5. Self-Healing (If Regressed)] \
        #text(size: 7.5pt)[Change-point detector triggers overrides + 5-step cooldown]
      ]
    ],
    [#text(size: 14pt, fill: rgb("#94A3B8"))[←]],
    [
      #block(fill: rgb("#DCFCE7"), inset: 8pt, radius: 4pt, width: 100%)[
        #text(weight: "bold", size: 8.5pt, fill: rgb("#15803D"))[4. Pareto Arbitration & Safety Gate] \
        #text(size: 7.5pt)[Tuning overrides applied; physical parameters clamped]
      ]
    ]
  )
]
]

#warning-box("Important Operational Realism Note", [
  *Not all tasks follow every step in this pipeline*:
  - In a balanced or nominal workload (`steady_state`), no conflict hazard is detected (Step 3 passes cleanly), so *Pareto arbitration is skipped* and proposals execute unaltered.
  - If no regression or stall occurs during execution, the *Self-Healing Engine remains completely idle*.
  - Claiming that every task triggers conflict arbitration or self-healing is incorrect and misrepresents the system's true behavior.
])

#pagebreak()
'''
