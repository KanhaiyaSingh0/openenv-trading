# Quick Start Guide - Trading Environment

Get your RL trading environment running in 5 minutes!

## 1️⃣ Install Dependencies

```bash
# Navigate to project
cd openenv_trading

# Install (using pip)
pip install -r server/requirements.txt

# Or using uv (faster)
uv sync
```

## 2️⃣ Quick Test (Optional)

Validate the environment works locally:

```bash
python test_trading_env.py
```

Expected output:
```
============================================================
Trading Environment Validation Tests
============================================================

Passed: 5 tests, Failed: 0
```

## 3️⃣ Start the Server

```bash
# Terminal 1
python -m server.app --port 8000

# Or using uvicorn directly
uvicorn server.app:app --host 0.0.0.0 --port 8000 --reload
```

Wait for message: `Uvicorn running on http://0.0.0.0:8000`

## 4️⃣ Test the API

Open new terminal and test endpoints:

```bash
# Test reset endpoint
curl -X POST http://localhost:8000/reset \
  -H "Content-Type: application/json" \
  -d '{"task": "easy"}'

# Test step endpoint
curl -X POST http://localhost:8000/step \
  -H "Content-Type: application/json" \
  -d '{"action": "BUY", "quantity": 10, "ticker": "STOCK"}'
```

Expected response: `200 OK` with TradingObservation JSON

## 5️⃣ Run Inference (with LLM)

Set up environment variables first:

```bash
# Create .env file if not exists
export HF_TOKEN="your_huggingface_token"
export MODEL_NAME="meta-llama/Llama-2-7b-chat-hf"
export API_BASE_URL="https://api-inference.huggingface.co/v1"
```

Run the trading agent:

```bash
# Terminal 2
python inference.py
```

Expected output:
```
[START] task=easy env=trading_env model=meta-llama/Llama-2-7b-chat-hf
[STEP] step=1 action=BUY 5 reward=0.05 done=false error=null
[STEP] step=2 action=HOLD 0 reward=0.02 done=false error=null
...
[END] success=true steps=10 score=0.500 rewards=0.05,0.02,...
[START] task=medium env=trading_env model=meta-llama/Llama-2-7b-chat-hf
...
```

---

## 🐳 Docker Setup

Build and run in Docker:

```bash
# Build image
docker build -t trading-env:latest .

# Run container
docker run -p 8000:8000 trading-env:latest

# Test
curl http://localhost:8000/reset
```

---

## 📚 What's Each Endpoint?

### POST /reset
Reset for a new episode.

**Request:**
```json
{
  "task": "easy"
}
```

**Response:**
```json
{
  "observation": {
    "current_price": 100.0,
    "portfolio_value": 10000.0,
    "cash_balance": 10000.0,
    ...
  },
  "done": false,
  "reward": 0.0
}
```

### POST /step
Execute one action.

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
    "portfolio_value": 9845.0,
    ...
  },
  "reward": 0.015,
  "done": false
}
```

---

## 🎯 Tasks

### Easy (10 steps)
- Uptrend market (+2% drift, 10% volatility)
- No margin constraints
- Goal: make 10% profit

### Medium (15 steps)
- Mean-reverting market (0% drift, 20% volatility)
- No margin constraints
- Goal: achieve Sharpe ratio > 0.5

### Hard (20 steps)
- Volatile downtrend (-1% drift, 30% volatility)
- **2:1 margin** (liquidation risk!)
- Goal: make 20% profit under margin constraint

---

## 🚀 Project Structure

```
trading-env/
├── inference.py           → LLM agent + main loop
├── models.py             → Data types (TradingAction, obs)
├── client.py             → HTTP client
├── openenv.yaml          → OpenEnv spec
├── README.md             → Full docs
├── server/
│   ├── app.py           → FastAPI server
│   ├── openEnv_proj_environment.py  → TradingEnvironment class
│   └── requirements.txt
├── Dockerfile
├── .env                 → Config (HF token, etc)
└── test_trading_env.py  → Unit tests
```

---

## 🔧 Troubleshooting

### Port 8000 already in use
```bash
# Use different port
python -m server.app --port 8001
```

### Import errors
```bash
# Reinstall
pip install -r server/requirements.txt --force-reinstall
```

### HF token not found
```bash
# Set token
export HF_TOKEN="hf_xxxxx..."
python inference.py
```

### Docker build fails
```bash
# Check log
docker build -t trading-env:latest . --no-cache
```

---

## 📖 Documentation

- **Full guide:** See [README.md](README.md)
- **Implementation details:** See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
- **Test results:** Run `python test_trading_env.py`

---

## ✅ Success Indicators

You'll know it's working when:

✓ Server starts without errors  
✓ `/reset` returns 200 with portfolio=$10,000  
✓ `/step` changes portfolio value and returns reward [0, 1]  
✓ Inference script completes all 3 tasks  
✓ Logs follow [START]/[STEP]/[END] format  
✓ Docker builds and runs  

---

## 📝 Next Steps

1. **Local testing** → Run `test_trading_env.py`
2. **API validation** → Test endpoints with curl
3. **Inference test** → Run with real LLM
4. **Docker build** → Verify container
5. **Submit to HF Spaces** → Deploy live

---

**Ready? Start with** `python -m server.app --port 8000`

Questions? Check [README.md](README.md) or [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md)
