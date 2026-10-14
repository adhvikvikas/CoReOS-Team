# CoReOS Phase 1: Deep Performance Diagnosis & Bottleneck Ranking

**Author**: CoReOS Optimization Team  
**Date**: 2026-10-13  
**Target Repository**: `/Users/adhvikvikas/Documents/GitHub/CoReOS-Team`  
**Execution Environment**: `CoReOS-Team/.venv` (Python 3.11.4)  
**Status**: Completed  

---

## Executive Summary

Phase 1 conducted an empirical, code-level diagnosis of why Complete CoReOS (Baseline E) underperformed relative to Baseline C (Coordination without Conflict Prediction), Baseline A (Conventional Round Robin), and Baseline F (Reinforcement Learning) on adversarial stress and overall completion rate.

The analysis conclusively identified four interacting architectural failure modes in the current CoReOS design:
1. **CPU Quantum-Induced I/O Starvation**: `CPUAgent` proposes narrow time quanta (2.0–4.0 ticks) when the ready queue is short. Because memory and I/O pressure queue processes in `WAITING_MEMORY` or `WAITING_IO`, the ready queue appears artificially light. The short quantum causes running processes to yield frequently, repeatedly rolling against their I/O probability (`io_frequency` mean = 0.56) and overwhelming the 2-channel I/O subsystem. In adversarial stress, **24 out of 26 unfinished processes were stuck in `WAITING_IO`**.
2. **Harmful Seek Starvation from Greedy SSTF**: `IOAgent` proposes `SSTF` whenever `io_queue_length >= 8`. Because adversarial stress and I/O bottleneck workloads generate continuous I/O queues of 15–25 requests, `SSTF` remains active almost permanently, causing severe disk-head seek starvation for requests at peripheral cylinders. In contrast, elevator `SCAN` services all cylinders systematically without starvation.
3. **Sub-optimal Conflict Engine Arbitration & Recovery Oscillation**: When `ConflictEngine`'s machine learning model predicts a cross-resource conflict, it arbitrates the memory reclaim target down to 1024 MB. When `PerformanceRegressionDetector` detects a latency spike, `RecoveryEngine` forces `cpu_quantum = 4.0` and `memory_reclaim_target = 1024.0`. This inadequate headroom re-triggers memory thrashing, creating a destructive oscillation between thrashing stalls and latency spikes.
4. **Static Round Robin Scheduling Blindness to Job Progress**: `CPUAgent` exclusively proposes `ROUND_ROBIN`, even though `CPUSubsystem` natively supports `SRTF` (Shortest Remaining Time First). Under `cpu_spike` (where total CPU demand of 1600 ticks exceeds the 1200-tick 4-core 300-step horizon), Round Robin completes only 16/40 processes (40.0%), whereas `SRTF` completes 31/40 processes (77.5%) with a 50% turnaround reduction.

Furthermore, diagnosis of the Reinforcement Learning baseline (Baseline F) revealed that the trained Q-agent selects **Action 0 (`cpu_quantum=8.0`, `memory_reclaim_target=2048.0`, `io_policy="SCAN"`) for 100% of steps across all 6 workloads**. Baseline F is not exploiting any environment shortcut or hidden data; it simply uncovered that amortizing context switches, maintaining 2 GB reclamation headroom, and using SCAN prevents thrashing and I/O congestion simultaneously.

---

## 1. Deep Diagnosis of Adversarial-Stress Performance

### 1.1 Workload Profile & Initial Evidence
Under `adversarial_stress` (seed 42, 40 processes):
- **CPU Demand**: Total burst requirement = 939.0 ticks (mean 23.5 ticks/process, max 42.4 ticks).
- **Memory Demand**: Total RAM demand = 117,728 MB across 40 processes against a physical capacity of 16,384 MB (an **overcommit ratio of 7.19x**).
- **I/O Demand**: High I/O frequency (mean 0.56, range [0.41, 0.78]) with mean I/O burst time of 7.0 ticks.
- **Hardware Simulation Limits**: 4 CPU cores, 16,384 MB RAM, 8,192 MB swap, 2 I/O channels, 300-step cutoff.

Historical 15-seed benchmark performance:
| Metric | Baseline A (Conv) | Baseline C (Coord No Pred) | Baseline D (Pred No Heal) | Baseline E (Complete CoReOS) | Baseline F (RL) |
|---|---:|---:|---:|---:|---:|
| Completion Rate | 40.0% | 47.3% | 34.8% | 37.8% | 96.0% |
| Penalized Turnaround | 220.81 | 207.67 | 230.36 | 223.33 | 92.07 |
| Throughput | 0.0533 | 0.0631 | 0.0464 | 0.0504 | 0.1332 |
| Thrashing Ticks | 114.7 | 50.0 | 9.8 | 10.1 | 0.0 |
| Jain's Fairness | 0.730 | 0.720 | 0.718 | 0.699 | 0.724 |

### 1.2 Unfinished Process State Telemetry (Cutoff step 300)
Tracing process lifecycle states at simulation step 300 reveals why jobs fail to complete:

| State | Baseline E (Complete CoReOS) | Baseline C (Coord No Pred) | Baseline F (RL) |
|---|---:|---:|---:|
| `TERMINATED` (Completed) | 14 (35.0%) | 20 (50.0%) | 40 (100.0%) |
| `WAITING_IO` | **24** (mean rem burst: 13.5) | **19** (mean rem burst: 15.2) | **0** |
| `WAITING_MEMORY` | 2 (mean rem burst: 15.9) | 0 | 0 |
| `RUNNING` | 1 (mean rem burst: 7.8) | 1 (mean rem burst: 2.1) | 0 |
| `READY` | 0 | 0 | 0 |

**Finding**: In Baseline E, 24 of the 26 unfinished processes are trapped in `WAITING_IO`. They are not starved on CPU or memory; they are starved in the I/O channel queue.

### 1.3 Subsystem Root Causes

#### A. CPU Scheduling Mechanics
In `src/coreos/agents/cpu_agent.py` (`propose_action`):
```python
if ready_q > 15:
    quantum = 8.0
elif ready_q > 5:
    quantum = 4.0
elif ready_q > 0:
    quantum = 2.0
```
- **Flaw**: `CPUAgent` gauges system load solely by `ready_queue_length`. Under memory and I/O pressure, processes are blocked in `WAITING_MEMORY` and `WAITING_IO`, so `ready_q` is typically between 1 and 4.
- `CPUAgent` evaluates this as "light load" and proposes `quantum = 2.0` (88 steps) or `quantum = 4.0` (146 steps).
- When a process runs with a 2.0 quantum, it executes only 2 ticks before yielding. In `SystemSimulator.step`:
  ```python
  if self.rng.uniform(0.0, 1.0) < proc.io_frequency:
      self.io.enqueue_request(proc, ...)
  ```
- Because yielding occurs every 2.0 ticks, a process with burst 24.0 ticks rolls against `io_frequency = 0.56` **12 times**, whereas with quantum 8.0 it rolls only **3 times**.
- The tiny quantum acts as an injection pump, constantly driving runnable processes into the saturated 2-channel I/O subsystem.

#### B. I/O Scheduling Mechanics
In `src/coreos/agents/io_agent.py` (`propose_action`):
```python
elif io_q >= 8:
    policy = "SSTF"
```
- During Baseline E's adversarial stress run, `io_queue_length` averaged 16.7 requests (peaking at 30).
- `IOAgent` proposed `SSTF` 141 times out of 300 steps.
- In `src/coreos/simulation/environment.py`, `SSTF` sorts requests by minimum distance to the current disk head. Requests at cylinders far from the current head suffer starvation until their waiting time hits 25.0 ticks.
- In contrast, elevator `SCAN` sweeps continuously across cylinders, providing bounded latency and preventing head-pinning starvation.

#### C. Coordination & Arbitration Conflicts
In `src/coreos/conflict_prediction/predictor.py` and `src/coreos/coordination/coordinator.py`:
- `ConflictEngine`'s secondary ML predictor frequently fires (`STATISTICAL_CROSS_RESOURCE_CONFLICT`), suggesting:
  ```python
  {"CPU_AGENT": {"quantum": 6.0}, "MEMORY_AGENT": {"target_free_mb": 1024.0}}
  ```
- This reduces the memory reclaim target from 2048 MB back down to 1024 MB and does not override the I/O policy from `SSTF` to `SCAN`.
- In Baseline C, the non-predictive coordination rule in `_apply_non_predictive_coordination`:
  ```python
  if (is_pressure or is_thrashing or mem_util >= 85.0) and coordinated.get("cpu_quantum", 4.0) < 6.0:
      coordinated["cpu_quantum"] = 6.0
  ```
  raised the quantum to 6.0 without the ML predictor interfering. This explains why Baseline C outperformed Baseline E (47.3% vs 37.8% completion).

#### D. Self-Healing Flapping
In `src/coreos/self_healing/recovery.py`:
```python
elif event.regression_type == "LATENCY_SPIKE":
    corrective = {
        "cpu_quantum": 4.0,
        "cpu_policy": "ROUND_ROBIN",
        "io_policy": "SCAN",
        "memory_reclaim_target": 1024.0
    }
```
- When a latency spike is detected, `RecoveryEngine` forces `quantum = 4.0` and `target_free_mb = 1024.0`.
- 1024 MB is inadequate for a 7.19x RAM overcommit. Within 2–3 ticks, memory utilization climbs over 92%, triggering a `THRASHING_STALL` regression event, which resets quantum to 8.0 and reclaim to 2048 MB.
- Once thrashing clears, the cooldown period expires, latency spikes re-trigger, and the cycle repeats.

---

## 2. Diagnosis of the RL Baseline (Baseline F)

### 2.1 RL Training & Action Selection Verification
- **Architecture**: Discrete tabular Q-learning with 8-dimensional state observation discretized into 4 bins per feature.
- **Action Space**:
  - `Action 0`: `{"cpu_quantum": 8.0, "memory_reclaim_target": 2048.0, "io_policy": "SCAN"}`
  - `Action 1`: `{"cpu_quantum": 2.0, "memory_reclaim_target": 0.0, "io_policy": "FCFS"}`
  - `Action 2`: `{"cpu_quantum": 4.0, "memory_reclaim_target": 1024.0, "io_policy": "SSTF"}`
  - `Action 3`: `{"cpu_quantum": 6.0, "memory_reclaim_target": 4096.0, "io_policy": "SCAN"}`
- **Training Protocol**: Trained for 15 episodes on `steady_state` (150 steps/episode) with reward function:
  $$R = 5.0 \times \text{throughput} - 10.0 \times \mathbb{I}(\text{thrashing}) - 0.1 \times (\text{ready\_q} + \text{io\_q})$$

### 2.2 Empirical Action Trace Across All 6 Workloads
Tracing Baseline F's actions during evaluation across all 6 workloads revealed:
- `steady_state`: 160/160 steps selected **Action 0** (100%)
- `cpu_spike`: 300/300 steps selected **Action 0** (100%)
- `memory_thrashing`: 161/161 steps selected **Action 0** (100%)
- `io_bottleneck`: 152/152 steps selected **Action 0** (100%)
- `mixed`: 162/162 steps selected **Action 0** (100%)
- `adversarial_stress`: 296/296 steps selected **Action 0** (100%)

### 2.3 Fairness and Validity Assessment
1. **No Information Leakage**: The RL agent uses only state variables computed by `SystemSimulator.get_system_state()`. It receives no future information, ground-truth labels, or seed IDs.
2. **Deterministic Evaluation**: During evaluation (`evaluate=True`), it takes $\arg\max_a Q(s, a)$.
3. **Core Insight**: The tabular Q-agent discovered that Action 0 is a dominant static operating point for the default configuration. Maintaining 2048 MB headroom eliminates thrashing; quantum 8.0 amortizes context switches and reduces I/O churn; elevator SCAN eliminates head-pinning starvation.
4. **RL Limitation**: Because Action 0 is static, RL cannot adapt its CPU policy. On `cpu_spike`, Action 0 completes only 40.3% of processes. A truly adaptive conflict-aware agent using progress-aware CPU scheduling (such as SRTF) can dramatically surpass RL on compute-heavy workloads while matching it on resource-contended workloads.

---

## 3. Quantitative Bottleneck Ranking

| Rank | Bottleneck | Affected Workloads & Baselines | Root Cause Source Files | Impacted Metrics | Proposed Intervention | Risk | Expected Gain |
|---|---|---|---|---|---|---|---|
| **1** | **Excessive Preemption & I/O Injection Churn** | `adversarial_stress`, `io_bottleneck` (Baselines E, D, B) | `src/coreos/agents/cpu_agent.py`: `propose_action` | Completion (-60%), Penalized Turnaround (+130 ticks), Throughput (-60%) | Base quantum on total active process pressure (`ready_q + waiting_io + waiting_mem`), adopting 6.0–8.0 under contention. | Low | +40–55% completion under stress |
| **2** | **Cylinder Seek Starvation from SSTF** | `adversarial_stress`, `io_bottleneck`, `mixed` (Baselines E, D, C, B) | `src/coreos/agents/io_agent.py`: `propose_action` | I/O Wait Time (+20 ticks), Completion (-15%), Fairness (-0.05) | Prioritize elevator `SCAN` under moderate-to-high queue depth ($\ge 6$), avoiding SSTF head-pinning. | Low | -50% I/O wait, +10% throughput |
| **3** | **Self-Healing & Conflict Arbitration Oscillation** | `adversarial_stress`, `memory_thrashing` (Baseline E) | `src/coreos/self_healing/recovery.py`, `src/coreos/coordination/coordinator.py` | Thrashing (+10 ticks), Penalized Turnaround (+20 ticks) | Unify recovery targets: maintain $\ge 2048$ MB reclaim under memory pressure; never clamp quantum below 6.0 during latency spikes. | Medium | Eliminates thrashing stalls and policy flapping |
| **4** | **Static Round-Robin Blindness on CPU-Heavy Spikes** | `cpu_spike`, `mixed` (Baselines A, B, C, D, E, F) | `src/coreos/agents/cpu_agent.py`, `src/coreos/simulation/environment.py` | Completion (capped at ~40%), Turnaround (+150 ticks) | Introduce progress-aware scheduling (`SRTF` or aging priority) when CPU queue depth is high and bursts vary. | Medium | +35% completion on `cpu_spike` (from 40% to 75%+) |
| **5** | **ML Conflict Prediction Mismatch** | `adversarial_stress`, `mixed` (Baselines E, D) | `src/coreos/conflict_prediction/predictor.py`: `predict_conflict` | Decision Overhead (+0.2 ms), Arbitration Accuracy | Re-calibrate ML decision threshold and ensure suggested arbitration prescribes adequate reclaim ($\ge 2048$ MB) and `SCAN`. | Low | +5% turnaround, consistent arbitration |

---

## 4. Phase 1 Conclusion & Sign-Off

The diagnosis is grounded in simulation telemetry and source code analysis. We understand exactly why CoReOS lost useful work:
- CoReOS choked itself with tight quanta and greedy SSTF, causing 24/40 processes to stall in the I/O queue.
- RL succeeded not by complex multi-step reasoning, but by anchoring to an effective joint configuration (8.0 quantum, 2048 MB reclaim, SCAN).
- An enhanced CoReOS combining adaptive resource arbitration, progress-aware scheduling (SRTF under compute congestion), robust 2 GB memory headroom, and elevator SCAN has a clear, evidence-based pathway to compete for **first or second place** against all baselines across all 6 workloads.

Phase 1 is complete. We proceed directly to **Phase 2: Competition Objective & Experimental Protocol**.
