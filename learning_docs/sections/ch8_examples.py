"""
Chapter 8: Worked Examples and Practical Interpretation
"""

def get_chapter_8():
    return r'''
= Worked Examples and Practical Interpretation

To solidify how CoReOS operates in practice, this chapter presents three comprehensive, step-by-step worked examples grounded in the system's verified behavior and outputs.

== Worked Example 1: Running an Adversarial Stress Simulation

=== 1. Starting Situation
The user opens the dashboard with the goal of evaluating how CoReOS behaves under severe, coupled resource pressure where memory demands exceed physical RAM while CPU queues and I/O channels are simultaneously flooded.

=== 2. What the User Does
1. Navigates to the *Simulation Lab* (`/simulation`).
2. Selects `adversarial_stress` from the Workload Profile dropdown.
3. Sets Target Policy to `Complete CoReOS`.
4. Adjusts the Number of Processes slider to `40`.
5. Sets Base CPU Quantum to `4.0` ms.
6. Sets Random Seed to `42` for exact reproducibility.
7. Clicks the blue *Run Simulation (250 ticks)* button.

=== 3. What Output Appears
- The simulation executes across 250 ticks in approximately 1.5 seconds.
- Four KPI Metric Cards update:
  - *Turnaround Time*: `89.99 ticks` (Average)
  - *Waiting Time*: `65.87 ticks` (Average)
  - *Throughput*: `0.0333 jobs/tick` (Overall)
  - *Context Switches*: `412` (Total)
- The *System Resource Usage* chart renders:
  - Memory utilization climbs rapidly, fluctuating between 85% and 92%.
  - CPU utilization peaks near 80%, but dips when memory reclamation runs.
  - I/O saturation rises to 45%–55%.
- The *Process Queue Dynamics* chart reveals:
  - CPU Ready Queue stays controlled at 2–5 processes.
  - I/O Request Queue gradually climbs to ~20 requests as memory flushes dirty pages.

=== 4. How to Interpret That Output
The workload successfully induced heavy memory pressure. Because memory climbed past 85%, the system was on the verge of thrashing. However, throughput did not collapse to zero, and the CPU ready queue remained small. This proves that the system avoided a fatal context-switch deadlock.

=== 5. What Conclusion Can Reasonably Be Drawn
Under seed 42 of `adversarial_stress`, Complete CoReOS prevented total system collapse, completing tasks with an average turnaround of 89.99 ticks without allowing page thrashing to paralyze CPU cores.

=== 6. What CANNOT Be Concluded from This Example Alone
- It does *not* prove that CoReOS will achieve 89.99 ticks on every workload or with 1,000 processes.
- It does *not* prove superiority over other baselines *by itself*—to prove superiority, this run must be compared against Baseline A under the exact same seed (which is done in Example 3 and Benchmark Lab).

#pagebreak()

== Worked Example 2: Examining a CPU-Memory Conflict (`THRASHING_CPU_COLLAPSE`)

=== 1. Starting Situation
Following the simulation run in Example 1, the user wants to understand *why* the system did not thrash, and inspect the specific conflict detection and arbitration decisions that saved the system.

=== 2. What the User Does
1. Navigates to the *Agent Control Center* (`/agents`).
2. Inspects the *Proposed vs. Coordinated Quantum* chart and scrolls the *Decision Audit Log* table to Step 48.
3. Cross-references the event by opening *Conflict Analysis* (`/conflicts`) in another tab.

=== 3. What Output Appears
In the *Agent Control Center* table at Step 48:
- *Step / Time*: `48 / 48.0 ticks`
- *CPU Proposed Q*: `2.0 ms`
- *Coordinated Q*: `8.0 ms`
- *Mem Target*: `1024 MB`
- *I/O Policy*: `SCAN`
- *Conflict Type*: `THRASHING_CPU_COLLAPSE`
- *Arbitration Applied*: `Yes` (Green checkmark)
- *Explanation*: *"High memory pressure detected (>88%); expanding CPU quantum to 8.0ms to suppress context switch thrashing."*

In the *Conflict Analysis* page:
- Conflict `CONF-003` is logged at tick 48.
- *Contributing Agents*: `CPU, MEMORY`
- *Severity*: `High`
- *Status*: `Resolved`
- *Resolution*: `Coordinator Arbitration`

=== 4. How to Interpret That Output
At tick 48, the CPU ready queue had grown slightly. The autonomous CPU Agent, focusing solely on processor responsiveness, proposed shortening the time slice to 2.0 ms so waiting jobs could run sooner. 

However, physical RAM was at 88% utilization. If the coordinator had permitted a 2.0 ms quantum, the processor would have switched processes every 2 ms, immediately triggering page faults for each process's memory working set and collapsing the CPU into thrashing.

The Conflict Engine predicted this hazard. The Coordinator applied *Pareto arbitration*, overriding the quantum to 8.0 ms. This allowed the currently running process to complete more work per context switch, amortizing memory overhead and suppressing thrashing.

=== 5. What Conclusion Can Reasonably Be Drawn
Pre-execution conflict prediction directly prevented an uncoordinated agent decision from destroying system stability. The coordinator successfully intervened before the dangerous action executed.

=== 6. What CANNOT Be Concluded from This Example Alone
- Expanding the quantum is not universally superior; under light loads with zero memory pressure, an 8.0 ms quantum would needlessly increase interactive waiting times. It was appropriate *specifically because* memory was near the thrashing threshold.

#pagebreak()

== Worked Example 3: Closed-Loop Self-Healing Recovery & Baseline Comparison

=== 1. Starting Situation
The user wants to evaluate what happens when a sudden, unexpected resource spike bypasses predictive filters, causing an active performance regression, and wants to benchmark the final outcome against conventional scheduling.

=== 2. What the User Does
1. Navigates to the *Self-Healing Center* (`/healing`).
2. Reviews the *Recent Self-Healing Actions* table and the *Healing Success Rate Over Time* chart.
3. Opens the *Benchmark Lab* (`/benchmarks`) to compare Baseline A (Conventional) against Baseline E (Complete CoReOS) and Baseline F (Learning RL).

=== 3. What Output Appears
In the *Self-Healing Center*:
- Action `HEAL-001` is recorded at Step 72:
  - *Issue Detected*: `Throughput Collapse`
  - *Strategy*: `Memory Reclaim & Quantum Expansion`
  - *Target*: `Memory & CPU Subsystem`
  - *Result*: `Success`
  - *Latency*: `4.00 ticks`
  - *Linked Conflicts*: `CONF-005, CONF-006`
- The *Success Rate Over Time* curve confirms 100% resolution with 0 failed attempts.

In the *Benchmark Lab* (under `adversarial_stress`):
- *Baseline A (Conventional Round Robin)*:
  - Average Turnaround: `118.11 ticks`
  - Thrashing Ticks: `22.0 ticks`
  - Completion Rate: `46.7%` (only ~18 of 40 jobs finished)
- *Baseline E (Complete CoReOS)*:
  - Average Turnaround: `89.99 ticks` (a 23.8% improvement)
  - Thrashing Ticks: `18.0 ticks`
  - Completion Rate: `100.0%` (all 40 jobs completed)
- *Baseline F (Learning RL)*:
  - Average Turnaround: `58.89 ticks` (a 50.1% improvement)
  - Thrashing Ticks: `12.0 ticks`
  - Completion Rate: `100.0%`

=== 4. How to Interpret That Output
At tick 72, simultaneous task arrivals overwhelmed the system, causing throughput to collapse below nominal thresholds. The `PerformanceRegressionDetector` confirmed the change-point after 3 ticks of patience. The `RecoveryEngine` took emergency control, forced aggressive memory reclamation, doubled the CPU quantum, and locked the policy under a 5-step cooldown period. Within 4 ticks, throughput recovered to baseline, and normal multi-agent control resumed.

When compared against Baseline A, the conventional static Round Robin scheduler lacked this closed-loop recovery mechanism. As a result, it remained trapped in swap wait, finishing only 46.7% of its jobs and suffering a disastrous 118.11 ticks turnaround. Both Complete CoReOS and Learning RL finished 100% of tasks.

=== 5. What Conclusion Can Reasonably Be Drawn
Closed-loop self-healing provides an essential safety net for multi-agent operating systems. When predictive models miss an anomaly, automated recovery with cooling-off intervals prevents sustained collapse and dramatically outperforms traditional static operating system schedulers.

=== 6. What CANNOT Be Concluded from This Example Alone
- Self-healing does not imply zero performance penalty; during the 4 ticks of recovery, system latency was degraded compared to ideal steady-state execution.
- Learning RL's 58.89 ms score does not guarantee production readiness; as discussed in Chapter 9, reinforcement learning policies exhibit vulnerability when exposed to out-of-distribution workloads absent during training.

#pagebreak()
'''
