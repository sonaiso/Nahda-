"""Tests for Graph Schema endpoints and core logic."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.graph.schema import export_schema
from app.graph.templates import (
    get_ops,
    get_root_classes,
    get_templates,
    get_templates_by_derivation,
    get_templates_by_form,
)
from app.main import create_app
from tests.auth_helpers import get_auth_headers


# ---------------------------------------------------------------------------
# Unit tests for schema module
# ---------------------------------------------------------------------------


def test_export_schema_structure() -> None:
    schema = export_schema()
    assert "labels" in schema
    assert "relationships" in schema
    assert "cypher_setup" in schema
    assert "minimal_kernel_relationships" in schema
    assert schema["label_count"] > 0
    assert schema["relationship_type_count"] > 0


def test_schema_labels_have_required_fields() -> None:
    schema = export_schema()
    for label in schema["labels"]:
        assert "label" in label
        assert "layer" in label
        assert "properties" in label
        assert isinstance(label["properties"], dict)


def test_schema_relationships_have_required_fields() -> None:
    schema = export_schema()
    for rel in schema["relationships"]:
        assert "type" in rel
        assert "from" in rel
        assert "to" in rel


def test_schema_contains_four_direction_relationships() -> None:
    schema = export_schema()
    rel_types = {r["type"] for r in schema["relationships"]}
    assert "NEXT" in rel_types
    assert "HAS_PART" in rel_types
    assert "PART_OF" in rel_types
    assert "CANDIDATE_OF" in rel_types
    assert "SUPPORTS" in rel_types


def test_schema_cypher_setup_is_valid_list() -> None:
    schema = export_schema()
    assert isinstance(schema["cypher_setup"], list)
    assert all(isinstance(stmt, str) for stmt in schema["cypher_setup"])
    assert any("CONSTRAINT" in stmt for stmt in schema["cypher_setup"])


# ---------------------------------------------------------------------------
# Unit tests for templates module
# ---------------------------------------------------------------------------


def test_templates_are_non_empty() -> None:
    templates = get_templates()
    assert len(templates) >= 30


def test_templates_have_required_fields() -> None:
    for tmpl in get_templates():
        assert "template_id" in tmpl
        assert "surface_pattern" in tmpl
        assert "slots" in tmpl
        assert "derivation_type" in tmpl
        assert "op_hooks" in tmpl
        assert isinstance(tmpl["op_hooks"], list)
        assert "constraints" in tmpl


def test_templates_by_form_verb_I() -> None:
    form_i = get_templates_by_form("I")
    assert len(form_i) >= 3
    for t in form_i:
        assert t["verb_form"] == "I"


def test_templates_by_form_verb_X() -> None:
    form_x = get_templates_by_form("X")
    assert len(form_x) >= 2
    assert any(t["template_id"] == "fx_masdar" for t in form_x)
    assert any(t["template_id"] == "fx_ism_fa3il" for t in form_x)


def test_templates_by_derivation_agent() -> None:
    agents = get_templates_by_derivation("Agent")
    assert len(agents) >= 3
    assert all(t["derivation_type"] == "Agent" for t in agents)


def test_templates_by_derivation_masdar() -> None:
    masdar = get_templates_by_derivation("Masdar")
    assert len(masdar) >= 8


def test_ops_are_non_empty() -> None:
    ops = get_ops()
    assert len(ops) >= 5
    for op in ops:
        assert "op_id" in op
        assert "op_type" in op
        assert "applies_to_classes" in op


def test_root_classes_are_non_empty() -> None:
    rcs = get_root_classes()
    assert len(rcs) >= 10
    class_names = [rc["class_name"] for rc in rcs]
    assert "sound" in class_names
    assert "doubled" in class_names
    assert "weak_a_w" in class_names


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


def test_graph_schema_endpoint() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.get("/graph/schema", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["version"] == "1.0"
        assert data["label_count"] > 0
        assert data["relationship_type_count"] > 0
        assert isinstance(data["labels"], list)
        assert isinstance(data["relationships"], list)
        assert isinstance(data["cypher_setup"], list)
        assert isinstance(data["minimal_kernel_relationships"], list)


def test_graph_schema_requires_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.get("/graph/schema")
        assert response.status_code == 401


def test_graph_templates_endpoint() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.get("/graph/templates", headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["template_count"] >= 30
        assert data["op_count"] >= 5
        assert data["root_class_count"] >= 10
        assert isinstance(data["templates"], list)
        assert isinstance(data["ops"], list)
        assert isinstance(data["root_classes"], list)


def test_graph_templates_have_form_x() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.get("/graph/templates", headers=headers)
        assert response.status_code == 200

        templates = response.json()["templates"]
        form_x_ids = {t["template_id"] for t in templates if t["verb_form"] == "X"}
        assert "fx_masdar" in form_x_ids
        assert "fx_ism_fa3il" in form_x_ids
        assert "fx_ism_maf3ul" in form_x_ids


def test_graph_analyze_endpoint_basic() -> None:
    payload = {"text": "المستخرجون"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "run_id" in data
        assert data["metrics"]["token_count"] == 1
        assert isinstance(data["tokens"], list)
        assert len(data["tokens"]) == 1

        tok = data["tokens"][0]
        assert tok["surface"] == "المستخرجون"
        assert len(tok["root_candidates"]) >= 1
        assert len(tok["pattern_candidates"]) >= 1
        assert len(tok["evidence"]) >= 1
        assert len(tok["seg_candidate"]["segments"]) >= 1


def test_graph_analyze_endpoint_multiple_tokens() -> None:
    payload = {"text": "كتب العلماء المقالات"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert data["metrics"]["token_count"] == 3
        assert len(data["tokens"]) == 3
        assert data["metrics"]["evidence_count"] >= 1
        assert data["metrics"]["root_candidate_count"] >= 3


def test_graph_analyze_candidates_have_scores() -> None:
    payload = {"text": "يستخرج"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json=payload, headers=headers)
        assert response.status_code == 200

        tok = response.json()["tokens"][0]
        for rc in tok["root_candidates"]:
            assert 0.0 <= rc["score"] <= 1.0
        for pc in tok["pattern_candidates"]:
            assert 0.0 <= pc["score"] <= 1.0
            assert "template_id" in pc
            assert "derivation_type" in pc


def test_graph_analyze_evidence_structure() -> None:
    payload = {"text": "الكاتبون"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json=payload, headers=headers)
        assert response.status_code == 200

        tok = response.json()["tokens"][0]
        assert len(tok["evidence"]) >= 2  # at least: prefix:ال + suffix:ون + root
        for ev in tok["evidence"]:
            assert ev["polarity"] in {"supports", "contradicts"}
            assert ev["weight"] > 0
            assert ev["feature"]


def test_graph_analyze_requires_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/graph/analyze", json={"text": "كتاب"})
        assert response.status_code == 401


def test_graph_analyze_rejects_blank_text() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json={"text": "   "}, headers=headers)
        assert response.status_code == 422


def test_graph_schema_has_eight_layers() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.get("/graph/schema", headers=headers)
        assert response.status_code == 200

        labels = response.json()["labels"]
        layers = {lbl["layer"] for lbl in labels}
        # Expect layers A-H + core
        for expected in [
            "A_text",
            "B_graphemic",
            "C_phonology",
            "D_morphemes",
            "E_morphology",
            "F_syntax",
            "G_semantics",
            "H_conceptual",
            "core",
        ]:
            assert expected in layers, f"Layer '{expected}' missing from schema"


def test_graph_analyze_triliteral_ratio() -> None:
    payload = {"text": "كتب وقرأ ودرس"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/graph/analyze", json=payload, headers=headers)
        assert response.status_code == 200

        metrics = response.json()["metrics"]
        assert 0.0 <= metrics["triliteral_ratio"] <= 1.0
