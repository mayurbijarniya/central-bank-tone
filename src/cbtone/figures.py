"""The report's figures."""

from __future__ import annotations

from datetime import date

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import polars as pl  # noqa: E402

from cbtone import paths, tables  # noqa: E402

BLUE, ORANGE, GREEN, GREY = "#2a78d6", "#eb6834", "#1baf7a", "#8a8a8a"
SHOWN = [("US", "Federal Reserve"), ("XM", "European Central Bank"),
         ("GB", "Bank of England"), ("IN", "Reserve Bank of India")]


def _style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#e6e6e6", linewidth=0.8)
    ax.set_axisbelow(True)


def _save(fig, name: str) -> None:
    paths.FIGURES.mkdir(parents=True, exist_ok=True)
    fig.savefig(paths.FIGURES / name, dpi=160, bbox_inches="tight",
                metadata={"Software": None, "CreationDate": None})
    plt.close(fig)


def global_tone(monthly: pl.DataFrame) -> None:
    frame = tables.global_tone(monthly).filter(pl.col("month") >= pl.date(1999, 1, 1))
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(frame["month"].to_list(), frame["tone"].to_list(), color=BLUE, linewidth=1.6)
    ax.axhline(0, color=GREY, linewidth=0.8, linestyle="--")
    for year, label in ((2008, "2008 crisis"), (2020, "Covid"), (2022, "2022 inflation")):
        ax.axvline(date(year, 1, 1), color="#cccccc", linewidth=0.8)
        ax.text(date(year, 2, 1), ax.get_ylim()[1], label, va="top", fontsize=8, color=GREY)
    ax.set_ylabel("Tone (hawkish +, dovish -)")
    ax.set_title("Average tone of central bank speeches, tested banks", loc="left")
    _style(ax)
    _save(fig, "global_tone.png")


def tone_and_rates(monthly: pl.DataFrame, rates: pl.DataFrame) -> None:
    fig, axes = plt.subplots(2, len(SHOWN), figsize=(12, 4.6), sharex=True,
                             gridspec_kw={"height_ratios": [1.2, 1]})
    for col, (area, name) in enumerate(SHOWN):
        tone = monthly.filter((pl.col("area") == area) & pl.col("tone").is_not_null()
                              & (pl.col("month") >= pl.date(1999, 1, 1)))
        rate = rates.filter((pl.col("area") == area) & (pl.col("month") >= pl.date(1999, 1, 1)))
        top, bottom = axes[0, col], axes[1, col]
        top.plot(tone["month"].to_list(), tone["tone"].to_list(), color=ORANGE, linewidth=1.1)
        top.axhline(0, color=GREY, linewidth=0.7, linestyle="--")
        top.set_title(name, loc="left", fontsize=10)
        bottom.step(rate["month"].to_list(), rate["rate"].to_list(), where="post",
                    color=GREEN, linewidth=1.3)
        _style(top)
        _style(bottom)
        bottom.xaxis.set_major_locator(mdates.YearLocator(8))
        bottom.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    axes[0, 0].set_ylabel("Speech tone")
    axes[1, 0].set_ylabel("Policy rate (%)")
    fig.suptitle("Speech tone and policy rates", x=0.01, ha="left", fontsize=12)
    _save(fig, "tone_and_rates.png")


def tone_before_decisions(rows: list[dict]) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.4))
    colors = {"cut": BLUE, "hold": GREY, "hike": ORANGE}
    for i, row in enumerate(rows):
        ax.errorbar(i, row["mean_tone"], yerr=[[row["mean_tone"] - row["low"]],
                                                [row["high"] - row["mean_tone"]]],
                    fmt="o", color=colors[row["decision"]], capsize=4, markersize=7)
        ax.annotate(f"{row['mean_tone']:+.3f}\n{row['months']:,} months", (i, row["high"]),
                    xytext=(0, 6), textcoords="offset points", ha="center", va="bottom",
                    fontsize=8)
    ax.axhline(0, color=GREY, linewidth=0.7, linestyle="--")
    ax.set_xticks(range(len(rows)), [f"before a {r['decision']}" for r in rows])
    ax.set_ylabel("Tone, 3 months to decision")
    ax.set_title("Tone in the months before each kind of decision", loc="left")
    ax.margins(y=0.35)
    _style(ax)
    _save(fig, "tone_before_decisions.png")


def placebo(result: dict) -> None:
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.hist(result["shuffled_gains"], bins=20, color="#c9d9f2", edgecolor="white",
            label="tone shuffled across months")
    ax.axvline(result["actual_gain"], color=ORANGE, linewidth=2, label="real tone")
    ax.set_xlabel("Improvement in test log loss from adding tone")
    ax.set_ylabel("Shuffles")
    ax.set_title(f"Placebo test, {result['runs']} shuffles (p = {result['p_value']:.2f})",
                 loc="left")
    ax.legend(frameon=False, fontsize=8)
    _style(ax)
    _save(fig, "placebo.png")


def render(output: dict) -> None:
    frames = output["_frames"]
    rates = pl.read_parquet(paths.MONTHLY_RATES)
    global_tone(frames["monthly"])
    tone_and_rates(frames["monthly"], rates)
    tone_before_decisions(output["tone_before_decisions"])
    placebo(output["placebo"])
