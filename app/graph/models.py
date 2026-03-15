"""
Graph Schema Node Models for Arabic Fractal Engine.

Each table represents a node label in the semantic graph.
Edges are captured via:
  - direct FK columns (for typed, frequent relationships)
  - GraphEdge table (for generic relationships with properties)

Layers (A–H) map to the problem specification:
  A) Text:      Sentence, Token
  B) Graphemic: Grapheme, Diacritic
  C) Phonology: Phoneme
  D) Morphemes: MorphemeLattice, Morpheme, Stem, Clitic
  E) Morphology: Root, RootClass, Pattern, Template, DerivationType, Lexeme
                 + Candidates: RootCandidate, PatternCandidate, SegCandidate
  F) Syntax:    Governor, Phrase, Clause, SyntacticFeature, DependencyEdge
  G) Semantics: Sense, SemanticFeature, Reference, SpeechAct
  H) Conceptual: Concept, RelationConcept, Norm, Illa
  Core: Evidence, Constraint, Rule, Op
"""

from __future__ import annotations

import uuid

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# A) Text layer
# ---------------------------------------------------------------------------

class GToken(Base):
    """Token node – one orthographic word in a sentence."""

    __tablename__ = "g_tokens"
    __table_args__ = (UniqueConstraint("run_id", "tok_index", name="uq_gtoken_run_idx"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    surface: Mapped[str] = mapped_column(String(256), index=True)
    norm: Mapped[str] = mapped_column(String(256))
    tok_index: Mapped[int] = mapped_column(Integer, index=True)
    is_punct: Mapped[bool] = mapped_column(Boolean, default=False)
    prev_token_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_token_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


# ---------------------------------------------------------------------------
# B) Graphemic layer
# ---------------------------------------------------------------------------

class Diacritic(Base):
    """Diacritic mark attached to a grapheme."""

    __tablename__ = "g_diacritics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    grapheme_id: Mapped[str] = mapped_column(
        ForeignKey("grapheme_units.id", ondelete="CASCADE"), index=True
    )
    mark: Mapped[str] = mapped_column(String(32))
    position: Mapped[int] = mapped_column(Integer, default=0)


# ---------------------------------------------------------------------------
# D) Morpheme layer
# ---------------------------------------------------------------------------

class MorphemeLattice(Base):
    """Ambiguity lattice holding multiple segmentation paths for one token."""

    __tablename__ = "g_morpheme_lattices"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    token_id: Mapped[str] = mapped_column(
        ForeignKey("g_tokens.id", ondelete="CASCADE"), index=True
    )


class Morpheme(Base):
    """One morpheme segment on a lattice path."""

    __tablename__ = "g_morphemes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lattice_id: Mapped[str] = mapped_column(
        ForeignKey("g_morpheme_lattices.id", ondelete="CASCADE"), index=True
    )
    form: Mapped[str] = mapped_column(String(128))
    morph_type: Mapped[str] = mapped_column(
        String(24), index=True
    )  # prefix/suffix/stem/clitic
    gloss: Mapped[str] = mapped_column(String(128), default="")
    path_rank: Mapped[int] = mapped_column(Integer, default=1)
    prev_morpheme_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_morpheme_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class Stem(Base):
    """Stem extracted from a morpheme of type 'stem'."""

    __tablename__ = "g_stems"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    morpheme_id: Mapped[str] = mapped_column(
        ForeignKey("g_morphemes.id", ondelete="CASCADE"), index=True
    )
    stem_surface: Mapped[str] = mapped_column(String(128), index=True)


# ---------------------------------------------------------------------------
# E) Morphology: Root / Pattern / Template / Derivation
# ---------------------------------------------------------------------------

class RootClass(Base):
    """Root class (weak1/weak2/hamzated/doubled/sound …)."""

    __tablename__ = "g_root_classes"
    __table_args__ = (UniqueConstraint("class_name", name="uq_root_class_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    class_name: Mapped[str] = mapped_column(String(48), index=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Root(Base):
    """Arabic root (radicals + class)."""

    __tablename__ = "g_roots"
    __table_args__ = (UniqueConstraint("root", name="uq_root"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    root: Mapped[str] = mapped_column(String(16), index=True)
    radicals_count: Mapped[int] = mapped_column(Integer, default=3)
    root_class_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_root_classes.id", ondelete="SET NULL"), nullable=True, index=True
    )


class Pattern(Base):
    """Morphological pattern (وزن) e.g. فَاعِل, مَفْعُول."""

    __tablename__ = "g_patterns"
    __table_args__ = (UniqueConstraint("pattern", name="uq_pattern"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    pattern: Mapped[str] = mapped_column(String(64), index=True)
    slots: Mapped[str] = mapped_column(String(64), default="F,A,L")


class Template(Base):
    """Surface template realising a pattern (with optional Op hooks)."""

    __tablename__ = "g_templates"
    __table_args__ = (UniqueConstraint("template_id", name="uq_template_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    template_id: Mapped[str] = mapped_column(String(64), index=True)
    surface_pattern: Mapped[str] = mapped_column(String(128))
    slots: Mapped[str] = mapped_column(String(64), default="F,A,L")
    level: Mapped[str] = mapped_column(String(32), default="triliteral")
    verb_form: Mapped[str | None] = mapped_column(String(8), nullable=True)
    pattern_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_patterns.id", ondelete="SET NULL"), nullable=True, index=True
    )


class DerivationType(Base):
    """Semantic derivation type (Agent/Patient/Masdar/Instrument …)."""

    __tablename__ = "g_derivation_types"
    __table_args__ = (UniqueConstraint("name", name="uq_deriv_name"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(64), index=True)
    family: Mapped[str] = mapped_column(String(32), default="noun")
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )


class Lexeme(Base):
    """Lexeme – lemma with POS and register."""

    __tablename__ = "g_lexemes"
    __table_args__ = (UniqueConstraint("lemma", "pos", name="uq_lexeme_lemma_pos"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lemma: Mapped[str] = mapped_column(String(256), index=True)
    pos: Mapped[str] = mapped_column(String(24), index=True)
    is_jamid: Mapped[bool] = mapped_column(Boolean, default=False)
    register: Mapped[str] = mapped_column(String(32), default="fus7a")
    root_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_roots.id", ondelete="SET NULL"), nullable=True, index=True
    )


# ---------------------------------------------------------------------------
# Candidates (per analysis run)
# ---------------------------------------------------------------------------

class RootCandidate(Base):
    """Root analysis candidate with score for a specific Stem."""

    __tablename__ = "g_root_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stem_id: Mapped[str] = mapped_column(
        ForeignKey("g_stems.id", ondelete="CASCADE"), index=True
    )
    root_id: Mapped[str] = mapped_column(
        ForeignKey("g_roots.id", ondelete="CASCADE"), index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.5)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    method: Mapped[str] = mapped_column(String(48), default="consonant_extract")


class PatternCandidate(Base):
    """Pattern analysis candidate for a specific Stem."""

    __tablename__ = "g_pattern_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    stem_id: Mapped[str] = mapped_column(
        ForeignKey("g_stems.id", ondelete="CASCADE"), index=True
    )
    pattern_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_patterns.id", ondelete="SET NULL"), nullable=True, index=True
    )
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_templates.id", ondelete="SET NULL"), nullable=True, index=True
    )
    score: Mapped[float] = mapped_column(Float, default=0.5)
    rank: Mapped[int] = mapped_column(Integer, default=1)
    method: Mapped[str] = mapped_column(String(48), default="template_match")
    alignment_json: Mapped[dict] = mapped_column(JSON, default=dict)


class SegCandidate(Base):
    """Segmentation candidate path on a MorphemeLattice."""

    __tablename__ = "g_seg_candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lattice_id: Mapped[str] = mapped_column(
        ForeignKey("g_morpheme_lattices.id", ondelete="CASCADE"), index=True
    )
    path_rank: Mapped[int] = mapped_column(Integer, default=1)
    score: Mapped[float] = mapped_column(Float, default=0.5)
    method: Mapped[str] = mapped_column(String(48), default="rule_based")
    segments_json: Mapped[list] = mapped_column(JSON, default=list)


# ---------------------------------------------------------------------------
# F) Syntax
# ---------------------------------------------------------------------------

class Governor(Base):
    """Syntactic governor (عامل) that induces case/mood."""

    __tablename__ = "g_governors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    token_id: Mapped[str] = mapped_column(
        ForeignKey("g_tokens.id", ondelete="CASCADE"), index=True
    )
    gov_type: Mapped[str] = mapped_column(
        String(32), index=True
    )  # jar/nasib/jazim/kana/inna/verb
    strength: Mapped[str] = mapped_column(String(16), default="strong")


class SyntacticFeature(Base):
    """Syntactic feature (case/mood/role/agreement …)."""

    __tablename__ = "g_syntactic_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    token_id: Mapped[str] = mapped_column(
        ForeignKey("g_tokens.id", ondelete="CASCADE"), index=True
    )
    feature_name: Mapped[str] = mapped_column(String(48), index=True)
    feature_value: Mapped[str] = mapped_column(String(64))
    source: Mapped[str] = mapped_column(String(48), default="governor")


# ---------------------------------------------------------------------------
# G) Semantics
# ---------------------------------------------------------------------------

class Sense(Base):
    """Lexical sense associated with a Lexeme."""

    __tablename__ = "g_senses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    lexeme_id: Mapped[str] = mapped_column(
        ForeignKey("g_lexemes.id", ondelete="CASCADE"), index=True
    )
    gloss: Mapped[str] = mapped_column(String(512))
    domain: Mapped[str] = mapped_column(String(64), default="general")
    priority: Mapped[int] = mapped_column(Integer, default=1)


class SemanticFeature(Base):
    """Semantic feature on a Token (mutabaqa/tadammun/iltizam, haqiqa/majaz …)."""

    __tablename__ = "g_semantic_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    token_id: Mapped[str] = mapped_column(
        ForeignKey("g_tokens.id", ondelete="CASCADE"), index=True
    )
    dalala: Mapped[str] = mapped_column(
        String(24), default="mutabaqa"
    )  # mutabaqa/tadammun/iltizam
    truth: Mapped[str] = mapped_column(String(16), default="haqiqa")  # haqiqa/majaz
    scope: Mapped[str] = mapped_column(String(16), default="khas")  # amm/khas
    restriction: Mapped[str] = mapped_column(String(16), default="mutlaq")  # mutlaq/muqayyad


# ---------------------------------------------------------------------------
# H) Conceptual / Normative
# ---------------------------------------------------------------------------

class Concept(Base):
    """Conceptual node (kulli/juz'i)."""

    __tablename__ = "g_concepts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(256), index=True)
    level: Mapped[str] = mapped_column(String(16), default="kulli")  # kulli/juz'i


class Norm(Base):
    """Normative node (wajib/haram/mubah …)."""

    __tablename__ = "g_norms"
    __table_args__ = (
        CheckConstraint(
            "norm_type IN ('wajib','mandub','mubah','makruh','haram','hukm')",
            name="ck_norm_type",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    norm_type: Mapped[str] = mapped_column(String(16), default="hukm")
    source_scope: Mapped[str] = mapped_column(String(64), default="")


class Illa(Base):
    """Illa/Condition/Mani' node for reasoning."""

    __tablename__ = "g_illas"
    __table_args__ = (
        CheckConstraint("kind IN ('illa','shart','mani')", name="ck_illa_kind"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(8), default="illa")  # illa/shart/mani
    pattern: Mapped[str] = mapped_column(String(256), default="")


# ---------------------------------------------------------------------------
# Core: Evidence + Constraint + Rule + Op
# ---------------------------------------------------------------------------

class Evidence(Base):
    """Evidence node supporting/contradicting a candidate or feature."""

    __tablename__ = "g_evidences"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(
        ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True
    )
    source_layer: Mapped[str] = mapped_column(String(32), index=True)
    rule_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    feature: Mapped[str] = mapped_column(String(64))
    value: Mapped[str] = mapped_column(String(256))
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    polarity: Mapped[str] = mapped_column(
        String(16), default="supports"
    )  # supports/contradicts
    explanation: Mapped[str] = mapped_column(Text, default="")
    # target node reference (flexible: any candidate / feature node id)
    target_node_type: Mapped[str] = mapped_column(String(48), default="")
    target_node_id: Mapped[str] = mapped_column(String(36), index=True, default="")


class Constraint(Base):
    """Constraint that must be satisfied by a candidate or feature node."""

    __tablename__ = "g_constraints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    template_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_templates.id", ondelete="CASCADE"), nullable=True, index=True
    )
    feature: Mapped[str] = mapped_column(String(64))
    required_value: Mapped[str] = mapped_column(String(256))
    penalty: Mapped[float] = mapped_column(Float, default=1.0)
    scope: Mapped[str] = mapped_column(String(16), default="token")  # token/stem/clause
    emitter_type: Mapped[str] = mapped_column(String(32), default="template")
    emitter_id: Mapped[str] = mapped_column(String(64), default="")


class Rule(Base):
    """Linguistic rule that emits Evidence."""

    __tablename__ = "g_rules"
    __table_args__ = (UniqueConstraint("rule_id", name="uq_g_rule_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    rule_id: Mapped[str] = mapped_column(String(64), index=True)
    layer: Mapped[str] = mapped_column(String(32), index=True)
    description: Mapped[str] = mapped_column(Text, default="")


class Op(Base):
    """Phonological operation (إعلال/إدغام/همزة/حذف/إبدال)."""

    __tablename__ = "g_ops"
    __table_args__ = (UniqueConstraint("op_id", name="uq_g_op_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    op_id: Mapped[str] = mapped_column(String(64), index=True)
    op_type: Mapped[str] = mapped_column(
        String(32), index=True
    )  # i3lal/idgham/hamza/hathf/ibdal
    priority: Mapped[int] = mapped_column(Integer, default=0)
    root_class_id: Mapped[str | None] = mapped_column(
        ForeignKey("g_root_classes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    description: Mapped[str] = mapped_column(Text, default="")


# ---------------------------------------------------------------------------
# Generic Graph Edge (for flexible relationships)
# ---------------------------------------------------------------------------

class GraphEdge(Base):
    """
    Generic directed edge between any two graph nodes.

    rel_type mirrors Neo4j relationship types:
      NEXT, HAS_PART, PART_OF, CANDIDATE_OF, SUPPORTS, CONTRADICTS,
      GOVERNS, DEPENDS_ON, HAS_ROOT_CANDIDATE, HAS_PATTERN_CANDIDATE,
      REALIZED_BY, MATCHES_TEMPLATE, HAS_OP_HOOK, …
    """

    __tablename__ = "g_edges"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    run_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    src_label: Mapped[str] = mapped_column(String(48), index=True)
    src_id: Mapped[str] = mapped_column(String(36), index=True)
    rel_type: Mapped[str] = mapped_column(String(64), index=True)
    dst_label: Mapped[str] = mapped_column(String(48), index=True)
    dst_id: Mapped[str] = mapped_column(String(36), index=True)
    props_json: Mapped[dict] = mapped_column(JSON, default=dict)
