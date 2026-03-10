from fastapi.testclient import TestClient

from app.main import create_app


def test_e2e_full_flow_default_routes() -> None:
    text = "لا كتاب في البيت"
    with TestClient(create_app()) as client:
        unicode_res = client.post("/analyze/unicode", json={"text": text})
        assert unicode_res.status_code == 200
        unicode_data = unicode_res.json()
        assert unicode_data["normalized_text"]

        morphology_res = client.post("/analyze/morphology", json={"text": text})
        assert morphology_res.status_code == 200
        morphology_data = morphology_res.json()
        assert morphology_data["metrics"]["token_count"] >= 1

        semantics_res = client.post("/analyze/semantics", json={"text": text})
        assert semantics_res.status_code == 200
        semantics_data = semantics_res.json()
        assert semantics_data["metrics"]["lexeme_count"] >= 1

        infer_res = client.post("/infer", json={"text": text})
        assert infer_res.status_code == 200
        infer_data = infer_res.json()
        assert infer_data["metrics"]["inference_count"] >= 1

        rule_res = client.post("/rule/evaluate", json={"text": text})
        assert rule_res.status_code == 200
        rule_data = rule_res.json()
        assert rule_data["metrics"]["rule_count"] >= 1

        manat_res = client.post(
            "/manat/apply",
            json={
                "text": text,
                "external_case_id": "e2e-case-001",
                "description": "end-to-end test case",
                "case_features": [
                    {
                        "feature_key": "كتاب",
                        "feature_value": "present",
                        "verification_state": "verified",
                    }
                ],
            },
        )
        assert manat_res.status_code == 200
        manat_data = manat_res.json()
        run_id = manat_data["run_id"]
        assert manat_data["metrics"]["rule_evaluated_count"] >= 1

        explain_res = client.get(f"/explain/{run_id}")
        assert explain_res.status_code == 200
        explain_data = explain_res.json()
        assert explain_data["summary"]["manat"] >= 1

        trace_res = client.get(f"/trace/{run_id}")
        assert trace_res.status_code == 200
        trace_data = trace_res.json()
        assert len(trace_data["events"]) >= 1


def test_e2e_v1_routes() -> None:
    text = "إن الكتاب في البيت"
    with TestClient(create_app()) as client:
        assert client.post("/v1/analyze/unicode", json={"text": text}).status_code == 200
        assert client.post("/v1/analyze/morphology", json={"text": text}).status_code == 200
        assert client.post("/v1/analyze/semantics", json={"text": text}).status_code == 200
        assert client.post("/v1/infer", json={"text": text}).status_code == 200
        assert client.post("/v1/rule/evaluate", json={"text": text}).status_code == 200

        manat_res = client.post(
            "/v1/manat/apply",
            json={
                "text": text,
                "external_case_id": "e2e-case-002",
                "description": "versioned routes test",
                "case_features": [],
            },
        )
        assert manat_res.status_code == 200
        run_id = manat_res.json()["run_id"]

        assert client.get(f"/v1/explain/{run_id}").status_code == 200
        assert client.get(f"/v1/trace/{run_id}").status_code == 200
