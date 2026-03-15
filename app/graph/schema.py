"""
Graph Schema definition for the Arabic Fractal Engine.

This module provides:
  - LABELS       : node label metadata (name, properties, constraints)
  - RELATIONSHIPS: edge metadata (type, source, target, properties)
  - export_schema(): returns the full schema as a plain dict (JSON-serialisable)

The schema is Neo4j-compatible: every label/relationship can be mapped 1-to-1
to a CREATE CONSTRAINT / CREATE INDEX / CREATE (n:Label …) statement in Cypher.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Node labels
# ---------------------------------------------------------------------------

LABELS: list[dict[str, Any]] = [
    # ── A) Text layer ──────────────────────────────────────────────────────
    {
        "label": "Document",
        "layer": "A_text",
        "properties": {
            "doc_id": "string",
            "source": "string",
            "genre": "string",
            "timestamp": "datetime",
        },
        "constraints": [{"type": "UNIQUE", "property": "doc_id"}],
    },
    {
        "label": "Sentence",
        "layer": "A_text",
        "properties": {"sent_id": "string", "index": "integer"},
        "constraints": [{"type": "UNIQUE", "property": "sent_id"}],
    },
    {
        "label": "Token",
        "layer": "A_text",
        "properties": {
            "tok_id": "string",
            "surface": "string",
            "norm": "string",
            "index": "integer",
            "is_punct": "boolean",
        },
        "constraints": [{"type": "UNIQUE", "property": "tok_id"}],
        "indexes": [{"property": "surface"}],
    },
    # ── B) Graphemic layer ─────────────────────────────────────────────────
    {
        "label": "Grapheme",
        "layer": "B_graphemic",
        "properties": {
            "char": "string",
            "index_in_token": "integer",
            "type": "string",
        },
        "constraints": [],
    },
    {
        "label": "Diacritic",
        "layer": "B_graphemic",
        "properties": {"mark": "string", "position": "integer"},
        "constraints": [],
    },
    {
        "label": "OrthVariant",
        "layer": "B_graphemic",
        "properties": {"form": "string", "policy": "string"},
        "constraints": [],
    },
    # ── C) Phonology ───────────────────────────────────────────────────────
    {
        "label": "Phoneme",
        "layer": "C_phonology",
        "properties": {
            "ipa": "string",
            "makhraj": "string",
            "sifat": "string",
            "voiced": "boolean",
            "manner": "string",
            "place": "string",
        },
        "constraints": [],
    },
    {
        "label": "Syllable",
        "layer": "C_phonology",
        "properties": {"shape": "string", "stressable": "boolean"},
        "constraints": [],
    },
    # ── D) Morpheme / Segmentation ─────────────────────────────────────────
    {
        "label": "MorphemeLattice",
        "layer": "D_morphemes",
        "properties": {"lat_id": "string"},
        "constraints": [{"type": "UNIQUE", "property": "lat_id"}],
    },
    {
        "label": "Morpheme",
        "layer": "D_morphemes",
        "properties": {
            "form": "string",
            "morph_type": "string",
            "gloss": "string",
        },
        "constraints": [],
    },
    {
        "label": "Stem",
        "layer": "D_morphemes",
        "properties": {"stem_surface": "string"},
        "constraints": [],
        "indexes": [{"property": "stem_surface"}],
    },
    {
        "label": "Clitic",
        "layer": "D_morphemes",
        "properties": {"clitic_type": "string"},
        "constraints": [],
    },
    # ── E) Morphology ──────────────────────────────────────────────────────
    {
        "label": "Root",
        "layer": "E_morphology",
        "properties": {
            "root": "string",
            "radicals_count": "integer",
            "root_class": "string",
        },
        "constraints": [{"type": "UNIQUE", "property": "root"}],
        "indexes": [{"property": "root"}],
    },
    {
        "label": "RootClass",
        "layer": "E_morphology",
        "properties": {"class_name": "string", "description": "string"},
        "constraints": [{"type": "UNIQUE", "property": "class_name"}],
    },
    {
        "label": "Pattern",
        "layer": "E_morphology",
        "properties": {"pattern": "string", "slots": "string"},
        "constraints": [{"type": "UNIQUE", "property": "pattern"}],
    },
    {
        "label": "Template",
        "layer": "E_morphology",
        "properties": {
            "template_id": "string",
            "surface_pattern": "string",
            "slots": "string",
            "level": "string",
            "verb_form": "string",
        },
        "constraints": [{"type": "UNIQUE", "property": "template_id"}],
    },
    {
        "label": "DerivationType",
        "layer": "E_morphology",
        "properties": {"name": "string", "family": "string"},
        "constraints": [{"type": "UNIQUE", "property": "name"}],
    },
    {
        "label": "Lexeme",
        "layer": "E_morphology",
        "properties": {
            "lemma": "string",
            "pos": "string",
            "is_jamid": "boolean",
            "register": "string",
        },
        "constraints": [{"type": "UNIQUE", "properties": ["lemma", "pos"]}],
        "indexes": [{"property": "lemma"}],
    },
    {
        "label": "RootCandidate",
        "layer": "E_morphology",
        "properties": {"score": "float", "rank": "integer", "method": "string"},
        "constraints": [],
    },
    {
        "label": "PatternCandidate",
        "layer": "E_morphology",
        "properties": {
            "score": "float",
            "rank": "integer",
            "method": "string",
            "alignment": "map",
        },
        "constraints": [],
    },
    {
        "label": "SegCandidate",
        "layer": "E_morphology",
        "properties": {
            "path_rank": "integer",
            "score": "float",
            "method": "string",
        },
        "constraints": [],
    },
    # ── F) Syntax ──────────────────────────────────────────────────────────
    {
        "label": "Governor",
        "layer": "F_syntax",
        "properties": {"gov_type": "string", "strength": "string"},
        "constraints": [],
    },
    {
        "label": "DependencyEdge",
        "layer": "F_syntax",
        "properties": {"rel": "string", "score": "float"},
        "constraints": [],
    },
    {
        "label": "Phrase",
        "layer": "F_syntax",
        "properties": {"ph_type": "string"},
        "constraints": [],
    },
    {
        "label": "Clause",
        "layer": "F_syntax",
        "properties": {"cl_type": "string"},
        "constraints": [],
    },
    {
        "label": "SyntacticFeature",
        "layer": "F_syntax",
        "properties": {
            "feature_name": "string",
            "feature_value": "string",
            "source": "string",
        },
        "constraints": [],
    },
    # ── G) Semantics ───────────────────────────────────────────────────────
    {
        "label": "Sense",
        "layer": "G_semantics",
        "properties": {"sense_id": "string", "gloss": "string", "domain": "string"},
        "constraints": [],
    },
    {
        "label": "SemanticFeature",
        "layer": "G_semantics",
        "properties": {
            "dalala": "string",
            "truth": "string",
            "scope": "string",
            "restriction": "string",
        },
        "constraints": [],
    },
    {
        "label": "Reference",
        "layer": "G_semantics",
        "properties": {"ref_type": "string", "target_kind": "string"},
        "constraints": [],
    },
    {
        "label": "SpeechAct",
        "layer": "G_semantics",
        "properties": {"act": "string", "force": "string"},
        "constraints": [],
    },
    # ── H) Conceptual / Normative ──────────────────────────────────────────
    {
        "label": "Concept",
        "layer": "H_conceptual",
        "properties": {"concept_id": "string", "name": "string", "level": "string"},
        "constraints": [],
    },
    {
        "label": "RelationConcept",
        "layer": "H_conceptual",
        "properties": {"rel": "string"},
        "constraints": [],
    },
    {
        "label": "Norm",
        "layer": "H_conceptual",
        "properties": {"type": "string", "source_scope": "string"},
        "constraints": [],
    },
    {
        "label": "Illa",
        "layer": "H_conceptual",
        "properties": {"kind": "string", "pattern": "string"},
        "constraints": [],
    },
    # ── Core: Evidence / Constraint / Rule / Op ────────────────────────────
    {
        "label": "Evidence",
        "layer": "core",
        "properties": {
            "source_layer": "string",
            "rule_id": "string",
            "feature": "string",
            "value": "string",
            "weight": "float",
            "polarity": "string",
            "explanation": "string",
        },
        "constraints": [],
    },
    {
        "label": "Constraint",
        "layer": "core",
        "properties": {
            "feature": "string",
            "required_value": "string",
            "penalty": "float",
            "scope": "string",
        },
        "constraints": [],
    },
    {
        "label": "Rule",
        "layer": "core",
        "properties": {"rule_id": "string", "layer": "string", "description": "string"},
        "constraints": [{"type": "UNIQUE", "property": "rule_id"}],
    },
    {
        "label": "Op",
        "layer": "core",
        "properties": {
            "op_id": "string",
            "op_type": "string",
            "priority": "integer",
            "description": "string",
        },
        "constraints": [{"type": "UNIQUE", "property": "op_id"}],
    },
    {
        "label": "RootClass",
        "layer": "core",
        "properties": {"class_name": "string", "description": "string"},
        "constraints": [{"type": "UNIQUE", "property": "class_name"}],
    },
]

# ---------------------------------------------------------------------------
# Relationship types (edges)
# ---------------------------------------------------------------------------

RELATIONSHIPS: list[dict[str, Any]] = [
    # ── Sequential (prev/next) ─────────────────────────────────────────────
    {"type": "NEXT", "from": "Token", "to": "Token", "props": {}},
    {"type": "NEXT", "from": "Grapheme", "to": "Grapheme", "props": {}},
    {"type": "NEXT", "from": "Syllable", "to": "Syllable", "props": {}},
    {"type": "NEXT", "from": "Morpheme", "to": "Morpheme", "props": {}},
    # ── Containment (upper/lower) ─────────────────────────────────────────
    {"type": "HAS_SENTENCE", "from": "Document", "to": "Sentence", "props": {}},
    {"type": "HAS_TOKEN", "from": "Sentence", "to": "Token", "props": {}},
    {"type": "HAS_GRAPHEME", "from": "Token", "to": "Grapheme", "props": {}},
    {"type": "HAS_DIACRITIC", "from": "Grapheme", "to": "Diacritic", "props": {}},
    {"type": "HAS_ORTH_VARIANT", "from": "Token", "to": "OrthVariant", "props": {}},
    {"type": "REALIZES", "from": "Grapheme", "to": "Phoneme", "props": {}},
    {"type": "HAS_SYLLABLE", "from": "Token", "to": "Syllable", "props": {}},
    {
        "type": "HAS_PART",
        "from": "Syllable",
        "to": "Phoneme",
        "props": {"position": "integer"},
    },
    {"type": "HAS_LATTICE", "from": "Token", "to": "MorphemeLattice", "props": {}},
    {
        "type": "HAS_PATH",
        "from": "MorphemeLattice",
        "to": "Morpheme",
        "props": {"rank": "integer"},
    },
    {"type": "PART_OF", "from": "Morpheme", "to": "Token", "props": {}},
    {"type": "REALIZES", "from": "Morpheme", "to": "Stem", "props": {}},
    # ── Morphology candidates ─────────────────────────────────────────────
    {
        "type": "HAS_ROOT_CANDIDATE",
        "from": "Stem",
        "to": "RootCandidate",
        "props": {},
    },
    {
        "type": "CANDIDATE_OF",
        "from": "RootCandidate",
        "to": "Root",
        "props": {"score": "float", "rank": "integer"},
    },
    {
        "type": "HAS_PATTERN_CANDIDATE",
        "from": "Stem",
        "to": "PatternCandidate",
        "props": {},
    },
    {
        "type": "CANDIDATE_OF",
        "from": "PatternCandidate",
        "to": "Pattern",
        "props": {"score": "float", "rank": "integer"},
    },
    {
        "type": "MATCHES_TEMPLATE",
        "from": "Stem",
        "to": "Template",
        "props": {"score": "float", "alignment": "map"},
    },
    {"type": "REALIZED_BY", "from": "Pattern", "to": "Template", "props": {}},
    {"type": "USES_TEMPLATE", "from": "DerivationType", "to": "Template", "props": {}},
    {"type": "HAS_ROOT", "from": "Lexeme", "to": "Root", "props": {}},
    {"type": "REALIZES_PATTERN", "from": "Lexeme", "to": "Pattern", "props": {}},
    {"type": "HAS_SENSE", "from": "Lexeme", "to": "Sense", "props": {}},
    {"type": "IN_CLASS", "from": "Root", "to": "RootClass", "props": {}},
    # ── Syntax ────────────────────────────────────────────────────────────
    {
        "type": "GOVERNS",
        "from": "Token",
        "to": "Token",
        "props": {"rel": "string", "score": "float"},
    },
    {
        "type": "HAS_DEP_EDGE",
        "from": "Token",
        "to": "DependencyEdge",
        "props": {},
    },
    {"type": "TO", "from": "DependencyEdge", "to": "Token", "props": {}},
    {"type": "HAS_PART", "from": "Clause", "to": "Token", "props": {}},
    {"type": "HAS_PART", "from": "Phrase", "to": "Token", "props": {}},
    {
        "type": "TRIGGERS",
        "from": "Governor",
        "to": "SyntacticFeature",
        "props": {},
    },
    # ── Semantics ─────────────────────────────────────────────────────────
    {
        "type": "HAS_SEM_FEATURE",
        "from": "Token",
        "to": "SemanticFeature",
        "props": {},
    },
    {
        "type": "REFERS_TO",
        "from": "Token",
        "to": "Reference",
        "props": {},
    },
    {"type": "TARGET", "from": "Reference", "to": "Token", "props": {}},
    {
        "type": "HAS_SPEECH_ACT",
        "from": "Clause",
        "to": "SpeechAct",
        "props": {},
    },
    # ── Conceptual / Normative ───────────────────────────────────────────
    {"type": "MAPS_TO", "from": "Sense", "to": "Concept", "props": {}},
    {
        "type": "RELATES",
        "from": "Concept",
        "to": "Concept",
        "props": {"rel": "string"},
    },
    {"type": "YIELDS", "from": "Clause", "to": "Norm", "props": {}},
    {"type": "BASED_ON", "from": "Norm", "to": "Illa", "props": {}},
    # ── Evidence / Constraint ─────────────────────────────────────────────
    {
        "type": "SUPPORTS",
        "from": "Evidence",
        "to": "RootCandidate",
        "props": {},
        "note": "also to PatternCandidate/SegCandidate/SyntacticFeature/SemanticFeature",
    },
    {
        "type": "CONTRADICTS",
        "from": "Evidence",
        "to": "RootCandidate",
        "props": {},
        "note": "also to PatternCandidate/SegCandidate",
    },
    {
        "type": "BECAUSE_OF",
        "from": "Evidence",
        "to": "Governor",
        "props": {},
        "note": "also to Template/Lexeme",
    },
    {
        "type": "APPLIES_TO",
        "from": "Constraint",
        "to": "PatternCandidate",
        "props": {},
        "note": "also to any Candidate or Feature node",
    },
    {
        "type": "EMITTED_BY",
        "from": "Constraint",
        "to": "Governor",
        "props": {},
        "note": "also to Rule/Template/Clause",
    },
    {"type": "EMITS", "from": "Rule", "to": "Evidence", "props": {}},
    {
        "type": "HAS_PRECONDITION",
        "from": "Template",
        "to": "Constraint",
        "props": {},
    },
    {"type": "HAS_OP_HOOK", "from": "Template", "to": "Op", "props": {}},
    {
        "type": "APPLIES_TO_CLASS",
        "from": "Op",
        "to": "RootClass",
        "props": {},
    },
]

# ---------------------------------------------------------------------------
# Minimal kernel (subset sufficient for "four directions")
# ---------------------------------------------------------------------------

MINIMAL_KERNEL_RELS: list[str] = [
    "NEXT",
    "HAS_PART",
    "PART_OF",
    "CANDIDATE_OF",
    "HAS_ROOT_CANDIDATE",
    "HAS_PATTERN_CANDIDATE",
    "SUPPORTS",
    "CONTRADICTS",
    "GOVERNS",
    "DEPENDS_ON",
]

# ---------------------------------------------------------------------------
# Cypher constraints / indexes for Neo4j
# ---------------------------------------------------------------------------

CYPHER_SETUP: list[str] = [
    "CREATE CONSTRAINT doc_id IF NOT EXISTS FOR (d:Document) REQUIRE d.doc_id IS UNIQUE;",
    "CREATE CONSTRAINT sent_id IF NOT EXISTS FOR (s:Sentence) REQUIRE s.sent_id IS UNIQUE;",
    "CREATE CONSTRAINT tok_id IF NOT EXISTS FOR (t:Token) REQUIRE t.tok_id IS UNIQUE;",
    "CREATE CONSTRAINT root_key IF NOT EXISTS FOR (r:Root) REQUIRE r.root IS UNIQUE;",
    "CREATE CONSTRAINT pat_key IF NOT EXISTS FOR (p:Pattern) REQUIRE p.pattern IS UNIQUE;",
    "CREATE CONSTRAINT tmpl_key IF NOT EXISTS FOR (t:Template) REQUIRE t.template_id IS UNIQUE;",
    "CREATE CONSTRAINT rule_key IF NOT EXISTS FOR (r:Rule) REQUIRE r.rule_id IS UNIQUE;",
    "CREATE CONSTRAINT op_key IF NOT EXISTS FOR (o:Op) REQUIRE o.op_id IS UNIQUE;",
    "CREATE CONSTRAINT lexeme_key IF NOT EXISTS FOR (l:Lexeme) REQUIRE (l.lemma, l.pos) IS UNIQUE;",
    "CREATE INDEX token_surface IF NOT EXISTS FOR (t:Token) ON (t.surface);",
    "CREATE INDEX lexeme_lemma IF NOT EXISTS FOR (l:Lexeme) ON (l.lemma);",
    "CREATE INDEX stem_surface IF NOT EXISTS FOR (s:Stem) ON (s.stem_surface);",
]


def export_schema() -> dict[str, Any]:
    """Return the complete schema as a JSON-serialisable dict."""
    return {
        "version": "1.0",
        "engine": "nahda-arabic-fractal",
        "labels": LABELS,
        "relationships": RELATIONSHIPS,
        "minimal_kernel_relationships": MINIMAL_KERNEL_RELS,
        "cypher_setup": CYPHER_SETUP,
        "label_count": len({lbl["label"] for lbl in LABELS}),
        "relationship_type_count": len({r["type"] for r in RELATIONSHIPS}),
    }
