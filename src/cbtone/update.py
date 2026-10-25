"""Add new speeches to the committed tables without rebuilding history.

Scoring history once takes hours; a week of new speeches takes seconds. This
step starts from the committed tables and the saved scorer, so it runs on any
machine without the raw archive (`cbtone update`, as often as wanted):

1. download the current year's BIS speeches, and the policy rates;
2. read the live feeds for anything newer than the archive;
3. score only speeches not already in the tables;
4. drop feed copies of speeches the archive now covers;
5. rebuild the monthly tables and the website's data.
"""

from __future__ import annotations

from datetime import date

import polars as pl

from cbtone import download, feeds, ingest, panel, paths, scorer, sentences, tables, web


def score_speeches(speeches: pl.DataFrame, model) -> pl.DataFrame:
    """Speech tone for speeches given as (speech_id, text)."""
    rows = [
        {"speech_id": sid, "n": n, "sentence": s}
        for sid, text in speeches.select("speech_id", "text").iter_rows()
        for n, s in enumerate(ingest.sentences(text))
    ]
    if not rows:
        return pl.DataFrame(schema={"speech_id": pl.Utf8, "tone": pl.Float64})
    pool = sentences.policy_sentences(pl.DataFrame(rows))
    if pool.is_empty():
        return pl.DataFrame(schema={"speech_id": pl.Utf8, "tone": pl.Float64})
    probabilities = model.predict_proba(scorer.embed(pool["sentence"].to_list()))
    classes = list(model.classes_)
    scored = pool.with_columns(
        label=pl.Series(list(model.classes_[probabilities.argmax(axis=1)])),
        tone=pl.Series(scorer.tone(probabilities, classes)),
    )
    return panel.speech_tone(scored)


def new_archive_speeches(known: set[str], year: int) -> pl.DataFrame:
    archives = [
        download.fetch(download.SPEECHES_URL.format(year=y),
                       paths.RAW_SPEECHES / f"speeches-{y}.zip", refresh=True)
        for y in (year - 1, year)
    ]
    built = ingest.build_speeches(ingest.read_speeches(archives)).filter(
        pl.col("english") & ~pl.col("speech_id").is_in(list(known))
    )
    return built.with_columns(source=pl.lit("bis"))


def new_feed_speeches(known: set[str], after: date) -> pl.DataFrame:
    found = feeds.fetch(after=after)
    if not found:
        return pl.DataFrame()
    frame = pl.DataFrame(found).with_columns(
        date=pl.col("date").str.to_date(),
        speech_id=pl.col("url").map_elements(feeds.speech_id, return_dtype=pl.Utf8),
    )
    frame = frame.filter(~pl.col("speech_id").is_in(list(known)))
    return frame.with_columns(
        text=pl.col("text").map_elements(ingest.clean, return_dtype=pl.Utf8),
        bank=pl.col("area"), speaker=pl.lit(None, pl.Utf8), source=pl.lit("feed"),
    )


def run_update(today: date | None = None) -> dict[str, int]:
    today = today or date.today()
    model = scorer.load(paths.SCORER)
    table = pl.read_parquet(paths.SPEECH_TONE)
    known = set(table["speech_id"])

    archive = new_archive_speeches(known, today.year)
    archive_end = max(
        d for d in (table.filter(pl.col("source") == "bis")["date"].max(),
                    archive["date"].max() if archive.height else None) if d
    )
    feed = new_feed_speeches(known, archive_end)

    added = [
        frame.join(score_speeches(frame, model), on="speech_id", how="left")
        for frame in (archive, feed)
        if not frame.is_empty()
    ]
    if added:
        named = [tables.with_names(a) for a in added]
        new = pl.concat(
            [a.select([c for c in tables.SPEECH_COLUMNS if c in a.columns]) for a in named],
            how="diagonal_relaxed",
        )
        table = pl.concat([table, new], how="diagonal_relaxed")

    # The archive's version replaces a feed's copy once the archive reaches that date.
    table = table.filter(~((pl.col("source") == "feed") & (pl.col("date") <= archive_end)))

    download.fetch(download.RATES_URL, paths.RAW_RATES, refresh=True)
    table = tables.write(table, ingest.read_rates())
    web.export()
    return {
        "archive_added": archive.height,
        "feed_added": 0 if feed.is_empty() else feed.height,
        "speeches": table.height,
    }
