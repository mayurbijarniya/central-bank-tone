"""The local model that scores every sentence without calling a language model.

Two candidates learn from the same labels:

words       TF-IDF on words and word pairs, then logistic regression
embeddings  BAAI/bge-small-en-v1.5 sentence embeddings, then logistic regression

The embedding model runs on a CPU through ONNX (fastembed), so scoring needs no
GPU and no paid service.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

from cbtone import paths

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
MODELS_DIR = paths.DATA / "models"
EMBEDDINGS = paths.PROCESSED / "embeddings"
CLASSES = ("dovish", "hawkish", "neutral")
THREADS = 4
BATCH = 32
C = 1.0  # chosen by `select`
STRENGTHS = (0.3, 1.0, 3.0, 10.0)


def _embedder():
    import os

    # Keep Hugging Face's download logs and cache inside the project, not in ~/.cache.
    os.environ.setdefault("HF_HOME", str(MODELS_DIR / "huggingface"))
    from fastembed import TextEmbedding

    return TextEmbedding(EMBEDDING_MODEL, cache_dir=str(MODELS_DIR), threads=THREADS)


def embed(texts: Iterable[str], cache: str | None = None) -> np.ndarray:
    """Sentence embeddings, in input order. Shorter sentences are batched together for speed.

    With `cache`, the result is stored under that name keyed by the exact texts,
    so repeated runs reuse it.
    """
    texts = list(texts)
    if cache:
        digest = hashlib.sha1("\n".join(texts).encode()).hexdigest()[:16]
        target = EMBEDDINGS / f"{cache}-{digest}.npy"
        if target.exists():
            return np.load(target)
    order = sorted(range(len(texts)), key=lambda i: len(texts[i]))
    vectors = list(_embedder().embed([texts[i] for i in order], batch_size=BATCH))
    out = np.empty((len(texts), len(vectors[0])), dtype=np.float32)
    for position, i in enumerate(order):
        out[i] = vectors[position]
    if cache:
        EMBEDDINGS.mkdir(parents=True, exist_ok=True)
        np.save(target, out)
    return out


def words_model(c: float = C) -> object:
    # TF-IDF features are sparse and many, so the same strength is set ten times looser.
    return make_pipeline(
        TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True),
        LogisticRegression(C=c * 10, max_iter=2000, class_weight="balanced"),
    )


def embeddings_model(c: float = C) -> LogisticRegression:
    return LogisticRegression(C=c, max_iter=2000, class_weight="balanced")


def select(texts: list[str], vectors: np.ndarray, labels: list[str], groups: list[str],
           strengths=STRENGTHS, folds: int = 5) -> dict:
    """Cross-validate both candidates at several strengths, folds grouped by speech.

    Grouping keeps every sentence of a speech on one side of each split, so a model
    is never scored on sentences from a speech it was trained on.
    """
    targets = np.array(labels)
    splits = list(GroupKFold(n_splits=folds).split(vectors, targets, groups))
    rows = []
    for c in strengths:
        for name, make, features in (("words", words_model, texts),
                                     ("embeddings", embeddings_model, vectors)):
            accuracy, macro_f1 = [], []
            for train, test in splits:
                model = make(c)
                if name == "words":
                    model.fit([features[i] for i in train], targets[train])
                    predicted = model.predict([features[i] for i in test])
                else:
                    model.fit(features[train], targets[train])
                    predicted = model.predict(features[test])
                scores = evaluate(list(targets[test]), list(predicted))
                accuracy.append(scores["accuracy"])
                macro_f1.append(scores["macro_f1"])
            rows.append({"model": name, "c": c, "accuracy": round(float(np.mean(accuracy)), 4),
                         "macro_f1": round(float(np.mean(macro_f1)), 4)})
    best = max(rows, key=lambda r: r["macro_f1"])
    return {"folds": folds, "candidates": rows, "chosen": {"model": best["model"], "c": best["c"]}}


def evaluate(truth: list[str], predicted: list[str]) -> dict[str, float]:
    return {
        "accuracy": round(float(accuracy_score(truth, predicted)), 4),
        "macro_f1": round(float(f1_score(truth, predicted, average="macro")), 4),
        "weighted_f1": round(float(f1_score(truth, predicted, average="weighted")), 4),
        "n": len(truth),
    }


def tone(probabilities: np.ndarray, classes: list[str]) -> np.ndarray:
    """Hawkish minus dovish probability for each sentence, from -1 to +1."""
    index = {c: i for i, c in enumerate(classes)}
    return probabilities[:, index["hawkish"]] - probabilities[:, index["dovish"]]


CHUNK = 20_000


def embed_pool(sentences: list[str], name: str = "pool") -> np.ndarray:
    """Embeddings for a long list, saved chunk by chunk so an interrupted run resumes."""
    folder = EMBEDDINGS / name
    folder.mkdir(parents=True, exist_ok=True)
    parts = []
    for start in range(0, len(sentences), CHUNK):
        chunk = sentences[start:start + CHUNK]
        digest = hashlib.sha1("\n".join(chunk).encode()).hexdigest()[:12]
        target = folder / f"{start:08d}-{digest}.npy"
        if not target.exists():
            np.save(target, embed(chunk))
        parts.append(np.load(target))
    return np.vstack(parts) if parts else np.empty((0, 384), dtype=np.float32)


def train(texts_embedded: np.ndarray, labels: list[str]) -> LogisticRegression:
    return embeddings_model().fit(texts_embedded, labels)


class SavedScorer:
    """A fitted logistic regression read back from JSON: enough to score new sentences."""

    def __init__(self, classes: list[str], coef: np.ndarray, intercept: np.ndarray) -> None:
        self.classes_ = np.array(classes)
        self.coef_ = coef
        self.intercept_ = intercept

    def predict_proba(self, vectors: np.ndarray) -> np.ndarray:
        logits = vectors @ self.coef_.T + self.intercept_
        logits -= logits.max(axis=1, keepdims=True)
        weights = np.exp(logits)
        return weights / weights.sum(axis=1, keepdims=True)

    def predict(self, vectors: np.ndarray) -> np.ndarray:
        return self.classes_[self.predict_proba(vectors).argmax(axis=1)]


def save(model: LogisticRegression, target) -> None:
    import json

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps({
        "embedding_model": EMBEDDING_MODEL,
        "classes": [str(c) for c in model.classes_],
        "coef": model.coef_.round(8).tolist(),
        "intercept": model.intercept_.round(8).tolist(),
    }))


def load(source) -> SavedScorer:
    import json

    data = json.loads(source.read_text())
    if data["embedding_model"] != EMBEDDING_MODEL:
        raise ValueError(f"scorer was trained on {data['embedding_model']} embeddings")
    return SavedScorer(data["classes"], np.array(data["coef"]), np.array(data["intercept"]))
