"""Render reports/FINDINGS.md from the saved results, so no number is typed by hand."""

from __future__ import annotations

from cbtone import banks, paths

NAMES = {**banks.NAMES, "XM": "euro area (ECB)"}


def pct(value: float, digits: int = 1) -> str:
    return f"{value * 100:.{digits}f}%"


def labeling_section(r: dict) -> str:
    llm, local = r["llm_fomc_test"], r["scorer_fomc_test"]
    lines = [
        "## Q1. How well can a cheap model read central bank tone?",
        "",
        "Measured against people: the 496 human-labeled Federal Reserve sentences of the "
        "Trillion Dollar Words test file, which no model or prompt was tuned on.",
        "",
        "| Labeler | Accuracy | Macro F1 | Weighted F1 |",
        "|---|---|---|---|",
        f"| Language model (DeepSeek V4.1 Flash), zero-shot | {pct(llm['accuracy'])} | "
        f"{llm['macro_f1']:.2f} | {llm['weighted_f1']:.2f} |",
        f"| Local scorer (bge-small embeddings + logistic regression) | "
        f"{pct(local['accuracy'])} | {local['macro_f1']:.2f} | {local['weighted_f1']:.2f} |",
        "",
        "For scale, a published benchmark on the same task reports an F1 score of 0.58 for "
        "zero-shot ChatGPT-3.5 and 0.70 for a fine-tuned RoBERTa-large. The language model "
        "sits between the two; the local scorer, which runs free on a laptop CPU, gives up "
        f"{(llm['accuracy'] - local['accuracy']) * 100:.1f} points of accuracy to it.",
    ]
    check = r["crosscheck"]
    first, second = (m.split("/")[-1] for m in check["models"])
    lines += [
        "",
        f"**Outside the Fed.** No people labeled sentences from other banks, so two language "
        f"models from different families labeled the same {check['sentences']} sentences from "
        f"{check['banks']} other central banks: {first} and {second} agreed "
        f"{pct(check['agreement'])} of the time (Cohen's kappa {check['kappa']:.2f}). On the "
        f"{check['consensus_sentences']} sentences where they agreed, the local scorer matched "
        f"their label {pct(check['scorer_on_consensus'])} of the time. This measures agreement, "
        "not accuracy.",
    ]
    return "\n".join(lines)


def policy_section(r: dict, before: list[dict], lead: dict) -> str:
    by = {row["decision"]: row for row in before}
    top = ", ".join(f"{NAMES.get(b['area'], b['area'])} {b['rho']:+.2f}" for b in r["banks"][:3])
    flat = [b for b in r["banks"] if abs(b["rho"]) < 0.05]
    negative = [b for b in r["banks"] if b["rho"] <= -0.05]
    lines = [
        "## Q2. Tone moves with policy",
        "",
        f"A bank's tone over three months, against the change in its policy rate over the next "
        f"three, across {r['months']:,} bank-months: rank correlation "
        f"**{r['pooled_rho']:+.2f}**. The relationship is positive at "
        f"**{r['banks_positive']} of {r['banks_total']}** banks "
        f"(sign test p = {r['sign_test_p']:.4f}); strongest at {top}.",
    ]

    def named(group: list[dict]) -> str:
        return ", ".join(f"{NAMES.get(b['area'], b['area'])} ({b['rho']:+.2f})" for b in group)

    if flat:
        lines.append(f"It is about zero at {named(flat)}.")
    if negative:
        lines.append(f"It is negative at {named(negative)}.")
    lines += [
        "",
        "| Next decision | Bank-months | Mean tone | 95% interval |",
        "|---|---|---|---|",
        *[
            f"| {d} | {by[d]['months']:,} | {by[d]['mean_tone']:+.3f} | "
            f"{by[d]['low']:+.3f} to {by[d]['high']:+.3f} |"
            for d in ("cut", "hold", "hike")
        ],
        "",
        "**But tone mostly echoes the cycle.** Its correlation with the rate change of the "
        f"*past* three months ({lead['with_past_3m_change']:+.2f}) and with inflation "
        f"({lead['with_inflation']:+.2f}) is as strong as with the *coming* change "
        f"({lead['with_next_3m_change']:+.2f}). Once the past change is accounted for, what is "
        f"left for the coming one is {lead['next_given_past']:+.2f}.",
        "",
        "![Tone before decisions](../outputs/figures/tone_before_decisions.png)",
        "",
        "![Tone and rates](../outputs/figures/tone_and_rates.png)",
    ]
    return "\n".join(lines)


def prediction_section(p: dict, placebo: dict) -> str:
    chosen = p["chosen"]
    rows = []
    for name, model in p["models"].items():
        for features, key in (("past rates and inflation", "baseline"),
                              ("plus speech tone", "with_tone")):
            test = model[key]["test"]
            mark = " (chosen)" if name == chosen else ""
            rows.append(
                f"| {name.replace('_', ' ')}{mark} | {features} | {test['log_loss']:.3f} | "
                f"{test['macro_f1']:.2f} | {pct(test['move_accuracy'])} |"
            )
    chosen_model = p["models"][chosen]
    tone_loss = chosen_model["with_tone"]["test"]["log_loss"]
    helped = tone_loss < chosen_model["baseline"]["test"]["log_loss"]
    verdict = (
        "Adding tone improved the chosen model" if helped
        else "Adding tone made the chosen model slightly worse"
    )
    significant = placebo["p_value"] < 0.05
    return "\n".join([
        "## Q3. Tone does not predict the next decision beyond rates and inflation"
        if not significant else "## Q3. Tone adds information about the next decision",
        "",
        f"For each bank and month, next month's decision (hike, hold, cut). Trained on "
        f"1999-2016 ({p['rows']['train']:,} bank-months), model chosen on 2017-2019 "
        f"({p['rows']['validation']:,}), tested once on 2020 onward ({p['rows']['test']:,}, of "
        f"which {chosen_model['baseline']['test']['moves']} were moves). The model was chosen "
        "by validation log loss before the test results were read.",
        "",
        "| Model | Features | Test log loss | Macro F1 | Moves called right |",
        "|---|---|---|---|---|",
        *rows,
        "",
        f"{verdict} (test log loss "
        f"{chosen_model['baseline']['test']['log_loss']:.3f} to "
        f"{chosen_model['with_tone']['test']['log_loss']:.3f}). The placebo test shuffles each "
        f"bank's tone across months {placebo['runs']} times: shuffled tone did at least as well "
        f"as real tone in a share of runs that gives **p = {placebo['p_value']:.2f}**. "
        + ("Real tone carries information that shuffled tone does not."
           if significant else
           "Real tone is no more useful than tone with its timing destroyed."),
        "",
        "This fits Q2. Tone tracks the policy cycle, but so do a bank's own recent moves and "
        "the latest inflation figure, which the baseline already has. What speeches say about "
        "the coming months is, on this evidence, mostly already in those numbers.",
        "",
        "![Placebo test](../outputs/figures/placebo.png)",
    ])


def render(results: dict) -> str:
    d = results["data"]
    text = "\n".join([
        "# Findings",
        "",
        "Generated from `outputs/results.json` by `cbtone analyze`. Do not edit by hand: "
        "re-run the pipeline instead.",
        "",
        f"**Data:** {d['speeches']:,} English speeches by central bankers from "
        f"{d['central_banks']} central banks, {d['first_speech']} to {d['last_speech']}: "
        f"{d['archive_speeches']:,} from the BIS archive (to {d['archive_last_speech']}) and "
        f"{d['feed_speeches']} from five banks' live feeds since. "
        f"{d['policy_sentences']:,} sentences about policy, prices, rates or the economy were "
        f"scored. Rate decisions are tested for {d['tested_banks']} central banks.",
        "",
        "![Average tone](../outputs/figures/global_tone.png)",
        "",
        labeling_section(results["labeling"]),
        "",
        policy_section(results["tone_and_policy"], results["tone_before_decisions"],
                       results["leads_or_follows"]),
        "",
        prediction_section(results["prediction"], results["placebo"]),
        "",
        "## Limits",
        "",
        "- **A model reads the tone, not people.** Its accuracy is measured above; single "
        "sentences are often misread, and the monthly averages smooth that out.",
        "- **The answer key is the Fed's.** Other banks phrase policy differently; outside the "
        "Fed there is only agreement between models, on 150 sentences.",
        "- **Every speaker counts the same.** A deputy governor's speech weighs as much as the "
        "governor's; the archive does not say who votes.",
        "- **Not causal.** Speeches and decisions both respond to the economy.",
        "- **Monthly decisions.** Two moves in one month count as one; an emergency cut and a "
        "scheduled one look alike.",
        "",
        "## Sources",
        "",
        "- [BIS central bankers' speeches](https://www.bis.org/cbspeeches/download.htm) "
        "(non-commercial use)",
        "- [BIS central bank policy rates](https://www.bis.org/statistics/dataportal/cbpol.htm)",
        "- [BIS consumer prices](https://data.bis.org/static/bulk/WS_LONG_CPI_csv_flat.zip)",
        "- Shah, Paturi and Chava (2023), "
        "[Trillion Dollar Words](https://arxiv.org/abs/2305.07972), "
        "human-labeled FOMC sentences (CC BY-NC 4.0)",
        "- Shah and Chava (2023), [Zero is Not Hero Yet](https://arxiv.org/abs/2305.16633), the "
        "benchmark figures quoted in Q1",
        "- Feeds: [Federal Reserve](https://www.federalreserve.gov/feeds/speeches.xml), "
        "[ECB](https://www.ecb.europa.eu/rss/press.html), "
        "[Bank of England](https://www.bankofengland.co.uk/rss/speeches), "
        "[Bank of Canada](https://www.bankofcanada.ca/content_type/speeches/feed/), "
        "[Reserve Bank of Australia](https://www.rba.gov.au/rss/rss-cb-speeches.xml)",
        "",
    ])
    paths.FINDINGS.parent.mkdir(parents=True, exist_ok=True)
    paths.FINDINGS.write_text(text)
    return text
