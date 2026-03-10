from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import create_app
from tests.auth_helpers import get_auth_headers


def test_health_endpoints() -> None:
    with TestClient(create_app()) as client:
        live_response = client.get("/health/live")
        assert live_response.status_code == 200
        assert live_response.json()["status"] == "ok"

        ready_response = client.get("/health/ready")
        assert ready_response.status_code == 200
        assert ready_response.json()["status"] == "ready"


def test_request_id_header_present() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.headers.get("X-Request-ID")
        assert response.headers.get("X-Trace-ID")


def test_metrics_endpoint_collects_requests() -> None:
    with TestClient(create_app()) as client:
        client.get("/health/live")
        metrics_response = client.get("/health/metrics")
        assert metrics_response.status_code == 200
        payload = metrics_response.json()
        assert "GET /health/live" in payload
        assert payload["GET /health/live"]["requests"] >= 1


def test_prometheus_metrics_endpoint() -> None:
    with TestClient(create_app()) as client:
        client.get("/health/live")
        response = client.get("/health/metrics/prometheus")
        assert response.status_code == 200
        assert "nahda_requests_total" in response.text
        assert "nahda_errors_total" in response.text


def test_auth_required_for_protected_route() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/analyze/unicode", json={"text": "كتاب"})
        assert response.status_code == 401


def test_unicode_endpoint() -> None:
    payload = {"text": "إِنَّ الكِتَاب"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/analyze/unicode", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "run_id" in data
        assert data["normalized_text"]
        assert "metrics" in data
        assert data["metrics"]["normalization_ratio"] >= 0


def test_morphology_endpoint() -> None:
    payload = {"text": "مكتوبات وكتاب"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/analyze/morphology", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["token_count"] == 2
        assert isinstance(data["patterns"], list)
        assert all("root" in item for item in data["patterns"])


def test_semantics_endpoint() -> None:
    payload = {"text": "الكتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/analyze/semantics", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["lexeme_count"] == 3
        assert isinstance(data["lexemes"], list)
        assert isinstance(data["indications"], list)
        assert all("token" in item for item in data["meaning_registry"])


def test_infer_endpoint() -> None:
    payload = {"text": "إن الكتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/infer", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["inference_count"] >= 1
        assert isinstance(data["inference"], list)
        assert "mafhum" in data["inference"][0]


def test_rule_evaluate_endpoint() -> None:
    payload = {"text": "لا كتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/rule/evaluate", json=payload, headers=headers)
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
        headers = get_auth_headers(client)
        response = client.post("/manat/apply", json=payload, headers=headers)
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
        headers = get_auth_headers(client)
        response = client.post("/manat/apply", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["suspend_count"] >= 1
        assert isinstance(data["tanzil_decisions"], list)


def test_explain_and_trace_endpoints() -> None:
    payload = {
        "text": "لا كتاب في البيت",
        "external_case_id": "case-003",
        "description": "trace check",
        "case_features": [
            {
                "feature_key": "كتاب",
                "feature_value": "present",
                "verification_state": "verified",
            }
        ],
    }
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        apply_response = client.post("/manat/apply", json=payload, headers=headers)
        assert apply_response.status_code == 200
        run_id = apply_response.json()["run_id"]

        explain_response = client.get(f"/explain/{run_id}", headers=headers)
        assert explain_response.status_code == 200
        explain_data = explain_response.json()
        assert explain_data["run_id"] == run_id
        assert "summary" in explain_data
        assert explain_data["summary"]["rules"] >= 1

        trace_response = client.get(f"/trace/{run_id}", headers=headers)
        assert trace_response.status_code == 200
        trace_data = trace_response.json()
        assert trace_data["run_id"] == run_id
        assert isinstance(trace_data["events"], list)
        assert len(trace_data["events"]) >= 1


def test_rate_limit_on_protected_routes() -> None:
    original_limit = settings.rate_limit_requests_per_window
    original_window = settings.rate_limit_window_seconds

    settings.rate_limit_requests_per_window = 3
    settings.rate_limit_window_seconds = 60
    try:
        with TestClient(create_app()) as client:
            headers = get_auth_headers(client)
            first = client.post("/analyze/unicode", json={"text": "كتاب"}, headers=headers)
            second = client.post("/analyze/morphology", json={"text": "كتاب"}, headers=headers)
            third = client.post("/analyze/semantics", json={"text": "كتاب"}, headers=headers)
            assert first.status_code == 200
            assert second.status_code == 200
            assert third.status_code == 429
    finally:
        settings.rate_limit_requests_per_window = original_limit
        settings.rate_limit_window_seconds = original_window
