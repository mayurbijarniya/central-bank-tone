import json
from datetime import date

import polars as pl

from cbtone import web


def test_clean_rounds_and_drops_nan():
    assert web._clean({"a": 0.123456, "b": float("nan"), "c": [date(2026, 1, 2)]}) == {
        "a": 0.1235, "b": None, "c": ["2026-01-02"]
    }


def test_bank_list_needs_three_recent_speeches_for_a_tone():
    speeches = pl.DataFrame({
        "area": ["US", "US", "US", "GB", "GB"],
        "date": [date(2026, 6, 1), date(2026, 6, 2), date(2026, 6, 3),
                 date(2026, 6, 1), date(2010, 1, 1)],
        "tone": [0.1, 0.2, 0.3, -0.2, 0.5],
    })
    rates = pl.DataFrame({"area": ["US"], "month": [date(2026, 6, 1)]})
    banks = {b["code"]: b for b in web.bank_list(speeches, rates, {"US": 0.2})}
    assert round(banks["US"]["recentTone"], 6) == 0.2
    assert banks["US"]["hasRates"] and banks["US"]["rho"] == 0.2
    assert banks["GB"]["recentTone"] is None and not banks["GB"]["hasRates"]


def test_written_json_is_compact(tmp_path, monkeypatch):
    monkeypatch.setattr(web.paths, "WEB_DATA", tmp_path)
    web._write("x/y.json", {"value": 1.0})
    assert json.loads((tmp_path / "x" / "y.json").read_text()) == {"value": 1.0}
    assert " " not in (tmp_path / "x" / "y.json").read_text()
