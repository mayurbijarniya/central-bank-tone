from datetime import date

import polars as pl

from cbtone import rates


def daily(values):
    return pl.DataFrame(
        {
            "area": ["US"] * len(values),
            "date": [d for d, _ in values],
            "rate": [r for _, r in values],
        }
    )


def test_month_end_moves_of_a_tenth_or_more_are_decisions():
    frame = rates.monthly(daily([
        (date(2024, 1, 31), 5.00),
        (date(2024, 2, 29), 5.25),   # hike
        (date(2024, 3, 31), 5.20),   # drift, a hold
        (date(2024, 4, 15), 5.00),
        (date(2024, 4, 30), 4.85),   # cut, read at month end
    ]))
    assert frame["decision"].to_list() == [None, "hike", "hold", "cut"]
    assert frame["change"].to_list() == [None, 0.25, -0.05, -0.35]


def test_a_missing_month_breaks_the_chain():
    frame = rates.monthly(daily([(date(2024, 1, 31), 1.0), (date(2024, 3, 31), 2.0)]))
    assert frame["change"].to_list() == [None, None]
    assert frame["decision"].to_list() == [None, None]
