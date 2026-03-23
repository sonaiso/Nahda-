"""Tests for the backward generation pipeline – sections 12–14 of the spec."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.generate_backward_pipeline import (
    Branch,
    ConstructionPlan,
    LexemeNode,
    RootKernel,
    PatternTemplate,
    IntraLexemeStructure,
    SyllableCircuit,
    Trace,
    _extract_content_tokens,
    _semantic_equivalence,
    _score_consistency,
    _score_minimal_contradiction,
    _score_morpho_syntactic_economy,
    _score_semantic_coverage,
    build_ils_from_root_pattern,
    build_syllables_from_ils,
    emit_unicode_text,
    plan_construction_from_meaning,
    rank_branches,
    realize_functional_units,
    select_lexemes_from_construction,
    select_root_pattern_for_lexemes,
)
from tests.auth_helpers import get_auth_headers


# ---------------------------------------------------------------------------
# Unit tests – individual pipeline stages
# ---------------------------------------------------------------------------


def test_extract_content_tokens_removes_particles() -> None:
    tokens = _extract_content_tokens("الكتاب في البيت")
    assert "في" not in tokens
    assert "الكتاب" in tokens
    assert "البيت" in tokens


def test_extract_content_tokens_empty() -> None:
    assert _extract_content_tokens("") == []
    assert _extract_content_tokens("في من و") == []


def test_plan_construction_from_meaning_returns_three_plans() -> None:
    branches = plan_construction_from_meaning("الكتاب في البيت", {})
    assert len(branches) == 3
    types = {b.value.structure_type for b in branches}
    assert types == {"nominal", "verbal", "annexation"}


def test_plan_construction_gates_pass() -> None:
    branches = plan_construction_from_meaning("العلم نور", {})
    for b in branches:
        passed = [s for s in b.trace.steps if s.startswith("PASS")]
        failed = [s for s in b.trace.steps if s.startswith("FAIL")]
        assert len(passed) >= 4
        assert len(failed) == 0


def test_select_lexemes_assigns_tokens_to_slots() -> None:
    plan = ConstructionPlan(
        structure_type="nominal",
        slots=["mubtada", "khabar"],
        syntactic_factors={"tense": "present"},
        case_values={"mubtada": "nominative", "khabar": "nominative"},
    )
    branches = select_lexemes_from_construction(plan, "الكتاب موجود", {})
    assert len(branches) == 1
    lexemes: list[LexemeNode] = branches[0].value
    slots = {lex.slot for lex in lexemes}
    assert "mubtada" in slots
    assert "khabar" in slots


def test_select_lexemes_rejects_empty_meaning() -> None:
    plan = ConstructionPlan(
        structure_type="nominal",
        slots=["mubtada", "khabar"],
        syntactic_factors={},
        case_values={"mubtada": "nominative", "khabar": "nominative"},
    )
    assert select_lexemes_from_construction(plan, "", {}) == []
    assert select_lexemes_from_construction(plan, "في من", {}) == []


def test_select_root_pattern_for_lexemes_returns_branches() -> None:
    lexemes = [
        LexemeNode("كتاب", "كتاب", "noun", "mubtada", ["ك", "ت", "ب"], "fa3l"),
        LexemeNode("بيت", "بيت", "noun", "khabar", ["ب", "ي", "ت"], "fa3l"),
    ]
    branches = select_root_pattern_for_lexemes(lexemes, {})
    assert len(branches) >= 1
    for b in branches:
        combo = b.value
        assert isinstance(combo, list)
        assert all(isinstance(r, RootKernel) and isinstance(p, PatternTemplate) for r, p in combo)


def test_build_ils_from_root_pattern_uses_surface_form() -> None:
    lex = LexemeNode("كتاب", "كتاب", "noun", "mubtada", ["ك", "ت", "ب"], "fa3l")
    root = RootKernel(["ك", "ت", "ب"])
    pat = PatternTemplate("fa3l", "CVC", "Masdar")
    branches = build_ils_from_root_pattern([(root, pat)], [lex], {})
    assert len(branches) == 1
    ils_list: list[IntraLexemeStructure] = branches[0].value
    assert ils_list[0].form == "كتاب"
    assert ils_list[0].lexeme.slot == "mubtada"


def test_build_syllables_from_ils() -> None:
    lex = LexemeNode("علم", "علم", "noun", "mubtada", ["ع", "ل", "م"], "fa3l")
    root = RootKernel(["ع", "ل", "م"])
    pat = PatternTemplate("fa3l", "CVC", "Masdar")
    ils = IntraLexemeStructure(lex, root, pat, "علم")
    branches = build_syllables_from_ils([ils], {})
    assert len(branches) == 1
    sylls: list[SyllableCircuit] = branches[0].value
    assert all(isinstance(s, SyllableCircuit) for s in sylls)
    assert all(s.text and s.pattern for s in sylls)


def test_realize_functional_units_produces_units() -> None:
    lex1 = LexemeNode("كتاب", "كتاب", "noun", "mubtada", ["ك", "ت", "ب"], "fa3l")
    lex2 = LexemeNode("علم", "علم", "noun", "khabar", ["ع", "ل", "م"], "fa3l")
    root = RootKernel(["ك", "ت", "ب"])
    pat = PatternTemplate("fa3l", "CVC", "Masdar")
    ils1 = IntraLexemeStructure(lex1, root, pat, "كتاب")
    ils2 = IntraLexemeStructure(lex2, RootKernel(["ع", "ل", "م"]), pat, "علم")
    sylls = [SyllableCircuit("ك", "C"), SyllableCircuit("تاب", "CVC")]
    branches = realize_functional_units([ils1, ils2], sylls, {})
    assert len(branches) == 1
    assert len(branches[0].value) == 2


def test_emit_unicode_text_joins_unit_texts() -> None:
    lex1 = LexemeNode("الكتاب", "كتاب", "noun", "mubtada", ["ك", "ت", "ب"], "fa3l")
    lex2 = LexemeNode("موجود", "موجود", "noun", "khabar", ["م", "و", "ج"], "fa3l")
    root = RootKernel(["ك", "ت", "ب"])
    pat = PatternTemplate("fa3l", "CVC", "Masdar")
    unit1_ils = IntraLexemeStructure(lex1, root, pat, "الكتاب")
    unit2_ils = IntraLexemeStructure(lex2, RootKernel(["م", "و", "ج"]), pat, "موجود")
    units = [
        __import__(
            "app.services.generate_backward_pipeline", fromlist=["FunctionalUnit"]
        ).FunctionalUnit(text="الكتاب", ils=unit1_ils, syllables=[], case_marker="u"),
        __import__(
            "app.services.generate_backward_pipeline", fromlist=["FunctionalUnit"]
        ).FunctionalUnit(text="موجود", ils=unit2_ils, syllables=[], case_marker=""),
    ]
    branches = emit_unicode_text(units, {})
    assert len(branches) == 1
    assert branches[0].value == "الكتاب موجود"


def test_semantic_equivalence_full_match() -> None:
    lexemes = [
        {"token": "الكتاب", "lemma": "كتاب"},
        {"token": "البيت", "lemma": "بيت"},
    ]
    assert _semantic_equivalence(lexemes, "الكتاب في البيت") is True


def test_semantic_equivalence_partial_match() -> None:
    lexemes = [{"token": "الكتاب", "lemma": "كتاب"}]
    # Only 1 of 2 content tokens covered (50 %) → should pass (≥50 %)
    assert _semantic_equivalence(lexemes, "الكتاب في البيت") is True


def test_semantic_equivalence_no_match() -> None:
    lexemes = [{"token": "سيارة", "lemma": "سيارة"}]
    # 0 of 2 content tokens → False
    assert _semantic_equivalence(lexemes, "الكتاب في البيت") is False


def test_score_consistency_all_pass() -> None:
    t = Trace("test")
    for _ in range(5):
        t.step("PASS gate")
    assert _score_consistency(t) == 1.0


def test_score_consistency_mixed() -> None:
    t = Trace("test")
    t.step("PASS gate1")
    t.step("FAIL gate2")
    assert _score_consistency(t) == 0.5


def test_score_minimal_contradiction_zero_fails() -> None:
    t = Trace("test")
    assert _score_minimal_contradiction(t) == 1.0


def test_score_minimal_contradiction_many_fails() -> None:
    t = Trace("test")
    for _ in range(15):
        t.step("FAIL gate")
    assert _score_minimal_contradiction(t) == 0.0


def test_score_morpho_syntactic_economy() -> None:
    assert _score_morpho_syntactic_economy("a b c") == 1.0       # 3 words
    assert _score_morpho_syntactic_economy("a") < 1.0            # 1 word
    assert _score_morpho_syntactic_economy("a b c d e f g") < 1.0  # 7 words


def test_score_semantic_coverage_full() -> None:
    assert _score_semantic_coverage("الكتاب البيت", "الكتاب في البيت") == 1.0


def test_score_semantic_coverage_empty_target() -> None:
    assert _score_semantic_coverage("الكتاب", "في من") == 0.5


def test_rank_branches_sorts_descending() -> None:
    low = Branch(value="x", trace=Trace("low", steps=["FAIL g1", "FAIL g2"], score=0.1))
    high = Branch(value="y", trace=Trace("high", steps=["PASS g1", "PASS g2"], score=0.9))
    ranked = rank_branches([low, high], "x y", {})
    assert ranked[0].trace.score >= ranked[-1].trace.score


# ---------------------------------------------------------------------------
# API endpoint tests
# ---------------------------------------------------------------------------


def test_generate_backward_requires_auth() -> None:
    with TestClient(create_app()) as client:
        response = client.post("/generate/backward", json={"meaning": "الكتاب"})
        assert response.status_code == 401


def test_generate_backward_rejects_blank_meaning() -> None:
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post(
            "/generate/backward", json={"meaning": "   "}, headers=headers
        )
        assert response.status_code == 422


def test_generate_backward_basic() -> None:
    payload = {"meaning": "الكتاب في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        assert "run_id" in data
        assert "target_meaning" in data
        assert "top_text" in data
        assert "branches" in data
        assert "metrics" in data


def test_generate_backward_metrics_consistent() -> None:
    payload = {"meaning": "العلم نور"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        metrics = data["metrics"]
        assert metrics["branch_count"] == len(data["branches"])
        assert metrics["verified_count"] <= metrics["branch_count"]
        assert 0.0 <= metrics["top_score"] <= 1.0


def test_generate_backward_branches_have_required_fields() -> None:
    payload = {"meaning": "يكتب العالم الكتاب"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        for branch in response.json()["branches"]:
            assert "text" in branch
            assert "score" in branch
            assert "verified" in branch
            assert "rank" in branch
            assert 0.0 <= branch["score"] <= 1.0


def test_generate_backward_branches_ranked_correctly() -> None:
    payload = {"meaning": "الكتاب موجود في البيت"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        branches = response.json()["branches"]
        ranks = [b["rank"] for b in branches]
        scores = [b["score"] for b in branches]
        # Ranks must be consecutive starting at 1
        assert ranks == list(range(1, len(branches) + 1))
        # Scores must be non-increasing
        assert scores == sorted(scores, reverse=True)


def test_generate_backward_top_text_matches_best_branch() -> None:
    payload = {"meaning": "العلم نافع"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        data = response.json()
        if data["branches"]:
            best_branch_text = data["branches"][0]["text"]
            assert data["top_text"] == best_branch_text


def test_generate_backward_run_id_is_uuid() -> None:
    payload = {"meaning": "كتب العالم"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200

        run_id = response.json()["run_id"]
        # UUID format: 8-4-4-4-12 hex chars
        import re
        uuid_pattern = re.compile(
            r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        )
        assert uuid_pattern.match(run_id), f"run_id {run_id!r} is not a valid UUID"


def test_generate_backward_v1_prefix() -> None:
    """The /v1 prefix registered in main.py should also work."""
    payload = {"meaning": "العلم نور"}
    with TestClient(create_app()) as client:
        headers = get_auth_headers(client)
        response = client.post("/v1/generate/backward", json=payload, headers=headers)
        assert response.status_code == 200
