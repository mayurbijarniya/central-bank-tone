"""Q3: does speech tone predict next month's decision beyond inflation and past rates?

The same rows and the same model are fitted twice, once on the baseline
features and once with tone added, so any difference comes from tone alone.
Models are trained on 1999-2016, chosen on 2017-2019 and tested once on
2020 onward.
"""

from __future__ import annotations

import numpy as np
import polars as pl
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score, log_loss
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

BASELINE = [
    "change", "change_3m", "change_6m", "change_12m", "last_move", "months_since_move",
    "rate", "inflation_lag1", "inflation_change_6m",
]
TONE = ["tone", "tone_change_3m"]
CLASSES = ["cut", "hike", "hold"]

TRAIN_END = "2016-12-01"
VALIDATION_END = "2019-12-01"
SEED = 0


def split(panel: pl.DataFrame) -> dict[str, pl.DataFrame]:
    """Rows with every feature present, cut by time."""
    usable = panel.drop_nulls(BASELINE + TONE + ["next_decision"]).sort("area", "month")
    train_end = pl.lit(TRAIN_END).str.to_date()
    validation_end = pl.lit(VALIDATION_END).str.to_date()
    return {
        "train": usable.filter(pl.col("month") <= train_end),
        "validation": usable.filter(
            (pl.col("month") > train_end) & (pl.col("month") <= validation_end)
        ),
        "test": usable.filter(pl.col("month") > validation_end),
    }


def models() -> dict[str, object]:
    # No class weights: log loss judges the probabilities, and reweighting classes
    # would distort them.
    return {
        "logistic": make_pipeline(StandardScaler(), LogisticRegression(max_iter=5000)),
        "boosted_trees": HistGradientBoostingClassifier(
            max_depth=3, learning_rate=0.05, max_iter=300, random_state=SEED,
        ),
    }


def scores(truth: np.ndarray, probabilities: np.ndarray, classes: list[str]) -> dict:
    predicted = np.array(classes)[probabilities.argmax(axis=1)]
    moves = truth != "hold"
    return {
        "log_loss": round(float(log_loss(truth, probabilities, labels=classes)), 4),
        "macro_f1": round(float(f1_score(truth, predicted, average="macro")), 4),
        "move_accuracy": round(float((predicted[moves] == truth[moves]).mean()), 4),
        "rows": int(len(truth)),
        "moves": int(moves.sum()),
    }


def fit_and_score(parts: dict[str, pl.DataFrame], features: list[str], model) -> dict:
    train = parts["train"]
    model.fit(train.select(features).to_numpy(), train["next_decision"].to_numpy())
    classes = list(model.classes_)
    out = {}
    for name in ("validation", "test"):
        part = parts[name]
        probabilities = model.predict_proba(part.select(features).to_numpy())
        out[name] = scores(part["next_decision"].to_numpy(), probabilities, classes)
    return out


def compare(panel: pl.DataFrame) -> dict:
    """Baseline against baseline plus tone, for each model."""
    parts = split(panel)
    results = {"rows": {k: v.height for k, v in parts.items()}, "models": {}}
    for name, model in models().items():
        results["models"][name] = {
            "baseline": fit_and_score(parts, BASELINE, model),
            "with_tone": fit_and_score(parts, BASELINE + TONE, models()[name]),
        }
    chosen = min(
        results["models"],
        key=lambda n: results["models"][n]["with_tone"]["validation"]["log_loss"],
    )
    results["chosen"] = chosen
    return results


def shuffle_tone(panel: pl.DataFrame, seed: int) -> pl.DataFrame:
    """Each bank's tone in a random order of months: same values, no timing."""
    rng = np.random.default_rng(seed)
    parts = []
    for _, group in panel.sort("area", "month").group_by("area", maintain_order=True):
        order = rng.permutation(group.height)
        parts.append(group.with_columns(
            pl.Series("tone", group["tone"].to_numpy()[order]),
            pl.Series("tone_change_3m", group["tone_change_3m"].to_numpy()[order]),
        ))
    return pl.concat(parts)


def placebo(panel: pl.DataFrame, model_name: str, runs: int = 100) -> dict:
    """How often shuffled tone improves test log loss as much as real tone does.

    Small gains appear by chance, because any extra column lets a model fit noise.
    """
    def gain(frame: pl.DataFrame) -> float:
        parts = split(frame)
        base = fit_and_score(parts, BASELINE, models()[model_name])["test"]["log_loss"]
        tone = fit_and_score(parts, BASELINE + TONE, models()[model_name])["test"]["log_loss"]
        return base - tone

    actual = gain(panel)
    shuffled = [gain(shuffle_tone(panel, seed)) for seed in range(runs)]
    return {
        "actual_gain": round(actual, 4),
        "shuffled_gain_mean": round(float(np.mean(shuffled)), 4),
        "shuffled_gain_95th": round(float(np.percentile(shuffled, 95)), 4),
        "p_value": round((1 + sum(g >= actual for g in shuffled)) / (runs + 1), 4),
        "runs": runs,
        "shuffled_gains": [round(g, 6) for g in shuffled],
    }
