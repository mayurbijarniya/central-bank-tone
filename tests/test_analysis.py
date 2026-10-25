from datetime import date

import numpy as np
import polars as pl

from cbtone import analysis


def test_partial_correlation_removes_a_shared_driver():
    rng = np.random.default_rng(0)
    driver = rng.normal(size=2000)
    x = driver + rng.normal(scale=0.3, size=2000)
    y = driver + rng.normal(scale=0.3, size=2000)
    assert np.corrcoef(x, y)[0, 1] > 0.8
    assert abs(analysis.partial_rank_correlation(x, y, driver)) < 0.1


def test_future_change_sums_the_next_months():
    frame = pl.DataFrame({
        "area": ["US"] * 5,
        "month": [date(2020, m, 1) for m in range(1, 6)],
        "change": [0.0, 0.25, 0.25, 0.0, -0.5],
        "tone": [0.1, 0.2, 0.3, 0.4, 0.5],
    })
    out = analysis.future_change(frame, months=3)
    assert out["change_ahead"].to_list() == [0.5, -0.25]


def test_tone_before_decisions_orders_the_means():
    frame = pl.DataFrame({
        "tone": [-0.2, -0.1, 0.0, 0.0, 0.1, 0.3],
        "next_decision": ["cut", "cut", "hold", "hold", "hike", "hike"],
    })
    rows = {r["decision"]: r for r in analysis.tone_before_decisions(frame)}
    assert rows["cut"]["mean_tone"] < rows["hold"]["mean_tone"] < rows["hike"]["mean_tone"]
    assert rows["hike"]["low"] <= rows["hike"]["mean_tone"] <= rows["hike"]["high"]
