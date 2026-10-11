# CoReOS Dataset Profile & Verification Report

> [!IMPORTANT]
> **Dataset Origin**: Kaggle [IT System Performance and Resource Metrics](https://www.kaggle.com/datasets/freshersstaff/it-system-performance-and-resource-metrics/data)
> **File Analyzed**: `Big_data_dataset.csv` (1.56 MB)
> **Total Observations**: 10,000 rows
> **Total Columns**: 12 columns

## 1. Schema Verification and Column Metadata

Expected 12 columns confirmed: **YES**

| Column Name | Inferred Type | Missing Count | Documented Unit | Category | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `cpu_utilization` | `float64` | 0 | % (Percentage) | CPU Resource | Percentage of CPU resources currently in use. |
| `memory_usage` | `float64` | 0 | % (Percentage) | Memory Resource | Percentage of RAM being utilized by running processes. |
| `disk_io` | `float64` | 0 | MB/s or IOPS | Storage / I/O | Rate of data being read from and written to storage. |
| `network_latency` | `float64` | 0 | ms (Milliseconds) | Network | Time delay for network packets to travel between endpoints. |
| `process_count` | `int64` | 0 | Count | Workload / Processes | Total number of active processes running on the system. |
| `thread_count` | `int64` | 0 | Count | Workload / Concurrency | Total number of active threads across all processes. |
| `context_switches` | `int64` | 0 | Count / Rate | CPU Scheduling Overhead | Number of times the CPU switches between processes/threads. |
| `cache_miss_rate` | `float64` | 0 | % or Ratio | Memory Hierarchy / Cache | Proportion of memory accesses failing in CPU cache. |
| `temperature` | `float64` | 0 | °C (Degrees Celsius) | Hardware / Thermals | System temperature, typically of CPU or mainboard. |
| `power_consumption` | `float64` | 0 | Watts (W) | Hardware / Energy | Electrical power usage of the system. |
| `uptime` | `float64` | 0 | Hours | System Stability | Total time the system has been running without a restart. |
| `status` | `int64` | 0 | Binary Indicator (0/1) | Target / Health Status | Operational status: 0 = Normal, 1 = Anomaly / Fault. |

## 2. Data Quality & Distribution Statistics

- **Duplicate Rows**: 0 (0.00%)
- **Missing Values**: Total 0 across all columns

### Numerical Summary Statistics

| Feature | Mean | Std | Min | 25% | 50% (Median) | 75% | Max | Skewness | Lag-1 Autocorr |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `cpu_utilization` | 51.95 | 27.32 | 5.00 | 28.40 | 51.79 | 75.30 | 99.97 | 0.02 | -0.0125 |
| `memory_usage` | 55.41 | 26.04 | 10.01 | 32.86 | 55.53 | 78.08 | 99.99 | -0.02 | 0.0107 |
| `disk_io` | 25.50 | 14.05 | 1.00 | 13.43 | 25.60 | 37.49 | 50.00 | -0.00 | -0.0022 |
| `network_latency` | 100.24 | 57.51 | 1.00 | 50.12 | 100.51 | 149.68 | 199.96 | 0.00 | -0.0007 |
| `process_count` | 517.24 | 275.02 | 50.00 | 277.00 | 512.00 | 755.00 | 999.00 | 0.03 | 0.0006 |
| `thread_count` | 1811.33 | 1167.26 | 100.00 | 862.00 | 1598.00 | 2598.50 | 4995.00 | 0.67 | 0.0160 |
| `context_switches` | 1038.86 | 549.99 | 100.00 | 559.00 | 1037.00 | 1508.00 | 1999.00 | 0.03 | 0.0098 |
| `cache_miss_rate` | 0.11 | 0.06 | 0.01 | 0.06 | 0.11 | 0.15 | 0.20 | -0.00 | 0.0274 |
| `temperature` | 62.38 | 18.88 | 30.01 | 45.98 | 62.19 | 78.98 | 94.99 | 0.01 | -0.0135 |
| `power_consumption` | 174.79 | 71.99 | 50.04 | 113.03 | 173.84 | 236.49 | 299.97 | 0.02 | -0.0061 |
| `uptime` | 500.38 | 286.61 | 1.33 | 251.08 | 503.66 | 746.41 | 999.91 | -0.00 | -0.0081 |
| `status` | 0.01 | 0.10 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 10.01 | 0.0006 |

## 3. Temporal Structure & Ordering Analysis

- **Explicit Timestamp Field**: None detected in dataset
- **Autocorrelation Analysis**:
  - If observations were a contiguous time series sampled at sub-second or minute intervals, consecutive metrics would typically exhibit strong positive autocorrelation ($r > 0.7$).
  - Observed Lag-1 Autocorrelation range: `[-0.0135, 0.0274]`.
  - **Finding**: Near-zero autocorrelation indicates observations may be permuted or independently sampled snapshots across distributed systems, rather than an unpermuted single-machine high-frequency time series.
  - **Methodological Rule**: We must **NOT** assume row indices represent a continuous clock time without documented sampling intervals. For simulation calibration, empirical distributions and joint copulas must be utilized.

## 4. Target Label & Class Distribution

- Target Column: `status`
  - Status `0`: 9,903 records (99.03%)
  - Status `1`: 97 records (0.97%)

## 5. Resource Categorization in CoReOS

| Resource Domain | Dataset Features | Simulator Role |
| :--- | :--- | :--- |
| **CPU Agent** | `cpu_utilization, context_switches` | Drives simulated process burst times, queue length, and CPU utilization calibration |
| **Memory Agent** | `memory_usage, cache_miss_rate` | Drives simulated memory footprint, cache contention, and page pressure |
| **I/O Agent** | `disk_io` | Drives simulated I/O bursts, queue delays, and throughput limits |
| **System Context** | `network_latency, temperature, power_consumption, uptime, status` | Environmental context features for Conflict Prediction and Regression Detection |

## 6. Data-to-Simulation Separation & Scope Boundaries

> [!NOTE]
> CoReOS strictly separates **Empirical Real Observations** from **Simulated Process-Level Data**.

### Supported Real-Data Applications:
- System health and anomaly detection (binary status prediction)
- Correlative cross-resource modeling (e.g., CPU vs Temperature vs Power)
- System-level resource pressure characterization
- Simulation calibration: empirical probability distributions for overall system load and context switch rates


### Inherent Limitations & Simulation Requirements:
- Lacks per-process identifiers (PID, arrival times, CPU burst lengths, memory allocations, page tables).
- Lacks individual I/O queue requests, disk seek times, and block sizes.
- Lacks high-resolution timestamps with documented sample intervals (seconds vs minutes).
- Does not record operating system scheduling decisions (FCFS vs Round Robin actions) or counterfactual outcomes.
- Crucial distinction: Real data reflects system-level operational aggregates; process-level execution trajectories must be simulated.


### Synthetic Workload Generator Calibration Strategy:
- Process arrival times: Poisson process calibrated to empirical `process_count` and `thread_count` distributions.
- CPU burst lengths: Lognormal/Exponential distribution calibrated to `cpu_utilization` and `context_switches`.
- Memory demand: Gaussian mixture calibrated to empirical `memory_usage` and `cache_miss_rate`.
- I/O operations: Bursty distribution calibrated to empirical `disk_io` and `network_latency`.

---
*Report automatically generated by CoReOS Dataset Profiler.*