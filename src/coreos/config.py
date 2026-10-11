"""
CoReOS Configuration Manager
Loads configuration from YAML with strongly-typed dataclasses and dataset path resolution.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml


@dataclass
class DatasetConfig:
    raw_path: str = "data/raw/Big_data_dataset.csv"
    fallback_path: str = "data/Big_data_dataset.csv"
    processed_dir: str = "data/processed"
    expected_features: List[str] = field(default_factory=lambda: [
        "cpu_utilization", "memory_usage", "disk_io", "network_latency",
        "process_count", "thread_count", "context_switches", "cache_miss_rate",
        "temperature", "power_consumption", "uptime"
    ])
    target_column: str = "status"


@dataclass
class SimulationConfig:
    random_seed: int = 42
    total_time_units: int = 500
    cpu_cores: int = 4
    context_switch_penalty: float = 0.5
    default_quantum: float = 4.0
    total_memory_mb: float = 16384.0
    page_size_kb: int = 4
    swap_capacity_mb: float = 8192.0
    page_fault_cost: float = 5.0
    memory_pressure_threshold: float = 0.85
    io_channels: int = 2
    base_io_latency: float = 3.0
    io_queue_capacity: int = 50
    io_bandwidth_mb_per_s: float = 250.0


@dataclass
class ConflictConfig:
    thrashing_threshold: float = 0.88
    io_saturation_threshold: float = 0.80
    confidence_threshold: float = 0.65
    use_ml_model: bool = True
    model_type: str = "gradient_boosting"


@dataclass
class SelfHealingConfig:
    regression_window_size: int = 20
    throughput_drop_threshold: float = 0.25
    turnaround_spike_threshold: float = 0.35
    patience_steps: int = 3
    cooling_off_period: int = 5
    max_recovery_attempts: int = 5
    enable_feedback_adjustment: bool = True


@dataclass
class EvaluationConfig:
    baselines: List[str] = field(default_factory=lambda: [
        "A_Conventional", "B_IndependentAgents", "C_CoordNoConflict",
        "D_ConflictNoHealing", "E_CompleteCoReOS", "F_LearningRL"
    ])
    workloads: List[str] = field(default_factory=lambda: [
        "steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "adversarial_stress"
    ])
    default_seeds: List[int] = field(default_factory=lambda: [42, 101, 202])
    reports_dir: str = "reports"


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


@dataclass
class CoReOSConfig:
    dataset: DatasetConfig = field(default_factory=DatasetConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)
    conflict: ConflictConfig = field(default_factory=ConflictConfig)
    healing: SelfHealingConfig = field(default_factory=SelfHealingConfig)
    evaluation: EvaluationConfig = field(default_factory=EvaluationConfig)

    def get_dataset_path(self, base_dir: Optional[Path] = None) -> Optional[Path]:
        """Resolves the dataset file path, preferring raw_path then fallback_path."""
        base = base_dir or Path(__file__).resolve().parent.parent.parent
        candidates = [
            base / self.dataset.raw_path,
            base / self.dataset.fallback_path,
            Path(self.dataset.raw_path),
            Path(self.dataset.fallback_path)
        ]
        for p in candidates:
            if p.exists() and p.is_file():
                return p
        return None


def load_config(config_path: Optional[str] = None) -> CoReOSConfig:
    """Loads configuration from YAML file or falls back to defaults."""
    default_path = Path(__file__).resolve().parent.parent.parent / "config" / "config.yaml"
    target_path = Path(config_path) if config_path else default_path

    if not target_path.exists():
        return CoReOSConfig()

    with open(target_path, "r") as f:
        data = yaml.safe_load(f) or {}

    ds_cfg = DatasetConfig(**data.get("dataset", {}))
    sim_cfg = SimulationConfig(**data.get("simulation", {}))
    conf_cfg = ConflictConfig(**data.get("conflict_prediction", {}))
    heal_cfg = SelfHealingConfig(**data.get("self_healing", {}))
    eval_cfg = EvaluationConfig(**data.get("evaluation", {}))

    return CoReOSConfig(
        dataset=ds_cfg,
        simulation=sim_cfg,
        conflict=conf_cfg,
        healing=heal_cfg,
        evaluation=eval_cfg
    )
