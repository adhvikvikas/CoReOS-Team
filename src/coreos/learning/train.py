"""
CoReOS Reinforcement Learning Agent & Training Pipeline
Implements Q-Learning on dynamic simulation transitions with model persistence.
"""

from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import json
import numpy as np
from src.coreos.learning.environment import CoReOSGymEnv


class RLAgent:
    def __init__(
        self,
        num_actions: int = 4,
        obs_bins: int = 4,
        alpha: float = 0.1,
        gamma: float = 0.95,
        epsilon: float = 0.2,
        epsilon_min: float = 0.02,
        epsilon_decay: float = 0.98
    ):
        self.num_actions = num_actions
        self.obs_bins = obs_bins
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        self.q_table: Dict[str, List[float]] = {}
        self.training_rewards: List[float] = []

    def _discretize_obs(self, obs: np.ndarray) -> str:
        bins = np.digitize(obs, np.linspace(0.0, 1.0, self.obs_bins + 1)[1:-1])
        return str(tuple(bins.tolist()))

    def get_q_values(self, state_key: str) -> List[float]:
        if state_key not in self.q_table:
            self.q_table[state_key] = [0.0] * self.num_actions
        return self.q_table[state_key]

    def select_action(self, obs: np.ndarray, evaluate: bool = False) -> int:
        state_key = self._discretize_obs(obs)
        q_vals = self.get_q_values(state_key)
        if not evaluate and np.random.uniform(0.0, 1.0) < self.epsilon:
            return int(np.random.randint(0, self.num_actions))
        return int(np.argmax(q_vals))

    def update(self, obs: np.ndarray, action: int, reward: float, next_obs: np.ndarray, done: bool):
        s_key = self._discretize_obs(obs)
        next_s_key = self._discretize_obs(next_obs)
        curr_q = self.get_q_values(s_key)[action]
        next_max = max(self.get_q_values(next_s_key)) if not done else 0.0
        new_q = curr_q + self.alpha * (reward + self.gamma * next_max - curr_q)
        self.q_table[s_key][action] = float(new_q)

    def train(self, env: CoReOSGymEnv, num_episodes: int = 25) -> List[float]:
        rewards = []
        for ep in range(num_episodes):
            obs = env.reset(seed=ep, workload_type="steady_state")
            total_r = 0.0
            done = False
            while not done:
                action = self.select_action(obs)
                next_obs, reward, done, _ = env.step(action)
                self.update(obs, action, reward, next_obs, done)
                obs = next_obs
                total_r += reward
            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            rewards.append(total_r)
        self.training_rewards = rewards
        return rewards

    def save(self, filepath: str):
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "q_table": self.q_table,
                "epsilon": self.epsilon,
                "training_rewards": self.training_rewards
            }, f)

    def load(self, filepath: str):
        path = Path(filepath)
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                self.q_table = data.get("q_table", {})
                self.epsilon = data.get("epsilon", 0.05)
                self.training_rewards = data.get("training_rewards", [])


def train_rl_model(episodes: int = 20, save_path: str = "reports/rl_checkpoint.json") -> RLAgent:
    print(f"[RL Trainer] Training Q-learning coordination agent for {episodes} episodes...")
    env = CoReOSGymEnv(max_steps=150)
    agent = RLAgent()
    agent.train(env, num_episodes=episodes)
    agent.save(save_path)
    print(f"[RL Trainer] Checkpoint saved to {save_path}")
    return agent


if __name__ == "__main__":
    train_rl_model()
