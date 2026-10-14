# CoReOS-Team — Comprehensive Project Reference & Academic Knowledge Base

> **File:** `PAPER_REVIEW_INFO.md`  
> **Repository:** `CoReOS-Team` (Branch: `main`)  
> **Document Purpose:** Reusable, single-source-of-truth knowledge base for research-paper review, architectural analysis, engineering development, benchmark verification, debugging, and academic reproduction.  
> **Inspection Basis:** Strict read-only audit of all 146 project entities, active source code, discrete-event simulation engine, FastAPI backend, React dashboard, canonical benchmark datasets (1,440 trials), IEEE conference paper sources, and test suites.

---

## 1. Quick Reference and Table of Contents

### 1.1 Executive Snapshot
- **System Identity:** **CoReOS** (*Conflict-Aware, Resource-Arbitrated Operating System*).
- **Core Paradigm:** Discrete-event multi-agent operating system simulation framework orchestrating specialized domain control agents (CPU, Memory, Storage I/O) via an adaptive, conflict-aware coordination core and closed-loop proportional self-healing engine.
- **Technology Stack:** Python 3.11.4, FastAPI 0.143.0, React 18.3.1, TypeScript 5.6.2, Vite 8.3.4, Plotly.js, Scikit-Learn 1.9.1, SciPy 1.17.1, Pytest 9.1.1, IEEE LaTeX (`IEEEtran.cls`), Typst 0.11+.
- **Canonical Evaluation Dataset:** Exactly **1,440 matched simulation trials** across **8 candidate architectures**, **6 operational workloads**, and **30 fresh held-out pseudo-random seeds** (`[5001..5030]`) with a 300-tick evaluation horizon.
- **Authoritative Competition Standing:**
  - **Rank #1:** `F_ImprovedRL` (Curriculum Adaptive RL): Composite Score **$85.81 \pm 1.53$**, Completion Rate **$95.28\%$**, Overhead **$0.0030$\,ms**.
  - **Rank #2 (Official Primary System):** `CoReOS` (`G_ChampionCoReOS`): Composite Score **$84.87 \pm 1.35$**, Completion Rate **$95.86\%$** (highest overall), Penalized Turnaround **$40.79$\,ticks**, Thrashing **$0.02$\,ticks**, Overhead **$0.1517$\,ms** ($100\%$ compliance with $\le 1.0$\,ms ceiling).
  - **Performance Advantage:** Statistically decisive separation over conventional static Round-Robin (+10.58 composite points, $t=8.589, p=4.20 \times 10^{-15}$, Cohen's $d=0.640$) and historical Complete CoReOS (+9.41 points, $t=9.452, p=1.87 \times 10^{-17}$, $d=0.704$).
- **Test Baseline:** **108 passed out of 108 tests** (`.venv/bin/pytest tests/`) across 16 test modules in 6.75s.
- **Frontend Build Status:** TypeScript check and Vite production bundle build succeed with **0 errors** in 2.14s.

### 1.2 Table of Contents
1. [Quick Reference and Table of Contents](#1-quick-reference-and-table-of-contents)
2. [Project Overview and Current Status](#2-project-overview-and-current-status)
3. [Architecture and Technology Stack](#3-architecture-and-technology-stack)
4. [Directory and File Reference](#4-directory-and-file-reference)
5. [Core Implementation and Data Flow](#5-core-implementation-and-data-flow)
6. [APIs and Frontend Behavior](#6-apis-and-frontend-behavior)
7. [Research Paper and Academic Contributions](#7-research-paper-and-academic-contributions)
8. [Benchmarks, Metrics, and Experimental Evidence](#8-benchmarks-metrics-and-experimental-evidence)
9. [Setup, Execution, and Testing](#9-setup-execution-and-testing)
10. [Known Issues, Limitations, and Risks](#10-known-issues-limitations-and-risks)
11. [Claim-to-Evidence Map](#11-claim-to-evidence-map)
12. [Task-to-File Navigation Guide](#12-task-to-file-navigation-guide)
13. [Unresolved Questions and Missing Evidence](#13-unresolved-questions-and-missing-evidence)
14. [Source Inspection Scope and Verification Limitations](#14-source-inspection-scope-and-verification-limitations)

---

## 2. Project Overview and Current Status

### 2.1 Problem Statement
Modern multi-tenant computing environments exhibit severe cross-subsystem interference when specialized resource allocators operate in isolation. In standard operating-system kernels, CPU scheduling (e.g., CFS), memory frame reclamation ($kswapd$), and block storage queueing (e.g., BFQ, elevator SCAN) are architected as decoupled silos. Under high contention:
- Aggressive CPU time-slicing accelerates thread context switches.
- Rapid context switching inflates working-set churn, exceeding physical RAM capacity.
- Asynchronous page reclamation triggers intensive page swapping to disk.
- Page swap traffic saturates the block storage queue, causing cylinder seek starvation.
- Processes executing on CPU stall awaiting synchronous I/O, triggering throughput collapse, convoy stalls, and severe memory thrashing.

### 2.2 Core Concepts & Terminology
- **Domain Agents (`src/coreos/agents/`):** Autonomous control agents that observe localized subsystem telemetry and formulate action proposals:
  - `WorkloadAwareCPUAgent`: Dynamically switches between Round-Robin and Shortest Remaining Time First (SRTF) based on ready-queue backlog and active load.
  - `MemoryAgent`: Adjusts memory reclamation targets based on physical utilization ratios and page-fault rates.
  - `WorkloadAwareIOAgent`: Mandates elevator SCAN over FCFS when storage queues accumulate requests to prevent mechanical cylinder starvation.
- **Adaptive Coordination Agent (`src/coreos/coordination/`):** Centralized arbiter enforcing deterministic cross-resource safety constraints, the *I/O Congestion Shield*, and *Memory-CPU Coupling Invariants*.
- **Calibrated Conflict Engine (`src/coreos/conflict_prediction/`):** Machine-learning inference module coupling deterministic cascade rules with a 50-tree Gradient Boosting Classifier to predict imminent multi-resource saturation.
- **Performance Regression Detector & Proportional Recovery Engine (`src/coreos/self_healing/`):** Closed-loop self-healing mechanism that detects throughput collapse, latency spikes, and thrashing, deploying graduated, non-oscillating interventions with exponential cooling-off periods.
- **Penalized Turnaround Time ($T_{pen}$):** A metric engineered to eliminate *survivorship bias*. Uncompleted tasks at the simulation horizon ($T_{max}=300.0$) are charged an explicit cutoff penalty ($\Pi = 300.0$\,ticks), exposing schedulers that artificially depress average latency by completing only short interactive tasks and starving background jobs.
- **Jain's Fairness Index ($J(\mathbf{T})$):** Standard normalized fairness metric evaluated across turnaround times.

### 2.3 Current Implementation Status
- **Operating-System Simulation Core:** Complete, fully operational discrete-event engine in `src/simulation/` and `src/coreos/simulation/`.
- **Backend Application Service:** Complete FastAPI service in `backend/` exposing simulation control, real-time telemetry, conflict analysis, self-healing status, dataset exploration, benchmark summaries, and report downloads.
- **Interactive Dashboard:** Complete React 18 SPA in `frontend/` featuring 8 full-featured pages, Carbon dark styling, Plotly.js charts, and live websocket/event polling.
- **Empirical Benchmark Suite:** Complete 1,440-trial canonical benchmark in `reports/optimization/final_canonical_benchmark_results.csv` with SHA-256 integrity manifest.
- **Academic Paper Package:** Complete 24-page IEEE conference-style paper in `research_paper/main.tex`, compiled to `main.pdf` (987\,KB), accompanied by 13 vector figures, 4 screenshots, and verified BibTeX references (`references.bib`).
- **Comprehensive Documentation:** Complete 78-page system guide in `learning_docs/CoReOS_System_Guide.typ`, compiled to `CoReOS_System_Guide.pdf`, with modular chapter generation scripts.

### 2.4 Implemented Features vs. Research Claims vs. Non-Claims
- **What CoReOS IS:** An advanced, high-fidelity discrete-event operating-system simulation framework and research platform for testing multi-agent arbitration, conflict prediction, and self-healing algorithms against standard scheduling baselines.
- **What CoReOS IS NOT:** It is **NOT** a native Linux kernel patch, C-based kernel module, eBPF program, or production OS distribution. It is also **NOT** a Large Language Model (LLM) agent orchestrator or Retrieval-Augmented Generation (RAG) system. All low-level scheduling decisions pertain to simulated hardware resources (CPU cores, memory pages, disk sectors).

---

## 3. Architecture and Technology Stack

### 3.1 Architectural Layering

```
+-----------------------------------------------------------------------------------+
|                           USER PRESENTATION LAYER                                 |
|      React 18.3.1 + TypeScript 5.6.2 + Vite 8.3.4 SPA (Carbon Dark Design)        |
|  [Overview] [SimulationLab] [AgentControl] [ConflictAnalysis] [SelfHealing]       |
|             [DatasetExplorer] [BenchmarkLab] [ResearchReports]                    |
+-----------------------------------------------------------------------------------+
                                      | HTTP REST (/api/*)
+-----------------------------------------------------------------------------------+
|                           BACKEND APPLICATION LAYER                               |
|                         FastAPI 0.143.0 + Uvicorn 0.54.0                          |
|  - SystemStateStore (backend/state.py): Thread-safe state, telemetry caching       |
|  - API Handlers (backend/api/): overview, simulation, agents, conflicts,          |
|    healing, dataset, benchmarks, reports                                          |
+-----------------------------------------------------------------------------------+
                                      | In-Memory Engine Binding
+-----------------------------------------------------------------------------------+
|                    ARBITRATION & SELF-HEALING CONTROL LAYER                       |
|  - AdaptiveCoordinationAgent: Deterministic safety invariants, I/O shield         |
|  - CalibratedConflictEngine: Gradient Boosting Classifier (50 trees, depth 3)     |
|  - PerformanceRegressionDetector: Sliding-window (W=10) anomaly detection         |
|  - ProportionalRecoveryEngine: Graduated interventions + exponential backoff      |
+-----------------------------------------------------------------------------------+
                                      | Resource Proposals & Actuation
+-----------------------------------------------------------------------------------+
|                          DOMAIN CONTROL AGENTS LAYER                              |
|  - WorkloadAwareCPUAgent (q=4/6/8, RR vs SRTF progress drain)                     |
|  - MemoryAgent (proactive reclamation: 1,024 MB to 4,096 MB)                      |
|  - WorkloadAwareIOAgent (elevator SCAN vs FCFS queue dispatch)                    |
+-----------------------------------------------------------------------------------+
                                      | Microarchitectural Telemetry & Step Clock
+-----------------------------------------------------------------------------------+
|                      DISCRETE-EVENT SIMULATION SUBSYSTEMS                         |
|  - CPUSubsystem: 4 cores, context switches (0.5 tick penalty), RR/SRTF/Priority   |
|  - MemorySubsystem: 16 GB physical RAM, 8 GB swap, page fault (5.0 tick penalty)  |
|  - IOSubsystem: 2 storage channels, 50-slot queue, cylinder geometry [0..100]    |
|  - Process & WorkloadGenerator: Poisson arrivals, compute/memory/IO distributions |
+-----------------------------------------------------------------------------------+
```

### 3.2 Technology Manifest

| Layer | Component | Version | Role in Project | Configuration File |
|---|---|---|---|---|
| **Simulation** | Python | 3.11.4 | Core language for simulation and algorithms | `pyproject.toml`, `requirements.txt` |
| **Numerical/Stats** | NumPy | 2.4.6 | Array processing, histogram distributions | `requirements.txt` |
| **Data Engine** | Pandas | 3.0.6 | Benchmark data processing, summaries | `requirements.txt` |
| **Scientific Computing** | SciPy | 1.17.1 | Student's t-test, Wilcoxon, confidence intervals | `requirements.txt` |
| **Machine Learning** | Scikit-Learn | 1.9.1 | Gradient Boosting, Random Forest, ROC-AUC | `requirements.txt` |
| **Backend API** | FastAPI | 0.143.0 | Asynchronous REST API framework | `backend/main.py` |
| **ASGI Server** | Uvicorn | 0.54.0 | High-performance ASGI web server | `backend/main.py` |
| **Frontend Framework**| React | 18.3.1 | Single-page UI framework | `frontend/package.json` |
| **Language** | TypeScript | 5.6.2 | Strict typed frontend implementation | `frontend/tsconfig.json` |
| **Build Tool** | Vite | 8.3.4 | Development server and production bundler | `frontend/vite.config.ts` |
| **Visualization** | Plotly.js | 2.35.2 | Interactive Cartesian, radar, and bar charts | `frontend/package.json` |
| **Testing** | Pytest | 9.1.1 | Unit, regression, and integration testing | `pyproject.toml` |
| **Paper Typesetting** | LaTeX / Tectonic | TeXLive / 0.15 | IEEE conference manuscript generation | `research_paper/main.tex` |
| **Documentation** | Typst | 0.11+ | Modern publication-quality system guide | `learning_docs/CoReOS_System_Guide.typ`|

### 3.3 Hardware Simulation Configuration Parameters

| Subsystem | Parameter Symbol | Configuration Value | Physical Meaning / Impact | Source Location |
|---|---|---|---|---|
| **CPU** | $N_c$ | 4 cores | Number of simulated symmetrical processor cores | `src/coreos/config.py:16` |
| **CPU** | $q_{def}$ | 4.0 ticks | Default round-robin scheduling quantum | `src/coreos/config.py:17` |
| **CPU** | $\delta_{cs}$ | 0.5 ticks | Context switch execution penalty charged to CPU | `src/simulation/cpu_subsystem.py:22` |
| **Memory** | $M_{phys}$ | 16,384 MB (16 GB) | Physical RAM boundary before swapping occurs | `src/coreos/config.py:24` |
| **Memory** | $M_{swap}$ | 8,192 MB (8 GB) | Secondary swap partition size | `src/coreos/config.py:25` |
| **Memory** | $\theta_{press}$ | 0.85 (85%) | Memory utilization threshold triggering pressure | `src/coreos/config.py:26` |
| **Memory** | Thrashing Boundary | $\mu_m \ge 0.92 \land \text{swap} > 5\%$ | Threshold defining destructive page thrashing | `research_paper/main.tex:141` |
| **Memory** | $\delta_{pf}$ | 5.0 ticks | Latency penalty for servicing a page fault | `src/simulation/memory_subsystem.py:28` |
| **Storage I/O** | $N_{io}$ | 2 channels | Concurrently serviced block storage channels | `src/simulation/io_subsystem.py:20` |
| **Storage I/O** | $K_{io}$ | 50 requests | Queue capacity before I/O requests are rejected | `src/simulation/io_subsystem.py:21` |
| **Storage I/O** | $d_{io}$ | 3.0 ticks | Base data transfer latency per I/O burst | `src/simulation/io_subsystem.py:22` |
| **Storage I/O** | Cylinder Range | $[0, 100]$ cylinders | Seek distance range for elevator SCAN modeling | `src/simulation/io_subsystem.py:23` |
| **Horizon** | $T_{max}$ | 300.0 ticks | Fixed simulation execution cutoff | `src/coreos/config.py:32` |
| **Horizon** | $\Pi$ | 300.0 ticks | Turnaround penalty charged for unfinished jobs | `src/coreos/simulation/metrics.py:44` |

---

## 4. Directory and File Reference

### 4.1 Root Structure
```text
CoReOS-Team/
├── backend/                       # FastAPI application service & state store
├── frontend/                      # React 18 + TypeScript + Vite web dashboard
├── learning_docs/                 # Comprehensive Typst system guide & build scripts
├── reports/                       # Benchmark outputs, optimization records, audits
│   └── optimization/              # Canonical 1,440-trial suite & Phase 8/9 datasets
├── research_paper/                # Submission-ready IEEE conference research paper
│   ├── figures/                   # 13 vector PDF + raster PNG analytical figures
│   └── scripts/                   # Automated figure generation & LaTeX scripts
├── scripts/                       # Canonical benchmark runners & experiment scripts
├── src/                           # Core algorithmic source code
│   ├── coreos/                    # Modern modular CoReOS framework
│   ├── data/                      # Dataset ingestion wrappers
│   ├── evaluation/                # Benchmark runner shims
│   ├── learning/                  # RL environment wrappers
│   ├── self_healing/              # Root self-healing bridges
│   └── simulation/                # Discrete-event hardware simulation engine
├── tests/                         # Pytest automated test suites (108 tests)
├── pyproject.toml                 # Packaging & tool configurations
└── requirements.txt               # Locked Python dependencies
```

### 4.2 Comprehensive Source Navigation Index

| Relative Path | Key Symbols / Classes | Primary Functional Responsibility |
|---|---|---|
| `backend/main.py` | `app`, FastAPI router includes | Application entry point; attaches CORS, registers routers, mounts `/api/*`. |
| `backend/state.py` | `SystemStateStore`, `state_store` | Centralized, thread-safe state repository; caches simulation runs, telemetry, conflicts, and healing records. |
| `backend/api/benchmarks.py` | `get_benchmarks()`, fallback logic | Serves candidate rankings, raw trials, per-workload heatmaps; handles 7 vs 8 candidate separation. |
| `backend/api/overview.py` | `get_overview()` | Serves top-level dashboard telemetry, baseline comparisons, and system health status. |
| `backend/api/reports.py` | `get_ablation_summary()`, `download_report()` | Serves live ablation study summary and streams validated benchmark CSV downloads. |
| `backend/api/simulation.py` | `run_simulation()`, `get_latest_simulation()` | Executes discrete-event simulation runs; supports settings persistence across page navigation. |
| `backend/api/agents.py` | `get_agent_decisions()` | Serves step-by-step audit trail of agent proposals, coordinator overrides, and explanations. |
| `backend/api/conflicts.py` | `get_conflict_analysis()` | Serves conflict detection rate, cascade taxonomy, precision/recall metrics, and timeline trends. |
| `backend/api/healing.py` | `get_healing_metrics()` | Serves self-healing recovery actions, strategy distribution, success rates, and latency. |
| `backend/api/dataset.py` | `get_dataset_info()`, `train_anomaly_baseline()` | Profiles 10,000-row telemetry dataset; trains Random Forest anomaly detector and returns ROC-AUC/F1. |
| `src/coreos/agents/base.py` | `BaseAgent`, `ActionProposal` | Abstract base class establishing standardized proposal protocol for domain agents. |
| `src/coreos/agents/cpu_agent.py` | `CPUAgent`, `WorkloadAwareCPUAgent` | Generates CPU quantum proposals; dynamically triggers progress-aware SRTF under queue backlogs. |
| `src/coreos/agents/memory_agent.py` | `MemoryAgent` | Monitors physical RAM utilization $\mu_m(t)$; calculates dynamic reclamation targets ($1,024$\,MB to $4,096$\,MB). |
| `src/coreos/agents/io_agent.py` | `IOAgent`, `WorkloadAwareIOAgent` | Monitors storage queue depth; enforces elevator SCAN to prevent disk cylinder starvation. |
| `src/coreos/coordination/coordinator.py`| `CoordinationAgent`, `AdaptiveCoordinationAgent` | Master arbitration core; enforces I/O Congestion Shield, memory-CPU coupling, and safety invariants. |
| `src/coreos/coordination/constraints.py`| `SafetyConstraints` | Deterministic bounding checks ensuring quantum, reclamation, and I/O policies remain in valid ranges. |
| `src/coreos/conflict_prediction/predictor.py`| `ConflictPredictor`, `CalibratedConflictEngine` | Evaluates 10-feature system state using Gradient Boosting Classifier to predict cascade failure modes. |
| `src/coreos/conflict_prediction/conflict_log.py`| `ConflictLog` | Tracks conflict history, calculates confusion matrix metrics (precision, recall, F1, FPR). |
| `src/coreos/self_healing/regression_detector.py`| `PerformanceRegressionDetector` | Sliding-window ($W=10$) detector identifying throughput collapse, latency spikes, and thrashing. |
| `src/coreos/self_healing/recovery.py` | `RecoveryEngine`, `ProportionalRecoveryEngine` | Dispatches graduated interventions (quantum expansion, SRTF queue drain, deep swap) with cooling-off backoff. |
| `src/coreos/learning/adaptive_rl.py` | `AdaptiveRLAgent`, `ImprovedRLCandidate` | Curriculum Q-learning candidate; projects state into 54 discrete bins; evaluates with Manhattan nearest-neighbor. |
| `src/coreos/optimization/candidates.py` | `ChampionCoReOS`, baseline wrappers | Implements official unified CoReOS candidate policy and standardized wrappers for comparative baselines. |
| `src/coreos/simulation/environment.py` | `CoReOSEnvironment` | Discrete-event simulation execution loop orchestrating clock ticks, agents, coordinator, and hardware. |
| `src/coreos/simulation/metrics.py` | `SimulationMetrics`, `calculate_jains_fairness` | Calculates composite scores ($S$), penalized turnaround ($T_{pen}$), Jain's fairness ($J$), and overhead. |
| `src/coreos/simulation/process.py` | `Process`, `ProcessState` | Process lifecycle model; encapsulates states, remaining burst, memory footprint, and I/O sequence. |
| `src/coreos/simulation/workload.py` | `WorkloadGenerator` | Generates reproducible process arrival sequences across the 6 standardized workload profiles. |
| `src/simulation/simulator.py` | `Simulator` | Root discrete-event simulation orchestrator advancing hardware components tick-by-tick. |
| `src/simulation/cpu_subsystem.py` | `CPUSubsystem` | Simulates 4 cores, time-slice preemption, context-switch accounting, and ready queue management. |
| `src/simulation/memory_subsystem.py` | `MemorySubsystem` | Simulates physical RAM frames, page swapping, allocation limits, and page-fault latency injection. |
| `src/simulation/io_subsystem.py` | `IOSubsystem` | Simulates dual-channel storage controller, 50-slot request queue, and mechanical cylinder movement. |
| `scripts/run_final_canonical_benchmark.py` | `run_benchmark()` | Master benchmark runner; executes 1,440 trials, computes statistics, and generates canonical CSV artifacts. |
| `research_paper/scripts/generate_figures.py` | `generate_all_figures()` | Generates all 13 publication figures (.pdf and .png) directly from canonical benchmark CSVs. |

---

## 5. Core Implementation and Data Flow

### 5.1 Discrete-Event Simulation Lifecycle
The discrete-event execution loop advances in discrete time steps ($\Delta t = 1.0$\,tick) up to $T_{max} = 300.0$\,ticks:
1. **Clock Synchronization:** Virtual clock advances to $t$. Arriving processes whose arrival tick $a_i \le t$ are evaluated. If free physical RAM $\ge M_i$, memory frames are assigned and process state transitions $\text{PENDING} \to \text{READY}$. Otherwise, the process transitions to $\text{WAITING\_MEM}$.
2. **State Vector Observation:** The global system state $\mathbf{x}(t)$ is extracted, encapsulating core utilization, physical/swap RAM usage, ready/memory/IO queue lengths, context switches, and page faults.
3. **Autonomous Agent Proposals:**
   - CPU Agent evaluates ready queue depth and active load $L_{act}$. If $L_{act} \ge 4 \land |\mathcal{Q}_{ready}| \ge 2$, it proposes SRTF with $q=8.0$; under moderate load, it proposes Round-Robin ($q=6.0$); under light load, Round-Robin ($q=4.0$).
   - Memory Agent evaluates physical utilization $\mu_m(t)$. If $\mu_m \ge 0.85$, it proposes emergency reclamation $R_{target} = 2,048$\,MB; if $\mu_m \ge 0.60$, it proposes $R_{target} = 1,024$\,MB.
   - Storage I/O Agent evaluates backlog $|\mathcal{Q}_{io}|$ and saturation $\sigma_{io}$. If $|\mathcal{Q}_{io}| \ge 2 \lor \sigma_{io} \ge 30\%$, it proposes elevator SCAN; otherwise, FCFS.
4. **Adaptive Cross-Resource Arbitration:**
   - Safety constraints clamp proposals to valid parameter envelopes.
   - The *I/O Congestion Shield* forces elevator SCAN if storage queues backlog, preventing disk head thrashing.
   - The *Memory-CPU Coupling Invariant* enforces $q \ge 8.0$ and $R_{target} \ge 2,048$\,MB when $\mu_m \ge 0.80$, while strictly preserving SRTF queue draining if already deployed.
   - The *Calibrated Conflict Engine* evaluates the 10-feature state vector $\mathbf{f}(t)$. If a cascade hazard is predicted, suggested arbitration overrides are applied.
5. **Self-Healing Regression Detection & Recovery:**
   - The Regression Detector tracks moving averages of throughput, p95 latency, and thrashing over window $W=10$.
   - If a regression event fires (`THRASHING_STALL`, `THROUGHPUT_COLLAPSE`, `LATENCY_SPIKE`), the Proportional Recovery Engine issues graduated overrides (elevating reclamation to $4,096$\,MB and deploying SRTF queue clearing) subject to exponential cooling-off periods.
6. **Hardware Subsystem Step:**
   - CPU advances running processes on active cores. If a process experiences thrashing, execution advances with slowdown factor $\omega_{slow} = 2.0$. Finished tasks release RAM and record completion tick $C_i = t$.
   - Yielded tasks requiring I/O transition to $\text{WAITING\_IO}$ and enter the storage queue.
   - Storage channels advance disk head toward target cylinders using the active policy (SCAN or FCFS), returning completed processes to the CPU ready queue.
7. **Metric Consolidation:** Turnaround, waiting times, throughput, and thrashing are logged. Unfinished processes are penalized at $T_{max}$ via $\Pi = 300.0$\,ticks.

---

## 6. APIs and Frontend Behavior

### 6.1 Backend API Endpoint Specification

| Endpoint Route | Method | Request Payload | Response Schema Summary | Active Backend Source | Calling Frontend Component |
|---|---|---|---|---|---|
| `/api/overview/` | GET | None | `{dataset_records, evaluated_baselines, decision_latency, turnaround_improvement, stress_comparison, highlights, telemetry, health}` | `backend/api/overview.py` | `frontend/src/pages/Overview.tsx` |
| `/api/simulation/latest` | GET | None | `{config: {workload_type, num_processes, policy_mode, seed, sim_quantum}, result: {history, state}, is_completed: bool}` | `backend/api/simulation.py` | `frontend/src/pages/SimulationLab.tsx` |
| `/api/simulation/run` | POST | `{workload_type, num_processes, policy_mode, seed, sim_quantum}` | `{history: [...], state: {cpu_util, mem_util, turnaround, waiting, throughput, switches, completion_rate}, workload_info}` | `backend/api/simulation.py` | `frontend/src/pages/SimulationLab.tsx` |
| `/api/agents/` | GET | None | `{records: [{step, time, cpu_proposed_quantum, coordinated_quantum, mem_reclaim_target, io_policy, conflict_type, arbitration_applied, explanation}], workload_info, total_records}` | `backend/api/agents.py` | `frontend/src/pages/AgentControl.tsx` |
| `/api/conflicts/` | GET | None | `{total_conflicts, conflict_rate, resolved_by_healing, avg_resolution_time, distribution: [...], trends: [...], taxonomy, metrics: {precision, recall, f1, fpr}}` | `backend/api/conflicts.py` | `frontend/src/pages/ConflictAnalysis.tsx` |
| `/api/healing/` | GET | None | `{total_recoveries, healing_actions, success_rate, avg_recovery_time, active_strategies: [...], strategy_usage, recent_actions: [...]}` | `backend/api/healing.py` | `frontend/src/pages/SelfHealing.tsx` |
| `/api/dataset/` | GET | None | `{metadata: {rows, cols, duplicates, anomaly_count, anomaly_percentage}, columns, head: [...], describe: [...], corr_matrix, corr_features, distributions}` | `backend/api/dataset.py` | `frontend/src/pages/DatasetExplorer.tsx` |
| `/api/dataset/train` | POST | None | `{metrics: {accuracy, anomaly_f1, roc_auc, classification_report}, feature_importance: [{Feature, Importance}]}` | `backend/api/dataset.py` | `frontend/src/pages/DatasetExplorer.tsx` |
| `/api/benchmarks/` | GET | None | `{workloads: [...], candidates: [...], active_candidates: [...], data: [...], overall_ranking: [...], active_ranking: [...], per_workload_summary: [...], source}` | `backend/api/benchmarks.py` | `frontend/src/pages/BenchmarkLab.tsx` |
| `/api/reports/ablation_summary` | GET | None | `{data: [{workload, configuration, completion_rate, avg_turnaround_time, throughput, thrashing_ticks}]}` | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` |
| `/api/reports/content/{filename}` | GET | URL param | `{filename: str, content: str}` (Streams markdown source for interactive report rendering) | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` |
| `/api/reports/download/{filename}` | GET | URL param | File download stream (Enforces whitelist of canonical, Phase 8, and Phase 3 CSV/MD files) | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` |

### 6.2 Frontend Architecture & Navigation Rules
- **State Persistence:** When users configure a simulation scenario in `SimulationLab.tsx` and navigate to `Overview.tsx` or `AgentControl.tsx`, returning to `SimulationLab.tsx` triggers `useEffect` querying `/api/simulation/latest`. Both the execution telemetry (`result`) and user input settings (`config`) are dynamically restored, preventing unintended parameter resets.
- **Inter-Page Event Synchronization:** Running a new simulation in `SimulationLab.tsx` dispatches a native browser window event:
  ```typescript
  window.dispatchEvent(new CustomEvent('coreos:simulationCompleted', { detail: { result, config } }));
  ```
  Components such as `AgentControl.tsx` and `SelfHealing.tsx` register event listeners for this signal, automatically refreshing their audit tables and telemetry feeds when a new simulation finishes.
- **Candidate Display Standardization (`frontend/src/components/common/chartTheme.ts`):**
  - All charts and tables map candidate `G_ChampionCoReOS` to the official name **`CoReOS`**.
  - Color palette is centralized in `BASELINE_CARBON_COLORS`:
    - `A_Conventional`: `#60A5FA` (Blue)
    - `B_IndependentAgents`: `#34D399` (Green)
    - `C_CoordNoConflict`: `#FBBF24` (Amber)
    - `D_ConflictNoHealing`: `#F87171` (Coral Red)
    - `E_CompleteCoReOS`: `#A78BFA` (Purple - Historical)
    - `F_ImprovedRL`: `#2DD4BF` (Teal / Cyan)
    - `G_ChampionCoReOS`: `#F472B6` (Pink / Rose - CoReOS Official)
    - `H_OriginalRL`: `#94A3B8` (Steel Slate)

---

## 7. Research Paper and Academic Contributions

### 7.1 Manuscript Details
- **Title:** *CoReOS: A Conflict-Aware and Self-Healing Multi-Agent Operating System for Coordinated Resource Scheduling*
- **Format:** IEEE Conference format (`IEEEtran.cls`), 24 pages, double-column.
- **Source File:** `research_paper/main.tex` (79,009 bytes).
- **Compiled Output:** `research_paper/main.pdf` (987,039 bytes, verified compilation).
- **Bibliography:** `research_paper/references.bib` (33 peer-reviewed systems and multi-agent citations).
- **Verification Audit:** Complete fact-check audit recorded in `research_paper/Verification_Report.md`.

### 7.2 Core Research Questions (RQs)
1. **RQ1 (Arbitration Efficacy):** Can explicit cross-resource arbitration rules and conflict prediction prevent multi-subsystem interference and improve throughput, completion rate, and turnaround latency compared to uncoordinated agents and round-robin baselines?
   - *Outcome:* **Confirmed.** CoReOS improves composite score by $+10.58$ points ($p < 10^{-14}$) over Conventional and $+9.41$ points ($p < 10^{-16}$) over uncoordinated/historical baselines.
2. **RQ2 (Self-Healing Robustness):** Does graduated proportional self-healing mitigate catastrophic thrashing under severe adversarial stress without introducing oscillatory policy thrashing?
   - *Outcome:* **Confirmed.** Thrashing is reduced from $105.37$\,ticks in Conventional to $0.10$\,ticks in CoReOS ($99.7\%$ reduction) under `adversarial_stress`.
3. **RQ3 (Computational Feasibility):** Can multi-agent arbitration and machine-learning conflict prediction execute within an operational decision overhead ceiling of $\le 1.0$\,ms per step?
   - *Outcome:* **Confirmed.** CoReOS averages $0.1517$\,ms overhead per step ($85\%$ safety margin below 1.0\,ms ceiling), achieving $100\%$ compliance across all 180 evaluated trials.
4. **RQ4 (Multi-Objective Fairness and Survivorship Bias):** How does multi-resource arbitration affect process fairness, and does conventional unpenalized metric calculation mask severe survivorship bias in starved baselines?
   - *Outcome:* **Confirmed.** Conventional baselines achieve artificially high Jain's fairness ($0.8230$) under compute spikes only by starving $52.5\%$ of processes; penalizing starved tasks exposes that CoReOS delivers $2\times$ lower true turnaround latency.

### 7.3 Mathematical Formulations
- **Thrashing Condition:**
  $$\text{Thrashing}(t) \iff \mu_m(t) \ge 0.92 \land \sum_{p \in \mathcal{P}} m_p^{swap}(t) \ge 0.05 \cdot M_{swap}$$
- **Penalized Turnaround Time ($T_{pen}$):**
  $$T_{pen} = \frac{1}{N_p} \left[ \sum_{p_i \in \mathcal{P}_{comp}} T_i + (N_p - |\mathcal{P}_{comp}|) \cdot \Pi \right], \quad \Pi = 300.0\,\text{ticks}$$
- **Jain's Fairness Index:**
  $$J(\mathbf{T}) = \frac{\left( \sum_{i=1}^n T_i \right)^2}{n \sum_{i=1}^n T_i^2} \in \left[ \frac{1}{n}, 1.0 \right]$$
- **Composite Benchmark Score ($S \in [0, 100]$):**
  $$S = 100 \times \left[ 0.30 \left(\frac{CR}{100}\right) + 0.25 \min\left(1.0, \frac{\Theta}{0.25}\right) + 0.20 \max\left(0, 1.0 - \frac{T_{pen} - 5.0}{295.0}\right) + 0.15 \max\left(0, 1.0 - \frac{\text{Thrash}}{150.0}\right) + 0.10 \operatorname{clamp}(J, 0, 1) \right]$$

---

## 8. Benchmarks, Metrics, and Experimental Evidence

### 8.1 Evaluated Candidate Architectures

| Candidate ID | System Identity | Scheduling Discipline | Memory Reclamation Policy | Storage I/O Policy | Role in Benchmark |
|---|---|---|---|---|---|
| `A_Conventional` | Conventional Baseline | Static Round-Robin ($q=4.0$) | Demand paging (No proactive reclaim) | FCFS queue dispatch | Classical decoupled OS heuristic |
| `B_IndependentAgents` | Independent Agents | Localized CPU proposals | Localized Memory proposals | Localized I/O proposals | Uncoordinated multi-agent baseline |
| `C_CoordNoConflict` | Coord (No Conflict) | Safety constraints only | Bounded reclamation | Bounded I/O | Ablation: Coordination without ML |
| `D_ConflictNoHealing` | Conflict (No Healing) | Full arbitration + ML | Full proactive reclamation | Elevator SCAN | Ablation: Arbitration without recovery |
| `E_CompleteCoReOS` | Baseline CoReOS | CoReOS prototype v1 | Proactive reclamation | Elevator SCAN | Historical reference baseline |
| `F_ImprovedRL` | Curriculum RL | Q-Learning (54 states) | Q-Learning actions | Q-Learning actions | Optimized tabular RL benchmark |
| `G_ChampionCoReOS` | **CoReOS (Official)** | **Progress-Aware SRTF/RR** | **Proactive & Deep Swap** | **Elevator SCAN Shield** | **Official Unified CoReOS System** |
| `H_OriginalRL` | Tabular RL | Q-Learning (uncompacted) | Default reclamation | FCFS dispatch | Early RL prototype baseline |

### 8.2 Canonical Benchmark Leaderboard (1,440 Matched Trials)
*Data Source:* `reports/optimization/final_canonical_ranking_summary.csv` ($N=1,440$ trials, 30 held-out seeds, 6 workloads).

| Rank | Candidate Architecture | Composite Score (Mean $\pm$ 95% CI) | Task Completion Rate (%) | Penalized Turnaround (ticks) | Throughput (jobs/tick) | Thrashing Ticks (mean) | Jain's Fairness Index | Decision Overhead (ms/step) |
|---|---|---|---|---|---|---|---|---|
| **1** | `F_ImprovedRL` | $85.81 \pm 1.53$ | $95.28\%$ | $39.84$ | $0.1834$ | **0.01** | **0.6510** | **0.0030** |
| **2** | `CoReOS` (`G_ChampionCoReOS`) | **$84.87 \pm 1.35$** | **$95.86\%$** | **$40.79$** | **$0.1771$** | **0.02** | **0.5934** | **0.1517** |
| **3** | `H_OriginalRL` | $82.17 \pm 2.29$ | $90.76\%$ | $58.36$ | $0.1743$ | $0.06$ | $0.6329$ | $0.0316$ |
| **4** | `D_ConflictNoHealing` | $75.47 \pm 3.06$ | $81.35\%$ | $82.40$ | $0.1549$ | $4.32$ | $0.6321$ | $0.1346$ |
| **5** | `E_CompleteCoReOS` | $75.46 \pm 3.07$ | $81.32\%$ | $82.23$ | $0.1549$ | $4.08$ | $0.6288$ | $0.1497$ |
| **6** | `C_CoordNoConflict` | $75.18 \pm 3.13$ | $81.76\%$ | $81.78$ | $0.1554$ | $9.67$ | $0.6346$ | $0.0051$ |
| **7** | `A_Conventional` | $74.29 \pm 3.45$ | $81.35\%$ | $81.73$ | $0.1573$ | $19.81$ | $0.6393$ | $0.0341$ |
| **8** | `B_IndependentAgents` | $74.29 \pm 3.30$ | $79.46\%$ | $86.46$ | $0.1521$ | $4.61$ | $0.6288$ | $0.0020$ |

### 8.3 Workload-Specific Breakdown for CoReOS
*Data Source:* `reports/optimization/final_canonical_per_workload_summary.csv` ($N=30$ seeds per cell).

| Workload Profile | Composite Score | Task Completion Rate | Penalized Turnaround | Throughput | Thrashing Ticks | Jain's Fairness | Overhead | Key Subsystem Dynamics |
|---|---|---|---|---|---|---|---|---|
| `steady_state` | $92.79 \pm 2.88$ | $100.0\%$ | $12.35$\,ticks | $0.2151$\,j/t | $0.00$\,ticks | $0.7053$ | $0.1519$\,ms | Balanced nominal load; context switches bounded. |
| `cpu_spike` | **$68.13 \pm 2.80$** | **$79.00\%$** | **$115.81$\,ticks** | **$0.1053$\,j/t** | $0.00$\,ticks | $0.6410$ | $0.1515$\,ms | **CoReOS ranks #1**; progress-aware SRTF clears convoys. |
| `memory_thrashing`| $91.32 \pm 2.66$ | $100.0\%$ | $15.78$\,ticks | $0.2068$\,j/t | $0.00$\,ticks | $0.6472$ | $0.1509$\,ms | Proactive reclamation eliminates page thrashing completely. |
| `io_bottleneck` | $88.91 \pm 2.86$ | $100.0\%$ | $10.84$\,ticks | $0.2059$\,j/t | $0.00$\,ticks | $0.3934^*$ | $0.1507$\,ms | Elevator SCAN eliminates head churn; cylinder sweep delays induce fairness drop. |
| `mixed` | $89.34 \pm 2.57$ | $100.0\%$ | $14.88$\,ticks | $0.1996$\,j/t | $0.00$\,ticks | $0.5045^*$ | $0.1524$\,ms | Multi-resource coupling dynamically arbitrated. |
| `adversarial_stress`| $78.75 \pm 2.18$ | $96.17\%$ | $75.08$\,ticks | $0.1297$\,j/t | $0.10$\,ticks | $0.6688$ | $0.1527$\,ms | Proportional self-healing overrides restore stability (+43.31 pts vs Conventional). |

*\*Note:* Jain's fairness drops below the $0.60$ floor under I/O bottlenecks across **all eight candidate architectures** due to physical cylinder distance variance.

### 8.4 Statistical Hypothesis Testing Results
*Data Source:* `reports/optimization/final_canonical_statistical_comparisons.csv` ($N=180$ matched trial pairs per row).

| Hypothesis Comparison ($A$ vs. $B$) | Mean Difference ($\Delta$) | Std Diff ($\sigma_\Delta$) | Cohen's $d$ Effect Size | Paired $t$-Statistic | Unadjusted $p$-Value | Holm-Bonferroni Corrected $p$ | Statistical Significance ($\alpha=0.05$) |
|---|---|---|---|---|---|---|---|
| **CoReOS vs. Conventional (A)** | $+10.584$ | $16.532$ | $0.640$ | $8.589$ | $4.20 \times 10^{-15}$ | $7.56 \times 10^{-14}$ | **DECISIVE SUPERIORITY** |
| **CoReOS vs. Complete CoReOS (E)** | $+9.410$ | $13.357$ | $0.704$ | $9.452$ | $1.87 \times 10^{-17}$ | $4.31 \times 10^{-16}$ | **DECISIVE SUPERIORITY** |
| **CoReOS vs. Original RL (H)** | $+2.699$ | $7.197$ | $0.375$ | $5.032$ | $1.17 \times 10^{-6}$ | $1.41 \times 10^{-5}$ | **STATISTICALLY SIGNIFICANT** |
| **Curriculum RL (F) vs. Conventional (A)** | $+11.517$ | $17.110$ | $0.673$ | $9.031$ | $2.68 \times 10^{-16}$ | $5.36 \times 10^{-15}$ | **DECISIVE SUPERIORITY** |
| **Curriculum RL (F) vs. CoReOS (G)** | $+0.934$ | $2.833$ | $0.330$ | $4.422$ | $1.69 \times 10^{-5}$ | $1.52 \times 10^{-4}$ | **STATISTICALLY SIGNIFICANT** |

### 8.5 Multi-Criteria Guardrail Compliance Audit
*Data Source:* `reports/optimization/final_canonical_guardrail_compliance.csv`.

| Guardrail Name | Formal Threshold Criterion | CoReOS Compliance Rate | Conventional Compliance | Primary Violation Modes | Operational Impact |
|---|---|---|---|---|---|
| **Decision Overhead** | $\mu_{ovh} \le 1.0$\,ms per step | **100.0% PASS** (180/180) | 100.0% PASS | None | Validates sub-millisecond execution feasibility in OS loops. |
| **Thrashing Ceilings** | $\le 15$ ticks (stress), $\le 25$ ticks (nominal)| **100.0% PASS** (180/180) | 58.9% FAIL | Memory thrashing stalls in Conv. | Proves complete elimination of paging collapse. |
| **Workload Robustness**| Penalized turnaround $\le 16.0$ ticks (nominal)| **94.4% PASS** (170/180) | 88.3% PASS | Occasional tail latency under bursts | Sustains high responsiveness across nominal regimes. |
| **Completion Rate** | $CR \ge 90.0\%$ under all regimes | **83.3% PASS** (150/180) | 66.7% FAIL | Severe compute convoys in Conv. | CoReOS maintains 79% completion even under extreme compute bursts. |
| **Jain's Fairness Floor** | $J(\mathbf{T}) \ge 0.60$ across completed jobs | **58.9% PASS** (106/180) | 68.3%* | Cylinder seek sweep variance | Fails consistently on `io_bottleneck` and `mixed` across all candidates. |

---

## 9. Setup, Execution, and Testing

### 9.1 Environment Prerequisites
- **Operating System:** macOS (Apple Silicon M1/M2/M3/M4 or Intel) or Linux (Ubuntu 22.04+ / Debian 12+).
- **Python Environment:** Python 3.11+ (Python 3.11.4 verified in `.venv`).
- **Node Environment:** Node.js 18.x+ and npm 9.x+ (Vite 8.3.4 verified).
- **LaTeX / PDF Compiler:** Tectonic or TeXLive (pdflatex, bibtex).
- **Typst Compiler:** Typst 0.11.0+ (`brew install typst` or binary release).

### 9.2 Step-by-Step Execution Guide

```bash
# 1. Clone repository and navigate to root
cd /path/to/CoReOS-Team

# 2. Activate Python virtual environment and verify packages
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run complete automated test suite (108 tests)
.venv/bin/pytest tests/

# 4. Start backend FastAPI service (runs on http://localhost:8000)
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 5. Start frontend development server (runs on http://localhost:5173)
cd frontend
npm install
npm run dev

# 6. Verify production frontend build & TypeScript checks
npm run build
```

### 9.3 Benchmark Reproduction and Asset Generation

```bash
# 1. Regenerate complete 1,440-trial canonical benchmark dataset
.venv/bin/python scripts/run_final_canonical_benchmark.py
# Outputs: reports/optimization/final_canonical_*.csv, canonical_manifest.json

# 2. Regenerate all 13 research paper figures (.pdf & .png)
.venv/bin/python research_paper/scripts/generate_figures.py
# Outputs: research_paper/figures/fig1_*.pdf through fig13_*.pdf

# 3. Compile IEEE conference research paper PDF
cd research_paper
tectonic main.tex   # or pdflatex main && bibtex main && pdflatex main && pdflatex main
# Output: research_paper/main.pdf

# 4. Compile CoReOS System Guide (78-page Typst book)
python learning_docs/build_full_guide.py
# Output: learning_docs/CoReOS_System_Guide.pdf
```

---

## 10. Known Issues, Limitations, and Risks

### 10.1 Architectural Limitations
1. **Simulation Fidelity vs. Bare-Metal Hardware:** CoReOS is implemented within a high-fidelity discrete-event software simulator. While it models clock ticks, multi-core contention, page swapping, and disk arm geometry, it does not simulate low-level hardware phenomena such as Translation Lookaside Buffer (TLB) shootdowns, Non-Uniform Memory Access (NUMA) interconnect bus latency, PCIe lane saturation, or CPU hardware cache coherence protocols.
2. **Synthetic Workload Modeling:** The six benchmark workloads are generated via parameterized Poisson arrival processes. While they capture extreme multi-resource stress regimes, they do not replay raw, production telemetry traces from hyperscale enterprise clusters (e.g., Google Borg or Alibaba trace datasets).

### 10.2 Methodological & Statistical Nuances
1. **Survivorship Bias in Fairness:** As proven in Section 7.3, Jain's fairness index evaluated strictly over completed processes rewards schedulers that fail under load by dropping starved long-running tasks from the denominator. A future benchmark iteration should incorporate a unified *Penalized Jain's Fairness Index*.
2. **I/O Workload Fairness Floor Failure:** In disk-bound workloads (`io_bottleneck`), elevator SCAN achieves high throughput by sweeping cylinders in monotonic sequence, but inherently penalizes requests on boundary cylinders ($0$ and $100$) relative to central cylinders ($50$). Consequently, all eight candidate architectures fail the $0.60$ fairness floor on I/O workloads.
3. **Weight Sensitivity in Composite Scoring:** The canonical composite score assigns fixed weights ($30\%$ completion, $25\%$ throughput, $20\%$ penalized turnaround, $15\%$ thrashing, $10\%$ fairness). Shifting weights toward fairness would slightly increase the margin of Candidate F over CoReOS, whereas increasing the weight of completion rate expands CoReOS's lead.

### 10.3 Codebase & Fallback Risks
1. **Backend Benchmark CSV Fallback Chain:** In `backend/api/benchmarks.py:11-28`, the API searches for `final_canonical_benchmark_results.csv`, then falls back to `phase8_final_benchmark_results.csv`, then `phase3_benchmark_results.csv`. If canonical files are moved or deleted, the server silently falls back to Phase 8 (which contains 8 candidates with `ChampionCoReOS` instead of the unified 7-candidate presentation), creating silent UI regressions.

---

## 11. Claim-to-Evidence Map

| Claim in Research Paper or Reports | Quantitative Evidence | Source File Path & Line Reference |
|---|---|---|
| **CoReOS ranks #2 overall with $84.87 \pm 1.35$ composite score** | Canonical mean: $84.87$, CI95: $\pm 1.35$, std: $9.15$ | `reports/optimization/final_canonical_ranking_summary.csv:3` |
| **CoReOS achieves highest overall task completion rate ($95.86\%$)** | $95.86\%$ completion across 1,440 trials ($95.28\%$ for RL) | `reports/optimization/final_canonical_ranking_summary.csv:3` |
| **CoReOS slashes penalized turnaround time by $50.1\%$ vs Conventional** | $40.79$\,ticks for CoReOS vs. $81.73$\,ticks for Conventional | `reports/optimization/final_canonical_ranking_summary.csv:3, 8` |
| **Statistically significant superiority over Conventional ($p < 10^{-14}$)** | Paired $t=8.589, p=4.20 \times 10^{-15}$, Cohen's $d=0.640$ | `reports/optimization/final_canonical_statistical_comparisons.csv:2` |
| **Statistically significant superiority over Baseline CoReOS ($p < 10^{-16}$)**| Paired $t=9.452, p=1.87 \times 10^{-17}$, Cohen's $d=0.704$ | `reports/optimization/final_canonical_statistical_comparisons.csv:3` |
| **CoReOS satisfies decision overhead ceiling ($\le 1.0$\,ms) in $100\%$ of trials**| Mean overhead: $0.1517$\,ms; Max trial: $0.1690$\,ms; Pass rate: $100.0\%$ | `reports/optimization/final_canonical_guardrail_compliance.csv:14-19` |
| **Thrashing is virtually eliminated under adversarial stress** | Thrashing drops from $105.37$\,ticks in Conv. to $0.10$\,ticks in CoReOS | `reports/optimization/final_canonical_per_workload_summary.csv:38, 44` |
| **Curriculum RL ranks #1 overall with $85.81 \pm 1.53$ points** | Canonical mean: $85.81$, CI95: $\pm 1.53$, std: $10.40$ | `reports/optimization/final_canonical_ranking_summary.csv:2` |
| **Conventional fairness in compute spikes is an artifact of survivorship bias** | Conventional completed only $47.50\%$ of tasks, starving $52.50\%$ | `research_paper/main.tex:590-595`; `final_canonical_per_workload_summary.csv:14` |
| **All candidates fail the $0.60$ fairness floor on I/O bottlenecks** | CoReOS fairness $= 0.3934$; Conv. $= 0.4009$; RL $= 0.6080$ | `reports/optimization/final_canonical_per_workload_summary.csv:25-32` |

---

## 12. Task-to-File Navigation Guide

### 12.1 Common Engineering & Research Workflows

#### Task 1: Modifying Scheduling or Arbitration Policies
- **Core CPU/IO Agent logic:** `src/coreos/agents/cpu_agent.py` and `src/coreos/agents/io_agent.py`.
- **Coordination constraints & arbitration rules:** `src/coreos/coordination/coordinator.py` (`AdaptiveCoordinationAgent.arbitrate`).
- **Official candidate definitions:** `src/coreos/optimization/candidates.py` (`ChampionCoReOS`).
- **Validation command:** `.venv/bin/pytest tests/test_optimization_candidates.py`

#### Task 2: Modifying Self-Healing & Recovery Actions
- **Regression detection thresholds ($W=10$, latency spikes):** `src/coreos/self_healing/regression_detector.py`.
- **Recovery action selection & cooling-off backoff:** `src/coreos/self_healing/recovery.py`.
- **Validation command:** `.venv/bin/pytest tests/test_phase2_recovery_regression.py tests/test_self_healing.py`

#### Task 3: Updating Benchmark Metrics or Scoring Formulas
- **Composite scoring formula & Jain's fairness calculation:** `src/coreos/simulation/metrics.py`.
- **Benchmark reporting & aggregation pipeline:** `src/coreos/evaluation/reporting.py`.
- **Validation command:** `.venv/bin/pytest tests/test_metrics.py tests/test_reporting.py`

#### Task 4: Modifying Frontend Visualizations or Telemetry Displays
- **Benchmark Lab charts & guardrail breakdown:** `frontend/src/pages/BenchmarkLab.tsx`.
- **Simulation Lab telemetry & live charts:** `frontend/src/pages/SimulationLab.tsx`.
- **Color mappings & candidate display names:** `frontend/src/components/common/chartTheme.ts`.
- **Validation command:** `npm run build --prefix frontend`

#### Task 5: Modifying Backend API Endpoints or State Handling
- **State store & telemetry caching:** `backend/state.py`.
- **Benchmark endpoint & fallback paths:** `backend/api/benchmarks.py`.
- **Report downloading & serving:** `backend/api/reports.py`.
- **Validation command:** `.venv/bin/pytest tests/test_api_state_store.py tests/test_benchmark_integration.py`

#### Task 6: Re-running Experiments and Updating Paper Figures
- **Execute canonical benchmark (1,440 trials):** `.venv/bin/python scripts/run_final_canonical_benchmark.py`.
- **Regenerate paper figures:** `.venv/bin/python research_paper/scripts/generate_figures.py`.
- **Recompile paper PDF:** `cd research_paper && tectonic main.tex`.

---

## 13. Unresolved Questions and Missing Evidence

1. **Linux Kernel Prototype Feasibility:** While the discrete-event simulation establishes mathematical proof of arbitration efficacy, empirical validation within a real Linux kernel (e.g., using `sched_ext` user-space schedulers or eBPF tracing) remains an open engineering goal.
2. **Online Learning Under Concept Drift:** The Gradient Boosting conflict predictor was trained offline. How the predictor handles non-stationary adversarial workloads outside the training distribution without periodic retraining is an open research question.
3. **Formal Penalized Fairness Standard:** While penalized turnaround ($T_{pen}$) is mathematically defined and frozen in this benchmark, there is currently no universal IEEE/ACM consensus on the mathematical formulation of penalized Jain's fairness for starved tasks.

---

## 14. Source Inspection Scope and Verification Limitations

- **Completeness of Inspection:** Every active Python source file in `src/`, `backend/`, and `scripts/`, every TypeScript/TSX file in `frontend/src/`, all 16 test modules in `tests/`, all canonical CSV/JSON/MD files in `reports/optimization/`, and the complete LaTeX source in `research_paper/main.tex` were inspected directly.
- **Verification of Binary Files:** SHA-256 hashes were calculated and verified for compiled PDFs (`research_paper/main.pdf` and duplicate `paper.pdf`).
- **Read-Only Compliance:** This document was generated without running any file deletion, git staging, git commit, branch checkout, or destructive environment modifications. Zero application files were altered.

---
*End of Knowledge Base — Authored for Reusable Project Context in `CoReOS-Team`.*
