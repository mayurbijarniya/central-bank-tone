"""The JSON the website reads, written to web/public/data.

The site is static: every chart reads one of these files, so it loads without
a server. "Score a speech" runs the saved scorer in the browser from a copy of
scorer.json.
"""

from __future__ import annotations

import json
import math
import shutil
from datetime import date, timedelta

import polars as pl

from cbtone import banks, feeds, panel, paths

RECENT_DAYS = 183
MIN_RECENT_SPEECHES = 3
LATEST_SPEECHES = 60


def _clean(value):
    if isinstance(value, float):
        return None if math.isnan(value) else round(value, 4)
    if isinstance(value, dict):
        return {k: _clean(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_clean(v) for v in value]
    if isinstance(value, date):
        return value.isoformat()
    return value


def _write(name: str, value) -> None:
    target = paths.WEB_DATA / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_clean(value), separators=(",", ":"), ensure_ascii=False))


def _month(frame: pl.DataFrame) -> pl.DataFrame:
    return frame.with_columns(pl.col("month").dt.strftime("%Y-%m"))


def bank_list(speeches: pl.DataFrame, monthly_rates: pl.DataFrame, rho: dict) -> list[dict]:
    """Every bank with speeches, with its tone over the last six months of the archive."""
    cutoff = speeches["date"].max() - timedelta(days=RECENT_DAYS)
    with_rates = set(monthly_rates["area"].unique())
    rows = []
    for (area,), group in speeches.drop_nulls("area").group_by("area", maintain_order=True):
        recent = group.filter((pl.col("date") >= cutoff) & pl.col("tone").is_not_null())
        rows.append({
            "code": area,
            "name": banks.NAMES.get(area, area),
            "region": banks.REGIONS.get(area, "Other"),
            "speeches": group.height,
            "first": group["date"].min(),
            "last": group["date"].max(),
            "recentTone": recent["tone"].mean() if recent.height >= MIN_RECENT_SPEECHES else None,
            "recentSpeeches": recent.height,
            "hasRates": area in with_rates,
            "tested": area in panel.TESTED,
            "live": area in feeds.FEEDS,
            "rho": rho.get(area),
        })
    return sorted(rows, key=lambda r: -r["speeches"])


def bank_detail(area: str, speeches: pl.DataFrame, monthly: pl.DataFrame,
                monthly_rates: pl.DataFrame) -> dict:
    tone = _month(monthly.filter((pl.col("area") == area) & pl.col("tone").is_not_null()))
    rate = _month(monthly_rates.filter(pl.col("area") == area))
    latest = speeches.filter(pl.col("area") == area).sort("date", descending=True).head(
        LATEST_SPEECHES
    )
    return {
        "code": area,
        "name": banks.NAMES.get(area, area),
        "region": banks.REGIONS.get(area, "Other"),
        "tone": [{"m": m, "tone": t, "n": n} for m, t, n in
                 tone.select("month", "tone", "window_speeches").iter_rows()],
        "rates": [{"m": m, "rate": r, "decision": d} for m, r, d in
                  rate.select("month", "rate", "decision").iter_rows()],
        "speeches": latest.select(
            "date", "speaker", "title", "url", "tone", "source"
        ).to_dicts(),
    }


def summary(results: dict) -> dict:
    return {
        "data": results["data"],
        "labeling": results["labeling"],
        "policy": {
            **{k: v for k, v in results["tone_and_policy"].items() if k != "banks"},
            "banks": [{**b, "name": banks.NAMES.get(b["area"], b["area"])}
                      for b in results["tone_and_policy"]["banks"]],
        },
        "beforeDecisions": results["tone_before_decisions"],
        "leadsOrFollows": results["leads_or_follows"],
        "prediction": results["prediction"],
        "placebo": results["placebo"],
    }


def export(results: dict | None = None) -> None:
    """Write every file the site reads from the committed tables and results."""
    results = results or json.loads(paths.RESULTS.read_text())
    speeches = pl.read_parquet(paths.SPEECH_TONE)
    monthly = pl.read_parquet(paths.MONTHLY_TONE)
    monthly_rates = pl.read_parquet(paths.MONTHLY_RATES)
    rho = {b["area"]: b["rho"] for b in results["tone_and_policy"]["banks"]}

    if paths.WEB_DATA.exists():
        shutil.rmtree(paths.WEB_DATA)
    listed = bank_list(speeches, monthly_rates, rho)
    _write("summary.json", {**summary(results), "lastSpeech": speeches["date"].max()})
    _write("global.json", [
        {"m": m, "tone": t, "banks": n}
        for m, t, n in _month(pl.read_parquet(paths.GLOBAL_TONE)).iter_rows()
    ])
    _write("banks.json", listed)
    # Copied rather than rewritten: _write rounds to four decimals, the weights need all eight.
    shutil.copyfile(paths.SCORER, paths.WEB_DATA / "scorer.json")
    for bank in listed:
        _write(f"banks/{bank['code']}.json",
               bank_detail(bank["code"], speeches, monthly, monthly_rates))
