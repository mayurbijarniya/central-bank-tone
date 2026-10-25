"""The compact tables committed to the repository.

Speech tone, monthly tone and monthly rates are small enough to commit, so the
website and `cbtone update` work without the raw archive or the hours of
scoring behind them.
"""

from __future__ import annotations

import polars as pl

from cbtone import banks, panel, paths, rates

SPEECH_COLUMNS = [
    "speech_id", "date", "area", "bank", "bank_name", "speaker", "title", "url", "source",
    "tone", "policy_sentences", "hawkish", "dovish",
]
FIRST_MONTH = pl.date(1997, 1, 1)
MIN_BANKS = 11


def with_names(frame: pl.DataFrame) -> pl.DataFrame:
    names = pl.DataFrame({"area": list(banks.NAMES), "bank_name": list(banks.NAMES.values())})
    return frame.drop("bank_name", strict=False).join(names, on="area", how="left")


def global_tone(monthly: pl.DataFrame) -> pl.DataFrame:
    """Mean tone across the tested banks each month.

    At least half the tested banks must have spoken in the window, so the average never
    rests on a different handful of banks, as it would after the archive ends and only
    the live feeds remain.
    """
    return (
        monthly.filter(pl.col("area").is_in(list(panel.TESTED)) & pl.col("tone").is_not_null())
        .group_by("month")
        .agg(tone=pl.col("tone").mean(), banks=pl.len())
        .filter(pl.col("banks") >= MIN_BANKS)
        .sort("month")
    )


def write(speeches: pl.DataFrame, daily_rates: pl.DataFrame) -> pl.DataFrame:
    """Write every table from speeches (with tone) and daily rates; returns the speech table."""
    paths.TABLES.mkdir(parents=True, exist_ok=True)
    table = (
        with_names(speeches).select(SPEECH_COLUMNS)
        .unique("speech_id", keep="last")
        .sort("date", "speech_id")
    )
    table.write_parquet(paths.SPEECH_TONE)
    monthly = panel.monthly_tone(table)
    with_names(monthly).write_parquet(paths.MONTHLY_TONE)
    global_tone(monthly).write_parquet(paths.GLOBAL_TONE)
    rates.monthly(daily_rates).filter(pl.col("month") >= FIRST_MONTH).select(
        "area", "month", "rate", "decision"
    ).write_parquet(paths.MONTHLY_RATES)
    return table
