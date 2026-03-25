import os
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
import anthropic

app = FastAPI(
    title="Text Intel API",
    description="AI-powered text analysis using Claude",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


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


ANALYSIS_PROMPT = """Analyze the following text and return a JSON object with these exact fields:

- sentiment: one of "positive", "negative", or "neutral"
- sentiment_score: float between 0.0 and 1.0 (1.0 = most positive, 0.0 = most negative, 0.5 = neutral)
- summary: concise summary in 3 sentences or fewer
- keywords: array of 5-10 important keywords/phrases from the text
- language: ISO 639-1 language code (e.g., "en", "zh", "ko", "ja", "fr", etc.)
- readability: one of "easy", "medium", or "hard"
- toxicity: one of "none", "low", "medium", or "high"
- topics: array of 2-5 main topics covered in the text
- word_count: approximate word count as integer

Return ONLY valid JSON, no markdown, no explanation.

Text to analyze:
{text}"""


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalyzeResponse)
async def analyze(request: AnalyzeRequest):
    word_count = len(request.text.split())

    try:
        message = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": ANALYSIS_PROMPT.format(text=request.text),
                }
            ],
        )
    except anthropic.AuthenticationError:
        raise HTTPException(status_code=500, detail="Invalid API key configuration")
    except anthropic.RateLimitError:
        raise HTTPException(status_code=429, detail="Rate limit exceeded, please try again later")
    except anthropic.APIError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")

    raw = message.content[0].text.strip()

    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=502, detail=f"Failed to parse AI response: {str(e)}")

    # Normalize and validate fields
    sentiment = data.get("sentiment", "neutral").lower()
    if sentiment not in ("positive", "negative", "neutral"):
        sentiment = "neutral"

    sentiment_score = float(data.get("sentiment_score", 0.5))
    sentiment_score = max(0.0, min(1.0, sentiment_score))

    readability = data.get("readability", "medium").lower()
    if readability not in ("easy", "medium", "hard"):
        readability = "medium"

    toxicity = data.get("toxicity", "none").lower()
    if toxicity not in ("none", "low", "medium", "high"):
        toxicity = "none"

    keywords = data.get("keywords", [])
    if not isinstance(keywords, list):
        keywords = []

    topics = data.get("topics", [])
    if not isinstance(topics, list):
        topics = []

    language = str(data.get("language", "en"))
    summary = str(data.get("summary", ""))
    ai_word_count = data.get("word_count", word_count)
    if not isinstance(ai_word_count, int):
        try:
            ai_word_count = int(ai_word_count)
        except (ValueError, TypeError):
            ai_word_count = word_count

    return AnalyzeResponse(
        sentiment=sentiment,
        sentiment_score=sentiment_score,
        summary=summary,
        keywords=keywords,
        language=language,
        readability=readability,
        toxicity=toxicity,
        topics=topics,
        word_count=ai_word_count,
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
