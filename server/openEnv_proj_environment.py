# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Trading Environment Implementation.

A reinforcement learning environment where an AI agent learns to execute trades,
manage risk, and maximize profit through dynamic price discovery. Supports 3 difficulty
levels: Easy (uptrend), Medium (mean-reverting), Hard (high volatility with margin).
"""

import random
from uuid import uuid4
from typing import Tuple
import math

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import TradingAction, TradingObservation
except ImportError:
    from models import TradingAction, TradingObservation


class TradingEnvironment(Environment):
    """
    A trading environment for reinforcement learning.
    
    Agent learns to: BUY, SELL, or HOLD a single stock.
    Episode ends when: margin level < 1.0 (liquidation) or max steps reached.
    Reward: daily P&L with risk penalties, scaled to [0, 1].
    """

    SUPPORTS_CONCURRENT_SESSIONS: bool = True
    
    # Task configurations: (name, volatility, drift, margin_requirement)
    TASKS = {
        "easy": {"volatility": 0.10, "drift": 0.02, "margin_req": float('inf'), "max_steps": 10},
        "medium": {"volatility": 0.20, "drift": 0.00, "margin_req": float('inf'), "max_steps": 15},
        "hard": {"volatility": 0.30, "drift": -0.01, "margin_req": 2.0, "max_steps": 20},
    }
    
    def __init__(self, task: str = "easy"):
        """Initialize the trading environment."""
        self.task_name = task.lower()
        if self.task_name not in self.TASKS:
            self.task_name = "easy"
        
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        # Portfolio state
        self.initial_balance = 10000.0
        self.cash_balance = self.initial_balance
        self.shares_held = 0
        self.cost_basis = 0.0
        self.holdings_value = 0.0
        
        # Price tracking
        self.current_price = 100.0
        self.price_history = [100.0]
        self.peak_value = self.initial_balance
        self.trough_value = self.initial_balance
        
        # Trading history
        self.transactions = []
        self.daily_returns = []
        
        # Get task config
        self.config = self.TASKS[self.task_name]
        self.volatility = self.config["volatility"]
        self.drift = self.config["drift"]
        self.margin_requirement = self.config["margin_req"]
        self.max_steps = self.config["max_steps"]

    def reset(self) -> TradingObservation:
        """Reset the environment for a new episode."""
        self._state = State(episode_id=str(uuid4()), step_count=0)
        
        self.cash_balance = self.initial_balance
        self.shares_held = 0
        self.cost_basis = 0.0
        self.current_price = 100.0
        self.price_history = [100.0]
        self.peak_value = self.initial_balance
        self.trough_value = self.initial_balance
        self.transactions = []
        self.daily_returns = []
        
        return self._get_observation(reward=0.0, done=False)

    def step(self, action: TradingAction) -> TradingObservation:
        """Execute one step in the environment."""
        self._state.step_count += 1
        
        # Simulate price movement (GBM: dS = mu*S*dt + sigma*S*dW)
        dt = 1.0 / 252.0  # daily timestep
        dW = random.gauss(0, math.sqrt(dt))
        price_change = self.current_price * (self.drift * dt + self.volatility * dW)
        self.current_price = max(self.current_price + price_change, 0.01)  # avoid negative prices
        self.price_history.append(self.current_price)
        if len(self.price_history) > 5:
            self.price_history.pop(0)
        
        # Get previous portfolio value for P&L calculation
        prev_portfolio_value = self.cash_balance + self.shares_held * (self.price_history[-2] if len(self.price_history) > 1 else self.current_price)
        
        # Execute action
        action_type = action.action.upper()
        quantity = max(0, action.quantity)
        
        if action_type == "BUY" and quantity > 0:
            cost = quantity * self.current_price
            if cost <= self.cash_balance:
                self.cash_balance -= cost
                if self.shares_held == 0:
                    self.cost_basis = self.current_price
                    self.shares_held += quantity
                else:
                    # Update average cost basis
                    total_cost = self.shares_held * self.cost_basis + cost
                    self.shares_held += quantity
                    self.cost_basis = total_cost / self.shares_held
                self.transactions.append({"action": "BUY", "qty": quantity, "price": self.current_price})
        
        elif action_type == "SELL" and quantity > 0:
            if quantity <= self.shares_held:
                proceeds = quantity * self.current_price
                self.cash_balance += proceeds
                self.shares_held -= quantity
                self.transactions.append({"action": "SELL", "qty": quantity, "price": self.current_price})
        
        # Calculate portfolio values
        self.holdings_value = self.shares_held * self.current_price
        portfolio_value = self.cash_balance + self.holdings_value
        
        # Calculate daily P&L
        daily_pnl = portfolio_value - prev_portfolio_value
        self.daily_returns.append(daily_pnl)
        
        # Update peak/trough for drawdown
        self.peak_value = max(self.peak_value, portfolio_value)
        self.trough_value = min(self.trough_value, portfolio_value)
        
        max_drawdown = (self.peak_value - self.trough_value) / self.peak_value if self.peak_value > 0 else 0.0
        
        # Calculate margin level
        if math.isinf(self.margin_requirement):
            margin_level = float('inf')
        else:
            margin_requirement_amount = self.holdings_value * (self.margin_requirement - 1.0) if self.margin_requirement > 1.0 else 0.0
            margin_level = portfolio_value / (margin_requirement_amount + 1e-6) if margin_requirement_amount > 0 else float('inf')
        
        # Determine if episode is done
        is_done = False
        if self._state.step_count >= self.max_steps:
            is_done = True
        if not math.isinf(self.margin_requirement) and margin_level < 1.0:
            is_done = True  # Margin call - liquidation
        
        # Calculate reward based on task grader
        reward = self._calculate_reward(portfolio_value, daily_pnl, max_drawdown, is_done)
        
        return self._get_observation(reward=reward, done=is_done)

    def _get_observation(self, reward: float, done: bool) -> TradingObservation:
        """Construct TradingObservation from current state."""
        portfolio_value = self.cash_balance + self.holdings_value
        
        # Calculate max drawdown
        max_dd = (self.peak_value - self.trough_value) / self.peak_value if self.peak_value > 0 else 0.0
        
        # Calculate margin level
        if math.isinf(self.margin_requirement):
            margin_level = float('inf')
        else:
            margin_req_amt = self.holdings_value * (self.margin_requirement - 1.0) if self.margin_requirement > 1.0 else 0.0
            margin_level = portfolio_value / (margin_req_amt + 1e-6) if margin_req_amt > 0 else float('inf')
        
        # Convert infinity to a large number for JSON serialization
        margin_level_val = 9999.0 if math.isinf(margin_level) else round(margin_level, 2)
        
        return TradingObservation(
            current_price=round(self.current_price, 2),
            price_history=[round(p, 2) for p in self.price_history[-5:]],
            portfolio_value=round(portfolio_value, 2),
            cash_balance=round(self.cash_balance, 2),
            shares_held=self.shares_held,
            cost_basis=round(self.cost_basis, 2),
            max_drawdown=round(max_dd, 4),
            margin_level=margin_level_val,
            step_count=self._state.step_count,
            task_name=self.task_name,
            total_transactions=len(self.transactions),
            daily_pnl=round(self.daily_returns[-1] if self.daily_returns else 0.0, 2),
            done=done,
            reward=round(reward, 4),
        )

    def _calculate_reward(self, portfolio_value: float, daily_pnl: float, max_drawdown: float, done: bool) -> float:
        """
        Calculate normalized reward [0, 1] based on task difficulty.
        
        Reward components:
        1. Portfolio return vs initial balance (main signal)
        2. Position-holding reward (encourages trading, not idle)
        3. Terminal bonus for profitable episodes
        """
        # Portfolio return as percentage of initial balance
        portfolio_return_pct = ((portfolio_value - self.initial_balance) / self.initial_balance) * 100
        
        # Base reward: portfolio performance relative to initial
        # Scale so that 0% return = 0.3, +1% = 0.5, -1% = 0.1
        base_reward = 0.3 + (portfolio_return_pct * 0.2)
        
        # Position reward: small bonus for having exposure (encourages trading)
        position_reward = 0.1 if self.shares_held > 0 else 0.0
        
        # Daily P&L component (amplified to be visible)
        daily_component = 0.0
        if daily_pnl > 0:
            daily_component = min(daily_pnl / 100.0, 0.3)  # Cap at 0.3
        
        if self.task_name == "easy":
            # Easy: reward holding and positive returns generously
            reward = base_reward + position_reward + daily_component
            
        elif self.task_name == "medium":
            # Medium: balance profit vs risk
            risk_penalty = max_drawdown * 0.5 if max_drawdown > 0.01 else 0.0
            reward = base_reward + position_reward + daily_component - risk_penalty
            
        else:  # hard
            # Hard: heavy risk management focus
            risk_penalty = max_drawdown * 1.0 if max_drawdown > 0.005 else 0.0
            margin_penalty = 0.2 if not math.isinf(self.margin_requirement) and self.holdings_value > self.cash_balance else 0.0
            reward = base_reward + daily_component - risk_penalty - margin_penalty
        
        # Terminal bonus/penalty
        if done:
            if portfolio_value > self.initial_balance:
                reward += 0.2  # Bonus for profitable episode
            elif portfolio_value < self.initial_balance * 0.98:
                reward -= 0.1  # Penalty for significant loss
        
        # Clamp to [0, 1]
        return max(min(reward, 1.0), 0.0)

    def _calculate_volatility(self) -> float:
        """Calculate daily return volatility."""
        if len(self.daily_returns) < 2:
            return 1.0
        mean_return = sum(self.daily_returns) / len(self.daily_returns)
        variance = sum((r - mean_return) ** 2 for r in self.daily_returns) / len(self.daily_returns)
        return math.sqrt(variance)

    @property
    def state(self) -> State:
        """Get the current environment state."""
        return self._state

