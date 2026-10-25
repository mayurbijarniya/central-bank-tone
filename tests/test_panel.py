from datetime import date

import polars as pl

from cbtone import panel


def test_monthly_tone_averages_speeches_over_the_window():
    speeches = pl.DataFrame({
        "area": ["US", "US", "US", "US"],
        "date": [date(2020, 1, 5), date(2020, 1, 20), date(2020, 3, 3), date(2020, 6, 1)],
        "tone": [0.2, 0.4, -0.3, 0.1],
    })
    tone = panel.monthly_tone(speeches, window=3).sort("month")
    by_month = {r["month"]: r for r in tone.iter_rows(named=True)}
    assert round(by_month[date(2020, 1, 1)]["tone"], 6) == 0.3
    assert by_month[date(2020, 2, 1)]["tone_month"] is None
    assert round(by_month[date(2020, 3, 1)]["tone"], 6) == 0.1   # (0.2 + 0.4 - 0.3) / 3
    assert by_month[date(2020, 5, 1)]["tone"] == -0.3             # only March is in the window
    assert by_month[date(2020, 6, 1)]["tone"] == 0.1


def test_speech_tone_is_the_mean_over_policy_sentences():
    scores = pl.DataFrame({
        "speech_id": ["a", "a", "b"],
        "tone": [0.5, -0.1, 0.0],
        "label": ["hawkish", "neutral", "neutral"],
    })
    out = panel.speech_tone(scores).sort("speech_id").to_dicts()
    assert out[0]["tone"] == 0.2 and out[0]["policy_sentences"] == 2 and out[0]["hawkish"] == 0.5
    assert out[1]["dovish"] == 0.0


def month_rates(area, months, values):
    return pl.DataFrame({
        "area": [area] * len(months),
        "date": [date(y, m, 28) for y, m in months],
        "rate": values,
    })


def test_rows_see_only_the_past_and_the_target_is_next_month():
    months = [(2020, m) for m in range(1, 13)]
    rates = month_rates("US", months, [1.0] * 6 + [1.25] * 6)
    inflation = pl.DataFrame({
        "area": ["US"] * 12,
        "month": [date(y, m, 1) for y, m in months],
        "inflation": [float(m) for _, m in months],
    })
    tone = pl.DataFrame({
        "area": ["US"], "month": [date(2020, 6, 1)], "speeches": [1], "window_speeches": [1],
        "tone_month": [0.4], "tone": [0.4],
    })
    frame = panel.build(rates, inflation, tone, banks=("US",))
    june = frame.filter(pl.col("month") == date(2020, 6, 1)).row(0, named=True)
    assert june["next_decision"] == "hike"        # the July move is June's target
    assert june["decision"] == "hold"
    assert june["inflation_lag1"] == 5.0          # May's prices, published in June
    assert june["tone"] == 0.4
    july = frame.filter(pl.col("month") == date(2020, 7, 1)).row(0, named=True)
    assert july["last_move"] == 1 and july["months_since_move"] == 0
    assert frame["month"].max() == date(2020, 11, 1)   # December has no next month
