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
