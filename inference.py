#!/usr/bin/env python3
"""
Trading Environment Inference Script - OpenEnv Hackathon
========================================================

MANDATORY REQUIREMENTS (per OpenEnv spec):
- Environment variables: API_BASE_URL, MODEL_NAME, HF_TOKEN
- Script name: inference.py in project root
- LLM client: OpenAI Client for all API calls
- Output format: [START], [STEP], [END] logs (EXACT format below)

STDOUT FORMAT (must be EXACT):
  [START] task=<task_name> env=<benchmark> model=<model_name>
  [STEP]  step=<n> action=<action_str> reward=<0.00> done=<true|false> error=<msg|null>
  [END]   success=<true|false> steps=<n> rewards=<r1,r2,...,rn>

Rules:
  - One [START] line at episode begin.
  - One [STEP] line per step, immediately after env.step() returns.
  - One [END] line after env.close(), always emitted (even on exception).
  - reward and rewards are formatted to 2 decimal places.
  - done and success are lowercase booleans: true or false.
  - error: error message or null.
  - All fields on a single line with no newlines within a line.
"""

import os
import re
import sys
import textwrap
from typing import List, Optional

import requests
from openai import OpenAI

# Load .env file for local development (optional — not needed in Docker)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed (e.g. in Docker) — that's fine

# ============================================================================
# CONFIGURATION FROM ENVIRONMENT VARIABLES
# (Using os.getenv with default values as required by the spec)
# ============================================================================
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN")

# Validate HF_TOKEN as required by the spec
if HF_TOKEN is None:
    raise ValueError("HF_TOKEN environment variable is required")

# Local trading environment server
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
BENCHMARK = "trading_env"

# Task configurations
TASKS = ["easy", "medium", "hard"]
MAX_STEPS_PER_TASK = {"easy": 10, "medium": 15, "hard": 20}


# ============================================================================
# LOGGING FUNCTIONS — EXACT FORMAT PER SPEC
# ============================================================================

def log_start(task: str, env: str, model: str) -> None:
    """Log episode start - EXACT FORMAT."""
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    """Log each step - EXACT FORMAT with LOWERCASE booleans."""
    error_val = error if error else "null"
    done_str = "true" if done else "false"  # MUST BE LOWERCASE
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_str} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, rewards: List[float]) -> None:
    """Log episode end - EXACT FORMAT per spec (MUST INCLUDE score field)."""
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    success_str = "true" if success else "false"  # MUST BE LOWERCASE
    
    # Calculate a score strictly between 0 and 1
    # We use the final reward, or average reward, but clamp it to (0.01, 0.99)
    if rewards:
        avg_reward = sum(rewards) / len(rewards)
        score = max(min(avg_reward, 0.99), 0.01)
    else:
        score = 0.01
        
    print(f"[END] success={success_str} steps={steps} score={score:.4f} rewards={rewards_str}", flush=True)


# ============================================================================
# TRADING LOGIC
# ============================================================================

def build_trading_prompt(state: dict, task: str, step: int) -> str:
    """Build market state prompt for LLM decision."""
    current_price = state.get("current_price", 100.0)
    price_history = state.get("price_history", [100.0])
    portfolio_value = state.get("portfolio_value", 10000.0)
    cash_balance = state.get("cash_balance", 5000.0)
    shares_held = state.get("shares_held", 0)
    cost_basis = state.get("cost_basis", 100.0)
    max_drawdown = state.get("max_drawdown", 0.0)
    margin_level = state.get("margin_level", 9999.0)
    daily_pnl = state.get("daily_pnl", 0.0)

    # Price trend
    if len(price_history) > 1:
        trend_pct = ((price_history[-1] - price_history[0]) / price_history[0]) * 100
        trend = "UP" if trend_pct > 0 else "DOWN"
    else:
        trend = "STABLE"

    # Position metrics
    if shares_held > 0:
        position_pnl_pct = ((current_price - cost_basis) / cost_basis) * 100
    else:
        position_pnl_pct = 0.0

    prompt = textwrap.dedent(f"""
    You are a professional trading agent. Decide: BUY, SELL, or HOLD?

    MARKET (Step {step})
    Price: ${current_price:.2f} ({trend})
    History: {str(price_history[-5:])}
    Daily P&L: ${daily_pnl:.2f}

    PORTFOLIO
    Total Value: ${portfolio_value:.2f}
    Cash: ${cash_balance:.2f}
    Position: {shares_held} @ ${cost_basis:.2f} ({position_pnl_pct:+.1f}%)

    METRICS
    Max Drawdown: {max_drawdown:.2%}
    Margin Level: {margin_level:.1f}x

    TASK: {task.upper()} (Easy=hold, Medium=balance, Hard=risk-manage)

    RESPOND WITH ONLY: ACTION QUANTITY
    (Examples: BUY 10, SELL 5, HOLD 0)
    """).strip()

    return prompt


def parse_action_response(response: str) -> tuple:
    """Parse LLM response into (action, quantity)."""
    try:
        # Extract last line with ACTION QUANTITY pattern
        lines = response.strip().split('\n')
        for line in reversed(lines):
            line = line.strip().upper()
            # Match "BUY|SELL|HOLD" followed by number
            match = re.search(r'(BUY|SELL|HOLD)\s+(\d+)', line)
            if match:
                action = match.group(1)
                qty = int(match.group(2))
                return action, max(0, min(qty, 100))

        # Fallback: just find the action word
        for action in ['BUY', 'SELL', 'HOLD']:
            if action in response.upper():
                return action, 0

        return "HOLD", 0
    except Exception:
        return "HOLD", 0


def run_trading_episode(task: str, client: OpenAI) -> tuple:
    """
    Run single trading episode.
    Connects to http://localhost:8000 trading environment server.
    Returns: (rewards, steps_taken, success)
    """
    max_steps = MAX_STEPS_PER_TASK[task]
    log_start(task=task, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    success = False

    try:
        # Reset environment
        reset_resp = requests.post(f"{SERVER_URL}/reset", json={"task": task}, timeout=10)
        if reset_resp.status_code != 200:
            log_end(success=False, steps=0, rewards=[])
            return [], 0, False

        state = reset_resp.json().get("observation", {})

        # Episode loop
        for step in range(1, max_steps + 1):
            try:
                # Get LLM decision
                prompt = build_trading_prompt(state, task, step)

                llm_resp = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "You are a trading agent. Respond with ACTION QUANTITY only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=150
                )

                action_str = llm_resp.choices[0].message.content
                action, quantity = parse_action_response(action_str)

                # Execute action in environment
                step_resp = requests.post(
                    f"{SERVER_URL}/step",
                    json={"action": {"action": action, "quantity": quantity, "ticker": "STOCK"}},
                    timeout=10
                )

                if step_resp.status_code != 200:
                    error_msg = f"HTTP {step_resp.status_code}"
                    log_step(step=step, action=f"{action} {quantity}", reward=0.01, done=True, error=error_msg)
                    rewards.append(0.01)
                    steps_taken = step
                    break

                result = step_resp.json()
                raw_reward = result.get("reward", 0.01)
                reward = max(min(raw_reward, 0.99), 0.01)  # Strictly (0, 1)
                done = result.get("done", False)
                state = result.get("observation", state)
                error = result.get("last_action_error", None)

                rewards.append(reward)
                log_step(step=step, action=f"{action} {quantity}", reward=reward, done=done, error=error)
                steps_taken = step

                if done:
                    break

            except requests.RequestException as e:
                log_step(step=step, action="ERROR", reward=0.01, done=True, error=str(e))
                rewards.append(0.01)
                steps_taken = step
                break
            except Exception as e:
                log_step(step=step, action="ERROR", reward=0.01, done=True, error=str(e))
                rewards.append(0.01)
                steps_taken = step
                break

        # Determine success based on having any positive reward
        success = any(r > 0 for r in rewards)

    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr, flush=True)
        log_end(success=False, steps=steps_taken, rewards=rewards)
        return rewards, steps_taken, False

    log_end(success=success, steps=steps_taken, rewards=rewards)
    return rewards, steps_taken, success


def main() -> None:
    """Run all 3 tasks."""
    try:
        # Initialize OpenAI client with HuggingFace API
        client = OpenAI(api_key=HF_TOKEN, base_url=API_BASE_URL)

        # Run all 3 tasks
        for task in TASKS:
            run_trading_episode(task, client)

    except Exception as e:
        print(f"[ERROR] {str(e)}", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main()
