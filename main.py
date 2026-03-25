import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator

# Local NLP libraries
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from langdetect import detect, LangDetectException
import textstat
import nltk
from nltk.tokenize import sent_tokenize, word_tokenize
from collections import Counter
import math

# Download required NLTK data (silent)
for resource in ["punkt", "punkt_tab", "stopwords"]:
    try:
        nltk.download(resource, quiet=True)
    except Exception:
        pass

from nltk.corpus import stopwords

app = FastAPI(
    title="Text Intel API",
    description="Local NLP-powered text analysis (no external APIs)",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Singletons ───────────────────────────────────────────────────────────────
_vader = SentimentIntensityAnalyzer()

# ── Toxicity keyword blacklist ────────────────────────────────────────────────
_TOXIC_HIGH = {
    "kill", "murder", "rape", "terrorist", "bomb", "genocide", "massacre",
    "nigger", "faggot", "cunt", "fuck you", "die bitch",
}
_TOXIC_MED = {
    "idiot", "stupid", "moron", "loser", "jerk", "ass", "bastard",
    "hate", "racist", "sexist", "bullshit", "dumb", "pathetic",
}
_TOXIC_LOW = {
    "annoying", "terrible", "awful", "disgusting", "horrible", "lame",
    "shut up", "ugly",
}

# ── Topic keyword rules ───────────────────────────────────────────────────────
_TOPIC_RULES: list[tuple[str, set[str]]] = [
    ("tech", {
        "technology", "software", "hardware", "ai", "machine learning",
        "computer", "internet", "data", "cloud", "algorithm", "robot",
        "programming", "developer", "startup", "app", "digital",
    }),
    ("business", {
        "market", "stock", "economy", "finance", "investment", "revenue",
        "profit", "company", "corporate", "trade", "gdp", "inflation",
        "entrepreneur", "startup", "industry", "commerce",
    }),
    ("sports", {
        "football", "soccer", "basketball", "tennis", "olympics", "athlete",
        "game", "match", "tournament", "championship", "score", "team",
        "player", "coach", "baseball", "cricket",
    }),
    ("health", {
        "health", "medical", "doctor", "hospital", "disease", "cancer",
        "vaccine", "treatment", "mental health", "diet", "exercise",
        "pandemic", "virus", "nutrition", "wellness", "medicine",
    }),
    ("politics", {
        "government", "election", "president", "congress", "senate",
        "parliament", "policy", "democrat", "republican", "vote",
        "legislation", "law", "political", "party", "minister",
    }),
    ("entertainment", {
        "movie", "film", "music", "celebrity", "actor", "singer",
        "concert", "album", "television", "show", "award", "oscar",
        "grammy", "netflix", "streaming", "game", "anime",
    }),
]


# ── Helper functions ──────────────────────────────────────────────────────────

def _detect_language(text: str) -> str:
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def _get_sentiment(text: str) -> tuple[str, float]:
    scores = _vader.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "positive"
        score = 0.5 + compound * 0.5  # map [0.05, 1] → [0.525, 1.0]
    elif compound <= -0.05:
        label = "negative"
        score = 0.5 + compound * 0.5  # map [-1, -0.05] → [0.0, 0.475]
    else:
        label = "neutral"
        score = 0.5
    return label, round(max(0.0, min(1.0, score)), 4)


def _summarize(text: str, n: int = 2) -> str:
    """Return first n sentences as summary."""
    try:
        sentences = sent_tokenize(text)
    except Exception:
        sentences = re.split(r"(?<=[.!?])\s+", text)
    return " ".join(sentences[:n]).strip()


def _extract_keywords(text: str, top_n: int = 8) -> list[str]:
    """TF-IDF-style keyword extraction over a single document."""
    try:
        tokens = word_tokenize(text.lower())
    except Exception:
        tokens = text.lower().split()

    try:
        stop = set(stopwords.words("english"))
    except Exception:
        stop = set()

    # Keep alphabetic tokens, length ≥ 3, not stopwords
    words = [w for w in tokens if w.isalpha() and len(w) >= 3 and w not in stop]
    if not words:
        return []

    freq = Counter(words)
    total = len(words)
    # Score = tf * log(1 / relative_freq)  (simple idf proxy)
    scored = {w: (c / total) * math.log(total / c + 1) for w, c in freq.items()}
    return [w for w, _ in sorted(scored.items(), key=lambda x: -x[1])[:top_n]]


def _get_readability(text: str) -> str:
    try:
        score = textstat.flesch_reading_ease(text)
    except Exception:
        return "medium"
    if score >= 60:
        return "easy"
    elif score >= 30:
        return "medium"
    else:
        return "hard"


def _get_toxicity(text: str) -> str:
    lower = text.lower()
    for phrase in _TOXIC_HIGH:
        if phrase in lower:
            return "high"
    for phrase in _TOXIC_MED:
        if phrase in lower:
            return "medium"
    for phrase in _TOXIC_LOW:
        if phrase in lower:
            return "low"
    return "none"


def _get_topics(text: str) -> list[str]:
    lower = text.lower()
    matched: list[str] = []
    for topic, keywords in _TOPIC_RULES:
        if any(kw in lower for kw in keywords):
            matched.append(topic)
        if len(matched) >= 5:
            break
    return matched if matched else ["other"]


# ── Models ────────────────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    text: str
    lang: str = "auto"

    @field_validator("text")
    @classmethod
    def text_max_length(cls, v):
        if len(v) > 5000:
            raise ValueError("Text exceeds 5000 character limit")
        if not v.strip():
            raise ValueError("Text cannot be empty")
        return v


class AnalyzeResponse(BaseModel):
    sentiment: str
    sentiment_score: float
    summary: str
    keywords: list[str]
    language: str
    readability: str
    toxicity: str
    topics: list[str]
    word_count: int


# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    text = request.text
    word_count = len(text.split())

    language = _detect_language(text) if request.lang == "auto" else request.lang
    sentiment, sentiment_score = _get_sentiment(text)
    summary = _summarize(text)
    keywords = _extract_keywords(text)
    readability = _get_readability(text)
    toxicity = _get_toxicity(text)
    topics = _get_topics(text)

    return AnalyzeResponse(
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        summary=summary,
        keywords=keywords,
        language=language,
        readability=readability,
        toxicity=toxicity,
        topics=topics,
        word_count=word_count,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
