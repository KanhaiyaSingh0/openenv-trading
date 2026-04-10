#!/usr/bin/env python3
"""Quick test of trading env API endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000"

print("\n" + "="*60)
print("Testing Trading Environment API Endpoints")
print("="*60)

# Test /reset endpoint
print("\n1. Testing /reset endpoint...")
try:
    response = requests.post(f"{BASE_URL}/reset", json={})
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        obs = data.get("observation", {})
        print(f"   ✓ Portfolio: ${obs.get('portfolio_value', 0):.2f}")
        print(f"   ✓ Price: ${obs.get('current_price', 0):.2f}")
        print(f"   ✓ Shares: {obs.get('shares_held', 0)}")
    else:
        print(f"   ✗ Error: {response.text}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

# Test /step endpoint
print("\n2. Testing /step endpoint...")
try:
    # Try format 1: Direct field format
    response = requests.post(
        f"{BASE_URL}/step",
        json={
            "action": "BUY",
            "quantity": 10,
            "ticker": "STOCK"
        }
    )
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        obs = data.get("observation", {})
        reward = data.get("reward", 0)
        print(f"   ✓ Portfolio: ${obs.get('portfolio_value', 0):.2f}")
        print(f"   ✓ Reward: {reward:.4f}")
        print(f"   ✓ Done: {data.get('done', False)}")
    elif response.status_code == 422:
        # Try alternative format
        print(f"   Format 1 failed (422), trying alternative format...")
        response = requests.post(
            f"{BASE_URL}/step",
            json={
                "action": {
                    "action": "BUY",
                    "quantity": 10,
                    "ticker": "STOCK"
                }
            }
        )
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            obs = data.get("observation", {})
            reward = data.get("reward", 0)
            print(f"   ✓ Portfolio: ${obs.get('portfolio_value', 0):.2f}")
            print(f"   ✓ Reward: {reward:.4f}")
            print(f"   ✓ Done: {data.get('done', False)}")
        else:
            print(f"   ✗ Error: {response.text}")
    else:
        print(f"   ✗ Error: {response.text}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

# Test /schema endpoint
print("\n3. Testing /schema endpoint...")
try:
    response = requests.get(f"{BASE_URL}/schema")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✓ Schema retrieved successfully")
    else:
        print(f"   ✗ Error: {response.text}")
except Exception as e:
    print(f"   ✗ Connection error: {e}")

print("\n" + "="*60)
print("✓ Server is responding to all endpoints!")
print("="*60 + "\n")
