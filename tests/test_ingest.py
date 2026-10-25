import zipfile
from datetime import date

import polars as pl

from cbtone import ingest, sentences

RATES_HEADER = (
    '"STRUCTURE","STRUCTURE_ID","ACTION","FREQ:Frequency","REF_AREA:Reference area",'
    '"TIME_PERIOD:Time period or range","OBS_VALUE:Observation Value"\n'
)


def test_clean_drops_layout_lines_and_links():
    text = (
        "## Introduction\n\nInflation has fallen.\n\n*      *      *\n\n"
        "BIS central bankers' speeches\n\n12\n\nSee the [report](/r.pdf) for detail."
    )
    assert ingest.clean(text) == "Inflation has fallen.\n\nSee the report for detail."


def test_sentences_keep_abbreviations_together():
    text = "Mr. Powell said U.S. inflation is still too high for comfort today. Rates will stay "\
           "where they are for some time to come."
    assert ingest.sentences(text) == [
        "Mr. Powell said U.S. inflation is still too high for comfort today.",
        "Rates will stay where they are for some time to come.",
    ]


def test_sentences_drop_fragments():
    assert ingest.sentences("Thank you.\n\nQuestions welcome.") == []


def test_english_share_separates_languages():
    english = "The rate of inflation is high and it is rising in the euro area."
    assert ingest.english_share(english) > 0.3
    assert ingest.english_share("La politique monétaire de la banque reste prudente.") < 0.15


def test_nan_text_is_not_a_rate(tmp_path):
    rows = [
        '"dataflow","BIS","I","D: Daily","NO: Norway","2024-01-01","NaN"',
        '"dataflow","BIS","I","D: Daily","NO: Norway","2024-01-02","4.5"',
        '"dataflow","BIS","I","M: Monthly","NO: Norway","2024-01","4.5"',
    ]
    archive = tmp_path / "rates.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("rates.csv", RATES_HEADER + "\n".join(rows) + "\n")
    frame = ingest.read_rates(archive)
    assert frame.to_dicts() == [{"area": "NO", "date": date(2024, 1, 2), "rate": 4.5}]


def test_policy_filter():
    assert sentences.is_policy("Inflation remains above our 2 percent objective.")
    assert sentences.is_policy("The labour market has tightened further.")
    assert not sentences.is_policy("We celebrate the bank's 75th anniversary today.")
    frame = pl.DataFrame({"sentence": ["Interest rates rose.", "A new banknote was issued."]})
    assert sentences.policy_sentences(frame)["sentence"].to_list() == ["Interest rates rose."]
