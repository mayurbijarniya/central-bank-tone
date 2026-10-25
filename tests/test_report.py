"""The findings and the README must quote results.json exactly."""

import json

import pytest

from cbtone import paths, report


@pytest.fixture(scope="module")
def results():
    if not paths.RESULTS.exists():
        pytest.skip("outputs/results.json not built; run `cbtone analyze`")
    return json.loads(paths.RESULTS.read_text())


def test_findings_render_without_gaps(results, tmp_path, monkeypatch):
    monkeypatch.setattr(report.paths, "FINDINGS", tmp_path / "FINDINGS.md")
    text = report.render(results)
    assert "{" not in text and "None" not in text and "nan" not in text


def test_committed_findings_are_current(results, tmp_path, monkeypatch):
    monkeypatch.setattr(report.paths, "FINDINGS", tmp_path / "FINDINGS.md")
    assert report.render(results) == paths.FINDINGS.read_text()


def test_readme_numbers_match_the_results(results):
    readme = (paths.ROOT / "README.md").read_text()
    data = results["data"]
    labeling = results["labeling"]
    policy = results["tone_and_policy"]
    before = {r["decision"]: r for r in results["tone_before_decisions"]}
    lead = results["leads_or_follows"]
    chosen = results["prediction"]["models"][results["prediction"]["chosen"]]

    assert f"{data['speeches']:,} speeches" in readme
    assert f"from {data['central_banks']} central" in readme
    assert f"**{report.pct(labeling['llm_fomc_test']['accuracy'])}**" in readme
    assert f"**{report.pct(labeling['scorer_fomc_test']['accuracy'])}**" in readme
    assert f"**{policy['banks_positive']} of {policy['banks_total']}**" in readme
    assert f"p = {policy['sign_test_p']:.4f}" in readme
    assert f"**{before['hike']['mean_tone']:+.3f}**" in readme
    assert f"**{before['cut']['mean_tone']:+.3f}**" in readme
    assert f"({lead['with_past_3m_change']:+.2f})" in readme
    assert f"({lead['with_inflation']:+.2f})" in readme
    assert f"({lead['with_next_3m_change']:+.2f})" in readme
    assert (f"log loss {chosen['baseline']['test']['log_loss']:.3f} to "
            f"{chosen['with_tone']['test']['log_loss']:.3f}") in readme
    assert f"p = {results['placebo']['p_value']:.2f}" in readme
    assert f"**{report.pct(labeling['crosscheck']['agreement'])}**" in readme


def test_scorer_uses_the_strength_cross_validation_chose(results):
    from cbtone import scorer

    assert results["scorer_selection"]["chosen"] == {"model": "embeddings", "c": scorer.C}
