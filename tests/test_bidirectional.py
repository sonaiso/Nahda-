"""Tests for the bidirectional Arabic language engine.

Covers:
  - POST /bidirectional/analyze  (forward: text → meaning)
  - POST /bidirectional/generate (backward: meaning → text)
  - Gate algebra unit tests
  - Engine service unit tests
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.bidirectional_engine import (
    ProofTrace,
    UnicodeAtom,
    FunctionalUnit,
    RootKernel,
    PatternTemplate,
    IntraLexemeStructure,
    ConstructionNetwork,
    MeaningStructure,
    Entity,
    EventNode,
    _identity_gate,
    _non_contradiction_gate,
    _license_gate,
    _template_fill_gate,
    _well_formedness_gate,
    _predication_gate,
    _meaning_consistency_gate,
    _build_unicode_atoms,
    _build_functional_units,
    run_generate_backward,
)
from tests.auth_helpers import get_auth_headers


# ─────────────────────────────────────────────────────────────────────────────
# Gate algebra unit tests
# ─────────────────────────────────────────────────────────────────────────────


def test_identity_gate_passes_on_valid_object():
    trace = ProofTrace()
    assert _identity_gate("hello", trace) is True
    assert "IdentityGate: ok" in trace.steps
    assert trace.score == 1.0


def test_identity_gate_fails_on_none():
    trace = ProofTrace()
    assert _identity_gate(None, trace) is False
    assert trace.score < 1.0
    assert any("null" in c for c in trace.contradictions)


def test_non_contradiction_gate_passes_no_conflict():
    trace = ProofTrace()
    assert _non_contradiction_gate(["RADICAL", "INFLECTIONAL"], trace) is True
    assert trace.score == 1.0


def test_non_contradiction_gate_fails_on_conflict():
    trace = ProofTrace()
    assert _non_contradiction_gate(["RADICAL", "VOCALIC"], trace) is False
    assert trace.score < 1.0
    assert trace.contradictions


def test_license_gate_passes_letter_with_role():
    trace = ProofTrace()
    atom = UnicodeAtom(id=0, codepoint=0x0643, category="Lo", combining_class=0)
    unit = FunctionalUnit(id=0, atoms=[atom], unit_type="LETTER", role_set=["RADICAL"], position=0)
    assert _license_gate(unit, trace) is True


def test_license_gate_fails_letter_without_role():
    trace = ProofTrace()
    atom = UnicodeAtom(id=0, codepoint=0x0643, category="Lo", combining_class=0)
    unit = FunctionalUnit(id=0, atoms=[atom], unit_type="LETTER", role_set=[], position=0)
    assert _license_gate(unit, trace) is False


def test_template_fill_gate_passes_sufficient_radicals():
    trace = ProofTrace()
    root = RootKernel(id=0, radicals=["ك", "ت", "ب"], semantic_field="general", concept_core="ك-ت-ب")
    pattern = PatternTemplate(id=0, radical_slots=["C1", "C2", "C3"], vowel_slots=["V1"], affix_slots=[], pattern_name="w3_c3")
    assert _template_fill_gate(root, pattern, trace) is True


def test_template_fill_gate_fails_too_few_radicals():
    trace = ProofTrace()
    root = RootKernel(id=0, radicals=["ك"], semantic_field="general", concept_core="ك")
    pattern = PatternTemplate(id=0, radical_slots=["C1", "C2", "C3"], vowel_slots=[], affix_slots=[], pattern_name="w3_c3")
    assert _template_fill_gate(root, pattern, trace) is False


def test_well_formedness_gate_passes():
    trace = ProofTrace()
    atom = UnicodeAtom(id=0, codepoint=0x0643, category="Lo", combining_class=0)
    unit = FunctionalUnit(id=0, atoms=[atom], unit_type="LETTER", role_set=["RADICAL"], position=0)
    ils = IntraLexemeStructure(id=0, units=[unit], consonantal_skeleton=[unit], vocalic_skeleton=[], augmentations=[], surface_form="ك")
    assert _well_formedness_gate(ils, trace) is True


def test_well_formedness_gate_fails_empty():
    trace = ProofTrace()
    ils = IntraLexemeStructure(id=0, units=[], consonantal_skeleton=[], vocalic_skeleton=[], augmentations=[], surface_form="")
    assert _well_formedness_gate(ils, trace) is False


def test_predication_gate_passes_single_lexeme():
    trace = ProofTrace()
    atom = UnicodeAtom(id=0, codepoint=0x0643, category="Lo", combining_class=0)
    unit = FunctionalUnit(id=0, atoms=[atom], unit_type="LETTER", role_set=["RADICAL"], position=0)
    root = RootKernel(id=0, radicals=["ك"], semantic_field="general", concept_core="ك")
    pattern = PatternTemplate(id=0, radical_slots=["C1"], vowel_slots=[], affix_slots=[], pattern_name="w1_c1")
    from app.services.bidirectional_engine import LexemeNode
    lex = LexemeNode(id=0, root=root, pattern=pattern, surface_form="ك", pos="noun", lexeme_type="JAMID", morph_state="MABNI", definiteness="INDEFINITE", universality="KULLI", features={})
    cn = ConstructionNetwork(id=0, lexemes=[lex], predication_relations=[], inclusion_relations=[], restriction_relations=[], case_values={})
    assert _predication_gate(cn, trace) is True


def test_meaning_consistency_gate_passes():
    trace = ProofTrace()
    ms = MeaningStructure(id=0, entities=[Entity(id=0, label="كتاب", lexeme_ref=0, entity_type="thing")], qualities=[], events=[], relations=[], universal_meanings=[], particulars=[], entailments=[])
    assert _meaning_consistency_gate(ms, trace) is True


def test_meaning_consistency_gate_fails_empty():
    trace = ProofTrace()
    ms = MeaningStructure(id=0, entities=[], qualities=[], events=[], relations=[], universal_meanings=[], particulars=[], entailments=[])
    assert _meaning_consistency_gate(ms, trace) is False


# ─────────────────────────────────────────────────────────────────────────────
# Unicode and functional unit builders
# ─────────────────────────────────────────────────────────────────────────────


def test_build_unicode_atoms_arabic():
    atoms = _build_unicode_atoms("كتاب")
    assert len(atoms) == 4
    assert all(a.category == "Lo" for a in atoms)


def test_build_unicode_atoms_normalizes_alef_variants():
    atoms_orig = _build_unicode_atoms("أكتب")
    atoms_norm = _build_unicode_atoms("اكتب")
    assert atoms_orig[0].codepoint == atoms_norm[0].codepoint


def test_build_functional_units_classifies_letter():
    trace = ProofTrace()
    atoms = _build_unicode_atoms("كتب")
    units = _build_functional_units(atoms, trace)
    letter_units = [u for u in units if u.unit_type == "LETTER"]
    assert len(letter_units) == 3


def test_build_functional_units_classifies_haraka():
    trace = ProofTrace()
    # kaf + fatha
    text = "كَ"
    atoms = _build_unicode_atoms(text)
    units = _build_functional_units(atoms, trace)
    unit_types = {u.unit_type for u in units}
    assert "LETTER" in unit_types
    assert "HARAKA" in unit_types


# ─────────────────────────────────────────────────────────────────────────────
# Backward generation unit tests
# ─────────────────────────────────────────────────────────────────────────────


def test_generate_backward_entities_only():
    meaning = {
        "entities": [{"id": 0, "label": "الكتاب", "entity_type": "thing"}],
        "events": [],
        "qualities": [],
        "relations": [],
    }
    result = run_generate_backward(meaning)
    assert result.valid is True
    assert result.generated_text != ""
    assert "الكتاب" in result.generated_text


def test_generate_backward_event_with_agent():
    meaning = {
        "entities": [
            {"id": 0, "label": "الطالب", "entity_type": "person"},
            {"id": 1, "label": "الكتاب", "entity_type": "thing"},
        ],
        "events": [
            {"id": 2, "label": "قرأ", "agent_id": 0, "patient_id": 1}
        ],
        "qualities": [],
        "relations": [{"type": "predication", "source": 2, "target": 0}],
    }
    result = run_generate_backward(meaning)
    assert result.valid is True
    assert "قرأ" in result.generated_text
    assert len(result.candidate_forms) >= 1


def test_generate_backward_empty_meaning_returns_invalid():
    meaning = {"entities": [], "events": [], "qualities": [], "relations": []}
    result = run_generate_backward(meaning)
    assert result.valid is False
    assert result.generated_text == ""


def test_generate_backward_multiple_candidates():
    meaning = {
        "entities": [
            {"id": 0, "label": "الطالب", "entity_type": "person"},
            {"id": 1, "label": "الكتاب", "entity_type": "thing"},
            {"id": 2, "label": "البيت", "entity_type": "place"},
        ],
        "events": [],
        "qualities": [],
        "relations": [],
    }
    result = run_generate_backward(meaning)
    assert result.valid is True
    assert len(result.candidate_forms) >= 2


# ─────────────────────────────────────────────────────────────────────────────
# API endpoint tests
# ─────────────────────────────────────────────────────────────────────────────


def test_bidirectional_analyze_endpoint():
    payload = {"text": "الكتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/analyze", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    assert "run_id" in data
    assert data["normalized_text"] != ""
    assert isinstance(data["unicode_atoms"], list)
    assert len(data["unicode_atoms"]) > 0
    assert isinstance(data["functional_units"], list)
    assert isinstance(data["intra_lexeme_structures"], list)
    assert isinstance(data["syllable_circuits"], list)
    assert isinstance(data["root_patterns"], list)
    assert isinstance(data["lexemes"], list)
    assert "construction_network" in data
    assert "trace" in data
    assert "metrics" in data
    assert data["metrics"]["atom_count"] > 0
    assert data["metrics"]["lexeme_count"] > 0
    assert data["trace"]["score"] > 0


def test_bidirectional_analyze_returns_layer_details():
    payload = {"text": "كتب الطالب"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/analyze", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()

    # Layer 0: unicode atoms
    assert all("codepoint" in a for a in data["unicode_atoms"])
    # Layer 1: functional units
    assert all("unit_type" in u for u in data["functional_units"])
    # Layer 2: ILS
    assert all("surface_form" in ils for ils in data["intra_lexeme_structures"])
    # Layer 4/5: root + pattern
    assert all("root" in rp and "pattern" in rp for rp in data["root_patterns"])
    # Layer 6: lexeme nodes
    assert all("pos" in l and "lexeme_type" in l for l in data["lexemes"])


def test_bidirectional_analyze_meaning_structure():
    payload = {"text": "الكتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/analyze", json=payload, headers=headers)

    data = response.json()
    ms = data.get("meaning_structure")
    assert ms is not None
    assert isinstance(ms["entities"], list)
    assert len(ms["entities"]) > 0


def test_bidirectional_generate_endpoint():
    payload = {
        "entities": [
            {"id": 0, "label": "الكتاب", "entity_type": "thing"},
            {"id": 1, "label": "البيت", "entity_type": "place"},
        ],
        "events": [],
        "qualities": [],
        "relations": [{"type": "restriction", "source": 0, "target": 1}],
    }
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/generate", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["generated_text"] != ""
    assert isinstance(data["candidate_forms"], list)
    assert len(data["candidate_forms"]) >= 1
    assert "trace" in data


def test_bidirectional_generate_empty_returns_400_or_invalid():
    payload = {"entities": [], "events": [], "qualities": [], "relations": []}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/generate", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False


def test_bidirectional_endpoints_require_auth():
    with TestClient(create_app()) as client:
        r1 = client.post("/bidirectional/analyze", json={"text": "كتاب"})
        r2 = client.post("/bidirectional/generate", json={"entities": [], "events": [], "qualities": [], "relations": []})

    assert r1.status_code == 401
    assert r2.status_code == 401


def test_bidirectional_analyze_gate_trace_has_steps():
    payload = {"text": "كتب"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/analyze", json=payload, headers=headers)

    data = response.json()
    trace = data["trace"]
    assert isinstance(trace["steps"], list)
    assert len(trace["steps"]) > 0
    assert isinstance(trace["contradictions"], list)
    assert isinstance(trace["score"], float)
    assert 0.0 <= trace["score"] <= 1.0


def test_bidirectional_generate_with_event():
    payload = {
        "entities": [
            {"id": 0, "label": "المعلم", "entity_type": "person"},
        ],
        "events": [
            {"id": 1, "label": "درّس", "agent_id": 0, "patient_id": None}
        ],
        "qualities": [],
        "relations": [],
    }
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/bidirectional/generate", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert "درّس" in data["generated_text"] or any("درّس" in c for c in data["candidate_forms"])
