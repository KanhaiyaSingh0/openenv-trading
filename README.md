---
title: Trading Environment - OpenEnv
emoji: 📈
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
app_port: 8000
base_path: /web
tags:
  - openenv
  - reinforcement-learning
  - trading
  - finance
---

# Trading Environment - OpenEnv Hackathon

A reinforcement learning environment where an AI agent learns to execute trades, manage portfolio risk, and maximize profit through dynamic price discovery. Built for the OpenEnv Hackathon.

## Overview

This environment simulates a single-stock trading market where an agent must decide when to BUY, SELL, or HOLD shares. The agent receives realistic market state observations and learns to optimize trading decisions through reward signals.

**Key Features:**
- **Realistic price dynamics** — Geometric Brownian Motion with configurable volatility and drift
- **Portfolio management** — Tracks cash, holdings, cost basis, and drawdowns
- **Risk constraints** — Margin system on hard difficulty (liquidation on margin call)
- **3 difficulty levels** — Easy (uptrend), Medium (mean-reversion), Hard (volatility + margin)
- **Scalable reward** — Profit-based rewards with risk penalties and efficiency bonuses

## Quick Start

### Installation

```bash
# Clone the repo
git clone <repo_url>
cd openenv_trading

# Install dependencies
pip install -r server/requirements.txt

# Set environment variables
export API_BASE_URL="https://api-inference.huggingface.co/v1"
export MODEL_NAME="meta-llama/Llama-2-7b-chat-hf"
export HF_TOKEN="your_hf_token_here"
```

### Run Locally (HTTP Server)

```bash
# Start the FastAPI server
python -m server.app --port 8000

# In another terminal, run inference
python inference.py
```

### Run with Docker

```bash
# Build Docker image
docker build -t trading-env:latest .

# Run container
docker run -p 8000:8000 trading-env:latest

# Test endpoint
curl http://localhost:8000/reset
```

## Environment Specification

### Action Space

```python
class TradingAction:
    action: str       # "BUY", "SELL", or "HOLD"
    quantity: int     # 0-1000 shares
    ticker: str       # Stock symbol (default: "STOCK")
```

**Example actions:**
- `TradingAction(action="BUY", quantity=10)` — Purchase 10 shares
- `TradingAction(action="SELL", quantity=5)` — Sell 5 shares
- `TradingAction(action="HOLD", quantity=0)` — Do nothing

### Observation Space

```python
class TradingObservation:
    # Market data
    current_price: float          # Latest stock price
    price_history: List[float]    # Last 5 prices [oldest...newest]
    
    # Portfolio state
    portfolio_value: float        # Total value (cash + holdings)
    cash_balance: float           # Available cash
    shares_held: int              # Shares owned
    cost_basis: float             # Average cost per share
    
    # Risk metrics
    max_drawdown: float           # Peak-to-trough loss
    margin_level: float           # Current margin (∞ = unlimited)
    
    # Progress
    step_count: int               # Current step (1-based)
    task_name: str                # "easy", "medium", or "hard"
    total_transactions: int       # Total trades executed
    daily_pnl: float              # Daily profit/loss
    
    # Control
    done: bool                    # Episode termination flag
    reward: float                 # Step reward [0, 1]
```

### Tasks

#### Task 1: Easy (10 steps)
- **Market:** Steady uptrend (drift=+2%, volatility=10%)
- **Capital:** $10,000
- **Margin:** Unlimited (no liquidation risk)
- **Goal:** Achieve 10% gain ($1,000 profit)
- **Grader:** Score = (final_value - 10000) / 1000, clamped to [0, 1]

#### Task 2: Medium (15 steps)
- **Market:** Mean-reverting (drift=0%, volatility=20%)
- **Capital:** $10,000
- **Margin:** Unlimited
- **Goal:** Achieve risk-adjusted returns (Sharpe ratio > 0.5)
- **Grader:** Score = Sharpe(daily_returns), clamped to [0, 1]

#### Task 3: Hard (20 steps)
- **Market:** High volatility (drift=-1%, volatility=30%)
- **Capital:** $10,000
- **Margin:** 2:1 (max holdings worth 2x portfolio = margin call if ratio < 1.0)
- **Goal:** Achieve 20% gain while managing margin
- **Grader:** Score = max(profit / 2000, 0), clamped to [0, 1]

## API Endpoints

### POST /reset
Reset the environment for a new episode.

**Request:**
```json
{
  "task": "easy"  // optional: "easy", "medium", or "hard" (default: "easy")
}
```

**Response:**
```json
{
  "observation": {
    "current_price": 100.0,
    "price_history": [100.0],
    "portfolio_value": 10000.0,
    "cash_balance": 10000.0,
    "shares_held": 0,
    "cost_basis": 0.0,
    "max_drawdown": 0.0,
    "margin_level": Infinity,
    "step_count": 0,
    "task_name": "easy",
    "total_transactions": 0,
    "daily_pnl": 0.0
  },
  "done": false,
  "reward": 0.0
}
```

### POST /step
Execute one step in the environment.

**Request:**
```json
{
  "action": "BUY",
  "quantity": 10,
  "ticker": "STOCK"
}
```

**Response:**
```json
{
  "observation": {
    "current_price": 101.5,
    "price_history": [100.0, 101.5],
    "portfolio_value": 9845.0,
    "cash_balance": 9845.0,
    "shares_held": 10,
    "cost_basis": 100.0,
    "max_drawdown": 0.0155,
    "margin_level": Infinity,
    "step_count": 1,
    "task_name": "easy",
    "total_transactions": 1,
    "daily_pnl": 15.0
  },
  "done": false,
  "reward": 0.015
}
```

### GET /schema
Get action and observation schemas.

### GET /state
Get current environment state.

## Reward Function

Rewards are normalized to [0, 1] and calculated per task:

**Easy Task:**
```
gain = (portfolio_value - initial_balance) / initial_balance
reward = min(gain / 0.10, 1.0)  # Need 10% gain for max reward
```

**Medium Task:**
```
sharpe = mean(daily_returns) / std(daily_returns)
reward = min(sharpe / 0.5, 1.0)  # Need Sharpe > 0.5 for max reward
```

**Hard Task:**
```
gain = (portfolio_value - initial_balance) / initial_balance
drawdown_penalty = max_drawdown * 0.2
reward = max(gain - drawdown_penalty, 0)
reward = min(reward / 0.20, 1.0)  # Need 20% gain for max reward
```

## Inference Script

The `inference.py` script runs an LLM-based trading agent:

1. **Load LLM:** Initialize OpenAI client with HuggingFace endpoint
2. **Loop tasks:** For each task (easy → medium → hard):
   - Reset environment
   - Run up to max_steps:
     - Build market observation prompt
     - Call LLM for decision (BUY/SELL/HOLD)
     - Execute action in environment
     - Log [STEP] result
   - Log [END] with final score
3. **Output:** Logs follow [START] / [STEP] / [END] format

**Environment variables required:**
- `API_BASE_URL` — LLM API endpoint
- `MODEL_NAME` — LLM model identifier
- `HF_TOKEN` — HuggingFace API key

**Example run:**
```bash
$ python inference.py
[START] task=easy env=trading_env model=Llama-2-7b-chat-hf
[STEP] step=1 action=BUY 5 reward=0.05 done=false error=null
[STEP] step=2 action=HOLD 0 reward=0.02 done=false error=null
...
[END] success=true steps=10 score=0.500 rewards=0.05,0.02,...
[START] task=medium env=trading_env model=Llama-2-7b-chat-hf
...
```

## Running Submission Validation

Before submitting, validate your environment:

```bash
# Download validator
curl -fsSL https://raw.githubusercontent.com/meta-pytorch/OpenEnv/main/scripts/validate-submission.sh \
  | bash -s -- https://your-space.hf.space

# Or run locally
./validate-submission.sh http://localhost:8000
```

The validator checks:
1. ✅ HF Space endpoint responds to /reset and /step
2. ✅ Docker builds successfully
3. ✅ openenv validate passes
4. ✅ All 3 tasks run without errors
5. ✅ Scores are in [0, 1] range
6. ✅ inference.py completes in < 20 minutes

## Development & Testing

### Test locally

```python
from client import TradingEnv
from models import TradingAction

# Connect to local server
env = TradingEnv(base_url="http://localhost:8000")

# Reset
obs = env.reset()
print(f"Portfolio: ${obs.observation.portfolio_value}")

# Step
action = TradingAction(action="BUY", quantity=10)
result = env.step(action)
print(f"Reward: {result.reward}, Done: {result.done}")

# Close
env.close()
```

### Run tests

```bash
pytest tests/
```

## Architecture

```
openenv_trading/
├── models.py                          # TradingAction, TradingObservation
├── client.py                          # TradingEnv client
├── inference.py                       # LLM trading agent
├── openenv.yaml                       # OpenEnv spec
├── server/
│   ├── app.py                        # FastAPI app
│   ├── openEnv_proj_environment.py   # TradingEnvironment class
│   └── requirements.txt               # Dependencies
├── Dockerfile                         # Container setup
├── pyproject.toml                     # Package config
└── README.md                          # This file
```

## Requirements

- Python 3.10+
- OpenEnv Core 0.2.2+
- FastAPI 0.115+
- Uvicorn 0.24+
- OpenAI Python client
- NumPy (for reward calculations)

See `server/requirements.txt` and `pyproject.toml` for full dependency list.

## Performance

**Computational requirements:**
- Runtime: < 20 minutes for inference.py
- Memory: ~ 2-4 GB (environment + LLM inference)
- CPU: Multi-core recommended (2+ vCPU)
- Disk: ~ 50 MB (excluding model weights)

## Limitations & Future Work

**Current v1:**
- Single stock only (expandable to multi-asset)
- No short selling
- No options/derivatives
- Fixed 3 tasks (customizable via config)

**Future enhancements:**
- Multi-stock portfolio management
- Short selling, margin calls
- Real historical price data feeds
- More sophisticated agent architectures
- Live trading integration (paper trading)

## Support

For issues or questions:
- GitHub Issues: [repo_url]/issues
- Email: support@openenv.org
- Discord: [community_link]

## License

BSD-3-Clause License — See LICENSE file

---

**Built for OpenEnv Hackathon 2026**

- Connecting to the environment
- Container cleanup when you call `close()`

## Building the Docker Image

Before using the environment, you need to build the Docker image:

```bash
# From project root
docker build -t openEnv_proj-env:latest -f server/Dockerfile .
```

## Deploying to Hugging Face Spaces

You can easily deploy your OpenEnv environment to Hugging Face Spaces using the `openenv push` command:

```bash
# From the environment directory (where openenv.yaml is located)
openenv push

# Or specify options
openenv push --namespace my-org --private
```

The `openenv push` command will:
1. Validate that the directory is an OpenEnv environment (checks for `openenv.yaml`)
2. Prepare a custom build for Hugging Face Docker space (enables web interface)
3. Upload to Hugging Face (ensuring you're logged in)

### Prerequisites

- Authenticate with Hugging Face: The command will prompt for login if not already authenticated

### Options

- `--directory`, `-d`: Directory containing the OpenEnv environment (defaults to current directory)
- `--repo-id`, `-r`: Repository ID in format 'username/repo-name' (defaults to 'username/env-name' from openenv.yaml)
- `--base-image`, `-b`: Base Docker image to use (overrides Dockerfile FROM)
- `--private`: Deploy the space as private (default: public)

### Examples

```bash
# Push to your personal namespace (defaults to username/env-name from openenv.yaml)
openenv push

# Push to a specific repository
openenv push --repo-id my-org/my-env

# Push with a custom base image
openenv push --base-image ghcr.io/meta-pytorch/openenv-base:latest

# Push as a private space
openenv push --private

# Combine options
openenv push --repo-id my-org/my-env --base-image custom-base:latest --private
```

After deployment, your space will be available at:
`https://huggingface.co/spaces/<repo-id>`

The deployed space includes:
- **Web Interface** at `/web` - Interactive UI for exploring the environment
- **API Documentation** at `/docs` - Full OpenAPI/Swagger interface
- **Health Check** at `/health` - Container health monitoring
- **WebSocket** at `/ws` - Persistent session endpoint for low-latency interactions

## Environment Details

### Action
**OpenenvProjAction**: Contains a single field
- `message` (str) - The message to echo back

### Observation
**OpenenvProjObservation**: Contains the echo response and metadata
- `echoed_message` (str) - The message echoed back
- `message_length` (int) - Length of the message
- `reward` (float) - Reward based on message length (length × 0.1)
- `done` (bool) - Always False for echo environment
- `metadata` (dict) - Additional info like step count

### Reward
The reward is calculated as: `message_length × 0.1`
- "Hi" → reward: 0.2
- "Hello, World!" → reward: 1.3
- Empty message → reward: 0.0

## Advanced Usage

### Connecting to an Existing Server

If you already have a Openenv Proj environment server running, you can connect directly:

```python
from openEnv_proj import OpenenvProjEnv

# Connect to existing server
openEnv_projenv = OpenenvProjEnv(base_url="<ENV_HTTP_URL_HERE>")

# Use as normal
result = openEnv_projenv.reset()
result = openEnv_projenv.step(OpenenvProjAction(message="Hello!"))
```

Note: When connecting to an existing server, `openEnv_projenv.close()` will NOT stop the server.

### Using the Context Manager

The client supports context manager usage for automatic connection management:

```python
from openEnv_proj import OpenenvProjAction, OpenenvProjEnv

# Connect with context manager (auto-connects and closes)
with OpenenvProjEnv(base_url="http://localhost:8000") as env:
    result = env.reset()
    print(f"Reset: {result.observation.echoed_message}")
    # Multiple steps with low latency
    for msg in ["Hello", "World", "!"]:
        result = env.step(OpenenvProjAction(message=msg))
        print(f"Echoed: {result.observation.echoed_message}")
```

The client uses WebSocket connections for:
- **Lower latency**: No HTTP connection overhead per request
- **Persistent session**: Server maintains your environment state
- **Efficient for episodes**: Better for many sequential steps

### Concurrent WebSocket Sessions

The server supports multiple concurrent WebSocket connections. To enable this,
modify `server/app.py` to use factory mode:

```python
# In server/app.py - use factory mode for concurrent sessions
app = create_app(
    OpenenvProjEnvironment,  # Pass class, not instance
    OpenenvProjAction,
    OpenenvProjObservation,
    max_concurrent_envs=4,  # Allow 4 concurrent sessions
)
```

Then multiple clients can connect simultaneously:

```python
from openEnv_proj import OpenenvProjAction, OpenenvProjEnv
from concurrent.futures import ThreadPoolExecutor

def run_episode(client_id: int):
    with OpenenvProjEnv(base_url="http://localhost:8000") as env:
        result = env.reset()
        for i in range(10):
            result = env.step(OpenenvProjAction(message=f"Client {client_id}, step {i}"))
        return client_id, result.observation.message_length

# Run 4 episodes concurrently
with ThreadPoolExecutor(max_workers=4) as executor:
    results = list(executor.map(run_episode, range(4)))
```

## Development & Testing

### Direct Environment Testing

Test the environment logic directly without starting the HTTP server:

```bash
# From the server directory
python3 server/openEnv_proj_environment.py
```

This verifies that:
- Environment resets correctly
- Step executes actions properly
- State tracking works
- Rewards are calculated correctly

### Running Locally

Run the server locally for development:

```bash
uvicorn server.app:app --reload
```

## Project Structure

```
openEnv_proj/
├── .dockerignore         # Docker build exclusions
├── __init__.py            # Module exports
├── README.md              # This file
├── openenv.yaml           # OpenEnv manifest
├── pyproject.toml         # Project metadata and dependencies
├── uv.lock                # Locked dependencies (generated)
├── client.py              # OpenenvProjEnv client
├── models.py              # Action and Observation models
└── server/
    ├── __init__.py        # Server module exports
    ├── openEnv_proj_environment.py  # Core environment logic
    ├── app.py             # FastAPI application (HTTP + WebSocket endpoints)
    └── Dockerfile         # Container image definition
```
