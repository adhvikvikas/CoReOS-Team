"""
CoReOS Global Configuration Module
Contains all simulation parameters, resource limits, agent policies,
conflict definitions, and evaluation settings.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional


@dataclass
class SimulationConfig:
    random_seed: int = 42
    total_time_units: int = 1000
    cpu_cores: int = 4
    context_switch_penalty: float = 0.5  # time units
    default_quantum: float = 4.0        # Round Robin default quantum
    
    # Memory subsystem
    total_memory_mb: float = 16384.0   # 16 GB simulated RAM
    page_size_kb: int = 4               # 4 KB per page
    swap_capacity_mb: float = 8192.0    # 8 GB swap space
    page_fault_cost: float = 5.0        # time penalty for page fault (disk access)
    memory_pressure_threshold: float = 0.85  # 85% utilization triggers pressure
    
    # I/O subsystem
    io_channels: int = 2
    base_io_latency: float = 3.0        # average I/O service time
    io_queue_capacity: int = 50
    io_bandwidth_mb_per_s: float = 250.0

    # Workload Generation (Calibrated from Kaggle Dataset)
    workload_type: str = "calibrated_synthetic"  # "calibrated_synthetic", "bursty", "memory_heavy", "io_heavy", "adversarial"
    target_process_count: int = 50
    process_arrival_rate: float = 0.8   # lambda for Poisson process arrival


@dataclass
class ConflictConfig:
    # Thresholds defining operational cross-resource conflicts
    thrashing_threshold: float = 0.90       # memory utilization where excessive paging occurs
    io_saturation_threshold: float = 0.85   # I/O queue capacity fraction
    cpu_starvation_wait_limit: float = 25.0 # Max wait before starvation penalty
    conflict_confidence_threshold: float = 0.65
    use_ml_model: bool = True
    ml_model_type: str = "gradient_boosting"  # "rule_based", "random_forest", "gradient_boosting"


@dataclass
class SelfHealingConfig:
    # Regression detection
    regression_window_size: int = 20
    throughput_drop_threshold: float = 0.25    # 25% drop relative to rolling window
    turnaround_spike_threshold: float = 0.35    # 35% increase in turnaround
    patience_steps: int = 3                     # consecutive steps before triggering healing
    
    # Recovery actions
    max_recovery_attempts: int = 5
    cooling_off_period: int = 5                 # steps between corrective actions to avoid thrashing
    enable_feedback_adjustment: bool = True


@dataclass
class SystemConfig:
    sim: SimulationConfig = field(default_factory=SimulationConfig)
    conflict: ConflictConfig = field(default_factory=ConflictConfig)
    healing: SelfHealingConfig = field(default_factory=SelfHealingConfig)
    data_path: str = "data/Big_data_dataset.csv"
    reports_dir: str = "reports"
    artifacts_dir: str = "reports"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sim": self.sim.__dict__,
            "conflict": self.conflict.__dict__,
            "healing": self.healing.__dict__,
            "data_path": self.data_path
        }


DEFAULT_CONFIG = SystemConfig()

STANDARD_SEEDS: List[int] = [42, 101, 202]


def get_standard_seeds(num_seeds: int = 3, explicit_seeds: Optional[List[int]] = None) -> List[int]:
    """
    Standardizes random seeds across all benchmark and ablation experiments.
    Canonical seed list: [42, 101, 202].
    If more seeds are requested, derives additional seeds deterministically: 202 + i * 100.
    """
    if explicit_seeds is not None:
        return list(explicit_seeds)
    if num_seeds <= len(STANDARD_SEEDS):
        return STANDARD_SEEDS[:num_seeds]
    additional = [STANDARD_SEEDS[-1] + (i + 1) * 100 for i in range(num_seeds - len(STANDARD_SEEDS))]
    return STANDARD_SEEDS + additional
