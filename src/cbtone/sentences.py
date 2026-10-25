"""Which sentences say something about monetary policy.

Most of a central banker's speech is about payments, supervision, financial
inclusion or history. Only sentences that mention policy, prices, rates or the
real economy can lean hawkish or dovish, so only those are scored, as in the
keyword filter of the Trillion Dollar Words study.
"""

from __future__ import annotations

import re

import polars as pl

POLICY_TERMS = [
    r"inflation\w*", r"disinflation\w*", r"deflation\w*", r"prices?", r"price stability",
    r"interest rates?", r"policy rates?", r"(?:bank|repo|cash|discount|deposit|lending) rate",
    r"federal funds", r"monetary policy", r"monetary conditions", r"policy stance",
    r"tighten\w*", r"eas(?:e|es|ed|ing)", r"accommodat\w*", r"restrictive\w*", r"stimul\w*",
    r"rate (?:increase|rise|hike|cut|reduction)s?", r"hik\w+", r"asset purchases?",
    r"quantitative easing", r"balance sheet", r"forward guidance",
    r"unemployment", r"employment", r"labou?r market\w*", r"wages?", r"output gap",
    r"economic growth", r"growth", r"gdp", r"economic activity", r"demand", r"recession\w*",
    r"overheat\w*", r"slack", r"productivity", r"expectations", r"exchange rate", r"currency",
]
POLICY = re.compile(r"\b(?:" + "|".join(POLICY_TERMS) + r")\b", re.IGNORECASE)


def is_policy(sentence: str) -> bool:
    return POLICY.search(sentence) is not None


def policy_sentences(sentences: pl.DataFrame) -> pl.DataFrame:
    """The sentences that mention policy, prices, rates or the real economy."""
    return sentences.filter(
        pl.col("sentence").map_elements(is_policy, return_dtype=pl.Boolean)
    )
