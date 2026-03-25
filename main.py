import os
import re
from collections import Counter
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import textstat

app = FastAPI(
    title="Text Intel API",
    description="Local NLP-powered text analysis",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_vader = SentimentIntensityAnalyzer()

_STOPWORDS = {
    "the","a","an","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do",
    "does","did","will","would","could","should","may","might","shall",
    "this","that","these","those","i","you","he","she","it","we","they",
    "my","your","his","her","its","our","their","what","which","who","how",
    "not","no","so","if","as","by","from","up","out","about","into","than",
}

_TOXIC_HIGH = {"kill","murder","rape","terrorist","bomb","genocide","massacre"}
_TOXIC_MED  = {"idiot","stupid","moron","loser","hate","racist","bullshit"}
_TOXIC_LOW  = {"annoying","terrible","awful","horrible","lame","shut up","ugly"}

_TOPIC_RULES = [
    ("tech",          {"technology","software","ai","computer","internet","data","cloud","algorithm","app","digital","robot","developer"}),
    ("business",      {"market","stock","economy","finance","investment","revenue","profit","company","trade","startup","commerce"}),
    ("sports",        {"football","soccer","basketball","tennis","olympics","athlete","game","match","tournament","championship","team","player"}),
    ("health",        {"health","medical","doctor","hospital","disease","cancer","vaccine","treatment","mental","diet","exercise","virus","medicine"}),
    ("politics",      {"government","election","president","congress","parliament","policy","vote","legislation","law","minister"}),
    ("entertainment", {"movie","film","music","celebrity","actor","singer","concert","album","television","netflix","streaming","anime"}),
]

_LANG_PATTERNS = [
    ("zh", re.compile(r'[\u4e00-\u9fff]')),
    ("ko", re.compile(r'[\uac00-\ud7a3]')),
    ("ja", re.compile(r'[\u3040-\u30ff]')),
    ("ar", re.compile(r'[\u0600-\u06ff]')),
    ("ru", re.compile(r'[\u0400-\u04ff]')),
]


def _detect_language(text: str) -> str:
    for lang, pat in _LANG_PATTERNS:
        if pat.search(text):
            return lang
    return "en"


def _get_sentiment(text: str) -> tuple[str, float]:
    scores = _vader.polarity_scores(text)
    c = scores["compound"]
    if c >= 0.05:
        return "positive", round(0.5 + c * 0.5, 4)
    elif c <= -0.05:
        return "negative", round(0.5 + c * 0.5, 4)
    return "neutral", 0.5


def _summarize(text: str, n: int = 2) -> str:
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return " ".join(sentences[:n])


def _extract_keywords(text: str, top_n: int = 8) -> list[str]:
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    words = [w for w in words if w not in _STOPWORDS]
    if not words:
        return []
    freq = Counter(words)
    return [w for w, _ in freq.most_common(top_n)]


def _get_readability(text: str) -> str:
    try:
        score = textstat.flesch_reading_ease(text)
        if score >= 60:
            return "easy"
        elif score >= 30:
            return "medium"
        return "hard"
    except Exception:
        return "medium"


def _get_toxicity(text: str) -> str:
    lower = text.lower()
    for p in _TOXIC_HIGH:
        if p in lower: return "high"
    for p in _TOXIC_MED:
        if p in lower: return "medium"
    for p in _TOXIC_LOW:
        if p in lower: return "low"
    return "none"


def _get_topics(text: str) -> list[str]:
    lower = text.lower()
    matched = [t for t, kws in _TOPIC_RULES if any(k in lower for k in kws)]
    return matched[:5] if matched else ["other"]


class AnalyzeRequest(BaseModel):
    text: str
    lang: str = "auto"

    @field_validator("text")
    @classmethod
    def validate_text(cls, v):
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


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    text = request.text
    language = _detect_language(text) if request.lang == "auto" else request.lang
    sentiment, score = _get_sentiment(text)
    return AnalyzeResponse(
        sentiment=sentiment,
        sentiment_score=score,
        summary=_summarize(text),
        keywords=_extract_keywords(text),
        language=language,
        readability=_get_readability(text),
        toxicity=_get_toxicity(text),
        topics=_get_topics(text),
        word_count=len(text.split()),
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
