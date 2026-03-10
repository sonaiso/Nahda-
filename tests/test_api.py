from fastapi.testclient import TestClient

from app.main import create_app

def test_unicode_endpoint() -> None:
    payload = {"text": "إِنَّ الكِتَاب"}
    with TestClient(create_app()) as client:
        response = client.post("/analyze/unicode", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "run_id" in data
        assert data["normalized_text"]
        assert "metrics" in data
        assert data["metrics"]["normalization_ratio"] >= 0


def test_morphology_endpoint() -> None:
    payload = {"text": "مكتوبات وكتاب"}
    with TestClient(create_app()) as client:
        response = client.post("/analyze/morphology", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["token_count"] == 2
        assert isinstance(data["patterns"], list)
        assert all("root" in item for item in data["patterns"])


def test_semantics_endpoint() -> None:
    payload = {"text": "الكتاب في البيت"}
    with TestClient(create_app()) as client:
        response = client.post("/analyze/semantics", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["lexeme_count"] == 3
        assert isinstance(data["lexemes"], list)
        assert isinstance(data["indications"], list)
        assert all("token" in item for item in data["meaning_registry"])


def test_infer_endpoint() -> None:
    payload = {"text": "إن الكتاب في البيت"}
    with TestClient(create_app()) as client:
        response = client.post("/infer", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["inference_count"] >= 1
        assert isinstance(data["inference"], list)
        assert "mafhum" in data["inference"][0]


def test_rule_evaluate_endpoint() -> None:
    payload = {"text": "لا كتاب في البيت"}
    with TestClient(create_app()) as client:
        response = client.post("/rule/evaluate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["rule_count"] >= 1
        assert isinstance(data["rules"], list)
        assert isinstance(data["tarjih_decisions"], list)


def test_manat_apply_endpoint_true_or_false() -> None:
    payload = {
        "text": "لا كتاب في البيت",
        "external_case_id": "case-001",
        "description": "book is present",
        "case_features": [
            {
                "feature_key": "كتاب",
                "feature_value": "present",
                "verification_state": "verified",
            }
        ],
    }
    with TestClient(create_app()) as client:
        response = client.post("/manat/apply", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["rule_evaluated_count"] >= 1
        assert isinstance(data["manat"], list)
        assert data["manat"][0]["applies_state"] in {"true", "false", "suspend"}


def test_manat_apply_endpoint_suspend_on_missing_feature() -> None:
    payload = {
        "text": "لا كتاب في البيت",
        "external_case_id": "case-002",
        "description": "missing feature input",
        "case_features": [],
    }
    with TestClient(create_app()) as client:
        response = client.post("/manat/apply", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["suspend_count"] >= 1
        assert isinstance(data["tanzil_decisions"], list)
