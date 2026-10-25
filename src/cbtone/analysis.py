"""Q1 and Q2: how well tone is read, and whether it moves with policy."""

from __future__ import annotations

import numpy as np
import polars as pl
from scipy import stats
from sklearn.metrics import cohen_kappa_score

from cbtone import labels, scorer

BOOTSTRAP = 2000
SEED = 0


def labeler_accuracy(model) -> dict:
    """The LLM and the local scorer against human labels, and the cross-check outside the Fed."""
    out = {}
    test = labels.fomc("test")
    llm_test = pl.read_csv(labels.LABELS_DIR / "fomc_test_llm.csv")
    out["llm_fomc_test"] = scorer.evaluate(
        llm_test["label"].to_list(), [p or "neutral" for p in llm_test["llm"].to_list()]
    )
    predicted = model.predict(scorer.embed(test["sentence"], cache="fomc_test"))
    out["scorer_fomc_test"] = scorer.evaluate(test["label"].to_list(), list(predicted))

    out["crosscheck"] = crosscheck_agreement(model)
    return out


def crosscheck_agreement(model) -> dict:
    """Two language models from different families, and the local scorer, on non-Fed sentences.

    There is no human answer here, so this measures agreement, not accuracy: where the two
    models agree, their shared label is used as the reference for the local scorer.
    """
    check = labels.crosscheck()
    # The first model is the one that labeled the training sample; the second is the check.
    first = labels.llm_labels()["model"][0]
    second = next(c for c in labels.crosscheck_models() if c != first)
    a, b = check[first].to_list(), check[second].to_list()
    local = list(model.predict(scorer.embed(check["sentence"], cache="crosscheck")))
    agreed = [i for i in range(len(a)) if a[i] == b[i]]
    return {
        "models": [first, second],
        "sentences": len(a),
        "banks": int(check["bank"].n_unique()),
        "agreement": round(sum(x == y for x, y in zip(a, b, strict=True)) / len(a), 4),
        "kappa": round(float(cohen_kappa_score(a, b)), 4),
        "scorer_vs_first": round(sum(x == y for x, y in zip(local, a, strict=True)) / len(a), 4),
        "scorer_vs_second": round(sum(x == y for x, y in zip(local, b, strict=True)) / len(a), 4),
        "consensus_sentences": len(agreed),
        "scorer_on_consensus": round(sum(local[i] == a[i] for i in agreed) / len(agreed), 4),
    }


def future_change(panel: pl.DataFrame, months: int = 3) -> pl.DataFrame:
    """Rate change over the next `months`, alongside each month's tone."""
    ahead = sum(pl.col("change").shift(-k).over("area") for k in range(1, months + 1))
    return panel.with_columns(change_ahead=ahead).drop_nulls(["tone", "change_ahead"])


def partial_rank_correlation(x: np.ndarray, y: np.ndarray, control: np.ndarray) -> float:
    """Spearman correlation of x and y after removing what `control` explains of each."""
    rx, ry, rc = (stats.rankdata(v) for v in (x, y, control))
    residual_x = rx - np.polyval(np.polyfit(rc, rx, 1), rc)
    residual_y = ry - np.polyval(np.polyfit(rc, ry, 1), rc)
    return float(np.corrcoef(residual_x, residual_y)[0, 1])


def leads_or_follows(panel: pl.DataFrame) -> dict:
    """Does tone run ahead of rate moves, or echo the moves and inflation already seen?"""
    frame = future_change(panel).drop_nulls(["change_3m", "inflation_lag1"])
    tone = frame["tone"].to_numpy()

    def rho(column: str) -> float:
        return round(float(stats.spearmanr(tone, frame[column]).statistic), 4)

    return {
        "with_next_3m_change": rho("change_ahead"),
        "with_past_3m_change": rho("change_3m"),
        "with_inflation": rho("inflation_lag1"),
        "next_given_past": round(partial_rank_correlation(
            tone, frame["change_ahead"].to_numpy(), frame["change_3m"].to_numpy()), 4),
        "months": frame.height,
    }


def tone_and_policy(panel: pl.DataFrame) -> dict:
    """Rank correlation of tone with the coming rate change, pooled and bank by bank."""
    frame = future_change(panel)
    pooled = stats.spearmanr(frame["tone"], frame["change_ahead"])
    by_bank = []
    for area, group in frame.group_by("area", maintain_order=True):
        if group.height >= 60:
            rho = stats.spearmanr(group["tone"], group["change_ahead"]).statistic
            by_bank.append({"area": area[0], "rho": round(float(rho), 4), "months": group.height})
    by_bank.sort(key=lambda r: r["rho"], reverse=True)
    positive = sum(r["rho"] > 0 for r in by_bank)
    return {
        "pooled_rho": round(float(pooled.statistic), 4),
        "pooled_p": float(pooled.pvalue),
        "months": frame.height,
        "banks": by_bank,
        "banks_positive": positive,
        "banks_total": len(by_bank),
        "sign_test_p": float(stats.binomtest(positive, len(by_bank)).pvalue) if by_bank else None,
    }


def tone_before_decisions(panel: pl.DataFrame) -> list[dict]:
    """Mean tone in the month before hikes, holds and cuts, with bootstrap intervals."""
    rng = np.random.default_rng(SEED)
    out = []
    frame = panel.drop_nulls(["tone", "next_decision"])
    for decision in ("cut", "hold", "hike"):
        values = frame.filter(pl.col("next_decision") == decision)["tone"].to_numpy()
        means = rng.choice(values, (BOOTSTRAP, len(values))).mean(axis=1)
        out.append({
            "decision": decision,
            "months": int(len(values)),
            "mean_tone": round(float(values.mean()), 4),
            "low": round(float(np.percentile(means, 2.5)), 4),
            "high": round(float(np.percentile(means, 97.5)), 4),
        })
    return out
