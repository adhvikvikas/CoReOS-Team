"""
CoReOS: Conflict-Aware, Self-Healing Multi-Agent AI Operating System Resource Manager
Package Initialization
"""

__version__ = "0.1.0"
__author__ = "CoReOS Research Team"

from src.coreos.config import load_config, CoReOSConfig
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector
from src.coreos.self_healing.recovery import RecoveryEngine
