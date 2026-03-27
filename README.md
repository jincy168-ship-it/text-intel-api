# Text Intel API

FastAPI API for lightweight English text analysis. One request returns sentiment, keywords, topics, readability, toxicity, summary, language, and word count using local heuristics and VADER sentiment — no external AI API calls.

## Features

- **Sentiment analysis** with score (`0.0-1.0`)
- **Auto-summary** from the opening sentences
- **Keyword extraction** (`0-8` keywords)
- **Language detection** (`en`, `zh`, `ko`, `ja`, `ar`, `ru`) when `lang` is set to `auto`
- **Readability rating** (`easy`, `medium`, `hard`)
- **Toxicity detection** (`none`, `low`, `medium`, `high`)
- **Topic classification** (`tech`, `business`, `sports`, `health`, `politics`, `entertainment`, `other`)
- **Word count**
- Input limit: **5,000 characters**
- CORS enabled for all origins

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
  "topics": ["tech"],
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

- Optimized for **English** input; non-English handling is limited to simple script-based detection unless you explicitly pass `lang`
- `lang: "auto"` uses regex-based script detection and defaults to `en` when no supported script is detected
- Summary is just the first `2` sentences of the text
- Keywords are extracted from English alphabetic words only and filtered with a small stopword list
- Topic and toxicity outputs are **rule-based heuristics**, not model-based moderation or deep classification
- Empty input is rejected
- Input over **5000 characters** is rejected

### GET `/health`

```json
{ "status": "ok" }
```

### Interactive Docs

After starting the server, visit:

- `/docs` - Swagger UI
- `/redoc` - ReDoc

---

## Local Development

### Prerequisites

- Python 3.11+

### Setup

```bash
git clone <your-repo-url>
cd text-intel-api

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

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

This repo includes both a `Procfile` and `railway.json`. Railway can build it with Nixpacks and run the app with the Procfile command.

### Option A: GitHub (recommended)

1. Push this project to a GitHub repo
2. Go to [railway.app](https://railway.app) -> **New Project** -> **Deploy from GitHub repo**
3. Select your repo
4. Railway will detect the Python app and build it with Nixpacks
5. Deploy and get your public URL from **Settings -> Domains**

### Option B: Railway CLI

```bash
npm install -g @railway/cli
railway login
railway init
railway up
```

### Notes

- No application-specific environment variables are required for the current codebase
- Railway injects `PORT`; locally the app defaults to `8000`
- The production start command in this repo is:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

---

## Publish to RapidAPI

1. Go to [rapidapi.com/provider](https://rapidapi.com/provider) -> **Add New API**
2. Fill in:
   - **Name:** Text Intel API
   - **Category:** Artificial Intelligence / Machine Learning
   - **Base URL:** `https://your-railway-url.up.railway.app`
3. Add endpoints:
   - `POST /analyze`
   - `GET /health`
4. Use the exact request and response schemas shown above
5. Set pricing/auth to match your business choice; the app itself currently does **not** enforce authentication
6. Submit for review

### RapidAPI docs sync checklist

Before publishing or updating the listing, make sure the RapidAPI page matches the current app behavior:

- Remove any mention of Anthropic, LLMs, or external AI API keys
- Describe the API as **local heuristic / VADER-based analysis**, not generative AI
- Keep the supported language note narrow: best for English, limited script detection for a few non-Latin scripts
- Keep the input limit at **5000 characters**
- Match the actual response fields exactly: `sentiment`, `sentiment_score`, `summary`, `keywords`, `language`, `readability`, `toxicity`, `topics`, `word_count`
- If you later add auth or RapidAPI proxy-secret validation in code, update both the RapidAPI listing and this README together

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `PORT` | Auto in Railway | Injected by Railway; defaults to `8000` locally |

---

## Tech Stack

- **FastAPI** - async web framework
- **Uvicorn** - ASGI server
- **VADER Sentiment** - English sentiment analysis
- **Pydantic v2** - request/response validation
- Rule-based heuristics for summary, keywords, topics, readability, language, and toxicity
