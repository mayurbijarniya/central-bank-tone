import numpy as np
from sklearn.linear_model import LogisticRegression

from cbtone import scorer


def fitted():
    rng = np.random.default_rng(0)
    vectors = rng.normal(size=(300, 8))
    index = (vectors[:, 0] > 0.5).astype(int) + (vectors[:, 0] > -0.5).astype(int)
    labels = np.array(scorer.CLASSES)[index]
    return LogisticRegression(max_iter=1000).fit(vectors, labels), vectors


def test_saved_scorer_gives_the_same_probabilities(tmp_path, monkeypatch):
    model, vectors = fitted()
    target = tmp_path / "scorer.json"
    scorer.save(model, target)
    loaded = scorer.load(target)
    assert list(loaded.classes_) == list(model.classes_)
    np.testing.assert_allclose(loaded.predict_proba(vectors), model.predict_proba(vectors),
                               atol=1e-6)
    assert (loaded.predict(vectors) == model.predict(vectors)).all()


def test_tone_is_hawkish_minus_dovish():
    probabilities = np.array([[0.1, 0.7, 0.2], [0.6, 0.1, 0.3]])
    np.testing.assert_allclose(
        scorer.tone(probabilities, ["dovish", "hawkish", "neutral"]), [0.6, -0.5]
    )


def test_evaluate_counts_and_scores():
    result = scorer.evaluate(["hawkish", "dovish", "neutral"], ["hawkish", "neutral", "neutral"])
    assert result["n"] == 3
    assert result["accuracy"] == round(2 / 3, 4)
