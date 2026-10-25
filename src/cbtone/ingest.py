"""Turn the BIS downloads into tidy Parquet tables.

speeches.parquet   one row per English speech, with the speaker's central bank
sentences.parquet  one row per sentence worth scoring
policy_rates.parquet  one row per central bank and day with a published rate
"""

from __future__ import annotations

import hashlib
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import duckdb
import polars as pl

from cbtone import banks, paths

# Lines that are layout, not speech: page furniture, separators, headings.
BOILERPLATE = re.compile(
    r"^(?:#.*|\**\s*(?:\*\s*)+|\d+(?:/\d+)?\.?|bis (?:central bankers['’] speeches|review).*)$",
    re.IGNORECASE,
)
LINK = re.compile(r"\[([^\]]*)\]\([^)]*\)")
SENTENCE_END = re.compile(r"(?<=[.!?])[\"”’)]?\s+(?=[A-Z“\"(])")
ABBREVIATION = re.compile(r"\b(?:Mr|Mrs|Ms|Dr|Prof|St|No|vs|e\.g|i\.e|cf|etc|Jan|Feb|Mar|Apr|"
                          r"Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|U\.S|U\.K|Fig|Vol|p|pp)\.$")

ENGLISH = frozenset((
    "the", "of", "and", "to", "in", "is", "that", "for", "on", "with",
    "as", "are", "be", "this", "by", "it", "we", "have", "has", "which",
))
MIN_ENGLISH_SHARE = 0.15
MIN_WORDS, MAX_WORDS = 8, 80


def english_share(text: str) -> float:
    """Share of words that are common English function words; about 0.3 for English prose."""
    words = re.findall(r"[a-z]+", text[:20000].lower())
    return sum(w in ENGLISH for w in words) / max(len(words), 1)


def clean(text: str) -> str:
    """Drop layout lines and markdown links, and join the rest into paragraphs."""
    kept = []
    for line in text.splitlines():
        line = LINK.sub(r"\1", line).replace("\\_", " ").strip()
        if not line or BOILERPLATE.match(line):
            kept.append("")
            continue
        kept.append(line)
    paragraphs = re.split(r"\n\s*\n", "\n".join(kept))
    return "\n\n".join(re.sub(r"\s+", " ", p).strip() for p in paragraphs if p.strip())


def sentences(text: str) -> list[str]:
    """Split cleaned text into sentences, keeping only those of a readable length."""
    out = []
    for paragraph in text.split("\n\n"):
        pieces = SENTENCE_END.split(paragraph)
        merged: list[str] = []
        for piece in pieces:
            # "Mr. Powell" and "U.S. inflation" end in a full stop but are not sentence ends.
            if merged and ABBREVIATION.search(merged[-1]):
                merged[-1] = f"{merged[-1]} {piece}"
            else:
                merged.append(piece)
        out.extend(merged)
    return [s for s in out if MIN_WORDS <= len(s.split()) <= MAX_WORDS]


def read_speeches(archives: list[Path]) -> pl.DataFrame:
    """Every speech in the yearly archives, as published."""
    with tempfile.TemporaryDirectory() as tmp:
        for archive in archives:
            with zipfile.ZipFile(archive) as z:
                z.extractall(tmp)
        con = duckdb.connect()
        frame = con.sql(
            f"""
            select url, title, description, author, text,
                   cast(substr(date, 1, 10) as date) as date
            from read_csv('{tmp}/*.csv', header = true, all_varchar = true,
                          max_line_size = 50000000)
            """
        ).pl()
        con.close()
    return frame


def build_speeches(raw: pl.DataFrame) -> pl.DataFrame:
    """One row per English speech, with its central bank and the policy rate it speaks to."""
    rows = []
    seen = set()
    for row in raw.sort("date", "url").iter_rows(named=True):
        text = clean(row["text"] or "")
        digest = hashlib.sha1(text.encode()).hexdigest()
        # A few speeches are published twice under different addresses; keep the first.
        if not text or digest in seen:
            continue
        seen.add(digest)
        bank = banks.bank_of(row["description"])
        rows.append(
            {
                "speech_id": row["url"].rsplit("/", 1)[-1].split(".")[0],
                "date": row["date"],
                "bank": bank,
                "area": banks.policy_area(bank, row["date"]),
                "speaker": row["author"],
                "title": row["title"],
                "description": row["description"],
                "url": row["url"],
                "words": len(text.split()),
                "english": english_share(text) >= MIN_ENGLISH_SHARE,
                "text": text,
            }
        )
    return pl.DataFrame(rows).sort("date", "speech_id")


def build_sentences(speeches: pl.DataFrame) -> pl.DataFrame:
    rows = []
    english = speeches.filter(pl.col("english")).select("speech_id", "text")
    for speech_id, text in english.iter_rows():
        for n, sentence in enumerate(sentences(text)):
            rows.append({"speech_id": speech_id, "n": n, "sentence": sentence})
    return pl.DataFrame(rows, schema={"speech_id": pl.Utf8, "n": pl.Int32, "sentence": pl.Utf8})


def read_rates(archive: Path = paths.RAW_RATES) -> pl.DataFrame:
    """Daily policy rates. Days without a rate are published as the text "NaN" and dropped."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
        source = next(Path(tmp).glob("*.csv"))
        con = duckdb.connect()
        frame = con.sql(
            f"""
            select split_part("REF_AREA:Reference area", ':', 1) as area,
                   cast("TIME_PERIOD:Time period or range" as date) as date,
                   try_cast("OBS_VALUE:Observation Value" as double) as rate
            from read_csv('{source}', all_varchar = true)
            where "FREQ:Frequency" like 'D:%'
            """
        ).pl()
        con.close()
    return (
        frame.filter(pl.col("rate").is_not_null() & pl.col("rate").is_not_nan())
        .sort("area", "date")
    )


def read_inflation(archive: Path = paths.RAW_PRICES) -> pl.DataFrame:
    """Monthly consumer price inflation, year on year, in percent."""
    with tempfile.TemporaryDirectory() as tmp:
        with zipfile.ZipFile(archive) as z:
            z.extractall(tmp)
        source = next(Path(tmp).glob("*.csv"))
        con = duckdb.connect()
        frame = con.sql(
            f"""
            select split_part("REF_AREA:Reference area", ':', 1) as area,
                   strptime("TIME_PERIOD:Time period or range", '%Y-%m')::date as month,
                   try_cast("OBS_VALUE:Observation Value" as double) as inflation
            from read_csv('{source}', all_varchar = true)
            where "FREQ:Frequency" like 'M:%'
              and "UNIT_MEASURE:Unit of measure" like '771:%'
            """
        ).pl()
        con.close()
    return (
        frame.filter(pl.col("inflation").is_not_null() & pl.col("inflation").is_not_nan())
        .sort("area", "month")
    )


def run() -> dict[str, int]:
    paths.PROCESSED.mkdir(parents=True, exist_ok=True)
    archives = sorted(paths.RAW_SPEECHES.glob("speeches-*.zip"))
    if not archives:
        raise FileNotFoundError(
            f"no speech archives in {paths.RAW_SPEECHES}; run `cbtone download`"
        )
    speeches = build_speeches(read_speeches(archives))
    sents = build_sentences(speeches)
    rates = read_rates()
    inflation = read_inflation()
    for frame, target in (
        (speeches, paths.SPEECHES),
        (sents, paths.SENTENCES),
        (rates, paths.RATES),
        (inflation, paths.INFLATION),
    ):
        tmp = target.with_suffix(".tmp")
        frame.write_parquet(tmp)
        shutil.move(tmp, target)
    return {
        "speeches": speeches.height,
        "sentences": sents.height,
        "rate_days": rates.height,
        "inflation_months": inflation.height,
    }
