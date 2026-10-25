from datetime import date

import numpy as np
import polars as pl

from cbtone import predict


def synthetic_panel(informative: bool, seed: int = 0) -> pl.DataFrame:
    """Bank-months where tone does, or does not, announce next month's decision."""
    rng = np.random.default_rng(seed)
    rows = []
    for area in ("AA", "BB", "CC", "DD"):
        for i in range(12 * 26):
            month = date(1999 + i // 12, i % 12 + 1, 1)
            decision = rng.choice(["cut", "hold", "hold", "hold", "hike"])
            signal = {"cut": -0.5, "hold": 0.0, "hike": 0.5}[decision] if informative else 0.0
            rows.append({
                "area": area, "month": month, "next_decision": decision,
                "tone": signal + rng.normal(0, 0.2), "tone_change_3m": rng.normal(0, 0.1),
                **{f: rng.normal() for f in predict.BASELINE},
            })
    return pl.DataFrame(rows)


def test_split_is_by_time():
    parts = predict.split(synthetic_panel(False))
    assert parts["train"]["month"].max() <= date(2016, 12, 1)
    assert parts["validation"]["month"].min() >= date(2017, 1, 1)
    assert parts["validation"]["month"].max() <= date(2019, 12, 1)
    assert parts["test"]["month"].min() >= date(2020, 1, 1)


def test_shuffling_keeps_each_banks_values():
    frame = synthetic_panel(True)
    shuffled = predict.shuffle_tone(frame, seed=1)
    for area in ("AA", "BB"):
        a = frame.filter(pl.col("area") == area)["tone"].sort().to_list()
        b = shuffled.filter(pl.col("area") == area)["tone"].sort().to_list()
        assert a == b
    assert shuffled["tone"].to_list() != frame.sort("area", "month")["tone"].to_list()


def test_informative_tone_beats_its_placebo():
    result = predict.placebo(synthetic_panel(True), "logistic", runs=19)
    assert result["actual_gain"] > result["shuffled_gain_95th"]
    assert result["p_value"] == 0.05   # better than all 19 shuffles


def test_uninformative_tone_does_not():
    result = predict.placebo(synthetic_panel(False), "logistic", runs=19)
    assert result["p_value"] > 0.05
