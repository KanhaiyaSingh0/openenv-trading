# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""
Data models for the Trading Environment.

The trading environment is a reinforcement learning environment where an AI agent
learns to execute trades, manage risk, and maximize profit through dynamic price discovery.
"""

from typing import Dict, List
from openenv.core.env_server.types import Action, Observation
from pydantic import Field


class TradingAction(Action):
    """Action for the Trading environment - trading decisions."""

    action: str = Field(..., description="Trading action: BUY, SELL, or HOLD")
    quantity: int = Field(default=0, description="Number of shares to buy/sell (0 for HOLD)")
    ticker: str = Field(default="STOCK", description="Stock ticker symbol")


class TradingObservation(Observation):
    """Observation from the Trading environment - market and portfolio state."""

    # Market data
    current_price: float = Field(default=100.0, description="Current stock price")
    price_history: List[float] = Field(default_factory=list, description="Last 5 prices [oldest...newest]")
    
    # Portfolio state
    portfolio_value: float = Field(default=10000.0, description="Total portfolio value (cash + holdings)")
    cash_balance: float = Field(default=10000.0, description="Available cash")
    shares_held: int = Field(default=0, description="Number of shares held")
    cost_basis: float = Field(default=0.0, description="Average cost per share")
    
    # Risk metrics
    max_drawdown: float = Field(default=0.0, description="Maximum drawdown from peak")
    margin_level: float = Field(default=float('inf'), description="Margin level (portfolio_value / margin_requirement)")
    
    # Episode progress
    step_count: int = Field(default=0, description="Current step number")
    task_name: str = Field(default="easy", description="Current task: easy, medium, or hard")
    
    # Additional info
    total_transactions: int = Field(default=0, description="Total number of trades executed")
    daily_pnl: float = Field(default=0.0, description="Daily profit/loss")
