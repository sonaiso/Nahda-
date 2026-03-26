"""Pydantic schemas for the graph analysis API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class GraphAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class EvidenceOut(BaseModel):
    ev_id: str
    source_layer: str
    rule_id: str
    feature: str
    value: str
    weight: float
    polarity: str
    explanation: str


class RootCandidateOut(BaseModel):
    root: str
    score: float
    rank: int
    method: str


class PatternCandidateOut(BaseModel):
    template_id: str
    pattern: str
    derivation_type: str
    score: float
    rank: int
    method: str


class SegCandidateOut(BaseModel):
    seg_id: str
    path_rank: int
    score: float
    method: str
    segments: list[str]


class GraphTokenOut(BaseModel):
    token_id: str
    surface: str
    norm: str
    tok_index: int
    stem_surface: str
    augmentations: list[str]
    root_candidates: list[RootCandidateOut]
    pattern_candidates: list[PatternCandidateOut]
    seg_candidate: SegCandidateOut
    evidence: list[EvidenceOut]


class GraphAnalysisMetrics(BaseModel):
    token_count: int
    triliteral_ratio: float
    evidence_count: int
    root_candidate_count: int
    pattern_candidate_count: int


class GraphAnalyzeResponse(BaseModel):
    run_id: str
    normalized_text: str
    tokens: list[GraphTokenOut]
    metrics: GraphAnalysisMetrics


# ── Schema export ─────────────────────────────────────────────────────────────

class SchemaLabelOut(BaseModel):
    label: str
    layer: str
    properties: dict[str, str]
    constraints: list[dict[str, Any]]
    indexes: list[dict[str, str]] = Field(default_factory=list)


class SchemaRelationshipOut(BaseModel):
    type: str
    from_label: str = Field(alias="from")
    to_label: str = Field(alias="to")
    props: dict[str, str]
    note: str = ""

    model_config = {"populate_by_name": True}


class GraphSchemaResponse(BaseModel):
    version: str
    engine: str
    label_count: int
    relationship_type_count: int
    labels: list[dict[str, Any]]
    relationships: list[dict[str, Any]]
    minimal_kernel_relationships: list[str]
    cypher_setup: list[str]


# ── Templates export ──────────────────────────────────────────────────────────

class TemplateOut(BaseModel):
    template_id: str
    surface_pattern: str
    slots: str
    level: str
    verb_form: str | None
    derivation_type: str
    op_hooks: list[str]
    constraints: list[dict[str, str]]
    example: str


class OpOut(BaseModel):
    op_id: str
    op_type: str
    priority: int
    applies_to_classes: list[str]
    description: str


class RootClassOut(BaseModel):
    class_name: str
    description: str


class GraphTemplatesResponse(BaseModel):
    template_count: int
    op_count: int
    root_class_count: int
    templates: list[TemplateOut]
    ops: list[OpOut]
    root_classes: list[RootClassOut]
