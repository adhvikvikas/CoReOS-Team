"""
CoReOS Benchmark Runner
Executes fair, reproducible comparisons across Baselines A through F
under identical workloads, initial conditions, and random seeds.
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
from src.config import SimulationConfig, ConflictConfig, SelfHealingConfig, get_standard_seeds, STANDARD_SEEDS
from src.simulation.simulator import SystemSimulator
from src.simulation.workload_generator import WorkloadGenerator
from src.agents.cpu_agent import CPUAgent
from src.agents.memory_agent import MemoryAgent
from src.agents.io_agent import IOAgent
from src.conflict_prediction.conflict_engine import ConflictEngine
from src.coordination.coordination_agent import CoordinationAgent
from src.self_healing.regression_detector import PerformanceRegressionDetector
from src.self_healing.recovery_engine import RecoveryEngine
from src.self_healing.feedback_mechanism import FeedbackMechanism
from src.learning.env import CoReOSEnv
from src.learning.rl_agent import RLAgent
from src.evaluation.metrics import compute_simulation_benchmark_summary


class BenchmarkRunner:
    def __init__(
        self,
        sim_config: Optional[SimulationConfig] = None,
        conflict_config: Optional[ConflictConfig] = None,
        healing_config: Optional[SelfHealingConfig] = None
    ):
        self.sim_config = sim_config or SimulationConfig()
        self.conflict_config = conflict_config or ConflictConfig()
        self.healing_config = healing_config or SelfHealingConfig()
        self.workload_gen = WorkloadGenerator(seed=self.sim_config.random_seed)

    def run_baseline_a_conventional(
        self,
        processes,
        enable_watermark_paging: bool = True,
        watermark_reclaim_mb: float = 1024.0,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Baseline A: Fixed Conventional Policies (Static RR + FCFS I/O + static watermark paging)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        # Deepcopy processes via attributes
        workload = [p.clone() for p in processes]
        sim.reset(workload)
        
        t0 = time.perf_counter()
        step_idx = 0
        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            reclaim_target = watermark_reclaim_mb if (enable_watermark_paging and state.get("is_under_memory_pressure", False)) else 0.0
            sim.step(dt=1.0, cpu_policy="ROUND_ROBIN", cpu_quantum=4.0, io_policy="FCFS", memory_reclaim_target=reclaim_target)
            step_idx += 1
        overhead_ms = (time.perf_counter() - t0) * 1000.0 / max(1, step_idx)

        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            total_processes=len(workload)
        )

    def run_baseline_b_independent_agents(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline B: Independent CPU, Memory, and I/O Agents without coordination."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()

        t0 = time.perf_counter()
        step_idx = 0
        decision_time = 0.0

        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            
            d_start = time.perf_counter()
            cpu_act = cpu_ag.propose_action(state)
            mem_act = mem_ag.propose_action(state)
            io_act = io_ag.propose_action(state)
            decision_time += (time.perf_counter() - d_start)

            # Apply actions independently without coordination
            sim.step(
                dt=1.0,
                cpu_policy=cpu_act.parameters.get("policy", "ROUND_ROBIN"),
                cpu_quantum=cpu_act.parameters.get("quantum", 4.0),
                io_policy=io_act.parameters.get("io_policy", "FCFS"),
                memory_reclaim_target=mem_act.parameters.get("target_free_mb", 0.0)
            )
            step_idx += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_idx)
        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            total_processes=len(workload)
        )

    def run_baseline_c_coordinated_no_conflict(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline C: Coordinated Agents without Conflict Prediction."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        conflict_engine = ConflictEngine(use_ml=False)
        coord_ag = CoordinationAgent(conflict_engine=conflict_engine, enable_conflict_prediction=False)

        decision_time = 0.0
        step_idx = 0

        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            d_start = time.perf_counter()
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, _ = coord_ag.coordinate(state, props)
            decision_time += (time.perf_counter() - d_start)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_idx += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_idx)
        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            total_processes=len(workload)
        )

    def run_baseline_d_conflict_aware_no_healing(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline D: Coordinated + Conflict Prediction, without Self-Healing."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        conflict_engine = ConflictEngine(confidence_threshold=self.conflict_config.conflict_confidence_threshold, use_ml=True)
        coord_ag = CoordinationAgent(conflict_engine=conflict_engine, enable_conflict_prediction=True)

        decision_time = 0.0
        step_idx = 0

        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            d_start = time.perf_counter()
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, _ = coord_ag.coordinate(state, props)
            decision_time += (time.perf_counter() - d_start)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_idx += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_idx)
        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            conflict_metrics=conflict_engine.get_metrics(),
            total_processes=len(workload)
        )

    def run_baseline_e_complete_coreos(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline E: Complete CoReOS Architecture (Coordinated + Conflict Prediction + Self-Healing)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        conflict_engine = ConflictEngine(confidence_threshold=self.conflict_config.conflict_confidence_threshold, use_ml=True)
        coord_ag = CoordinationAgent(conflict_engine=conflict_engine, enable_conflict_prediction=True)
        detector = PerformanceRegressionDetector(self.healing_config)
        recovery_eng = RecoveryEngine(self.healing_config)
        feedback = FeedbackMechanism(conflict_engine=conflict_engine)

        decision_time = 0.0
        step_idx = 0

        while not sim.is_done() and step_idx < 300:
            state = sim.get_system_state()
            d_start = time.perf_counter()

            # 1. Propose and coordinate
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, prediction = coord_ag.coordinate(state, props)

            # 2. Check for regression
            reg_event = detector.observe_and_detect(state)
            detector.record_decision(decision)

            # 3. Apply recovery override if regression detected
            if reg_event is not None:
                overrides = recovery_eng.select_corrective_action(reg_event, step_idx, state)
                if overrides:
                    decision.update(overrides)

            # 4. Process feedback to adapt conflict predictor
            feedback.process_feedback(prediction, reg_event, step_idx)
            recovery_eng.track_recovery_progress(step_idx, state)

            decision_time += (time.perf_counter() - d_start)

            # Step simulation
            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_idx += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_idx)
        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            conflict_metrics=conflict_engine.get_metrics(),
            healing_metrics=recovery_eng.get_metrics(),
            total_processes=len(workload)
        )

    def run_baseline_f_learning_rl(
        self,
        processes,
        pre_trained_agent: Optional[RLAgent] = None,
        seed: Optional[int] = None,
        max_steps: int = 300
    ) -> Dict[str, Any]:
        """Baseline F: Reinforcement Learning Multi-Agent Coordination (Evaluation Horizon = 300 steps)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.sim_config
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        # Consistent 300-step evaluation horizon matching Baselines A-E
        env = CoReOSEnv(simulator=sim, max_steps=max_steps)
        rl_agent = pre_trained_agent or RLAgent()
        if pre_trained_agent is None:
            # Training horizon clearly distinguished: 150-step episodes for training exploration
            train_env = CoReOSEnv(max_steps=150)
            rl_agent.train(train_env, num_episodes=15)

        # Reset simulation with benchmark processes
        sim.reset(workload)
        state = sim.get_system_state()
        obs = env._extract_obs(state)

        t0 = time.perf_counter()
        step_idx = 0
        done = False

        while not done and step_idx < max_steps:
            action = rl_agent.select_action(obs, evaluate=True)
            obs, _, done, state = env.step(action)
            step_idx += 1

        overhead_ms = (time.perf_counter() - t0) * 1000.0 / max(1, step_idx)
        return compute_simulation_benchmark_summary(
            completed_processes=sim.completed_processes,
            simulation_history=sim.history,
            overhead_ms=overhead_ms,
            total_processes=len(workload)
        )

    def run_full_suite(
        self,
        workload_types: Optional[List[str]] = None,
        num_seeds: int = 3,
        seeds: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """
        Runs comprehensive benchmark suite across all baselines, workloads, and standardized seeds.
        """
        workloads = workload_types or ["steady_state", "cpu_spike", "memory_thrashing", "io_bottleneck", "adversarial_stress"]
        seeds_list = get_standard_seeds(num_seeds=num_seeds, explicit_seeds=seeds)
        records = []

        # Pretrain RL agent once with training horizon
        print("[Benchmark] Pre-training RL agent for Baseline F (training horizon: 150 steps)...")
        rl_agent = RLAgent()
        train_env = CoReOSEnv(max_steps=150)
        rl_agent.train(train_env, num_episodes=15)

        for w_type in workloads:
            for seed in seeds_list:
                # Set exact reproducible seed without arbitrary offsets
                self.workload_gen.set_seed(seed)
                # Generate identical workload for all baselines
                base_procs = self.workload_gen.generate_workload(
                    num_processes=40,
                    workload_type=w_type
                )

                baselines = {
                    "A_Conventional": self.run_baseline_a_conventional(base_procs, seed=seed),
                    "B_IndependentAgents": self.run_baseline_b_independent_agents(base_procs, seed=seed),
                    "C_CoordNoConflict": self.run_baseline_c_coordinated_no_conflict(base_procs, seed=seed),
                    "D_ConflictNoHealing": self.run_baseline_d_conflict_aware_no_healing(base_procs, seed=seed),
                    "E_CompleteCoReOS": self.run_baseline_e_complete_coreos(base_procs, seed=seed),
                    "F_LearningRL": self.run_baseline_f_learning_rl(base_procs, pre_trained_agent=rl_agent, seed=seed, max_steps=300)
                }

                for b_name, metrics in baselines.items():
                    rec = {
                        "baseline": b_name,
                        "workload": w_type,
                        "seed": seed,
                        "total_processes": metrics["total_processes"],
                        "completed_processes": metrics["completed_processes"],
                        "unfinished_processes": metrics["unfinished_processes"],
                        "completion_rate": metrics["completion_rate"],
                        "avg_turnaround_time": metrics["avg_turnaround_time"],
                        "p95_turnaround_time": metrics["p95_turnaround_time"],
                        "avg_waiting_time": metrics["avg_waiting_time"],
                        "avg_response_time": metrics["avg_response_time"],
                        "throughput": metrics["throughput"],
                        "jains_fairness": metrics["jains_fairness_index"],
                        "thrashing_ticks": metrics["thrashing_ticks"],
                        "decision_overhead_ms": metrics["decision_overhead_ms"]
                    }
                    records.append(rec)

        df = pd.DataFrame(records)
        return df


if __name__ == "__main__":
    runner = BenchmarkRunner()
    df = runner.run_full_suite(workload_types=["steady_state", "adversarial_stress"], num_seeds=2)
    print("\nBenchmark Suite Summary (Mean across runs):")
    summary = df.groupby(["workload", "baseline"])[["avg_turnaround_time", "throughput", "thrashing_ticks", "decision_overhead_ms"]].mean()
    print(summary)
