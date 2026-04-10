# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""Trading Environment Client."""

from typing import Dict
import sys
import os

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

# Handle both relative and absolute imports
try:
    from models import TradingAction, TradingObservation
except ImportError:
    try:
        from .models import TradingAction, TradingObservation
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from models import TradingAction, TradingObservation


class TradingEnv(
    EnvClient[TradingAction, TradingObservation, State]
):
    """
    Client for the Trading Environment.

    This client maintains a persistent WebSocket connection to the trading environment server,
    enabling efficient multi-step interactions for the RL trading agent.

    Example:
        >>> with TradingEnv(base_url="http://localhost:8000") as client:
        ...     result = client.reset()
        ...     print(f"Portfolio: ${result.observation.portfolio_value}")
        ...
        ...     result = client.step(TradingAction(action="BUY", quantity=10))
        ...     print(f"New portfolio: ${result.observation.portfolio_value}")

    Example with Docker:
        >>> client = TradingEnv.from_docker_image("trading-env:latest")
        >>> try:
        ...     result = client.reset()
        ...     result = client.step(TradingAction(action="BUY", quantity=5))
        ... finally:
        ...     client.close()
    """

    def _step_payload(self, action: TradingAction) -> Dict:
        """
        Convert TradingAction to JSON payload.

        Args:
            action: TradingAction instance

        Returns:
            Dictionary representation suitable for JSON encoding
        """
        return {
            "action": action.action,
            "quantity": action.quantity,
            "ticker": action.ticker,
        }

    def _parse_result(self, payload: Dict) -> StepResult[TradingObservation]:
        """
        Parse server response into StepResult[TradingObservation].

        Args:
            payload: JSON response data from server

        Returns:
            StepResult with TradingObservation
        """
        obs_data = payload.get("observation", {})
        observation = TradingObservation(
            current_price=obs_data.get("current_price", 100.0),
            price_history=obs_data.get("price_history", []),
            portfolio_value=obs_data.get("portfolio_value", 10000.0),
            cash_balance=obs_data.get("cash_balance", 10000.0),
            shares_held=obs_data.get("shares_held", 0),
            cost_basis=obs_data.get("cost_basis", 0.0),
            max_drawdown=obs_data.get("max_drawdown", 0.0),
            margin_level=obs_data.get("margin_level", float('inf')),
            step_count=obs_data.get("step_count", 0),
            task_name=obs_data.get("task_name", "easy"),
            total_transactions=obs_data.get("total_transactions", 0),
            daily_pnl=obs_data.get("daily_pnl", 0.0),
            done=payload.get("done", False),
            reward=payload.get("reward"),
            metadata=obs_data.get("metadata", {}),
        )

        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict) -> State:
        """
        Parse server response into State object.

        Args:
            payload: JSON response from state request

        Returns:
            State object with episode_id and step_count
        """
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
