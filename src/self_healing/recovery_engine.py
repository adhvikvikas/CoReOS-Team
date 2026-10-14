"""
CoReOS Self-Healing: Recovery Engine
Selects and executes corrective actions upon performance regression detection,
enforcing cooling-off periods and measuring recovery time and success rates.
"""

from typing import Dict, Any, Optional, List
from src.config import SelfHealingConfig
from src.self_healing.regression_detector import RegressionEvent


class RecoveryEngine:
    def __init__(self, config: Optional[SelfHealingConfig] = None):
        self.config = config or SelfHealingConfig()
        
        # State tracking
        self.last_recovery_step: int = -100
        self.active_recovery: Optional[RegressionEvent] = None
        self.active_recovery_start_time: float = 0.0
        
        # Telemetry
        self.recovery_records: List[Dict[str, Any]] = []
        self.policy_switches: int = 0
        self.consecutive_retries: int = 0
        self.max_retries: int = 4
        self.max_cooling_off_period: int = 25

    @property
    def is_cooling_off(self) -> bool:
        return False  # Handled per step index check

    def select_corrective_action(
        self,
        event: RegressionEvent,
        current_step: int,
        system_state: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Determines corrective intervention parameters based on regression type.
        Returns override parameter dictionary, or None if in cooling-off period.
        """
        # Enforce bounded cooling-off period with backoff limit to prevent policy flapping
        effective_cooling = min(
            self.max_cooling_off_period,
            self.config.cooling_off_period * (1 + self.consecutive_retries)
        )
        if (current_step - self.last_recovery_step) < effective_cooling:
            return None

        self.last_recovery_step = current_step
        self.active_recovery = event
        self.active_recovery_start_time = system_state.get("time", 0.0)
        self.policy_switches += 1

        corrective_overrides = {}

        if event.regression_type == "THRASHING_STALL":
            # Graduated reclamation: reclaim 2048 MB to halt thrashing without mass process eviction
            corrective_overrides = {
                "memory_reclaim_target": 2048.0,
                "cpu_quantum": 8.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SCAN"
            }

        elif event.regression_type == "THROUGHPUT_COLLAPSE":
            # Lengthen quantum to clear backlogged batch processes and engage SCAN
            corrective_overrides = {
                "cpu_quantum": 6.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SCAN"
            }

        elif event.regression_type == "LATENCY_SPIKE":
            # Avoid SSTF seek starvation; deploy elevator SCAN and balanced 4.0 quantum
            corrective_overrides = {
                "cpu_quantum": 4.0,
                "cpu_policy": "ROUND_ROBIN",
                "io_policy": "SCAN",
                "memory_reclaim_target": 1024.0
            }

        return corrective_overrides

    def track_recovery_progress(self, current_step: int, system_state: Dict[str, Any]):
        """Evaluates whether current system metrics have recovered back to healthy baseline."""
        if self.active_recovery is None:
            return

        current_time = system_state.get("time", 0.0)
        elapsed_time = current_time - self.active_recovery_start_time
        is_thrashing = system_state.get("is_thrashing", False)
        mem_util = system_state.get("memory_utilization", 0.0)

        # Recovery criteria: no thrashing and metrics stabilized
        recovered = (not is_thrashing) and (mem_util < 88.0)
        timed_out = elapsed_time >= 25.0

        if recovered:
            self.consecutive_retries = max(0, self.consecutive_retries - 1)
        elif timed_out:
            self.consecutive_retries = min(self.max_retries, self.consecutive_retries + 1)

        if recovered or timed_out:  # Timeout after 25 time units
            success = recovered
            self.recovery_records.append({
                "regression_type": self.active_recovery.regression_type,
                "recovery_time": round(elapsed_time, 2),
                "success": success,
                "policy_switches_total": self.policy_switches
            })
            self.active_recovery = None

    def get_metrics(self) -> Dict[str, Any]:
        """Returns recovery metrics: success rate, mean recovery time, policy switches."""
        if not self.recovery_records:
            return {
                "total_recoveries": 0,
                "success_rate": 0.0,
                "avg_recovery_time": 0.0,
                "policy_switches": self.policy_switches,
                "consecutive_retries": self.consecutive_retries
            }

        successes = sum(1 for r in self.recovery_records if r["success"])
        success_rate = successes / len(self.recovery_records)
        avg_time = float(sum(r["recovery_time"] for r in self.recovery_records) / len(self.recovery_records))

        return {
            "total_recoveries": len(self.recovery_records),
            "success_rate": round(success_rate, 4),
            "avg_recovery_time": round(avg_time, 2),
            "policy_switches": self.policy_switches,
            "consecutive_retries": self.consecutive_retries
        }

