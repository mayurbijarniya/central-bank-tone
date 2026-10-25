import numpy as np
import pytest
from fastapi.testclient import TestClient

from cbtone import api, scorer


class FakeScorer:
    classes_ = np.array(["dovish", "hawkish", "neutral"])

    def predict_proba(self, vectors):
        return np.tile([0.1, 0.8, 0.1], (len(vectors), 1))


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(api, "model", lambda: FakeScorer())
    monkeypatch.setattr(scorer, "embed", lambda texts: np.zeros((len(list(texts)), 4)))
    return TestClient(api.app)


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_score_returns_each_policy_sentence(client):
    text = ("Inflation remains well above our target and rates may need to rise further. "
            "We are proud to open our new visitor centre in the capital this spring.")
    body = client.post("/score", json={"text": text}).json()
    assert body["policy_sentences"] == 1
    assert body["sentences"][0]["label"] == "hawkish"
    assert body["tone"] == pytest.approx(0.7)


def test_text_without_policy_has_no_tone(client):
    body = client.post("/score", json={"text": "We welcome everyone to the annual dinner tonight."})
    assert body.json() == {"tone": None, "policy_sentences": 0, "sentences": []}


def test_empty_text_is_rejected(client):
    assert client.post("/score", json={"text": ""}).status_code == 422
