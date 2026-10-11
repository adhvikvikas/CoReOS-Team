# CoReOS Limitations, Simulation Assumptions, and Safety Boundaries

## 1. Simulation Abstractions vs. Real Operating System Kernels

CoReOS is a discrete-event research simulator implemented in Python. It evaluates operating system resource management concepts at an architectural level. It does **not** replace or modify the host operating system kernel.

### Specific Modeling Simplifications:
1. **CPU Subsystem**:
   - Models core execution, preemption, quantum expiration, and parameterized context switch penalties.
   - Does *not* model hardware interrupt handling (IRQs), translation lookaside buffer (TLB) shootdowns, processor cache hierarchies (L1/L2/L3 cache line evictions), or NUMA memory bus contention.
2. **Memory Subsystem**:
   - Models physical RAM allocation, page demand, swap storage, page fault latency penalties, and thrashing states.
   - Does *not* model MMU hardware page tables, kernel page fault traps, buddy allocator fragmentation, or virtual address translation mechanisms.
3. **Storage / I/O Subsystem**:
   - Models request queueing, channel capacity, contention slowdown, and seek optimization algorithms (FCFS, SSTF, SCAN).
   - Does *not* model DMA controllers, NVMe submission/completion ring buffers, file system journaling, or block device driver interrupts.

---

## 2. Dataset Scope and Limitations

1. **Snapshot Representation**: The Kaggle dataset (`Big_data_dataset.csv`) contains 10,000 system-level aggregate observations across 12 metrics. Analysis confirmed near-zero lag-1 autocorrelation, indicating independent machine snapshots rather than a continuous chronological time series.
2. **Absence of Per-Process Telemetry**: The dataset contains no per-process identifiers, thread arrival timestamps, individual CPU burst lengths, page allocation addresses, or disk block addresses.
3. **Ground Truth Scope**: The real dataset supports system-level anomaly prediction (via the `status` flag) and cross-metric correlation modeling. Process-level trajectories are generated via the calibrated simulator.

---

## 3. Learning Module Scope

1. **Simulation-Grounded Transitions**: Reinforcement learning transitions are collected exclusively from dynamic simulation runs. Ordinary static CSV rows are not treated as RL transitions.
2. **Q-Learning Bounds**: The implemented RL agent uses discretized Q-learning with safe action mappings. It is designed to demonstrate multi-agent coordination tradeoffs rather than claiming production kernel readiness.
3. **Safety Isolation**: Hard resource safety constraints are enforced by the coordinator outside the learning policy, guaranteeing that exploratory or unconverged RL actions cannot cause illegal states.

---

## 4. Security & Host Resource Safety Boundaries

- **No Host Mutation**: CoReOS does not alter host process priorities (`nice`), modify host scheduling (`sched_setscheduler`), or allocate raw host memory blocks.
- **No External LLM / API Dependency**: The entire application runs offline with zero API keys or external network calls.
- **No Shell Execution**: Resource decisions are strictly internal Python state mutations inside the simulated environment.
