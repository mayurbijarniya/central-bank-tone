"""Policy rate decisions by central bank and month.

The BIS publishes each policy rate daily. A month's decision is read from the
end-of-month rate: up or down by at least 0.10 percentage points is a hike or a
cut, anything smaller a hold. The threshold drops the drift of market-based
rates some banks targeted in the 1990s and early 2000s, while keeping every
announced move since (the smallest are the Bank of Japan's and the Bank of
England's 0.15-point steps).
"""

from __future__ import annotations

import polars as pl

DECISION_THRESHOLD = 0.10


def monthly(rates: pl.DataFrame) -> pl.DataFrame:
    """End-of-month rate, change on the month before, and the decision it implies."""
    return (
        rates.sort("area", "date")
        .with_columns(month=pl.col("date").dt.truncate("1mo"))
        .group_by("area", "month", maintain_order=True)
        .agg(rate=pl.col("rate").last(), last_day=pl.col("date").last())
        .with_columns(
            change=pl.when(
                pl.col("month").dt.offset_by("-1mo") == pl.col("month").shift(1).over("area")
            ).then((pl.col("rate") - pl.col("rate").shift(1)).over("area"))
        )
        .with_columns(
            decision=pl.when(pl.col("change") >= DECISION_THRESHOLD)
            .then(pl.lit("hike"))
            .when(pl.col("change") <= -DECISION_THRESHOLD)
            .then(pl.lit("cut"))
            .when(pl.col("change").is_not_null())
            .then(pl.lit("hold"))
        )
        .with_columns(pl.col("change").round(6))
    )
