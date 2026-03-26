# Text Intel API

English text analysis API. Single API call returns sentiment, keywords, topics, readability, toxicity, and more — no AI API costs, no rate limits on your end.

## Features

- **Sentiment analysis** with score (0.0–1.0)
- **Auto-summarization** (≤3 sentences)
- **Keyword extraction** (5–10 keywords)
- **Language detection** (ISO 639-1 code)
- **Readability rating** (easy / medium / hard)
- **Toxicity detection** (none / low / medium / high)
- **Topic classification**
- **Word count**
- Optimized for **English text**
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

### Example Use Cases

#### 1) Long product-feedback text

**Request**
```json
{
  "text": "FastAPI helped our small product team ship an internal analytics dashboard in two weekends instead of two months. The API was easy to document, the response times stayed stable under load, and the team finally stopped arguing about whether Python was too slow for production. We still had rough edges around deployment and monitoring, but overall the migration reduced support tickets, made onboarding easier, and gave the product manager much better visibility into customer behavior.",
  "lang": "auto"
}
```

**Response**
```json
{
  "sentiment": "positive",
  "sentiment_score": 0.83,
  "summary": "FastAPI helped a product team ship an internal analytics dashboard much faster than expected. The migration improved maintenance, visibility, and onboarding despite some deployment and monitoring rough edges.",
  "keywords": ["fastapi", "product", "team", "internal", "analytics", "dashboard", "response", "maintenance"],
  "language": "en",
  "readability": "medium",
  "toxicity": "none",
  "topics": ["tech", "business"],
  "word_count": 57
}
```

#### 2) Negative support / complaint text

**Request**
```json
{
  "text": "This service is a complete mess. The support team ignored us for days, the dashboard kept crashing during client demos, and every promised fix introduced a new problem. We lost trust and had to apologize to customers.",
  "lang": "auto"
}
```

**Response**
```json
{
  "sentiment": "negative",
  "sentiment_score": 0.12,
  "summary": "The service caused repeated failures, poor support experiences, and customer trust issues. The user describes crashes, delays, and broken promises.",
  "keywords": ["service", "complete", "mess", "support", "team", "ignored", "dashboard", "customers"],
  "language": "en",
  "readability": "medium",
  "toxicity": "none",
  "topics": ["tech", "business"],
  "word_count": 34
}
```

#### 3) Toxic / hostile language edge case

**Request**
```json
{
  "text": "Your product is awful, your roadmap is stupid, and this whole release was a bullshit mess.",
  "lang": "auto"
}
```

**Response**
```json
{
  "sentiment": "negative",
  "sentiment_score": 0.09,
  "summary": "Your product is awful, your roadmap is stupid, and this whole release was a bullshit mess.",
  "keywords": ["product", "awful", "roadmap", "stupid", "whole", "release", "bullshit", "mess"],
  "language": "en",
  "readability": "easy",
  "toxicity": "medium",
  "topics": ["other"],
  "word_count": 15
}
```

#### 4) Minimal short-text edge case

**Request**
```json
{
  "text": "OK.",
  "lang": "auto"
}
```

**Response**
```json
{
  "sentiment": "positive",
  "sentiment_score": 0.65,
  "summary": "OK.",
  "keywords": [],
  "language": "en",
  "readability": "easy",
  "toxicity": "none",
  "topics": ["other"],
  "word_count": 1
}
```

### Notes on Behavior

- Best optimized for **English** input
- `lang: "auto"` uses simple script-based detection (`en`, `zh`, `ko`, `ja`, `ar`, `ru`)
- Empty input is rejected
- Input over **5000 characters** is rejected
- Topic labels are rule-based (`tech`, `business`, `sports`, `health`, `politics`, `entertainment`, `other`)
- Toxicity is heuristic-based (`none`, `low`, `medium`, `high`)

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
- **VADER Sentiment** — battle-tested English NLP library
- **Pydantic v2** — request/response validation
- Zero external AI API calls — fast, predictable, no token costs
