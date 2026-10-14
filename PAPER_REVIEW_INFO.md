# CoReOS-Team — Comprehensive Project Reference & Academic Knowledge Base

> **File:** `PAPER_REVIEW_INFO.md`  
> **Repository:** `CoReOS-Team` (Branch: `main`)  
> **Inspected Git Commit:** `8eef6484b2e792bd212a9013128f0ab03c4bba99`  
> **Last Verification Date:** 2026-10-14  
> **Reviewed Paper Artifact:** `research_paper/main.pdf` (987,039 bytes, 21 pages, compiled with Tectonic / `xdvipdfmx (0.1)` on 2026-10-14 00:35:28 UTC)  
> **Document Purpose:** Audited, reusable, single-source-of-truth knowledge base for research-paper review, architectural analysis, engineering development, benchmark verification, debugging, and academic reproduction.  
> **Inspection Basis:** Strict read-only audit of all 146 project entities, active source code, discrete-event simulation engine, FastAPI backend, React dashboard, canonical benchmark datasets (1,440 trials across 8 candidates, 6 workloads, and 30 seeds), IEEE conference paper sources (`research_paper/main.tex`), and test suites.

---

### Evidence Status Legend

To maintain strict scientific integrity, claims and metrics throughout this document are annotated with explicit evidence labels:
- **`[Verified]`:** Directly verified against active implementation, canonical benchmark CSVs, test outputs, or reproducible mathematical calculations.
- **`[Documented, not independently verified]`:** Recorded in an existing paper, report, or comment, but lacks independent experimental or mathematical confirmation in the repository.
- **`[Inferred]`:** A reasoned analytical interpretation rather than a directly measured metric.
- **`[Unresolved]`:** Conflicting, missing, or insufficient evidence in the repository prevents an authoritative conclusion.

---

## 1. Quick Reference and Table of Contents

### 1.1 Executive Snapshot
- **System Identity:** **CoReOS** (*Conflict-Aware, Resource-Arbitrated Operating System*).
- **Core Paradigm:** Discrete-event multi-agent operating system simulation framework orchestrating specialized domain control agents (CPU, Memory, Storage I/O) via an adaptive, conflict-aware coordination core and closed-loop proportional self-healing engine. `[Verified]`
- **Technology Stack:** Python 3.11.4, FastAPI 0.143.0, React 18.3.1 (React 19 in frontend manifest), TypeScript 5.6.2, Vite 8.3.0+, Plotly.js, Scikit-Learn 1.9.1, SciPy 1.17.1, Pytest 9.1.1, IEEE LaTeX (`IEEEtran.cls`), Typst 0.11+. `[Verified]`
- **Canonical Evaluation Dataset:** Exactly **1,440 matched simulation trials** across **8 candidate architectures**, **6 operational workloads**, and **30 fresh held-out pseudo-random seeds** (`[5001..5030]`) with a 300-tick evaluation horizon (`reports/optimization/final_canonical_benchmark_results.csv`). `[Verified]`
- **Authoritative Competition Standing:**
  - **Rank #1 (Composite Winner):** `F_ImprovedRL` (Curriculum Adaptive RL): Composite Score **$85.81 \pm 1.53$**, Completion Rate $95.28\%$, Overhead **$0.0030$\,ms**. `[Verified]`
  - **Rank #2 (Official Primary System):** `CoReOS` (`G_ChampionCoReOS`): Composite Score **$84.87 \pm 1.35$**, Completion Rate **$95.86\%$** (highest overall across all candidates), Penalized Turnaround $40.79$\,ticks, Thrashing $0.02$\,ticks, Decision Overhead $0.1517$\,ms ($100\%$ compliance with $\le 1.0$\,ms ceiling). `[Verified]`
  - **Performance Advantage vs. Conventional Baselines:** Statistically decisive separation over conventional static Round-Robin (+10.58 composite points, paired $t=8.589, p=4.20 \times 10^{-15}, p_{holm}=7.56 \times 10^{-14}$, Cohen's $d=0.640$) and historical Complete CoReOS (+9.41 points, $t=9.452, p=1.87 \times 10^{-17}, p_{holm}=4.31 \times 10^{-16}$, $d=0.704$). `[Verified]`
  - **CoReOS vs. Curriculum RL Standing:** Curriculum RL holds a $+0.934$ composite score margin over CoReOS ($85.81$ vs. $84.87$; $t=4.422, p=1.69 \times 10^{-5}, p_{holm}=1.52 \times 10^{-4}$, $d=0.330$). While statistically significant across the 180 paired observations, the practical gap is small ($< 1.1\%$ relative difference), and CoReOS achieves superior completion rate ($95.86\%$ vs. $95.28\%$). `[Verified]`
  - **Thrashing Reduction under Stress:** Under severe `adversarial_stress`, thrashing falls from $105.37$\,ticks in Conventional to $0.10$\,ticks in CoReOS—representing an exact **$99.9\%$ reduction** ($\frac{105.37 - 0.10}{105.37} = 99.905\%$). `[Verified]`
- **Test Baseline:** **108 passed out of 108 tests** (`.venv/bin/pytest tests/`) across 16 test modules in 6.75s. `[Verified]`
- **Frontend Build Status:** TypeScript checks and Vite production bundle build succeed with **0 errors**. `[Verified]`

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
10. [Research Validity, Limitations, and Methodological Critique](#10-research-validity-limitations-and-methodological-critique)
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
- **Domain Agents (`src/coreos/agents/` and `src/coreos/optimization/candidates.py`):** Autonomous control agents that observe localized subsystem telemetry and formulate action proposals:
  - `WorkloadAwareCPUAgent`: Dynamically switches between Round-Robin ($q=4.0, 6.0$) and Shortest Remaining Time First (SRTF, $q=8.0$) based on ready-queue backlog, active load, and CPU utilization, with a guard preventing SRTF deployment on pure I/O workloads. `[Verified]`
  - `MemoryAgent`: Adjusts memory reclamation targets based on physical utilization ratios and page-fault rates ($1,024$\,MB to $4,096$\,MB). `[Verified]`
  - `WorkloadAwareIOAgent`: Mandates elevator SCAN over FCFS when storage queues accumulate requests ($|\mathcal{Q}_{io}| \ge 2 \lor \sigma_{io} \ge 30\%$) to prevent mechanical cylinder starvation. `[Verified]`
- **Adaptive Coordination Agent (`src/coreos/coordination/`):** Centralized arbiter enforcing deterministic cross-resource safety constraints, the *I/O Congestion Shield*, and *Memory-CPU Coupling Invariants*. `[Verified]`
- **Calibrated Conflict Engine (`src/coreos/conflict_prediction/`):** Machine-learning inference module coupling deterministic cascade rules with a 50-tree Gradient Boosting Classifier to predict imminent multi-resource saturation. `[Verified]`
- **Performance Regression Detector & Proportional Recovery Engine (`src/coreos/self_healing/`):** Closed-loop self-healing mechanism that detects throughput collapse, latency spikes, and thrashing over a sliding window ($W=10$), deploying graduated interventions with exponential cooling-off periods. `[Verified]`
- **Penalized Turnaround Time ($T_{pen}$):** A metric engineered to penalize uncompleted tasks at the simulation horizon ($T_{max}=300.0$\,ticks) via an explicit cutoff penalty ($\Pi = 300.0$\,ticks). Observations show this counteracts *survivorship bias* where unpenalized averages artificially reward schedulers that drop long jobs. `[Verified]`
- **Jain's Fairness Index ($J(\mathbf{T})$):** Standard normalized fairness metric evaluated across turnaround times. `[Verified]`

### 2.3 Current Implementation Status
- **Operating-System Simulation Core:** Complete, fully operational discrete-event engine in `src/simulation/` and `src/coreos/simulation/`. `[Verified]`
- **Backend Application Service:** Complete FastAPI service in `backend/` exposing simulation control, real-time telemetry, conflict analysis, self-healing status, dataset exploration, benchmark summaries, and report downloads. `[Verified]`
- **Interactive Dashboard:** Complete React SPA in `frontend/` featuring 8 pages, Carbon dark styling, Plotly.js charts, and live websocket/event polling. `[Verified]`
- **Empirical Benchmark Suite:** Complete 1,440-trial canonical benchmark in `reports/optimization/final_canonical_benchmark_results.csv` with SHA-256 integrity manifest. `[Verified]`
- **Academic Paper Package:** Complete 21-page IEEE conference-style paper in `research_paper/main.tex`, compiled to `main.pdf` (987,039 bytes, 21 pages), accompanied by 13 vector figures, 4 screenshots, and verified BibTeX references (`references.bib`). `[Verified]`
- **Comprehensive Documentation:** Complete 78-page system guide in `learning_docs/CoReOS_System_Guide.typ`, compiled to `CoReOS_System_Guide.pdf`, with modular chapter generation scripts. `[Verified]`

### 2.4 Implemented Features vs. Research Claims vs. Non-Claims
- **What CoReOS IS:** An advanced, high-fidelity discrete-event operating-system simulation framework and research platform for evaluating multi-agent arbitration, conflict prediction, and self-healing algorithms against standard scheduling baselines. `[Verified]`
- **What CoReOS IS NOT:**
  - It is **NOT** a native Linux kernel patch, C-based kernel module, eBPF program, or production OS distribution. All scheduling decisions operate in a Python discrete-event simulation model. `[Verified]`
  - It is **NOT** a Large Language Model (LLM) agent orchestrator or Retrieval-Augmented Generation (RAG) system. All agents evaluate numerical vectors and discrete scheduling actions. `[Verified]`
  - Python simulator execution overhead ($0.1517$\,ms) cannot be equated with real-world operating system kernel interrupt latency. Real kernels require sub-microsecond dispatch cycles. `[Inferred]`

---

## 3. Architecture and Technology Stack

### 3.1 Architectural Layering

```
+-----------------------------------------------------------------------------------+
|                           USER PRESENTATION LAYER                                 |
|      React SPA + TypeScript + Vite 8.3.0+ (Carbon Dark Design System)             |
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
|  - WorkloadAwareCPUAgent (q=4/6/8, RR vs SRTF progress drain, non-I/O guard)      |
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

| Layer | Component | Declared Version | Role in Project | Configuration File | Evidence Status |
|---|---|---|---|---|---|
| **Simulation** | Python | 3.11.4 | Core language for simulation and algorithms | `pyproject.toml`, `requirements.txt` | `[Verified]` |
| **Numerical/Stats** | NumPy | 2.4.6 | Array processing, histogram distributions | `requirements.txt` | `[Verified]` |
| **Data Engine** | Pandas | 3.0.6 | Benchmark data processing, summaries | `requirements.txt` | `[Verified]` |
| **Scientific Computing** | SciPy | 1.17.1 | Student's t-test, Wilcoxon, confidence intervals | `requirements.txt` | `[Verified]` |
| **Machine Learning** | Scikit-Learn | 1.9.1 | Gradient Boosting, Random Forest, ROC-AUC | `requirements.txt` | `[Verified]` |
| **Backend API** | FastAPI | 0.143.0 | Asynchronous REST API framework | `backend/main.py` | `[Verified]` |
| **ASGI Server** | Uvicorn | 0.54.0 | High-performance ASGI web server | `backend/main.py` | `[Verified]` |
| **Frontend Framework**| React | 18.3.1 (19.2 in manifest) | Single-page UI framework | `frontend/package.json` | `[Verified]` |
| **Language** | TypeScript | ~6.0.2 / 5.6.2 | Strict typed frontend implementation | `frontend/package.json` | `[Verified]` |
| **Build Tool** | Vite | ^8.3.0 | Development server and production bundler | `frontend/package.json` | `[Verified]` |
| **Runtime Requirement**| Node.js | 18+ (inferred from Vite 8) | Runtime prerequisite for frontend build tooling | `frontend/package.json` (no `engines` pin) | `[Inferred]` |
| **Visualization** | Plotly.js | 4.1.2 / 2.35.2 | Interactive Cartesian, radar, and bar charts | `frontend/package.json` | `[Verified]` |
| **Testing** | Pytest | 9.1.1 | Unit, regression, and integration testing | `pyproject.toml` | `[Verified]` |
| **Paper Typesetting** | LaTeX / Tectonic | Tectonic (`xdvipdfmx`) | IEEE conference manuscript generation | `research_paper/main.tex` | `[Verified]` |
| **Documentation** | Typst | 0.11+ | Modern publication-quality system guide | `learning_docs/CoReOS_System_Guide.typ`| `[Verified]` |

### 3.3 Hardware Simulation Configuration Parameters

| Subsystem | Parameter Symbol | Configuration Value | Physical Meaning / Impact | Source Location | Evidence Status |
|---|---|---|---|---|---|
| **CPU** | $N_c$ | 4 cores | Number of simulated symmetrical processor cores | `src/coreos/config.py:16` | `[Verified]` |
| **CPU** | $q_{def}$ | 4.0 ticks | Default round-robin scheduling quantum | `src/coreos/config.py:17` | `[Verified]` |
| **CPU** | $\delta_{cs}$ | 0.5 ticks | Context switch execution penalty charged to CPU | `src/simulation/cpu_subsystem.py:22` | `[Verified]` |
| **Memory** | $M_{phys}$ | 16,384 MB (16 GB) | Physical RAM boundary before swapping occurs | `src/coreos/config.py:24` | `[Verified]` |
| **Memory** | $M_{swap}$ | 8,192 MB (8 GB) | Secondary swap partition size | `src/coreos/config.py:25` | `[Verified]` |
| **Memory** | $\theta_{press}$ | 0.85 (85%) | Memory utilization threshold triggering pressure | `src/coreos/config.py:26` | `[Verified]` |
| **Memory** | Thrashing Boundary | $\mu_m \ge 0.92 \land \text{swap} > 5\%$ | Threshold defining destructive page thrashing | `research_paper/main.tex:141` | `[Verified]` |
| **Memory** | $\delta_{pf}$ | 5.0 ticks | Latency penalty for servicing a page fault | `src/simulation/memory_subsystem.py:28` | `[Verified]` |
| **Storage I/O** | $N_{io}$ | 2 channels | Concurrently serviced block storage channels | `src/simulation/io_subsystem.py:20` | `[Verified]` |
| **Storage I/O** | $K_{io}$ | 50 requests | Queue capacity before I/O requests are rejected | `src/simulation/io_subsystem.py:21` | `[Verified]` |
| **Storage I/O** | $d_{io}$ | 3.0 ticks | Base data transfer latency per I/O burst | `src/simulation/io_subsystem.py:22` | `[Verified]` |
| **Storage I/O** | Cylinder Range | $[0, 100]$ cylinders | Seek distance range for elevator SCAN modeling | `src/simulation/io_subsystem.py:23` | `[Verified]` |
| **Horizon** | $T_{max}$ | 300.0 ticks | Fixed simulation execution cutoff | `src/coreos/config.py:32` | `[Verified]` |
| **Horizon** | $\Pi$ | 300.0 ticks | Turnaround penalty charged for unfinished jobs | `src/coreos/simulation/metrics.py:44` | `[Verified]` |

---

## 4. Directory and File Reference

### 4.1 Root Structure
```text
CoReOS-Team/
├── backend/                       # FastAPI application service & state store
├── frontend/                      # React SPA + TypeScript + Vite web dashboard
├── learning_docs/                 # Typst system guide & modular generation scripts
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

| Relative Path | Key Symbols / Classes | Primary Functional Responsibility | Evidence Status |
|---|---|---|---|
| `backend/main.py` | `app`, FastAPI router mounts | Application entry point; attaches CORS, registers routers, mounts `/api/*`. | `[Verified]` |
| `backend/state.py` | `SystemStateStore`, `state_store` | Centralized, thread-safe state repository; caches simulation runs, telemetry, conflicts, and healing records. | `[Verified]` |
| `backend/api/benchmarks.py` | `get_benchmarks()`, fallback logic | Serves candidate rankings, raw trials, per-workload heatmaps; handles 7 active vs. 8 canonical candidate separation. | `[Verified]` |
| `backend/api/overview.py` | `get_overview()` | Serves top-level dashboard telemetry, baseline comparisons, and system health status. | `[Verified]` |
| `backend/api/reports.py` | `get_ablation_summary()`, `download_report()` | Serves live ablation study summary and streams validated benchmark CSV downloads. | `[Verified]` |
| `backend/api/simulation.py` | `run_simulation()`, `get_latest_simulation()` | Executes discrete-event simulation runs; supports settings persistence across page navigation. | `[Verified]` |
| `backend/api/agents.py` | `get_agent_decisions()` | Serves step-by-step audit trail of agent proposals, coordinator overrides, and explanations. | `[Verified]` |
| `backend/api/conflicts.py` | `get_conflict_analysis()` | Serves conflict detection rate, cascade taxonomy, precision/recall metrics, and timeline trends. | `[Verified]` |
| `backend/api/healing.py` | `get_healing_metrics()` | Serves self-healing recovery actions, strategy distribution, success rates, and latency. | `[Verified]` |
| `backend/api/dataset.py` | `get_dataset_info()`, `train_anomaly_baseline()` | Profiles 10,000-row telemetry dataset; trains Random Forest anomaly detector and returns ROC-AUC/F1. | `[Verified]` |
| `src/coreos/agents/base.py` | `BaseResourceAgent`, `AgentAction` | Abstract base class establishing standardized proposal protocol for domain agents. | `[Verified]` |
| `src/coreos/agents/cpu_agent.py` | `CPUAgent` | Baseline heuristic agent adjusting Round-Robin quantum ($q=2, 4, 8$) strictly on ready-queue depth ($>0, >5, >15$). | `[Verified]` |
| `src/coreos/agents/memory_agent.py` | `MemoryAgent` | Monitors physical RAM utilization $\mu_m(t)$; calculates dynamic reclamation targets ($1,024$\,MB to $4,096$\,MB). | `[Verified]` |
| `src/coreos/agents/io_agent.py` | `IOAgent` | Baseline heuristic agent selecting SCAN ($\ge 25$), SSTF ($\ge 8$), or FCFS ($<8$) based on queue depth. | `[Verified]` |
| `src/coreos/optimization/candidates.py` | `WorkloadAwareCPUAgent`, `WorkloadAwareIOAgent`, `ChampionCoReOS` | Implements the official Champion CoReOS domain agents and wrappers for comparative benchmark candidates. | `[Verified]` |
| `src/coreos/coordination/coordinator.py`| `CoordinationAgent`, `AdaptiveCoordinationAgent` | Master arbitration core; enforces I/O Congestion Shield, memory-CPU coupling, and safety invariants. | `[Verified]` |
| `src/coreos/coordination/constraints.py`| `SafetyConstraints` | Deterministic bounding checks ensuring quantum, reclamation, and I/O policies remain in valid ranges. | `[Verified]` |
| `src/coreos/conflict_prediction/predictor.py`| `ConflictPredictor`, `CalibratedConflictEngine` | Evaluates 10-feature system state using Gradient Boosting Classifier to predict cascade failure modes. | `[Verified]` |
| `src/coreos/conflict_prediction/conflict_log.py`| `ConflictLog` | Tracks conflict history, calculates confusion matrix metrics (precision, recall, F1, FPR). | `[Verified]` |
| `src/coreos/self_healing/regression_detector.py`| `PerformanceRegressionDetector` | Sliding-window ($W=10$) detector identifying throughput collapse, latency spikes, and thrashing. | `[Verified]` |
| `src/coreos/self_healing/recovery.py` | `RecoveryEngine`, `ProportionalRecoveryEngine` | Dispatches graduated interventions (quantum expansion, SRTF queue drain, deep swap) with cooling-off backoff. | `[Verified]` |
| `src/coreos/learning/adaptive_rl.py` | `AdaptiveRLAgent`, `ImprovedRLCandidate` | Curriculum Q-learning candidate; projects state into 54 discrete bins; evaluates with Manhattan nearest-neighbor. | `[Verified]` |
| `src/coreos/simulation/environment.py` | `CoReOSEnvironment` | Discrete-event simulation execution loop orchestrating clock ticks, agents, coordinator, and hardware. | `[Verified]` |
| `src/coreos/simulation/metrics.py` | `SimulationMetrics`, `calculate_jains_fairness` | Calculates composite scores ($S$), penalized turnaround ($T_{pen}$), Jain's fairness ($J$), and overhead. | `[Verified]` |
| `src/coreos/simulation/process.py` | `Process`, `ProcessState` | Process lifecycle model; encapsulates states, remaining burst, memory footprint, and I/O sequence. | `[Verified]` |
| `src/coreos/simulation/workload.py` | `WorkloadGenerator` | Generates reproducible process arrival sequences across the 6 standardized workload profiles. | `[Verified]` |
| `src/simulation/simulator.py` | `Simulator` | Root discrete-event simulation orchestrator advancing hardware components tick-by-tick. | `[Verified]` |
| `src/simulation/cpu_subsystem.py` | `CPUSubsystem` | Simulates 4 cores, time-slice preemption, context-switch accounting, and ready queue management. | `[Verified]` |
| `src/simulation/memory_subsystem.py` | `MemorySubsystem` | Simulates physical RAM frames, page swapping, allocation limits, and page-fault latency injection. | `[Verified]` |
| `src/simulation/io_subsystem.py` | `IOSubsystem` | Simulates dual-channel storage controller, 50-slot request queue, and mechanical cylinder movement. | `[Verified]` |
| `scripts/run_final_canonical_benchmark.py` | `run_benchmark()` | Master benchmark runner; executes 1,440 trials, computes statistics, and generates canonical CSV artifacts. | `[Verified]` |
| `research_paper/scripts/generate_figures.py` | `generate_all_figures()` | Generates all 13 publication figures (.pdf and .png) directly from canonical benchmark CSVs. | `[Verified]` |

---

## 5. Core Implementation and Data Flow

### 5.1 Discrete-Event Simulation Lifecycle
The discrete-event execution loop advances in discrete time steps ($\Delta t = 1.0$\,tick) up to $T_{max} = 300.0$\,ticks:
1. **Clock Synchronization:** Virtual clock advances to $t$. Arriving processes whose arrival tick $a_i \le t$ are evaluated. If free physical RAM $\ge M_i$, memory frames are assigned and process state transitions $\text{PENDING} \to \text{READY}$. Otherwise, the process transitions to $\text{WAITING\_MEM}$.
2. **State Vector Observation:** The global system state $\mathbf{x}(t)$ is extracted, encapsulating core utilization, physical/swap RAM usage, ready/memory/IO queue lengths, context switches, and page faults.
3. **Autonomous Agent Proposals:**
   - **WorkloadAwareCPUAgent (`src/coreos/optimization/candidates.py:250-290`):**
     Evaluates ready queue depth $|\mathcal{Q}_{ready}|$, waiting memory count $|\mathcal{Q}_{mem}|$, storage queue depth $|\mathcal{Q}_{io}|$, CPU utilization $\mu_{cpu}$, memory utilization $\mu_m$, and total active load $L_{act} = |\mathcal{Q}_{ready}| + |\mathcal{Q}_{mem}| + |\mathcal{Q}_{io}|$.
     - *Pure I/O Guard:* Identifies pure I/O workloads via:
       $$\text{is\_pure\_io} = \left(|\mathcal{Q}_{io}| > |\mathcal{Q}_{ready}|\right) \land \left(\mu_m < 75.0\%\right) \land \left(|\mathcal{Q}_{mem}| == 0\right) \land \left(\mu_{cpu} < 75.0\%\right)$$
     - *SRTF Progress Drain Branch:* If $\neg \text{is\_pure\_io}$ and $\left(|\mathcal{Q}_{ready}| \ge 3 \lor (L_{act} \ge 4 \land |\mathcal{Q}_{ready}| \ge 2) \lor \mu_{cpu} \ge 85.0\%\right)$, proposes **SRTF** with $q=8.0$.
     - *Moderate Load Branch:* Elif $L_{act} > 2 \lor |\mathcal{Q}_{ready}| > 1$, proposes **Round-Robin** with $q=6.0$.
     - *Light Load Branch:* Otherwise, proposes **Round-Robin** with $q=4.0$.
   - **MemoryAgent (`src/coreos/agents/memory_agent.py`):**
     Evaluates physical utilization $\mu_m(t)$. If $\mu_m \ge 0.85$, proposes emergency reclamation $R_{target} = 2,048$\,MB; if $\mu_m \ge 0.60$, proposes $R_{target} = 1,024$\,MB.
   - **WorkloadAwareIOAgent (`src/coreos/optimization/candidates.py:320-355`):**
     Evaluates storage backlog $|\mathcal{Q}_{io}|$ and saturation $\sigma_{io}$. If $|\mathcal{Q}_{io}| \ge 2 \lor \sigma_{io} \ge 30\%$, proposes elevator **SCAN**; otherwise, **FCFS**.
4. **Adaptive Cross-Resource Arbitration:**
   - Safety constraints clamp proposals to valid parameter envelopes.
   - The *I/O Congestion Shield* forces elevator SCAN if storage queues backlog, preventing disk head thrashing.
   - The *Memory-CPU Coupling Invariant* enforces $q \ge 8.0$ and $R_{target} \ge 2,048$\,MB when $\mu_m \ge 0.80$, while strictly preserving SRTF queue draining if already deployed.
   - The *Calibrated Conflict Engine* evaluates the 10-feature state vector $\mathbf{f}(t)$. If a cascade hazard is predicted, suggested arbitration overrides are applied.
5. **Self-Healing Regression Detection & Recovery:**
   - The Regression Detector tracks moving averages of throughput, p95 latency, and thrashing over window $W=10$.
   - If a regression event fires (`THRASHING_STALL`, `THROUGHPUT_COLLAPSE`, `LATENCY_SPIKE`), the Proportional Recovery Engine issues graduated overrides (elevating reclamation to $4,096$\,MB and deploying SRTF queue clearing) subject to exponential cooling-off periods ($T_{cool} = T_{base} \cdot (1 + \text{retries})$).
6. **Hardware Subsystem Step:**
   - CPU advances running processes on active cores. If a process experiences thrashing, execution advances with slowdown factor $\omega_{slow} = 2.0$. Finished tasks release RAM and record completion tick $C_i = t$.
   - Yielded tasks requiring I/O transition to $\text{WAITING\_IO}$ and enter the storage queue.
   - Storage channels advance disk head toward target cylinders using the active policy (SCAN or FCFS), returning completed processes to the CPU ready queue.
7. **Metric Consolidation:** Turnaround, waiting times, throughput, and thrashing are logged. Unfinished processes are penalized at $T_{max}$ via $\Pi = 300.0$\,ticks.

---

## 6. APIs and Frontend Behavior

### 6.1 Backend API Endpoint Specification

| Endpoint Route | Method | Request Payload | Response Schema Summary | Active Backend Source | Calling Frontend Component | Evidence Status |
|---|---|---|---|---|---|---|
| `/api/overview/` | GET | None | `{dataset_records, evaluated_baselines, decision_latency, turnaround_improvement, stress_comparison, highlights, telemetry, health}` | `backend/api/overview.py` | `frontend/src/pages/Overview.tsx` | `[Verified]` |
| `/api/simulation/latest` | GET | None | `{config: {workload_type, num_processes, policy_mode, seed, sim_quantum}, result: {history, state}, is_completed: bool}` | `backend/api/simulation.py` | `frontend/src/pages/SimulationLab.tsx` | `[Verified]` |
| `/api/simulation/run` | POST | `{workload_type, num_processes, policy_mode, seed, sim_quantum}` | `{history: [...], state: {cpu_util, mem_util, turnaround, waiting, throughput, switches, completion_rate}, workload_info}` | `backend/api/simulation.py` | `frontend/src/pages/SimulationLab.tsx` | `[Verified]` |
| `/api/agents/` | GET | None | `{records: [{step, time, cpu_proposed_quantum, coordinated_quantum, mem_reclaim_target, io_policy, conflict_type, arbitration_applied, explanation}], workload_info, total_records}` | `backend/api/agents.py` | `frontend/src/pages/AgentControl.tsx` | `[Verified]` |
| `/api/conflicts/` | GET | None | `{total_conflicts, conflict_rate, resolved_by_healing, avg_resolution_time, distribution: [...], trends: [...], taxonomy, metrics: {precision, recall, f1, fpr}}` | `backend/api/conflicts.py` | `frontend/src/pages/ConflictAnalysis.tsx` | `[Verified]` |
| `/api/healing/` | GET | None | `{total_recoveries, healing_actions, success_rate, avg_recovery_time, active_strategies: [...], strategy_usage, recent_actions: [...]}` | `backend/api/healing.py` | `frontend/src/pages/SelfHealing.tsx` | `[Verified]` |
| `/api/dataset/` | GET | None | `{metadata: {rows, cols, duplicates, anomaly_count, anomaly_percentage}, columns, head: [...], describe: [...], corr_matrix, corr_features, distributions}` | `backend/api/dataset.py` | `frontend/src/pages/DatasetExplorer.tsx` | `[Verified]` |
| `/api/dataset/train` | POST | None | `{metrics: {accuracy, anomaly_f1, roc_auc, classification_report}, feature_importance: [{Feature, Importance}]}` | `backend/api/dataset.py` | `frontend/src/pages/DatasetExplorer.tsx` | `[Verified]` |
| `/api/benchmarks/` | GET | None | `{workloads: [...], candidates: [...], active_candidates: [...], data: [...], overall_ranking: [...], active_ranking: [...], per_workload_summary: [...], source}` | `backend/api/benchmarks.py` | `frontend/src/pages/BenchmarkLab.tsx` | `[Verified]` |
| `/api/reports/ablation_summary` | GET | None | `{data: [{workload, configuration, completion_rate, avg_turnaround_time, throughput, thrashing_ticks}]}` | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` | `[Verified]` |
| `/api/reports/content/{filename}` | GET | URL param | `{filename: str, content: str}` (Streams markdown source for interactive report rendering) | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` | `[Verified]` |
| `/api/reports/download/{filename}` | GET | URL param | File download stream (Enforces whitelist of canonical, Phase 8, and Phase 3 CSV/MD files) | `backend/api/reports.py` | `frontend/src/pages/ResearchReports.tsx` | `[Verified]` |

### 6.2 Frontend Architecture, Seven vs. Eight Candidates, and Navigation
- **Seven vs. Eight Candidate Presentation:**
  - The canonical dataset (`reports/optimization/final_canonical_benchmark_results.csv`) contains **8 candidates** across 1,440 trials. `[Verified]`
  - `backend/api/benchmarks.py` returns all 8 candidates in `candidates` and filters out `E_CompleteCoReOS` to produce `active_candidates` (7 candidates). `[Verified]`
  - `frontend/src/pages/BenchmarkLab.tsx` defaults to displaying the **7 active candidates** (re-ranked 1 through 7 in `active_ranking`), but provides an interactive user toggle: *"Show Historical Baseline (Complete CoReOS v1)"* to expose all 8 candidates. `[Verified]`
  - In `frontend/src/components/common/chartTheme.ts`, candidate `G_ChampionCoReOS` is mapped to display label **`CoReOS`**. `[Verified]`
- **State Persistence:** When users configure a simulation scenario in `SimulationLab.tsx` and navigate across pages, returning to `SimulationLab.tsx` triggers `useEffect` querying `/api/simulation/latest`. Both execution telemetry (`result`) and user input settings (`config`) are restored, preventing unintended parameter resets. `[Verified]`
- **Inter-Page Event Synchronization:** Running a new simulation in `SimulationLab.tsx` dispatches a native browser window event:
  ```typescript
  window.dispatchEvent(new CustomEvent('coreos:simulationCompleted', { detail: { result, config } }));
  ```
  Components such as `AgentControl.tsx` and `SelfHealing.tsx` register event listeners for this signal, refreshing their audit tables when a simulation finishes. `[Verified]`

---

## 7. Research Paper and Academic Contributions

### 7.1 Manuscript Details
- **Title:** *CoReOS: A Conflict-Aware and Self-Healing Multi-Agent Operating System for Coordinated Resource Scheduling* `[Verified]`
- **Format:** IEEE Conference format (`IEEEtran.cls`), double-column. `[Verified]`
- **Source File:** `research_paper/main.tex` (79,009 bytes, 796 lines). `[Verified]`
- **Verified PDF Output:** `research_paper/main.pdf` (987,039 bytes, **21 pages**, compiled via Tectonic with `xdvipdfmx (0.1)` on 2026-10-14 00:35:28 UTC). `[Verified]`
- **Bibliography:** `research_paper/references.bib` (33 peer-reviewed systems and multi-agent citations). `[Verified]`
- **Cross-Reference Validation:** All citations and section references resolve; equations and tables match manuscript text. `[Verified]`

### 7.2 Core Research Questions (RQs) and Verified Findings
1. **RQ1 (Arbitration Efficacy):** Can explicit cross-resource arbitration rules and conflict prediction prevent multi-subsystem interference and improve throughput, completion rate, and turnaround latency compared to uncoordinated agents and round-robin baselines?
   - *Finding:* **Supported.** CoReOS improves composite score by $+10.58$ points ($p_{holm}=7.56 \times 10^{-14}$) over Conventional and $+9.41$ points ($p_{holm}=4.31 \times 10^{-16}$) over uncoordinated/historical baselines. However, Curriculum RL (`F_ImprovedRL`) ranks #1 overall ($85.81 \pm 1.53$ vs. $84.87 \pm 1.35$ for CoReOS), while CoReOS achieves the highest completion rate ($95.86\%$). `[Verified]`
2. **RQ2 (Self-Healing Robustness):** Does graduated proportional self-healing mitigate catastrophic thrashing under severe adversarial stress without introducing oscillatory policy thrashing?
   - *Finding:* **Partially Supported.** Under `adversarial_stress`, thrashing falls from $105.37$\,ticks in Conventional to $0.10$\,ticks in CoReOS—an exact **$99.9\%$ reduction** ($99.905\%$). `[Verified]`  
   - *Methodological Caveat:* The claim that self-healing introduces "no oscillatory policy thrashing" is an **unmeasured qualitative assertion**. No metric in the benchmark logs policy oscillation frequency, state flipping rate, or Lyapunov stability. `[Inferred]`
3. **RQ3 (Computational Feasibility):** Can multi-agent arbitration and machine-learning conflict prediction execute within an operational decision overhead ceiling of $\le 1.0$\,ms per step?
   - *Finding:* **Supported within Simulation Context.** CoReOS averages $0.1517$\,ms per step ($100\%$ compliance across all 180 trials below 1.0\,ms). `[Verified]`  
   - *Methodological Caveat:* This metric reflects Python function execution inside a discrete-event simulator. It **does not demonstrate feasibility in a production operating-system kernel**, where context switch and dispatch routines must execute in $< 1-5\,\mu\text{s}$. `[Inferred]`
4. **RQ4 (Multi-Objective Fairness and Survivorship Bias):** How does multi-resource arbitration affect process fairness, and does conventional unpenalized metric calculation mask severe survivorship bias in starved baselines?
   - *Finding:* **Supported by Empirical Observation.** In Section III-C (Eq. 7-8) and Section VI-D of the paper, evidence shows that Conventional achieves an artificially high unpenalized Jain's fairness ($0.8230$) under `cpu_spike` by completing only $47.50\%$ of tasks and dropping $52.50\%$ from the calculation. Penalizing starved jobs exposes that CoReOS delivers $2\times$ lower true turnaround latency. `[Verified]`

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

| Candidate ID | System Identity | Scheduling Discipline | Memory Reclamation Policy | Storage I/O Policy | Role in Benchmark | Evidence Status |
|---|---|---|---|---|---|---|
| `A_Conventional` | Conventional Baseline | Static Round-Robin ($q=4.0$) | Demand paging (No proactive reclaim) | FCFS queue dispatch | Classical decoupled OS heuristic | `[Verified]` |
| `B_IndependentAgents` | Independent Agents | Localized CPU proposals | Localized Memory proposals | Localized I/O proposals | Uncoordinated multi-agent baseline | `[Verified]` |
| `C_CoordNoConflict` | Coord (No Conflict) | Safety constraints only | Bounded reclamation | Bounded I/O | Ablation: Coordination without ML | `[Verified]` |
| `D_ConflictNoHealing` | Conflict (No Healing) | Full arbitration + ML | Full proactive reclamation | Elevator SCAN | Ablation: Arbitration without recovery | `[Verified]` |
| `E_CompleteCoReOS` | Baseline CoReOS | CoReOS prototype v1 | Proactive reclamation | Elevator SCAN | Historical reference baseline | `[Verified]` |
| `F_ImprovedRL` | Curriculum RL | Q-Learning (54 states) | Q-Learning actions | Q-Learning actions | Optimized tabular RL benchmark | `[Verified]` |
| `G_ChampionCoReOS` | **CoReOS (Official)** | **Progress-Aware SRTF/RR** | **Proactive & Deep Swap** | **Elevator SCAN Shield** | **Official Unified CoReOS System** | `[Verified]` |
| `H_OriginalRL` | Tabular RL | Q-Learning (uncompacted) | Default reclamation | FCFS dispatch | Early RL prototype baseline | `[Verified]` |

### 8.2 Canonical Benchmark Leaderboard (1,440 Matched Trials)
*Data Source:* `reports/optimization/final_canonical_ranking_summary.csv` ($N=1,440$ trials, 30 held-out seeds, 6 workloads).  
*Bolding Convention:* **Bold text** strictly indicates the best-performing candidate for each individual metric according to optimization direction: Higher is better for Composite Score, Completion Rate, Throughput, and Jain's Fairness; Lower is better for Penalized Turnaround, Thrashing, and Overhead.

| Overall Rank | Candidate Architecture | Composite Score (Mean $\pm$ 95% CI) | Task Completion Rate (%) | Penalized Turnaround (ticks) | Throughput (jobs/tick) | Thrashing Ticks (mean) | Jain's Fairness Index | Decision Overhead (ms/step) |
|---|---|---|---|---|---|---|---|---|
| **1** | `F_ImprovedRL` | **$85.81 \pm 1.53$** | $95.28\%$ | **$39.84$** | **$0.1834$** | **0.01** | **0.6510** | $0.0030$ |
| **2** | `CoReOS` (`G_ChampionCoReOS`) | $84.87 \pm 1.35$ | **$95.86\%$** | $40.79$ | $0.1771$ | $0.02$ | $0.5934$ | $0.1517$ |
| **3** | `H_OriginalRL` | $82.17 \pm 2.29$ | $90.76\%$ | $58.36$ | $0.1743$ | $0.06$ | $0.6329$ | $0.0316$ |
| **4** | `D_ConflictNoHealing` | $75.47 \pm 3.06$ | $81.35\%$ | $82.40$ | $0.1549$ | $4.32$ | $0.6321$ | $0.1346$ |
| **5** | `E_CompleteCoReOS` | $75.46 \pm 3.07$ | $81.32\%$ | $82.23$ | $0.1549$ | $4.08$ | $0.6288$ | $0.1497$ |
| **6** | `C_CoordNoConflict` | $75.18 \pm 3.13$ | $81.76\%$ | $81.78$ | $0.1554$ | $9.67$ | $0.6346$ | $0.0051$ |
| **7** | `A_Conventional` | $74.29 \pm 3.45$ | $81.35\%$ | $81.73$ | $0.1573$ | $19.81$ | $0.6393$ | $0.0341$ |
| **8** | `B_IndependentAgents` | $74.29 \pm 3.30$ | $79.46\%$ | $86.46$ | $0.1521$ | $4.61$ | $0.6288$ | **0.0020** |

*Key Takeaway:* `F_ImprovedRL` ranks #1 on Composite Score ($85.81$), Penalized Turnaround ($39.84$\,ticks), Throughput ($0.1834$\,j/t), Thrashing ($0.01$\,ticks), and Fairness ($0.6510$). `CoReOS` ranks #2 on Composite Score ($84.87$) and achieves #1 ranking specifically on Task Completion Rate ($95.86\%$). `B_IndependentAgents` achieves the lowest decision overhead ($0.0020$\,ms).

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

*\*Workload Fairness Caveat:* Under `io_bottleneck`, **seven out of eight candidates** fail the $0.60$ floor across $100\%$ of their trials ($0.0\%$ pass rate; mean fairness ranging from $0.3878$ to $0.4237$). The sole exception is `F_ImprovedRL`, which achieves a mean fairness of **$0.6080$** and passes the $0.60$ floor in **$63.3\%$** of its trials (19/30 seeds). Under `mixed`, all eight candidates experience fairness depression ($0.4571$ to $0.5045$). `[Verified]`

### 8.4 Statistical Hypothesis Testing Results
*Data Source:* `reports/optimization/final_canonical_statistical_comparisons.csv` ($N=180$ matched trial pairs per comparison, 28 total pairwise combinations across 8 candidates).  
*Adjustment Procedure:* Two-tailed paired Student's $t$-test with Holm-Bonferroni step-down correction ($\alpha=0.05$) controlling Family-Wise Error Rate (FWER) across the family of 28 hypotheses.

| Hypothesis Comparison ($A$ vs. $B$) | Mean Diff ($\Delta$) | Std Diff ($\sigma_\Delta$) | Cohen's $d$ | Paired $t$-Stat | Unadjusted $p$-Value | Holm-Bonferroni Corrected $p$ | Significant ($\alpha=0.05$)? | Interpretation |
|---|---|---|---|---|---|---|---|---|
| **CoReOS vs. Conventional (A)** | $+10.584$ | $16.532$ | $0.640$ | $8.589$ | $4.20 \times 10^{-15}$ | $7.56 \times 10^{-14}$ | **True (Significant)** | Decisive superiority over static heuristic |
| **CoReOS vs. Complete CoReOS (E)** | $+9.410$ | $13.357$ | $0.704$ | $9.452$ | $1.87 \times 10^{-17}$ | $4.31 \times 10^{-16}$ | **True (Significant)** | Decisive superiority over prototype |
| **CoReOS vs. Original RL (H)** | $+2.699$ | $7.197$ | $0.375$ | $5.032$ | $1.17 \times 10^{-6}$ | $1.41 \times 10^{-5}$ | **True (Significant)** | Statistically significant advantage |
| **Curriculum RL (F) vs. Conventional (A)**| $+11.517$ | $17.110$ | $0.673$ | $9.031$ | $2.68 \times 10^{-16}$ | $5.36 \times 10^{-15}$ | **True (Significant)** | Decisive superiority over static heuristic |
| **Curriculum RL (F) vs. CoReOS (G)** | $+0.934$ | $2.833$ | $0.330$ | $4.422$ | $1.69 \times 10^{-5}$ | $1.52 \times 10^{-4}$ | **True (Significant)** | Statistically significant lead for RL |
| **Coord (C) vs. Conventional (A)** | $+0.893$ | $4.604$ | $0.194$ | $2.601$ | $0.0101$ | $0.0504$ | **False (Not Sig.)** | Not statistically distinguishable |
| **Conflict (D) vs. Complete CoReOS (E)** | $+0.004$ | $1.521$ | $0.002$ | $0.031$ | $0.9750$ | $1.0000$ | **False (Not Sig.)** | Functionally identical candidates |
| **Conventional (A) vs. Independent (B)** | $+0.003$ | $3.186$ | $0.001$ | $0.013$ | $0.9897$ | $1.0000$ | **False (Not Sig.)** | Statistically indistinguishable performance |

*Statistical Nuance:* 23 of the 28 pairwise comparisons are statistically significant under Holm-Bonferroni correction ($\alpha=0.05$), while 5 comparisons fail to achieve significance. Adjusted $p$-values are strictly $< 10^{-13}$ **only for comparisons against the bottom baselines** (Conventional, Complete CoReOS, Independent Agents). For comparisons between top performers (e.g., CoReOS vs. Original RL, or Curriculum RL vs. CoReOS), adjusted $p$-values lie in the $10^{-5}$ to $10^{-4}$ range ($1.41 \times 10^{-5}$ and $1.52 \times 10^{-4}$, respectively). `[Verified]`

### 8.5 Multi-Criteria Guardrail Compliance Audit
*Data Source:* `reports/optimization/final_canonical_benchmark_results.csv` and `final_canonical_guardrail_compliance.csv` ($N=180$ matched trials per candidate across all 6 workloads).

| Guardrail Name | Formal Threshold Criterion | CoReOS Compliance Rate | Conventional Compliance Rate | Curriculum RL (`F_ImprovedRL`) Rate | Operational Impact & Primary Failure Modes |
|---|---|---|---|---|---|
| **Decision Overhead** | $\mu_{ovh} \le 1.0$\,ms per step | **100.0% PASS** (180/180) | **100.0% PASS** (180/180) | **100.0% PASS** (180/180) | All evaluated candidates comfortably satisfy sub-millisecond simulation step threshold. |
| **Thrashing Ceilings** | $\le 15$ ticks (stress), $\le 25$ ticks (nominal)| **100.0% PASS** (180/180) | **79.4% PASS** (143/180; 37 fails) | **100.0% PASS** (180/180) | Conventional suffers 30 thrashing failures on `adversarial_stress` (mean $105.37$\,ticks) and 7 on `memory_thrashing`. CoReOS achieves 100% compliance. |
| **Fairness Floor** | $J(\mathbf{T}) \ge 0.60$ per completed trial | **59.4% PASS** (107/180; 73 fails) | **65.0% PASS** (117/180; 63 fails) | **75.6% PASS** (136/180; 44 fails) | CoReOS fails on `io_bottleneck` (30/30 fails) and `mixed` (29/30 fails). Conventional fails on `io_bottleneck` (30/30) and `mixed` (29/30). F_ImprovedRL passes 19/30 on `io_bottleneck`. |
| **Workload Robustness**| $CR = 100\% \land T_{avg} \le 16.0$ ticks on `steady_state` & `mixed` | **81.7% PASS** (49/60 trials) | **75.0% PASS** (45/60 trials) | **83.3% PASS** (50/60 trials) | Evaluated over 60 trials (30 `steady_state`, 30 `mixed`). Violations are driven by turnaround tail latencies under mixed contention. |
| **Overall Guardrail Compliant**| All 4 guardrails satisfied simultaneously | **58.9% PASS** (106/180; 74 fails) | **43.9% PASS** (79/180; 101 fails) | **75.6% PASS** (136/180; 44 fails) | Evaluates whether a trial passed every individual guardrail concurrently. CoReOS achieves 58.9% overall compliance, limited almost entirely by I/O and mixed fairness drops. |

---

## 9. Setup, Execution, and Testing

### 9.1 Environment Prerequisites
- **Operating System:** macOS (Apple Silicon M1/M2/M3/M4 or Intel) or Linux (Ubuntu 22.04+ / Debian 12+).
- **Python Environment:** Python 3.11+ (Python 3.11.4 verified in `.venv`).
- **Node Environment:** Node.js 18.x+ and npm 9.x+ (Vite 8.3.0+ verified in `frontend/package.json`).
- **LaTeX / PDF Compiler:** Tectonic or TeXLive (pdflatex, bibtex).
- **Typst Compiler:** Typst 0.11.0+ (`brew install typst` or binary release).

### 9.2 Step-by-Step Execution Guide

```bash
# 1. Navigate to repository root
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
# Output: research_paper/main.pdf (21 pages, 987 KB)

# 4. Compile CoReOS System Guide (78-page Typst book)
python learning_docs/build_full_guide.py
# Output: learning_docs/CoReOS_System_Guide.pdf
```

---

## 10. Research Validity, Limitations, and Methodological Critique

This section systematically records the research-validity concerns, empirical nuances, and methodological boundaries identified during the audit:

### 10.1 RQ1 and Overall Candidate Ranking
- **Statistical vs. Practical Significance:** Curriculum RL (`F_ImprovedRL`) ranks #1 overall with a composite score of $85.81 \pm 1.53$, while CoReOS (`G_ChampionCoReOS`) ranks #2 with $84.87 \pm 1.35$. The paired $t$-test indicates that this $+0.934$ point advantage for RL is statistically significant ($p_{holm} = 1.52 \times 10^{-4}$). However, practical significance is modest: the gap is under $1.1\%$ of the composite scale, and CoReOS achieves superior completion rate ($95.86\%$ vs. $95.28\%$). CoReOS must not be described as the overall composite winner. `[Verified]`

### 10.2 RQ2 and Recovery Stability
- **Unmeasured Policy Oscillation:** The claim that proportional self-healing operates "without introducing oscillatory policy thrashing" is an **unmeasured qualitative inference**. While page thrashing ticks are rigorously tracked ($\mu_m \ge 0.92 \land \text{swap} > 5\%$), the benchmark does not measure actuator oscillation frequency, policy switching rate, or damping ratio. New telemetry metrics are required to scientifically prove non-oscillatory stability. `[Inferred]`

### 10.3 RQ3 and Operational Overhead
- **Simulation Overhead vs. Kernel Feasibility:** The measured decision overhead ($0.1517$\,ms for CoReOS, $0.0030$\,ms for RL) represents the time required to evaluate Python functions and decision trees inside the discrete-event simulator. While this satisfies the simulator's $\le 1.0$\,ms threshold, **it does not establish feasibility for production operating-system kernels**. Real kernel scheduling paths (e.g., Linux CFS or eBPF schedulers) execute in $< 1-5\,\mu\text{s}$. Sub-millisecond Python execution in user-space cannot be extrapolated to bare-metal kernel viability without kernel-level prototyping. `[Inferred]`

### 10.4 Ablation Confounding
- **Coupled Mechanism Modifications:** In the ablation sequence (`A_Conventional` $\to$ `B_IndependentAgents` $\to$ `C_CoordNoConflict` $\to$ `D_ConflictNoHealing` $\to$ `G_ChampionCoReOS`), candidate `G_ChampionCoReOS` unifies proportional self-healing with the progress-aware `WorkloadAwareCPUAgent` (SRTF dispatch). Because self-healing and SRTF were introduced simultaneously, the $+9.40$ composite improvement over `D_ConflictNoHealing` cannot be causally attributed to self-healing alone; it represents the joint effect of both mechanisms. `[Inferred]`

### 10.5 Pseudo-Replication and Workload Clustering
- **Hierarchical Dependency in Hypothesis Testing:** The statistical comparisons evaluate $N=180$ matched observation pairs across 6 distinct workloads ($6 \times 30$ seeds). Treating all 180 pairs as independent observations ignores the intra-workload correlation structure (e.g., all 30 seeds of `cpu_spike` share identical convoy dynamics). While paired testing accounts for seed matching, a linear mixed-effects model with workload as a random effect would provide a more rigorous hierarchical assessment. `[Inferred]`

### 10.6 Training, Tuning, and Generalization Fairness
- **Held-Out Seeds vs. Held-Out Workloads:** The canonical benchmark evaluates 30 held-out seeds (`[5001..5030]`) on the same 6 workload profiles used during development. This demonstrates seed-level generalization, but does **not** demonstrate workload-level generalization to unseen stress profiles. Furthermore, Curriculum RL underwent multi-epoch Q-learning training across workloads, whereas heuristic baselines utilized fixed, hand-tuned parameters. `[Inferred]`

### 10.7 Composite Score Sensitivity
- **Untested Weight Configurations:** The canonical composite score uses fixed weights: $0.30$ Completion, $0.25$ Throughput, $0.20$ Penalized Turnaround, $0.15$ Thrashing, and $0.10$ Fairness. No formal sensitivity analysis across alternative weightings exists in the repository. Statements regarding how candidate rankings would shift under altered weights remain untested hypotheses. `[Unresolved]`

### 10.8 Guardrail and Fairness Realities
- **Workload-Specific Fairness Collapse:** On disk-bound workloads (`io_bottleneck`), physical cylinder geometry causes elevator SCAN to delay peripheral cylinders ($0$ and $100$) relative to central cylinders ($50$), causing 7 of 8 candidates to fail the $0.60$ floor in $100\%$ of trials. `F_ImprovedRL` is the only candidate that passes on `io_bottleneck` ($63.3\%$ pass rate, mean $0.6080$). CoReOS's overall guardrail pass rate ($58.9\%$) is depressed primarily by fairness on I/O and mixed workloads. `[Verified]`

### 10.9 Survivorship Bias Interpretation
- **Observational Evidence vs. Mathematical Proof:** Section III-C and Section VI-D of the paper document that unpenalized metrics drop starved tasks from the denominator, producing artificially favorable fairness numbers for failing baselines. While the empirical observations strongly support this mechanism, cautious language ("observed," "is consistent with") is preferred over asserting mathematical "proof." `[Verified]`

---

## 11. Claim-to-Evidence Map

| Claim in Research Paper or Reports | Quantitative Evidence | Source File Path & Line Reference | Evidence Status |
|---|---|---|---|
| **CoReOS ranks #2 overall with $84.87 \pm 1.35$ composite score** | Canonical mean: $84.87$, CI95: $\pm 1.35$, std: $9.15$ | `reports/optimization/final_canonical_ranking_summary.csv:3` | `[Verified]` |
| **Curriculum RL ranks #1 overall with $85.81 \pm 1.53$ composite score** | Canonical mean: $85.81$, CI95: $\pm 1.53$, std: $10.40$ | `reports/optimization/final_canonical_ranking_summary.csv:2` | `[Verified]` |
| **CoReOS achieves highest overall task completion rate ($95.86\%$)** | $95.86\%$ completion across 1,440 trials ($95.28\%$ for RL) | `reports/optimization/final_canonical_ranking_summary.csv:3` | `[Verified]` |
| **CoReOS slashes penalized turnaround time by $50.1\%$ vs Conventional** | $40.79$\,ticks for CoReOS vs. $81.73$\,ticks for Conventional | `reports/optimization/final_canonical_ranking_summary.csv:3, 8` | `[Verified]` |
| **Statistically significant superiority over Conventional ($p_{holm} < 10^{-13}$)** | Paired $t=8.589, p=4.20 \times 10^{-15}, p_{holm}=7.56 \times 10^{-14}, d=0.640$ | `reports/optimization/final_canonical_statistical_comparisons.csv:12` | `[Verified]` |
| **Statistically significant superiority over Baseline CoReOS ($p_{holm} < 10^{-15}$)**| Paired $t=9.452, p=1.87 \times 10^{-17}, p_{holm}=4.31 \times 10^{-16}, d=0.704$ | `reports/optimization/final_canonical_statistical_comparisons.csv:7` | `[Verified]` |
| **Statistically significant gap between Curriculum RL and CoReOS ($p_{holm} = 1.52 \times 10^{-4}$)**| Paired $t=4.422, p=1.69 \times 10^{-5}, p_{holm}=1.52 \times 10^{-4}, d=0.330$ | `reports/optimization/final_canonical_statistical_comparisons.csv:21` | `[Verified]` |
| **CoReOS satisfies decision overhead ceiling ($\le 1.0$\,ms) in $100\%$ of trials**| Mean overhead: $0.1517$\,ms; Max trial: $0.1690$\,ms; Pass rate: $100.0\%$ (180/180) | `reports/optimization/final_canonical_guardrail_compliance.csv:8-13` | `[Verified]` |
| **Thrashing is reduced by $99.9\%$ under adversarial stress** | Thrashing drops from $105.37$\,ticks in Conv. to $0.10$\,ticks in CoReOS ($99.905\%$) | `reports/optimization/final_canonical_per_workload_summary.csv:38, 44` | `[Verified]` |
| **Conventional fairness in compute spikes reflects survivorship bias** | Conventional completed only $47.50\%$ of tasks, starving $52.50\%$ | `research_paper/main.tex:590-595`; `final_canonical_per_workload_summary.csv:14` | `[Verified]` |
| **Seven candidates fail $0.60$ fairness floor on I/O bottlenecks; RL passes** | 7 candidates fail in 100% of trials ($0.0\%$ pass rate); `F_ImprovedRL` achieves $0.6080$ ($63.3\%$ pass rate) | `reports/optimization/final_canonical_per_workload_summary.csv:25-32`; `final_canonical_guardrail_compliance.csv:5` | `[Verified]` |
| **Absence of oscillatory policy thrashing in self-healing** | Page thrashing is bounded, but actuator oscillation is unmeasured | `research_paper/main.tex:295` | `[Inferred]` |
| **Sub-millisecond overhead implies Linux kernel feasibility** | Evaluated only in Python discrete-event simulation, not bare-metal kernel | `research_paper/main.tex:354-360` | `[Inferred]` |
| **Causal attribution of ablation gains solely to self-healing** | `G_ChampionCoReOS` unified both self-healing and SRTF CPU dispatch | `src/coreos/optimization/candidates.py:465-515` | `[Inferred]` |

---

## 12. Task-to-File Navigation Guide

### 12.1 Common Engineering & Research Workflows

#### Task 1: Modifying Scheduling or Arbitration Policies
- **Domain CPU/IO Agent implementations:** `src/coreos/optimization/candidates.py` (`WorkloadAwareCPUAgent`, `WorkloadAwareIOAgent`) and baseline heuristics in `src/coreos/agents/cpu_agent.py`, `src/coreos/agents/io_agent.py`.
- **Coordination constraints & arbitration rules:** `src/coreos/coordination/coordinator.py` (`AdaptiveCoordinationAgent.arbitrate`).
- **Official candidate definitions:** `src/coreos/optimization/candidates.py` (`ChampionCoReOS`).
- **Validation command:** `.venv/bin/pytest tests/test_optimization_candidates.py`

#### Task 2: Modifying Self-Healing & Recovery Actions
- **Regression detection thresholds ($W=10$, latency spikes):** `src/coreos/self_healing/regression_detector.py`.
- **Recovery action selection & cooling-off backoff:** `src/coreos/self_healing/recovery.py` (`ProportionalRecoveryEngine`).
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
- **Benchmark endpoint & 7 vs. 8 candidate presentation:** `backend/api/benchmarks.py`.
- **Report downloading & serving:** `backend/api/reports.py`.
- **Validation command:** `.venv/bin/pytest tests/test_api_state_store.py tests/test_benchmark_integration.py`

#### Task 6: Re-running Experiments and Updating Paper Figures
- **Execute canonical benchmark (1,440 trials):** `.venv/bin/python scripts/run_final_canonical_benchmark.py`.
- **Regenerate paper figures:** `.venv/bin/python research_paper/scripts/generate_figures.py`.
- **Recompile paper PDF:** `cd research_paper && tectonic main.tex`.

---

## 13. Unresolved Questions and Missing Evidence

1. **Linux Kernel Prototype Feasibility:** While discrete-event simulation establishes mathematical proof of cross-resource arbitration efficacy, empirical validation within a real Linux kernel (e.g., using `sched_ext` user-space schedulers or eBPF tracing) remains unexecuted and represents an open engineering challenge. `[Unresolved]`
2. **Policy Oscillation Metrics:** Recovery smoothness and absence of policy thrashing are currently inferred from low memory thrashing and stable turnaround times. Quantitative metrics tracking actuator switching frequency and control Lyapunov functions are needed to formally verify non-oscillatory stability. `[Unresolved]`
3. **Weight Sensitivity Analysis:** No empirical parameter sweep across composite scoring weights exists in the repository. The impact of weight adjustments on candidate rankings remains an untested hypothesis. `[Unresolved]`
4. **Generalization to Non-Stationary Workloads:** The Gradient Boosting conflict predictor was trained offline on stationary telemetry traces. How the system performs under real-world concept drift without periodic online retraining is an open research question. `[Unresolved]`
5. **Formal Standard for Penalized Fairness:** While penalized turnaround ($T_{pen}$) is mathematically defined and frozen in this benchmark, there is currently no universal IEEE/ACM consensus on formulating a penalized Jain's fairness index for starved tasks. `[Unresolved]`

---

## 14. Source Inspection Scope and Verification Limitations

- **Completeness of Inspection:** Every active Python source file in `src/`, `backend/`, and `scripts/`, every TypeScript/TSX file in `frontend/src/`, all 16 test modules in `tests/`, all canonical CSV/JSON/MD files in `reports/optimization/`, and the complete LaTeX source in `research_paper/main.tex` were inspected directly.
- **Verification of Binary Files:** `research_paper/main.pdf` (987,039 bytes, 21 pages) was verified using file metadata (`mdls`) and cross-checked against compilation logs and LaTeX sources.
- **Read-Only Safety Compliance:** This audit was conducted with zero modifications to application code, tests, configuration, datasets, research paper source files, or Git state. `PAPER_REVIEW_INFO.md` is the sole authorized modification.

---
*End of Audited Knowledge Base — Authored for Reusable Project Context in `CoReOS-Team`.*
