"""Score every policy sentence and combine them into speech tone.

The scorer is the one chosen by cross-validation in `scorer`: sentence
embeddings plus logistic regression, trained on the human FOMC labels and the
language-model labels together.
"""

from __future__ import annotations

import numpy as np
import polars as pl

from cbtone import feeds, ingest, labels, paths, scorer, sentences


def training_set() -> dict:
    """Human FOMC labels and language-model labels together, with each sentence's speech.

    FOMC sentences carry no speech id, so they are grouped in fives in file order,
    which keeps neighbouring sentences from the same document together.
    """
    human = labels.fomc("train")
    machine = labels.llm_labels()
    return {
        "texts": human["sentence"].to_list() + machine["sentence"].to_list(),
        "vectors": np.vstack([
            scorer.embed(human["sentence"], cache="fomc_train"),
            scorer.embed(machine["sentence"], cache="llm"),
        ]),
        "labels": human["label"].to_list() + machine["label"].to_list(),
        "groups": [f"fomc-{i // 5}" for i in range(human.height)] + machine["speech_id"].to_list(),
    }


def fitted_scorer():
    data = training_set()
    return scorer.train(data["vectors"], data["labels"])


def scorer_selection() -> dict:
    data = training_set()
    return scorer.select(data["texts"], data["vectors"], data["labels"], data["groups"])


def score(pool: pl.DataFrame, model, cache: str) -> pl.DataFrame:
    """Class probabilities, the most likely label and tone for each sentence in `pool`."""
    vectors = scorer.embed_pool(pool["sentence"].to_list(), name=cache)
    probabilities = model.predict_proba(vectors)
    classes = list(model.classes_)
    return pool.select("speech_id", "n").with_columns(
        *[pl.Series(f"p_{c}", probabilities[:, i]) for i, c in enumerate(classes)],
        pl.Series("label", np.array(classes)[probabilities.argmax(axis=1)]),
        pl.Series("tone", scorer.tone(probabilities, classes)),
    )


def feed_speeches(after) -> pl.DataFrame:
    """Speeches from the live feeds dated after the archive's last speech, in archive shape."""
    found = feeds.saved().filter(pl.col("date") > after)
    if found.is_empty():
        return pl.DataFrame()
    return found.with_columns(
        speech_id=pl.col("url").map_elements(feeds.speech_id, return_dtype=pl.Utf8),
        bank=pl.col("area"),
        speaker=pl.lit(None, pl.Utf8),
        description=pl.lit(None, pl.Utf8),
        words=pl.col("text").str.split(" ").list.len(),
        english=pl.lit(True),
        source=pl.lit("feed"),
    )


def run() -> dict[str, int]:
    model = fitted_scorer()
    archive = pl.read_parquet(paths.SPEECHES).with_columns(source=pl.lit("bis"))
    pool = labels.policy_pool().sort("speech_id", "n")
    scored = score(pool, model, cache="pool")

    newer = feed_speeches(archive["date"].max())
    if not newer.is_empty():
        rows = [
            {"speech_id": sid, "n": n, "sentence": s}
            for sid, text in newer.select("speech_id", "text").iter_rows()
            for n, s in enumerate(ingest.sentences(ingest.clean(text)))
        ]
        feed_pool = sentences.policy_sentences(
            pl.DataFrame(rows).with_columns(pl.col("n").cast(pl.Int32))
        ).sort("speech_id", "n")
        scored = pl.concat([scored, score(feed_pool, model, cache="feeds")])
        archive = pl.concat([archive, newer.select(archive.columns)], how="vertical_relaxed")

    scored.write_parquet(paths.SCORES)
    archive.write_parquet(paths.ALL_SPEECHES)
    return {"sentences_scored": scored.height, "feed_speeches": newer.height}
