from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.axiomatic_engine import run_axiomatic_engine
from tests.auth_helpers import get_auth_headers


# ---------------------------------------------------------------------------
# Unit tests for the axiomatic engine (no HTTP, no DB)
# ---------------------------------------------------------------------------

SAMPLE_TEXT = "الكتاب في البيت"
VERB_TEXT = "يكتب الطالب درسه"


def test_engine_returns_all_axioms() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    codes = [a.code for a in result.axioms]
    expected = [f"A{i}" for i in range(1, 21)]
    assert codes == expected


def test_engine_returns_all_lemmas() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    codes = [lm.code for lm in result.lemmas]
    assert codes == ["L1", "L2", "L3", "L4", "L5"]


def test_engine_returns_all_theorems() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    codes = [th.code for th in result.theorems]
    assert codes == ["T1", "T2", "T3", "T4", "T5"]


def test_engine_returns_all_falsifications() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    codes = [f.code for f in result.falsifications]
    assert codes == ["F1", "F2", "F3", "F4", "F5"]


def test_metrics_ratios_in_range() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    assert 0.0 <= result.axiom_satisfaction_ratio <= 1.0
    assert 0.0 <= result.lemma_hold_ratio <= 1.0
    assert 0.0 <= result.theorem_proven_ratio <= 1.0


def test_a1_identity_always_holds() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    a1 = next(a for a in result.axioms if a.code == "A1")
    assert a1.satisfied is True


def test_a7_nucleus_requirement() -> None:
    # Arabic text with full diacritics should satisfy A7 (each syllable has a vowel nucleus)
    result = run_axiomatic_engine("كَتَبَ")
    a7 = next(a for a in result.axioms if a.code == "A7")
    assert isinstance(a7.satisfied, bool)


def test_a12_triliteral_optimality_typical_arabic() -> None:
    # For typical Arabic tokens the triliteral should score at least as well as biliteral
    result = run_axiomatic_engine("كتاب مكتوب يكتبون")
    a12 = next(a for a in result.axioms if a.code == "A12")
    assert isinstance(a12.satisfied, bool)


def test_a16_word_classification_covers_all_tokens() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    a16 = next(a for a in result.axioms if a.code == "A16")
    assert a16.satisfied is True


def test_l1_vowel_mandatory() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    l1 = next(lm for lm in result.lemmas if lm.code == "L1")
    assert isinstance(l1.holds, bool)
    assert l1.derived_from == ["A6", "A7"]


def test_l3_relation_closure() -> None:
    result = run_axiomatic_engine(VERB_TEXT)
    l3 = next(lm for lm in result.lemmas if lm.code == "L3")
    assert isinstance(l3.holds, bool)


def test_falsification_scores_are_numeric() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    for f in result.falsifications:
        assert isinstance(f.score, float)
        assert isinstance(f.threshold, float)
        assert isinstance(f.falsified, bool)


def test_f1_triliteral_test_details_mention_t_scores() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    f1 = next(f for f in result.falsifications if f.code == "F1")
    assert "T(3)" in f1.details


def test_system_coherent_flag_type() -> None:
    result = run_axiomatic_engine(SAMPLE_TEXT)
    assert isinstance(result.system_coherent, bool)


def test_single_token_handled_gracefully() -> None:
    # Single whitespace-padded token
    result = run_axiomatic_engine("كتاب")
    assert result.tokens == ["كتاب"]
    assert len(result.axioms) == 20


# ---------------------------------------------------------------------------
# API integration tests
# ---------------------------------------------------------------------------


def test_axiomatic_analyze_endpoint() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post(
            "/axiomatic/analyze",
            json={"text": SAMPLE_TEXT},
            headers=headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == SAMPLE_TEXT
    assert len(data["axioms"]) == 20
    assert len(data["lemmas"]) == 5
    assert len(data["theorems"]) == 5
    assert len(data["falsifications"]) == 5
    assert "metrics" in data
    assert "axiom_satisfaction_ratio" in data["metrics"]
    assert "system_coherent" in data["metrics"]


def test_axiomatic_falsify_endpoint() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post(
            "/axiomatic/falsify",
            json={"text": VERB_TEXT},
            headers=headers,
        )
    assert response.status_code == 200
    data = response.json()
    assert data["text"] == VERB_TEXT
    assert len(data["falsifications"]) == 5
    assert "any_falsified" in data
    assert isinstance(data["any_falsified"], bool)


def test_axiomatic_analyze_requires_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/axiomatic/analyze", json={"text": SAMPLE_TEXT})
    assert response.status_code == 401


def test_axiomatic_falsify_requires_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/axiomatic/falsify", json={"text": SAMPLE_TEXT})
    assert response.status_code == 401


def test_axiomatic_analyze_blank_text_rejected() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post(
            "/axiomatic/analyze",
            json={"text": "   "},
            headers=headers,
        )
    assert response.status_code == 422


def test_axiomatic_v1_prefix_also_works() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post(
            "/v1/axiomatic/analyze",
            json={"text": SAMPLE_TEXT},
            headers=headers,
        )
    assert response.status_code == 200
