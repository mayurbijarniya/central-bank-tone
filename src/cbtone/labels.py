"""The labeled sentences the local scorer learns from and is tested on.

Three sets, each saved in `labels/` so results can be checked and reproduced
without calling a language model again:

fomc                   human labels on Federal Reserve sentences (Shah, Paturi and
                       Chava, 2023)
llm.csv                language-model labels on a sample of every bank's policy sentences
crosscheck.csv         150 sentences from 20 banks other than the Fed, labeled by two
crosscheck_labels.csv  language models from different families, to see whether they agree
                       outside Fed language
"""

from __future__ import annotations

import csv
import math

import polars as pl

from cbtone import llm, paths, sentences

LABELS_DIR = paths.ROOT / "labels"
LLM_LABELS = LABELS_DIR / "llm.csv"
CROSSCHECK = LABELS_DIR / "crosscheck.csv"
CROSSCHECK_LABELS = LABELS_DIR / "crosscheck_labels.csv"
FOMC = paths.RAW / "fomc"
FOMC_NAMES = {0: "dovish", 1: "hawkish", 2: "neutral"}

SAMPLE_SIZE = 8000
SEED = 2026
BATCH = 25


def fomc(split: str) -> pl.DataFrame:
    """The human-labeled FOMC sentences, `train` or `test`."""
    frame = pl.read_csv(FOMC / f"{split}.csv")
    return frame.select(
        "sentence", pl.col("label").replace_strict(FOMC_NAMES).alias("label"), "year"
    )


def policy_pool() -> pl.DataFrame:
    """Every policy sentence, with its speech's bank and date."""
    speeches = pl.read_parquet(paths.SPEECHES).select("speech_id", "date", "area")
    pool = pl.read_parquet(paths.SENTENCES).join(speeches, on="speech_id")
    return sentences.policy_sentences(pool).with_columns(
        pl.col("area").fill_null("other")
    )


def sample(pool: pl.DataFrame, size: int = SAMPLE_SIZE, seed: int = SEED,
           exclude: pl.DataFrame | None = None) -> pl.DataFrame:
    """A sample spread across banks.

    Each bank's share is proportional to the square root of its sentence count,
    so the euro area and the Fed do not crowd out smaller banks, while banks
    with a handful of speeches are not oversampled either.
    """
    if exclude is not None:
        pool = pool.join(exclude.select("speech_id", "n"), on=["speech_id", "n"], how="anti")
    counts = pool.group_by("area").len().sort("area")
    weights = {a: math.sqrt(n) for a, n in counts.iter_rows()}
    total = sum(weights.values())
    quotas = {a: min(n, round(size * weights[a] / total)) for a, n in counts.iter_rows()}
    parts = [
        pool.filter(pl.col("area") == area).sample(quota, seed=seed)
        for area, quota in sorted(quotas.items())
        if quota
    ]
    return pl.concat(parts).sort("area", "speech_id", "n")


def label_sample(chosen: pl.DataFrame, target=LLM_LABELS) -> llm.Usage:
    """Label every sentence in `chosen` not already in `target`, appending as it goes."""
    config = llm.settings()
    usage = llm.Usage()
    done = set()
    if target.exists():
        done = {(r["speech_id"], int(r["n"])) for r in csv.DictReader(target.open())}
    todo = chosen.filter(
        ~pl.struct("speech_id", "n").map_elements(
            lambda r: (r["speech_id"], r["n"]) in done, return_dtype=pl.Boolean
        )
    )
    new_file = not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", newline="") as handle:
        writer = csv.writer(handle)
        if new_file:
            writer.writerow(["speech_id", "n", "area", "date", "sentence", "label", "model"])
        rows = todo.select("speech_id", "n", "area", "date", "sentence").rows()
        for start in range(0, len(rows), BATCH):
            batch = rows[start:start + BATCH]
            labels = llm.label([r[4] for r in batch], usage, config)
            for row, label in zip(batch, labels, strict=True):
                if label is not None:
                    writer.writerow([*row, label, config["LLM_MODEL"]])
            handle.flush()
    return usage


def llm_labels() -> pl.DataFrame:
    return pl.read_csv(LLM_LABELS, schema_overrides={"date": pl.Date, "speech_id": pl.Utf8})


def label_crosscheck(model: str | None = None) -> llm.Usage:
    """Add one model's labels for the cross-check sentences to `crosscheck_labels.csv`.

    `model` overrides LLM_MODEL, so a second model can label the same sentences.
    """
    config = llm.settings()
    if model:
        config = {**config, "LLM_MODEL": model}
    chosen = pl.read_csv(CROSSCHECK, schema_overrides={"speech_id": pl.Utf8})
    usage = llm.Usage()
    rows = []
    for start in range(0, chosen.height, BATCH):
        batch = chosen.slice(start, BATCH)
        found = llm.label(batch["sentence"].to_list(), usage, config)
        rows.extend((row, config["LLM_MODEL"], label)
                    for row, label in zip(batch["row"], found, strict=True))
    new = pl.DataFrame(rows, schema=["row", "model", "label"], orient="row")
    if CROSSCHECK_LABELS.exists():
        kept = pl.read_csv(CROSSCHECK_LABELS).filter(pl.col("model") != config["LLM_MODEL"])
        new = pl.concat([kept, new])
    new.sort("model", "row").write_csv(CROSSCHECK_LABELS)
    return usage


def crosscheck_models() -> list[str]:
    return sorted(pl.read_csv(CROSSCHECK_LABELS)["model"].unique())


def crosscheck() -> pl.DataFrame:
    """The cross-check sentences with one label column per model."""
    sentences_ = pl.read_csv(CROSSCHECK, schema_overrides={"speech_id": pl.Utf8})
    labels = pl.read_csv(CROSSCHECK_LABELS).pivot(on="model", index="row", values="label")
    return sentences_.join(labels, on="row", how="left")
