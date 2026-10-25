"""cbtone: download, ingest, label, score, analyze, update.

cbtone download   fetch the BIS speeches, policy rates and prices
cbtone ingest     tidy speeches, sentences, rates and inflation into Parquet
cbtone label      label a sample of sentences with a language model (needs .env; costs money)
cbtone score      score every policy sentence with the local model (hours the first time)
cbtone analyze    answer Q1-Q3, write results, figures, findings and the website's data
cbtone update     add new speeches from the archive and live feeds
cbtone all        ingest, score and analyze, in order
"""

from __future__ import annotations

import argparse

from cbtone import paths

STEPS = ["download", "ingest", "label", "score", "analyze", "update", "all"]


def download() -> None:
    from cbtone import download as fetch

    files = fetch.run()
    print(f"{len(files)} files in {paths.RAW}")


def ingest() -> None:
    from cbtone import ingest as tidy

    print(tidy.run())


def label() -> None:
    import polars as pl

    from cbtone import labels

    pool = labels.policy_pool()
    exclude = pl.read_csv(labels.CROSSCHECK, schema_overrides={"speech_id": pl.Utf8})
    usage = labels.label_sample(labels.sample(pool, exclude=exclude))
    labels.label_crosscheck()
    print(f"{usage.calls} calls, {usage.prompt_tokens:,} prompt and "
          f"{usage.completion_tokens:,} completion tokens")
    print("label the cross-check with a second model: "
          "labels.label_crosscheck('<another model id>')")


def score() -> None:
    import polars as pl

    from cbtone import feeds, tone

    archive_end = pl.read_parquet(paths.SPEECHES)["date"].max()
    feeds.fetch(after=archive_end)
    print(tone.run())


def analyze() -> None:
    from cbtone import figures, report, run

    output = run.analyze()
    saved = run.write(output)
    figures.render(output)
    report.render(saved)
    print(f"wrote {paths.RESULTS}, {paths.TABLES}/, {paths.WEB_DATA}/, {paths.FINDINGS}")


def update() -> None:
    from cbtone import update as refresh

    print(refresh.run_update())


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="cbtone", description=__doc__.splitlines()[0])
    parser.add_argument("step", choices=STEPS)
    args = parser.parse_args(argv)
    actions = {
        "download": download, "ingest": ingest, "label": label, "score": score,
        "analyze": analyze, "update": update,
    }
    for step in ["ingest", "score", "analyze"] if args.step == "all" else [args.step]:
        actions[step]()


if __name__ == "__main__":
    main()
