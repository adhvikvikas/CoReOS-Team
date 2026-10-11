# CoReOS: Literature Review and Novelty Validation Report

## 1. Executive Summary
This literature review examines existing systems and scientific publications across seven foundational areas:
1. Multi-Agent Resource Allocation
2. Operating-System Scheduling
3. Cross-Resource Interference
4. Conflict-Aware Orchestration
5. Performance-Regression Detection
6. Self-Healing Resource Management
7. Reinforcement Learning for Resource Management

We explicitly assess the positioning of **CoReOS** against landmark prior art, delineate established concepts from proposed hypotheses, and establish clear novelty boundaries.

---

## 2. Systematic Review of Prior Art

### A. Cross-Resource Interference & Conflict-Aware Orchestration

#### 1. Paragon: QoS-Aware Scheduling for Heterogeneous Datacenters
- **Citation**: Delimitrou, C., & Kozyrakis, C. (ASPLOS 2013). *Paragon: QoS-Aware Scheduling for Heterogeneous Datacenters*. ACM.
- **Problem**: In multi-tenant environments, co-locating applications on shared physical hardware causes unpredictable QoS degradation due to microarchitectural contention (shared caches, memory buses).
- **Method**: Collaborative filtering (matrix factorization) to classify applications based on their sensitivity to interference and how much interference they cause.
- **Environment**: Linux clusters running cloud benchmarks.
- **Results**: Reduced QoS violations by up to 90% while improving datacenter utilization.
- **Limitations**: Requires profiling offline or during admission; does not provide process-level dynamic scheduling adaptation or closed-loop self-healing during sudden workload surges.
- **Comparison to CoReOS**: Paragon predicts interference *at placement time* (macroscopic admission control). CoReOS investigates *runtime multi-agent coordination* where active CPU, memory, and I/O agents negotiate parameters dynamically during execution.

#### 2. Quasar: Resource-Efficient and QoS-Aware Cluster Management
- **Citation**: Delimitrou, C., & Kozyrakis, C. (ASPLOS 2014). *Quasar: Resource-Efficient and QoS-Aware Cluster Management*. ACM.
- **Problem**: Cluster schedulers either overprovision resources or suffer severe SLA violations.
- **Method**: Fast profiling upon job submission followed by joint allocation of compute, memory, and network resources.
- **Environment**: 200-server cluster with batch and latency-critical services.
- **Results**: Maintained 99th-percentile latency targets while increasing cluster efficiency by 47%.
- **Limitations**: Focuses on container/VM-level orchestration rather than internal operating system scheduling mechanisms.
- **Comparison to CoReOS**: CoReOS explores internal OS subsystem interactions (e.g., CPU quantum vs memory swap traffic vs I/O channel contention).

#### 3. Heracles: Autonomous QoS Management for Datacenters
- **Citation**: Lo, D., et al. (ISCA 2015). *HERACLES: Improving Resource Efficiency at Scale*. ACM.
- **Problem**: Co-locating latency-critical services with best-effort batch tasks without violating sub-millisecond SLOs.
- **Method**: Feedback controller coordinating multiple hardware isolation mechanisms (hardware cores, CPU frequencies, memory bandwidth via Intel CAT, and network egress).
- **Environment**: Multi-core production servers at Google.
- **Results**: Enabled up to 90% server utilization without degrading latency-critical SLOs.
- **Limitations**: Relies on specific hardware isolation features (e.g., Intel CAT); treats tasks as black-box co-tenants rather than autonomous resource agents.
- **Comparison to CoReOS**: While Heracles employs centralized feedback control, CoReOS investigates distributed resource agents (CPU, Memory, I/O) that independently propose actions and arbitrate multi-dimensional conflicts through a dedicated coordination agent.

---

### B. Multi-Agent Systems & Reinforcement Learning in Resource Allocation

#### 4. Multi-Agent Resource Allocation in Cloud/OS Environments
- **Citation**: Ye, D., et al. (IEEE TPDS 2016). *Multi-Agent Reinforcement Learning for Resource Allocation in Cloud Computing*.
- **Problem**: Centralized allocators suffer scalability bottlenecks in dynamic, large-scale multi-tier cloud clusters.
- **Method**: Independent Q-learning agents representing virtual machines negotiating for server resources.
- **Environment**: CloudSim discrete-event simulator.
- **Results**: Demonstrated competitive throughput compared to centralized heuristics with lower communication overhead.
- **Limitations**: Independent Q-learners suffer non-stationarity and lack cross-resource conflict mediation, leading to localized optimization traps.
- **Comparison to CoReOS**: CoReOS directly addresses the failure mode of independent agents (demonstrated in Baseline B) by implementing an explicit Conflict Prediction Engine and Arbitration layer.

#### 5. SchedMD & Learning-Based OS Schedulers
- **Citation**: Mao, H., et al. (SIGCOMM 2016). *Resource Management with Deep Reinforcement Learning*. ACM.
- **Problem**: Complex scheduling objectives (minimizing job slowdown under multi-resource constraints) are difficult for fixed heuristics.
- **Method**: Deep RL (Policy Gradient) mapping cluster states directly to scheduling allocations.
- **Environment**: Trace-driven cluster simulation.
- **Results**: Outperformed conventional heuristics like Tetris and Fair Sharing.
- **Limitations**: High training sample complexity, risk of catastrophic regressions on out-of-distribution workloads, and lack of deterministic fallback policies.
- **Comparison to CoReOS**: CoReOS implements rule-based and ML-fused conflict prediction as the primary architecture, positioning reinforcement learning (Baseline F) as an experimental ablation rather than a sole black-box dependency. CoReOS enforces hard deterministic fallbacks when model confidence drops.

---

### C. Self-Healing & Regression Detection

#### 6. Autonomous Performance Regression Detection
- **Citation**: Nguyen, T. H. D., et al. (IEEE TSE 2014). *Automated Detection of Performance Regressions Using Statistical Process Control*.
- **Problem**: Identifying performance anomalies in noisy enterprise telemetry without excessive false alarms.
- **Method**: Control charts and change-point analysis on system response metrics.
- **Results**: Reduced regression diagnosis time by 60%.
- **Limitations**: Passive diagnostic tool; does not perform closed-loop autonomous remediation or OS policy reconfiguration.
- **Comparison to CoReOS**: CoReOS integrates statistical regression detection with an active Recovery Engine that applies parameter overrides (e.g. quantum adjustments, emergency swap compaction, I/O prioritization) within a bounded cooling-off period.

---

## 3. Position and Hypotheses of CoReOS

CoReOS builds upon the foundations of these prior systems while investigating specific, open research hypotheses:

| System / Paper | Target Layer | Coordination Paradigm | Conflict Prediction | Self-Healing Remediation |
| :--- | :--- | :--- | :--- | :--- |
| **Paragon** (ASPLOS '13) | Datacenter / VM Placement | Centralized CF Recommender | Offline / Admission | No (Static Placement) |
| **Quasar** (ASPLOS '14) | Datacenter / Container | Centralized Resource Pack | Job Profiling | Re-scale / Migrate |
| **Heracles** (ISCA '15) | Single-Node Server | Centralized Sub-second Control | No explicit predictor | Reactive throttling |
| **Ye et al.** (TPDS '16) | Cloud Multi-Tier | Independent Multi-Agent RL | None (Uncoordinated) | No |
| **CoReOS (This Work)** | Operating System Subsystems | Multi-Agent with Arbitration | Runtime Rule + ML Fusion | Closed-Loop Policy Overrides & Sensitivity Feedback |

### Research Hypotheses Under Investigation:
1. **Hypothesis 1 (Conflict Prediction)**: Joint cross-resource features (e.g., combining high memory utilization with short CPU quantum) predict system thrashing and latency degradation before execution more reliably than univariate thresholding.
2. **Hypothesis 2 (Coordination vs Independent Agents)**: Independent resource agents without cross-subsystem mediation trigger mutual interference under high load, whereas conflict-aware coordination reduces mean turnaround time.
3. **Hypothesis 3 (Self-Healing Value)**: Closed-loop regression detection with cooling-off periods can arrest performance collapse without causing oscillatory policy thrashing.
4. **Hypothesis 4 (Overhead Feasibility)**: The computational latency of multi-agent coordination and conflict prediction is negligible (<0.2 ms/tick), enabling real-time OS applicability.
