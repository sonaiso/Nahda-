"""Pydantic schemas for the bidirectional language engine endpoints."""
from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


# ── Requests ──────────────────────────────────────────────────────────────────


class BidirectionalAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class EntityIn(BaseModel):
    id: int
    label: str
    entity_type: str = "thing"


class EventIn(BaseModel):
    id: int
    label: str
    agent_id: int | None = None
    patient_id: int | None = None


class QualityIn(BaseModel):
    id: int
    label: str
    target_entity_id: int


class MeaningRelationIn(BaseModel):
    type: str
    source: int
    target: int


class BidirectionalGenerateRequest(BaseModel):
    entities: list[EntityIn] = Field(default_factory=list)
    events: list[EventIn] = Field(default_factory=list)
    qualities: list[QualityIn] = Field(default_factory=list)
    relations: list[MeaningRelationIn] = Field(default_factory=list)
    universal_meanings: list[str] = Field(default_factory=list)
    particulars: list[str] = Field(default_factory=list)
    entailments: list[str] = Field(default_factory=list)


# ── Layer output models ────────────────────────────────────────────────────────


class UnicodeAtomOut(BaseModel):
    id: int
    codepoint: int
    category: str
    combining_class: int


class FunctionalUnitOut(BaseModel):
    id: int
    char: str
    unit_type: str
    role_set: list[str]
    position: int


class IntraLexemeStructureOut(BaseModel):
    id: int
    surface_form: str
    consonantal_skeleton: list[str]
    vocalic_skeleton: list[str]
    augmentations: list[str]


class SyllableCircuitOut(BaseModel):
    id: int
    onset: list[str]
    nucleus: list[str]
    coda: list[str]
    weight: str


class RootOut(BaseModel):
    id: int
    radicals: list[str]
    semantic_field: str
    concept_core: str


class PatternOut(BaseModel):
    id: int
    pattern_name: str
    radical_slots: list[str]
    vowel_slots: list[str]
    affix_slots: list[str]


class RootPatternOut(BaseModel):
    root: RootOut
    pattern: PatternOut


class LexemeNodeOut(BaseModel):
    id: int
    surface_form: str
    pos: str
    lexeme_type: str
    morph_state: str
    definiteness: str
    universality: str
    root_radicals: list[str]


class ConstructionRelationOut(BaseModel):
    type: str
    source: int
    target: int


class ConstructionNetworkOut(BaseModel):
    id: int
    lexeme_count: int
    predication_relations: list[ConstructionRelationOut]
    inclusion_relations: list[ConstructionRelationOut]
    restriction_relations: list[ConstructionRelationOut]
    case_values: dict[str, str]


class EntityOut(BaseModel):
    id: int
    label: str
    entity_type: str


class EventOut(BaseModel):
    id: int
    label: str
    agent_id: int | None
    patient_id: int | None


class QualityOut(BaseModel):
    id: int
    label: str
    target_entity_id: int


class MeaningRelationOut(BaseModel):
    type: str
    source: int
    target: int


class MeaningStructureOut(BaseModel):
    id: int
    entities: list[EntityOut]
    events: list[EventOut]
    qualities: list[QualityOut]
    relations: list[MeaningRelationOut]
    universal_meanings: list[str]
    particulars: list[str]
    entailments: list[str]


class GateTraceOut(BaseModel):
    steps: list[str]
    contradictions: list[str]
    score: float


class BidirectionalAnalyzeMetrics(BaseModel):
    atom_count: int
    functional_unit_count: int
    ils_count: int
    syllable_count: int
    lexeme_count: int
    relation_count: int
    entity_count: int
    event_count: int
    gate_score: float


# ── Responses ─────────────────────────────────────────────────────────────────


class BidirectionalAnalyzeResponse(BaseModel):
    run_id: str
    normalized_text: str
    unicode_atoms: list[UnicodeAtomOut]
    functional_units: list[FunctionalUnitOut]
    intra_lexeme_structures: list[IntraLexemeStructureOut]
    syllable_circuits: list[SyllableCircuitOut]
    root_patterns: list[RootPatternOut]
    lexemes: list[LexemeNodeOut]
    construction_network: ConstructionNetworkOut
    meaning_structure: MeaningStructureOut | None
    trace: GateTraceOut
    valid: bool
    metrics: BidirectionalAnalyzeMetrics


class BidirectionalGenerateResponse(BaseModel):
    generated_text: str
    candidate_forms: list[str]
    trace: GateTraceOut
    valid: bool
