import pytest

from cbtone import llm


def test_parse_reads_one_label_per_sentence():
    reply = 'Here you go:\n```json\n{"labels": ["Hawkish", "neutral", "dovish"]}\n```'
    assert llm.parse(reply, 3) == ["hawkish", "neutral", "dovish"]


@pytest.mark.parametrize(
    "reply",
    ['{"labels": ["hawkish"]}', '{"labels": ["hawkish", "bullish"]}', "no json here", "{bad"],
)
def test_parse_rejects_replies_that_do_not_fit(reply):
    assert llm.parse(reply, 2) is None


def test_prompt_numbers_the_sentences():
    assert llm.prompt(["A.", "B."]).endswith("1. A.\n2. B.")


def test_settings_come_from_env_file_or_environment(tmp_path, monkeypatch):
    monkeypatch.setattr(llm.paths, "ROOT", tmp_path)
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    (tmp_path / ".env").write_text(
        "# comment\nLLM_BASE_URL=https://example.test/v1\nLLM_API_KEY='k'\nLLM_MODEL=m\n"
    )
    assert llm.settings() == {
        "LLM_BASE_URL": "https://example.test/v1", "LLM_API_KEY": "k", "LLM_MODEL": "m"
    }
    monkeypatch.setenv("LLM_MODEL", "other")
    assert llm.settings()["LLM_MODEL"] == "other"


def test_settings_say_what_is_missing(tmp_path, monkeypatch):
    monkeypatch.setattr(llm.paths, "ROOT", tmp_path)
    for key in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="LLM_API_KEY"):
        llm.settings()
