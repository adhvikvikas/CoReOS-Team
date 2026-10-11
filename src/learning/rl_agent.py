"""
CoReOS Reinforcement Learning Agent
Tabular / Function-Approximated Q-Learning Agent for discrete multi-agent coordination.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from src.learning.env import CoReOSEnv


class RLAgent:
    """
    Q-Learning coordination agent trained on simulation transitions.
    """

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
        
        # Discretized Q-table: mapping discretized state tuple -> np.ndarray of shape (num_actions,)
        self.q_table: Dict[Tuple[int, ...], np.ndarray] = {}
        self.training_rewards: List[float] = []

    def _discretize_obs(self, obs: np.ndarray) -> Tuple[int, ...]:
        # Discretize continuous 8D vector into small bucket tuples
        bins = np.digitize(obs, np.linspace(0.0, 1.0, self.obs_bins + 1)[1:-1])
        return tuple(bins.tolist())

    def get_q_values(self, state_key: Tuple[int, ...]) -> np.ndarray:
        if state_key not in self.q_table:
            self.q_table[state_key] = np.zeros(self.num_actions, dtype=np.float32)
        return self.q_table[state_key]

    def select_action(self, obs: np.ndarray, evaluate: bool = False) -> int:
        state_key = self._discretize_obs(obs)
        q_vals = self.get_q_values(state_key)

        if not evaluate and np.random.uniform(0.0, 1.0) < self.epsilon:
            return int(np.random.randint(0, self.num_actions))
        return int(np.argmax(q_vals))

    def update(
        self,
        obs: np.ndarray,
        action: int,
        reward: float,
        next_obs: np.ndarray,
        done: bool
    ):
        s_key = self._discretize_obs(obs)
        next_s_key = self._discretize_obs(next_obs)

        current_q = self.get_q_values(s_key)[action]
        next_max_q = np.max(self.get_q_values(next_s_key)) if not done else 0.0

        # Bellman update
        new_q = current_q + self.alpha * (reward + self.gamma * next_max_q - current_q)
        self.q_table[s_key][action] = new_q

    def train(self, env: CoReOSEnv, num_episodes: int = 25) -> List[float]:
        """Trains agent across multiple simulation episodes."""
        episode_rewards = []

        for ep in range(num_episodes):
            obs = env.reset(seed=ep, workload_type="steady_state")
            total_reward = 0.0
            done = False

            while not done:
                action = self.select_action(obs)
                next_obs, reward, done, _ = env.step(action)
                self.update(obs, action, reward, next_obs, done)
                obs = next_obs
                total_reward += reward

            self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
            episode_rewards.append(total_reward)

        self.training_rewards = episode_rewards
        return episode_rewards
