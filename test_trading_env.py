#!/usr/bin/env python3
"""
Quick test script to validate TradingEnvironment functionality.
Tests core logic without requiring FastAPI server.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server.openEnv_proj_environment import TradingEnvironment
from models import TradingAction

def test_easy_task():
    """Test easy task (uptrend market)."""
    print("\n" + "="*60)
    print("Testing EASY Task (Uptrend)")
    print("="*60)
    
    env = TradingEnvironment(task="easy")
    obs = env.reset()
    
    print(f"Reset: Portfolio=${obs.portfolio_value:.2f}, Price=${obs.current_price:.2f}")
    assert obs.portfolio_value == 10000.0, "Initial portfolio should be $10,000"
    assert len(obs.price_history) == 1, "Price history should have 1 element after reset"
    
    # Run a few steps
    for step in range(1, 6):
        action = TradingAction(action="BUY", quantity=5) if step % 2 == 1 else TradingAction(action="HOLD", quantity=0)
        obs = env.step(action)
        
        print(f"Step {step}: Action={action.action:4s} Qty={action.quantity:3d} | "
              f"Price=${obs.current_price:7.2f} | Portfolio=${obs.portfolio_value:7.2f} | "
              f"Reward={obs.reward:.4f} | Shares={obs.shares_held} | Done={obs.done}")
        
        assert 0 <= obs.reward <= 1, f"Reward must be in [0,1], got {obs.reward}"
        assert obs.step_count == step, f"Step count mismatch: {obs.step_count} != {step}"
    
    print(f"✓ Easy task validation passed")
    return True


def test_medium_task():
    """Test medium task (mean-reverting market)."""
    print("\n" + "="*60)
    print("Testing MEDIUM Task (Mean-Revert)")
    print("="*60)
    
    env = TradingEnvironment(task="medium")
    obs = env.reset()
    
    print(f"Reset: Portfolio=${obs.portfolio_value:.2f}, Task={obs.task_name}")
    assert obs.task_name == "medium", "Task name should be 'medium'"
    
    rewards = []
    for step in range(1, 6):
        action = TradingAction(action="BUY", quantity=3)
        obs = env.step(action)
        rewards.append(obs.reward)
        
        print(f"Step {step}: Price=${obs.current_price:7.2f} | Portfolio=${obs.portfolio_value:7.2f} | "
              f"Reward={obs.reward:.4f} | MaxDD={obs.max_drawdown:.4f}")
    
    print(f"  Total rewards: {sum(rewards):.4f}, Avg reward: {sum(rewards)/len(rewards):.4f}")
    print(f"✓ Medium task validation passed")
    return True


def test_hard_task():
    """Test hard task (volatile market with margin)."""
    print("\n" + "="*60)
    print("Testing HARD Task (Volatility + Margin)")
    print("="*60)
    
    env = TradingEnvironment(task="hard")
    obs = env.reset()
    
    print(f"Reset: Portfolio=${obs.portfolio_value:.2f}, Margin={obs.margin_level}")
    assert not hasattr(obs.margin_level, '__iter__'), "Margin level should be numeric"
    
    done = False
    step_count = 0
    for step in range(1, 11):
        # Oscillate between BUY and SELL
        action = TradingAction(action="BUY", quantity=20) if step % 2 == 1 else TradingAction(action="SELL", quantity=10)
        obs = env.step(action)
        step_count = step
        
        print(f"Step {step}: Action={action.action:4s} | Price=${obs.current_price:7.2f} | "
              f"Portfolio=${obs.portfolio_value:7.2f} | Margin={obs.margin_level:.2f}x | "
              f"Reward={obs.reward:.4f} | Done={obs.done}")
        
        if obs.done:
            done = True
            print(f"  Episode ended at step {step}")
            break
    
    print(f"✓ Hard task validation passed (Final: Done={done}, Steps={step_count})")
    return True


def test_reward_scaling():
    """Test reward scaling is correctly bounded to [0, 1]."""
    print("\n" + "="*60)
    print("Testing Reward Scaling")
    print("="*60)
    
    for task_name in ["easy", "medium", "hard"]:
        env = TradingEnvironment(task=task_name)
        obs = env.reset()
        
        rewards = []
        for step in range(1, 6):
            action = TradingAction(action="BUY", quantity=10)
            obs = env.step(action)
            rewards.append(obs.reward)
            
            assert 0.0 <= obs.reward <= 1.0, f"Reward {obs.reward} out of bounds for task {task_name}"
        
        print(f"  {task_name:8s}: rewards={[f'{r:.3f}' for r in rewards]}")
    
    print(f"✓ Reward scaling validation passed")
    return True


def test_portfolio_tracking():
    """Test portfolio value tracking."""
    print("\n" + "="*60)
    print("Testing Portfolio Tracking")
    print("="*60)
    
    env = TradingEnvironment(task="easy")
    obs = env.reset()
    initial_value = obs.portfolio_value
    
    # Buy shares
    action = TradingAction(action="BUY", quantity=50)
    obs = env.step(action)
    
    cost = 50 * obs.current_price
    expected_cash = initial_value - cost
    expected_holdings = 50 * obs.current_price
    expected_portfolio = expected_cash + expected_holdings
    
    print(f"After BUY 50 shares:")
    print(f"  Price: ${obs.current_price:.2f}")
    print(f"  Cash: ${obs.cash_balance:.2f} (expected ~${expected_cash:.2f})")
    print(f"  Holdings: ${50 * obs.current_price:.2f}")
    print(f"  Portfolio: ${obs.portfolio_value:.2f} (expected ~${expected_portfolio:.2f})")
    
    # Verify portfolio is cash + holdings
    portfolio_check = obs.cash_balance + (obs.shares_held * obs.current_price)
    assert abs(portfolio_check - obs.portfolio_value) < 0.01, "Portfolio calculation error"
    
    print(f"✓ Portfolio tracking validation passed")
    return True


def main():
    """Run all tests."""
    print("\n" + "█"*60)
    print("█ Trading Environment Validation Tests")
    print("█"*60)
    
    tests = [
        test_easy_task,
        test_medium_task,
        test_hard_task,
        test_reward_scaling,
        test_portfolio_tracking,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} FAILED: {str(e)}")
            failed += 1
    
    print("\n" + "█"*60)
    print(f"█ Results: {passed} passed, {failed} failed")
    print("█"*60 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
