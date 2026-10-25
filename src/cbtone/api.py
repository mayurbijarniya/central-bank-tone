"""A scoring API, for scoring text from other programs.

    uvicorn cbtone.api:app --port 8000

POST /score takes speech text and returns the tone of each policy sentence,
using the same saved scorer and embedding model as the archive. The model loads
once, on the first request. The website does the same in the browser
(web/src/lib/tone.ts), so it needs no server.
"""

from __future__ import annotations

import os
from functools import lru_cache

import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from cbtone import ingest, paths, scorer, sentences

MAX_CHARACTERS = 50_000
MAX_SENTENCES = 400

app = FastAPI(title="Central bank tone", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CBTONE_ALLOWED_ORIGINS", "http://localhost:3000").split(","),
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class ScoreRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_CHARACTERS)


class SentenceScore(BaseModel):
    sentence: str
    tone: float
    label: str
    hawkish: float
    dovish: float
    neutral: float


class ScoreResponse(BaseModel):
    tone: float | None
    policy_sentences: int
    sentences: list[SentenceScore]


@lru_cache(maxsize=1)
def model() -> scorer.SavedScorer:
    return scorer.load(paths.SCORER)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/score")
def score(request: ScoreRequest) -> ScoreResponse:
    found = [s for s in ingest.sentences(ingest.clean(request.text)) if sentences.is_policy(s)]
    if len(found) > MAX_SENTENCES:
        raise HTTPException(413, f"at most {MAX_SENTENCES} policy sentences per request")
    if not found:
        return ScoreResponse(tone=None, policy_sentences=0, sentences=[])

    fitted = model()
    probabilities = fitted.predict_proba(scorer.embed(found))
    classes = [str(c) for c in fitted.classes_]
    tones = scorer.tone(probabilities, classes)
    column = {c: i for i, c in enumerate(classes)}
    rows = [
        SentenceScore(
            sentence=text,
            tone=round(float(tone), 4),
            label=classes[int(np.argmax(p))],
            hawkish=round(float(p[column["hawkish"]]), 4),
            dovish=round(float(p[column["dovish"]]), 4),
            neutral=round(float(p[column["neutral"]]), 4),
        )
        for text, tone, p in zip(found, tones, probabilities, strict=True)
    ]
    return ScoreResponse(
        tone=round(float(np.mean(tones)), 4), policy_sentences=len(rows), sentences=rows
    )
