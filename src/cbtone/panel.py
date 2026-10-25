"""One row per central bank and month: speech tone, the policy rate and inflation.

Everything in a row is known by the end of that month, and the target is the
decision taken the month after, so no row can see its own answer:

- tone uses speeches given up to the end of the month;
- inflation is lagged one month further, because a month's consumer prices
  are published during the following month.
"""

from __future__ import annotations

import polars as pl

from cbtone import rates

# Banks with a published policy rate and at least 100 English speeches since
# 1999, less Hong Kong and Denmark, whose rates follow the US dollar and the
# euro by design.
TESTED = (
    "US", "XM", "IN", "GB", "JP", "CA", "MY", "PH", "AU", "SE", "CH",
    "ZA", "NO", "TH", "NZ", "RS", "CL", "CN", "IL", "KR", "TR",
)
FIRST_MONTH = "1999-01-01"
TONE_WINDOW = 3  # months of speeches averaged into a bank's tone


def speech_tone(scores: pl.DataFrame) -> pl.DataFrame:
    """Tone of each speech: the mean hawkish-minus-dovish score of its policy sentences."""
    return scores.group_by("speech_id").agg(
        tone=pl.col("tone").mean(),
        policy_sentences=pl.len(),
        hawkish=(pl.col("label") == "hawkish").mean(),
        dovish=(pl.col("label") == "dovish").mean(),
    )


def monthly_tone(speeches: pl.DataFrame, window: int = TONE_WINDOW) -> pl.DataFrame:
    """Each bank's tone by month: speeches in the month, and the mean over the last `window`.

    `speeches` needs area, date and tone. Every speech counts once, however long.
    """
    by_month = (
        speeches.filter(pl.col("area").is_not_null() & pl.col("tone").is_not_null())
        .with_columns(month=pl.col("date").dt.truncate("1mo"))
        .group_by("area", "month")
        .agg(tone_sum=pl.col("tone").sum(), speeches=pl.len())
    )
    span = by_month.group_by("area").agg(
        start=pl.col("month").min(), end=pl.col("month").max()
    )
    grid = span.with_columns(
        month=pl.date_ranges("start", "end", interval="1mo")
    ).explode("month").select("area", "month")
    full = (
        grid.join(by_month, on=["area", "month"], how="left")
        .with_columns(pl.col("tone_sum", "speeches").fill_null(0))
        .sort("area", "month")
    )
    rolled = full.with_columns(
        window_sum=pl.col("tone_sum").rolling_sum(window, min_samples=1).over("area"),
        window_speeches=pl.col("speeches").rolling_sum(window, min_samples=1).over("area"),
    )
    return rolled.with_columns(
        tone_month=pl.when(pl.col("speeches") > 0)
        .then(pl.col("tone_sum") / pl.col("speeches")),
        tone=pl.when(pl.col("window_speeches") > 0)
        .then(pl.col("window_sum") / pl.col("window_speeches")),
    ).select("area", "month", "speeches", "window_speeches", "tone_month", "tone")


def build(daily_rates: pl.DataFrame, inflation: pl.DataFrame, tone: pl.DataFrame,
          banks: tuple[str, ...] = TESTED) -> pl.DataFrame:
    """The bank-month panel with features known at month end and next month's decision."""
    months = rates.monthly(daily_rates).filter(pl.col("area").is_in(list(banks)))
    lagged_inflation = inflation.with_columns(
        month=pl.col("month").dt.offset_by("1mo")
    ).rename({"inflation": "inflation_lag1"})

    frame = (
        months.join(lagged_inflation, on=["area", "month"], how="left")
        .join(tone, on=["area", "month"], how="left")
        .sort("area", "month")
    )
    moved = pl.col("decision").is_in(["hike", "cut"])
    frame = frame.with_columns(
        change_3m=pl.col("change").rolling_sum(3).over("area"),
        change_6m=pl.col("change").rolling_sum(6).over("area"),
        change_12m=pl.col("change").rolling_sum(12).over("area"),
        last_move=pl.when(moved).then(
            pl.when(pl.col("decision") == "hike").then(1).otherwise(-1)
        ).forward_fill().over("area").fill_null(0),
        move_index=moved.cast(pl.Int32).cum_sum().over("area"),
        inflation_change_6m=(
            pl.col("inflation_lag1") - pl.col("inflation_lag1").shift(6)
        ).over("area"),
        tone_change_3m=(pl.col("tone") - pl.col("tone").shift(3)).over("area"),
        next_decision=pl.col("decision").shift(-1).over("area"),
        next_month=pl.col("month").shift(-1).over("area"),
    )
    frame = frame.with_columns(
        months_since_move=pl.int_range(pl.len()).over(["area", "move_index"]),
    )
    gap = (pl.col("next_month").dt.month() - pl.col("month").dt.month()
           + 12 * (pl.col("next_month").dt.year() - pl.col("month").dt.year()))
    return frame.filter(
        (pl.col("month") >= pl.lit(FIRST_MONTH).str.to_date())
        & pl.col("next_decision").is_not_null()
        & (gap == 1)
    ).drop("move_index", "next_month")
