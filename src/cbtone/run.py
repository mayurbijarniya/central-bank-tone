"""Run the analysis and write every output the report, figures and website read."""

from __future__ import annotations

import json
import math

import polars as pl

from cbtone import analysis, panel, paths, predict, scorer, tables, tone, web

PLACEBO_RUNS = 100
DECIMALS = 10


def speech_table() -> pl.DataFrame:
    """Every speech with its tone."""
    speeches = pl.read_parquet(paths.ALL_SPEECHES).filter(pl.col("english"))
    scores = pl.read_parquet(paths.SCORES)
    return speeches.join(panel.speech_tone(scores), on="speech_id", how="left")


def coverage(speeches: pl.DataFrame, scores: pl.DataFrame) -> dict:
    bis = speeches.filter(pl.col("source") == "bis")
    return {
        "speeches": speeches.height,
        "archive_speeches": bis.height,
        "feed_speeches": speeches.height - bis.height,
        "first_speech": str(speeches["date"].min()),
        "archive_last_speech": str(bis["date"].max()),
        "last_speech": str(speeches["date"].max()),
        "central_banks": int(speeches["bank"].drop_nulls().n_unique()),
        "policy_sentences": scores.height,
        "tested_banks": len(panel.TESTED),
    }


def analyze() -> dict:
    model = tone.fitted_scorer()
    speeches = speech_table()
    scores = pl.read_parquet(paths.SCORES)
    monthly = panel.monthly_tone(speeches)
    frame = panel.build(
        pl.read_parquet(paths.RATES), pl.read_parquet(paths.INFLATION), monthly
    )
    comparison = predict.compare(frame)
    return {
        "data": coverage(speeches, scores),
        "labeling": analysis.labeler_accuracy(model),
        "scorer_selection": tone.scorer_selection(),
        "tone_and_policy": analysis.tone_and_policy(frame),
        "tone_before_decisions": analysis.tone_before_decisions(frame),
        "leads_or_follows": analysis.leads_or_follows(frame),
        "prediction": comparison,
        "placebo": predict.placebo(frame, comparison["chosen"], runs=PLACEBO_RUNS),
        "_frames": {"speeches": speeches, "monthly": monthly, "panel": frame, "model": model},
    }


def rounded(value):
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, DECIMALS)
    if isinstance(value, dict):
        return {k: rounded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [rounded(v) for v in value]
    return value


def write(output: dict) -> dict:
    """Save results.json, the committed tables, the scorer and the website's data."""
    frames = output["_frames"]
    results = rounded({k: v for k, v in output.items() if k != "_frames"})
    paths.RESULTS.parent.mkdir(parents=True, exist_ok=True)
    paths.RESULTS.write_text(json.dumps(results, indent=2) + "\n")
    tables.write(frames["speeches"], pl.read_parquet(paths.RATES))
    scorer.save(frames["model"], paths.SCORER)
    web.export(results)
    return results
