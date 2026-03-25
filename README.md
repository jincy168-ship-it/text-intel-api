# Text Intel API

AI-powered text analysis API built with FastAPI + Claude claude-haiku. Single API call returns sentiment, summary, keywords, topics, readability, toxicity, and more.

## Features

- **Sentiment analysis** with score (0.0–1.0)
- **Auto-summarization** (≤3 sentences)
- **Keyword extraction** (5–10 keywords)
- **Language detection** (ISO 639-1 code)
- **Readability rating** (easy / medium / hard)
- **Toxicity detection** (none / low / medium / high)
- **Topic classification**
- **Word count**
- Supports any language Claude understands
- Input limit: 5,000 characters
- CORS fully open (RapidAPI compatible)

## API Reference

### POST `/analyze`

**Request:**
```json
{
  "text": "Your text here (max 5000 chars)",
  "lang": "auto"
}
```

**Response:**
```json
{
  "sentiment": "positive",
  "sentiment_score": 0.85,
  "summary": "The text discusses...",
  "keywords": ["AI", "analysis", "FastAPI"],
  "language": "en",
  "readability": "medium",
  "toxicity": "none",
  "topics": ["technology", "AI"],
  "word_count": 42
}
```

### GET `/health`

```json
{ "status": "ok" }
```

### Interactive Docs

Visit `/docs` (Swagger UI) or `/redoc` after starting the server.

---

## Local Development

### Prerequisites

- Python 3.11+
- Anthropic API key

### Setup

```bash
git clone <your-repo-url>
cd text-intel-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY=sk-ant-...

# Start server
uvicorn main:app --reload --port 8000
```

Server runs at `http://localhost:8000`

### Test

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"text": "FastAPI is an amazing framework for building APIs quickly and efficiently!"}'
```

---

## Deploy to Railway

### Option A: GitHub (recommended)

1. Push this project to a GitHub repo
2. Go to [railway.app](https://railway.app) → **New Project** → **Deploy from GitHub repo**
3. Select your repo
4. Railway auto-detects Python via Nixpacks
5. Go to **Variables** tab → add `ANTHROPIC_API_KEY = sk-ant-...`
6. Railway deploys automatically — get your public URL from **Settings → Domains**

### Option B: Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up

# Set environment variable
railway variables set ANTHROPIC_API_KEY=sk-ant-...
```

### Notes

- Railway free tier: 500 hours/month (enough for personal/dev use)
- Set `PORT` is injected automatically by Railway — no manual config needed
- Cold starts may take ~2s on free tier

---

## Publish to RapidAPI

1. Go to [rapidapi.com/provider](https://rapidapi.com/provider) → **Add New API**
2. Fill in:
   - **Name:** Text Intel API
   - **Category:** Artificial Intelligence / Machine Learning
   - **Base URL:** `https://your-railway-url.up.railway.app`
3. Add endpoints:
   - `POST /analyze` — with request body schema
   - `GET /health`
4. Set **Security:** No Auth (you can add `X-RapidAPI-Proxy-Secret` header validation later)
5. Configure **Pricing:** Free tier or freemium plans
6. Submit for review

### Optional: Validate RapidAPI Proxy Secret

Add this to `main.py` for extra security:

```python
from fastapi import Header

RAPIDAPI_SECRET = os.environ.get("RAPIDAPI_PROXY_SECRET")

@app.post("/analyze")
async def analyze(request: AnalyzeRequest, x_rapidapi_proxy_secret: str = Header(None)):
    if RAPIDAPI_SECRET and x_rapidapi_proxy_secret != RAPIDAPI_SECRET:
        raise HTTPException(status_code=403, detail="Forbidden")
    ...
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | ✅ Yes | Your Anthropic API key |
| `PORT` | Auto | Injected by Railway (default: 8000 locally) |

---

## Tech Stack

- **FastAPI** 0.115 — async web framework
- **Uvicorn** — ASGI server
- **Anthropic Python SDK** — Claude API client
- **Pydantic v2** — request/response validation
- **Claude claude-haiku** — fast, cost-efficient model (~$0.0008/1K tokens)
