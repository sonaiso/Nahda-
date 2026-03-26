"""
Graph analysis service.

Orchestrates the construction of the graph for a given Arabic text:
  1. Tokenisation + MorphemeLattice
  2. Stem extraction
  3. Root / Pattern candidate generation via template matching
  4. Evidence emission from morphological rules
  5. Persistence to the relational DB (graph node tables)

The service does NOT commit to a Neo4j instance; it builds the same
graph in the SQL DB using the graph node models, and returns a
plain-dict representation suitable for JSON export or graph DB import.
"""

from __future__ import annotations

import re
import unicodedata
import uuid
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.graph.models import (
    Evidence,
    GToken,
    Morpheme,
    MorphemeLattice,
    PatternCandidate,
    Root,
    RootCandidate,
    SegCandidate,
    Stem,
)
from app.graph.templates import TEMPLATES, get_ops, get_root_classes
from app.models.entities import LayerExecution
from app.services.unicode_pipeline import run_unicode_pipeline

# ---------------------------------------------------------------------------
# Arabic character helpers
# ---------------------------------------------------------------------------

ARABIC_LETTER_RE = re.compile(r"[\u0621-\u064A\u0670\u0671]")
DIACRITIC_CHARS = set("\u064B\u064C\u064D\u064E\u064F\u0650\u0651\u0652\u0670")
PREFIXES = ("ال", "و", "ف", "ب", "ك", "ل", "س", "أ")
SUFFIXES = (
    "ون",
    "ين",
    "ات",
    "ان",
    "تان",
    "تين",
    "وا",
    "ها",
    "هم",
    "هن",
    "هما",
    "كم",
    "نا",
    "ة",
    "ه",
    "ي",
)


def strip_diacritics(text: str) -> str:
    return "".join(c for c in text if c not in DIACRITIC_CHARS)


def extract_consonants(token: str) -> list[str]:
    clean = strip_diacritics(token)
    # Normalise alef variants
    clean = unicodedata.normalize("NFC", clean)
    clean = (
        clean.replace("\u0622", "\u0627")
        .replace("\u0623", "\u0627")
        .replace("\u0625", "\u0627")
    )
    return [c for c in clean if ARABIC_LETTER_RE.match(c)]


def strip_affixes(token: str) -> tuple[str, list[str]]:
    """Strip known Arabic prefixes/suffixes; return stem and augmentation list."""
    work = strip_diacritics(token)
    augmentations: list[str] = []

    if work.startswith("ال") and len(work) > 3:
        work = work[2:]
        augmentations.append("prefix:ال")

    for pref in PREFIXES:
        if pref == "ال":
            continue
        if work.startswith(pref) and len(work) - len(pref) >= 3:
            work = work[len(pref):]
            augmentations.append(f"prefix:{pref}")
            break

    for suf in SUFFIXES:
        if work.endswith(suf) and len(work) - len(suf) >= 3:
            work = work[: -len(suf)]
            augmentations.append(f"suffix:{suf}")
            break

    return work, augmentations


# ---------------------------------------------------------------------------
# Template matching
# ---------------------------------------------------------------------------

def _score_template_match(consonants: list[str], template: dict) -> float:
    """
    Simple consonant-count heuristic matching consonant list against template.

    Returns a score in [0, 1].
    """
    slots = [s.strip() for s in template["slots"].split(",")]
    num_slots = len(slots)
    if num_slots == 0:
        return 0.0
    matches = min(len(consonants), num_slots)
    return round(matches / num_slots, 4)


def generate_candidates(
    stem_surface: str,
    max_root_candidates: int = 3,
    max_pattern_candidates: int = 3,
) -> tuple[list[dict], list[dict]]:
    """
    Generate root and pattern candidates for a given stem surface.

    Returns:
        root_candidates   – list of {root, score, rank, method}
        pattern_candidates – list of {template_id, pattern, score, rank, method, alignment}
    """
    consonants = extract_consonants(stem_surface)

    # Root candidates: take first 3 consonants as primary candidate
    root_cands: list[dict] = []
    if len(consonants) >= 3:
        root_cands.append(
            {
                "root": "".join(consonants[:3]),
                "score": 0.90,
                "rank": 1,
                "method": "consonant_extract",
            }
        )
        if len(consonants) >= 4:
            root_cands.append(
                {
                    "root": "".join(consonants[:4]),
                    "score": 0.70,
                    "rank": 2,
                    "method": "quad_consonant_extract",
                }
            )
    elif len(consonants) == 2:
        root_cands.append(
            {
                "root": "".join(consonants) + "_",
                "score": 0.60,
                "rank": 1,
                "method": "consonant_extract",
            }
        )
    else:
        root_cands.append(
            {"root": "_" * 3, "score": 0.10, "rank": 1, "method": "fallback"}
        )

    # Pattern candidates: score every template by consonant count match
    scored: list[tuple[float, dict]] = []
    for tmpl in TEMPLATES:
        score = _score_template_match(consonants, tmpl)
        scored.append((score, tmpl))

    scored.sort(key=lambda x: -x[0])
    pat_cands: list[dict] = []
    seen_patterns: set[str] = set()
    rank = 1
    for score, tmpl in scored[:max_pattern_candidates * 4]:
        pat_key = tmpl["surface_pattern"]
        if pat_key in seen_patterns:
            continue
        seen_patterns.add(pat_key)
        pat_cands.append(
            {
                "template_id": tmpl["template_id"],
                "pattern": tmpl["surface_pattern"],
                "derivation_type": tmpl["derivation_type"],
                "score": score,
                "rank": rank,
                "method": "template_match",
                "alignment": {
                    "consonants": consonants,
                    "slots": tmpl["slots"],
                },
            }
        )
        rank += 1
        if rank > max_pattern_candidates:
            break

    return root_cands[: max_root_candidates], pat_cands


# ---------------------------------------------------------------------------
# Dataclasses for service result
# ---------------------------------------------------------------------------


@dataclass
class GraphTokenResult:
    token_id: str
    surface: str
    norm: str
    tok_index: int
    stem_surface: str
    augmentations: list[str]
    root_candidates: list[dict]
    pattern_candidates: list[dict]
    seg_candidate: dict
    evidence: list[dict]


@dataclass
class GraphAnalysisResult:
    run_id: str
    normalized_text: str
    tokens: list[GraphTokenResult]
    token_count: int
    triliteral_ratio: float
    ops: list[dict] = field(default_factory=list)
    root_classes: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Emit evidence rules
# ---------------------------------------------------------------------------

_SUFFIX_CASE_EVIDENCE = {
    "suffix:ون": {"feature": "case", "value": "nominative", "weight": 0.85},
    "suffix:ين": {"feature": "case", "value": "genitive_or_accusative", "weight": 0.75},
    "suffix:ان": {"feature": "number", "value": "dual_nominative", "weight": 0.90},
    "suffix:ات": {"feature": "gender", "value": "feminine_plural", "weight": 0.90},
    "suffix:ة": {"feature": "gender", "value": "feminine", "weight": 0.95},
    "prefix:ال": {"feature": "definiteness", "value": "definite", "weight": 0.99},
    "prefix:و": {"feature": "conjunction", "value": "waw_atf", "weight": 0.95},
    "prefix:ف": {"feature": "conjunction", "value": "fa_atf", "weight": 0.90},
    "prefix:ب": {"feature": "preposition", "value": "bi_jar", "weight": 0.95},
    "prefix:ك": {"feature": "preposition", "value": "ka_jar", "weight": 0.90},
    "prefix:ل": {"feature": "preposition", "value": "li_jar", "weight": 0.90},
}


def _build_evidence(
    run_id: str,
    augmentations: list[str],
    root_cands: list[dict],
    pat_cands: list[dict],
) -> list[dict]:
    evidences: list[dict] = []

    for aug in augmentations:
        ev_meta = _SUFFIX_CASE_EVIDENCE.get(aug)
        if ev_meta:
            evidences.append(
                {
                    "ev_id": str(uuid.uuid4()),
                    "source_layer": "morpheme",
                    "rule_id": f"rule_{aug.replace(':', '_')}",
                    "feature": ev_meta["feature"],
                    "value": ev_meta["value"],
                    "weight": ev_meta["weight"],
                    "polarity": "supports",
                    "explanation": f"Suffix/prefix '{aug}' indicates {ev_meta['feature']}={ev_meta['value']}",
                    "target_node_type": "SemanticFeature",
                    "target_node_id": "",
                }
            )

    if root_cands:
        top_root = root_cands[0]
        evidences.append(
            {
                "ev_id": str(uuid.uuid4()),
                "source_layer": "morphology",
                "rule_id": "rule_root_consonant_extract",
                "feature": "root",
                "value": top_root["root"],
                "weight": top_root["score"],
                "polarity": "supports",
                "explanation": f"Top root candidate: {top_root['root']} (score={top_root['score']})",
                "target_node_type": "RootCandidate",
                "target_node_id": "",
            }
        )

    if pat_cands:
        top_pat = pat_cands[0]
        evidences.append(
            {
                "ev_id": str(uuid.uuid4()),
                "source_layer": "morphology",
                "rule_id": "rule_template_match",
                "feature": "pattern",
                "value": top_pat["pattern"],
                "weight": top_pat["score"],
                "polarity": "supports",
                "explanation": f"Top pattern match: {top_pat['pattern']} via {top_pat['template_id']}",
                "target_node_type": "PatternCandidate",
                "target_node_id": "",
            }
        )

    return evidences


# ---------------------------------------------------------------------------
# Main service function
# ---------------------------------------------------------------------------


def run_graph_analysis(db: Session, text: str) -> GraphAnalysisResult:
    """
    Analyse Arabic text and persist the graph to the relational DB.

    Pipeline:
      1. Unicode normalisation (reuse existing pipeline)
      2. Tokenise
      3. For each token: strip affixes → Stem → Root/Pattern candidates
      4. Emit Evidence
      5. Persist nodes (GToken, MorphemeLattice, Morpheme, Stem, Candidates, Evidence)
      6. Return structured result
    """
    unicode_result = run_unicode_pipeline(db=db, text=text)
    run_id = unicode_result.run_id
    tokens_text = [t for t in unicode_result.normalized_text.split() if t]

    token_results: list[GraphTokenResult] = []
    prev_token_id: str | None = None
    token_rows: list[GToken] = []
    lattice_rows: list[MorphemeLattice] = []
    morpheme_rows: list[Morpheme] = []
    stem_rows: list[Stem] = []
    root_cand_rows: list[RootCandidate] = []
    pat_cand_rows: list[PatternCandidate] = []
    seg_cand_rows: list[SegCandidate] = []
    evidence_rows: list[Evidence] = []

    triliteral_count = 0

    for idx, surface in enumerate(tokens_text):
        tok_id = str(uuid.uuid4())
        norm = strip_diacritics(surface)
        stem_surface, augmentations = strip_affixes(surface)
        root_cands, pat_cands = generate_candidates(stem_surface)

        # ── Token row ─────────────────────────────────────────────────────
        tok_row = GToken(
            id=tok_id,
            run_id=run_id,
            surface=surface,
            norm=norm,
            tok_index=idx,
            is_punct=not bool(ARABIC_LETTER_RE.search(surface)),
            prev_token_id=prev_token_id,
        )
        token_rows.append(tok_row)

        # Update previous token's next pointer
        if prev_token_id and token_rows:
            for t in token_rows:
                if t.id == prev_token_id:
                    t.next_token_id = tok_id
                    break

        # ── MorphemeLattice ───────────────────────────────────────────────
        lat_id = str(uuid.uuid4())
        lat = MorphemeLattice(id=lat_id, run_id=run_id, token_id=tok_id)
        lattice_rows.append(lat)

        # ── Morpheme segments (simple: prefix* + stem + suffix*) ──────────
        morph_id_prefix: str | None = None
        morph_id_stem: str | None = None
        morph_id_suffix: str | None = None
        prev_morph_id: str | None = None

        pref_augs = [a for a in augmentations if a.startswith("prefix:")]
        suf_augs = [a for a in augmentations if a.startswith("suffix:")]

        if pref_augs:
            morph_id_prefix = str(uuid.uuid4())
            morpheme_rows.append(
                Morpheme(
                    id=morph_id_prefix,
                    lattice_id=lat_id,
                    form=pref_augs[0].split(":")[1],
                    morph_type="prefix",
                    path_rank=1,
                    prev_morpheme_id=None,
                )
            )
            prev_morph_id = morph_id_prefix

        morph_id_stem = str(uuid.uuid4())
        morpheme_rows.append(
            Morpheme(
                id=morph_id_stem,
                lattice_id=lat_id,
                form=stem_surface,
                morph_type="stem",
                path_rank=1,
                prev_morpheme_id=prev_morph_id,
            )
        )
        prev_morph_id = morph_id_stem

        if suf_augs:
            morph_id_suffix = str(uuid.uuid4())
            morpheme_rows.append(
                Morpheme(
                    id=morph_id_suffix,
                    lattice_id=lat_id,
                    form=suf_augs[0].split(":")[1],
                    morph_type="suffix",
                    path_rank=1,
                    prev_morpheme_id=prev_morph_id,
                )
            )

        # ── Stem ──────────────────────────────────────────────────────────
        stem_id = str(uuid.uuid4())
        stem_rows.append(
            Stem(id=stem_id, morpheme_id=morph_id_stem, stem_surface=stem_surface)
        )

        # ── SegCandidate ──────────────────────────────────────────────────
        seg_cand_id = str(uuid.uuid4())
        seg_cand = {
            "seg_id": seg_cand_id,
            "path_rank": 1,
            "score": 0.85,
            "method": "rule_based",
            "segments": [
                *[a.split(":")[1] for a in pref_augs],
                stem_surface,
                *[a.split(":")[1] for a in suf_augs],
            ],
        }
        seg_cand_rows.append(
            SegCandidate(
                id=seg_cand_id,
                lattice_id=lat_id,
                path_rank=1,
                score=0.85,
                method="rule_based",
                segments_json=seg_cand["segments"],
            )
        )

        # ── Root candidates ───────────────────────────────────────────────
        rc_ids: list[str] = []
        for rc in root_cands:
            rc_id = str(uuid.uuid4())
            rc_ids.append(rc_id)
            # Ensure root exists in g_roots (upsert-like: check first)
            root_obj = db.query(Root).filter_by(root=rc["root"]).first()
            if root_obj is None:
                root_obj = Root(
                    id=str(uuid.uuid4()),
                    root=rc["root"],
                    radicals_count=len([c for c in rc["root"] if c != "_"]),
                )
                db.add(root_obj)
                db.flush()

            root_cand_rows.append(
                RootCandidate(
                    id=rc_id,
                    stem_id=stem_id,
                    root_id=root_obj.id,
                    score=rc["score"],
                    rank=rc["rank"],
                    method=rc["method"],
                )
            )

            if rc["rank"] == 1 and "_" not in rc["root"]:
                triliteral_count += 1

        # ── Pattern candidates ────────────────────────────────────────────
        for pc in pat_cands:
            pc_id = str(uuid.uuid4())
            pat_cand_rows.append(
                PatternCandidate(
                    id=pc_id,
                    stem_id=stem_id,
                    pattern_id=None,
                    template_id=None,
                    score=pc["score"],
                    rank=pc["rank"],
                    method=pc["method"],
                    alignment_json=pc.get("alignment", {}),
                )
            )

        # ── Evidence ──────────────────────────────────────────────────────
        evidences = _build_evidence(run_id, augmentations, root_cands, pat_cands)
        for ev in evidences:
            evidence_rows.append(
                Evidence(
                    id=ev["ev_id"],
                    run_id=run_id,
                    source_layer=ev["source_layer"],
                    rule_id=ev.get("rule_id"),
                    feature=ev["feature"],
                    value=ev["value"],
                    weight=ev["weight"],
                    polarity=ev["polarity"],
                    explanation=ev["explanation"],
                    target_node_type=ev.get("target_node_type", ""),
                    target_node_id=ev.get("target_node_id", ""),
                )
            )

        token_results.append(
            GraphTokenResult(
                token_id=tok_id,
                surface=surface,
                norm=norm,
                tok_index=idx,
                stem_surface=stem_surface,
                augmentations=augmentations,
                root_candidates=root_cands,
                pattern_candidates=pat_cands,
                seg_candidate=seg_cand,
                evidence=evidences,
            )
        )

        prev_token_id = tok_id

    # ── Persist all rows ──────────────────────────────────────────────────
    db.add_all(token_rows)
    db.add_all(lattice_rows)
    db.add_all(morpheme_rows)
    db.add_all(stem_rows)
    db.add_all(root_cand_rows)
    db.add_all(pat_cand_rows)
    db.add_all(seg_cand_rows)
    db.add_all(evidence_rows)

    db.add(
        LayerExecution(
            run_id=run_id,
            layer_name="graph_analysis",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={
                "token_count": len(tokens_text),
                "evidence_count": len(evidence_rows),
            },
        )
    )
    db.commit()

    triliteral_ratio = (
        round(triliteral_count / len(tokens_text), 4) if tokens_text else 0.0
    )

    return GraphAnalysisResult(
        run_id=run_id,
        normalized_text=unicode_result.normalized_text,
        tokens=token_results,
        token_count=len(tokens_text),
        triliteral_ratio=triliteral_ratio,
        ops=get_ops(),
        root_classes=get_root_classes(),
    )
