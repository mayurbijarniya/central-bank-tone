"""Where every input and output lives, relative to the project root."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DATA = ROOT / "data"
RAW = DATA / "raw"
RAW_SPEECHES = RAW / "speeches"
RAW_RATES = RAW / "WS_CBPOL_csv_flat.zip"
RAW_PRICES = RAW / "WS_LONG_CPI_csv_flat.zip"
RAW_FEEDS = RAW / "feeds"

PROCESSED = DATA / "processed"
SPEECHES = PROCESSED / "speeches.parquet"
SENTENCES = PROCESSED / "sentences.parquet"
RATES = PROCESSED / "policy_rates.parquet"
INFLATION = PROCESSED / "inflation.parquet"
SCORES = PROCESSED / "sentence_scores.parquet"
ALL_SPEECHES = PROCESSED / "all_speeches.parquet"

OUTPUTS = ROOT / "outputs"
FIGURES = OUTPUTS / "figures"
TABLES = OUTPUTS / "tables"
SPEECH_TONE = TABLES / "speeches.parquet"
MONTHLY_TONE = TABLES / "monthly_tone.parquet"
GLOBAL_TONE = TABLES / "global_tone.parquet"
MONTHLY_RATES = TABLES / "policy_rates.parquet"
SCORER = TABLES / "scorer.json"
WEB_DATA = ROOT / "web" / "public" / "data"
RESULTS = OUTPUTS / "results.json"
FINDINGS = ROOT / "reports" / "FINDINGS.md"
