"""
CoReOS Experiment Suite
Executes comprehensive benchmark comparisons and ablation studies.
"""

from typing import Dict, Any, List, Optional
import time
import numpy as np
import pandas as pd
from src.coreos.config import CoReOSConfig, SimulationConfig, get_standard_seeds, STANDARD_SEEDS
from src.coreos.simulation.environment import SystemSimulator
from src.coreos.simulation.workload import WorkloadGenerator
from src.coreos.simulation.metrics import compute_simulation_metrics
from src.coreos.agents.cpu_agent import CPUAgent
from src.coreos.agents.memory_agent import MemoryAgent
from src.coreos.agents.io_agent import IOAgent
from src.coreos.conflict_prediction.predictor import ConflictEngine
from src.coreos.coordination.coordinator import CoordinationAgent
from src.coreos.self_healing.regression_detector import PerformanceRegressionDetector
from src.coreos.self_healing.recovery import RecoveryEngine, FeedbackMechanism
from src.coreos.learning.environment import CoReOSGymEnv
from src.coreos.learning.train import RLAgent
from src.coreos.baselines.schedulers import ConventionalScheduler, IndependentAgentScheduler


class ExperimentSuite:
    def __init__(self, config: Optional[CoReOSConfig] = None):
        self.config = config or CoReOSConfig()
        self.workload_gen = WorkloadGenerator(seed=self.config.simulation.random_seed)

    def run_baseline_c(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline C: Coordinated without Conflict Prediction."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.config.simulation
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        engine = ConflictEngine(use_ml=False)
        coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=False)

        decision_time = 0.0
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            t0 = time.perf_counter()
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, _ = coord.coordinate(state, props)
            decision_time += (time.perf_counter() - t0)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, total_processes=len(workload))

    def run_baseline_d(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline D: Coordinated + Conflict Prediction (No Self-Healing)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.config.simulation
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        engine = ConflictEngine(use_ml=True)
        coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)

        decision_time = 0.0
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            t0 = time.perf_counter()
            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, _ = coord.coordinate(state, props)
            decision_time += (time.perf_counter() - t0)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, conflict_metrics=engine.get_metrics(), total_processes=len(workload))

    def run_baseline_e_complete(self, processes, seed: Optional[int] = None) -> Dict[str, Any]:
        """Baseline E: Complete CoReOS (Coordinated + Conflict Prediction + Self-Healing)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.config.simulation
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        cpu_ag = CPUAgent()
        mem_ag = MemoryAgent()
        io_ag = IOAgent()
        engine = ConflictEngine(use_ml=True)
        coord = CoordinationAgent(conflict_engine=engine, enable_conflict_prediction=True)
        detector = PerformanceRegressionDetector(self.config.healing)
        recovery = RecoveryEngine(self.config.healing)
        feedback = FeedbackMechanism(engine)

        decision_time = 0.0
        step_i = 0
        while not sim.is_done() and step_i < 300:
            state = sim.get_system_state()
            t0 = time.perf_counter()

            props = {
                "CPU_AGENT": cpu_ag.propose_action(state),
                "MEMORY_AGENT": mem_ag.propose_action(state),
                "IO_AGENT": io_ag.propose_action(state)
            }
            decision, prediction = coord.coordinate(state, props)

            reg_event = detector.observe_and_detect(state)
            detector.record_decision(decision)

            if reg_event is not None:
                overrides = recovery.select_corrective_action(reg_event, step_i, state)
                if overrides:
                    decision.update(overrides)

            feedback.process_feedback(prediction, reg_event, step_i)
            recovery.track_recovery_progress(step_i, state)

            decision_time += (time.perf_counter() - t0)

            sim.step(
                dt=1.0,
                cpu_policy=decision["cpu_policy"],
                cpu_quantum=decision["cpu_quantum"],
                io_policy=decision["io_policy"],
                memory_reclaim_target=decision["memory_reclaim_target"]
            )
            step_i += 1

        overhead_ms = (decision_time * 1000.0) / max(1, step_i)
        return compute_simulation_metrics(
            sim.completed_processes, sim.history, overhead_ms,
            conflict_metrics=engine.get_metrics(),
            healing_metrics=recovery.get_metrics(),
            total_processes=len(workload)
        )

    def run_baseline_f_rl(
        self,
        processes,
        pre_trained_agent: Optional[RLAgent] = None,
        seed: Optional[int] = None,
        max_steps: int = 300
    ) -> Dict[str, Any]:
        """Baseline F: Reinforcement Learning Multi-Agent Coordination (Evaluation Horizon = 300 steps)."""
        sim_cfg = SimulationConfig(random_seed=seed) if seed is not None else self.config.simulation
        sim = SystemSimulator(sim_cfg)
        workload = [p.clone() for p in processes]
        sim.reset(workload)

        # Consistent 300-step evaluation horizon matching Baselines A-E
        env = CoReOSGymEnv(simulator=sim, max_steps=max_steps)
        agent = pre_trained_agent
        if agent is None:
            agent = RLAgent()
            # Training horizon clearly distinguished: 150-step episodes for training exploration
            train_env = CoReOSGymEnv(max_steps=150)
            agent.train(train_env, num_episodes=15)

        sim.reset(workload)
        state = sim.get_system_state()
        obs = env._extract_obs(state)

        t0 = time.perf_counter()
        step_i = 0
        done = False
        while not done and step_i < max_steps:
            action = agent.select_action(obs, evaluate=True)
            obs, _, done, state = env.step(action)
            step_i += 1

        overhead_ms = (time.perf_counter() - t0) * 1000.0 / max(1, step_i)
        return compute_simulation_metrics(sim.completed_processes, sim.history, overhead_ms, total_processes=len(workload))

    def run_benchmark_suite(
        self,
        workload_types: Optional[List[str]] = None,
        num_seeds: int = 3,
        seeds: Optional[List[int]] = None
    ) -> pd.DataFrame:
        """Executes full benchmark suite across all baselines and workloads with standardized seeds."""
        workloads = workload_types or self.config.evaluation.workloads
        seeds_list = get_standard_seeds(num_seeds=num_seeds, explicit_seeds=seeds)
        records = []

        # Pretrain RL agent once with training horizon
        rl_agent = RLAgent()
        train_env = CoReOSGymEnv(max_steps=150)
        rl_agent.train(train_env, num_episodes=15)

        for w_type in workloads:
            for s in seeds_list:
                # Set exact reproducible seed without arbitrary offsets
                self.workload_gen.set_seed(s)
                base_procs = self.workload_gen.generate_workload(num_processes=40, workload_type=w_type)
                sim_cfg = SimulationConfig(random_seed=s)

                runs = {
                    "A_Conventional": ConventionalScheduler.run_round_robin(base_procs, quantum=4.0, config=sim_cfg),
                    "B_IndependentAgents": IndependentAgentScheduler.run(base_procs, config=sim_cfg),
                    "C_CoordNoConflict": self.run_baseline_c(base_procs, seed=s),
                    "D_ConflictNoHealing": self.run_baseline_d(base_procs, seed=s),
                    "E_CompleteCoReOS": self.run_baseline_e_complete(base_procs, seed=s),
                    "F_LearningRL": self.run_baseline_f_rl(base_procs, pre_trained_agent=rl_agent, seed=s, max_steps=300)
                }

                for b_name, m in runs.items():
                    records.append({
                        "baseline": b_name,
                        "workload": w_type,
                        "seed": s,
                        "total_processes": m["total_processes"],
                        "completed_processes": m["completed_processes"],
                        "unfinished_processes": m["unfinished_processes"],
                        "completion_rate": m["completion_rate"],
                        "avg_turnaround_time": m["avg_turnaround_time"],
                        "p95_turnaround_time": m["p95_turnaround_time"],
                        "avg_waiting_time": m["avg_waiting_time"],
                        "avg_response_time": m["avg_response_time"],
                        "throughput": m["throughput"],
                        "jains_fairness": m["jains_fairness_index"],
                        "thrashing_ticks": m["thrashing_ticks"],
                        "decision_overhead_ms": m["decision_overhead_ms"]
                    })

        return pd.DataFrame(records)
