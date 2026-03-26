from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class AxiomRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class AxiomResultOut(BaseModel):
    code: str
    name: str
    satisfied: bool
    evidence: str


class LemmaResultOut(BaseModel):
    code: str
    name: str
    derived_from: list[str]
    holds: bool
    rationale: str


class TheoremResultOut(BaseModel):
    code: str
    name: str
    depends_on: list[str]
    proven: bool
    rationale: str


class FalsificationResultOut(BaseModel):
    code: str
    name: str
    score: float
    threshold: float
    falsified: bool
    details: str


class AxiomMetrics(BaseModel):
    axiom_satisfaction_ratio: float
    lemma_hold_ratio: float
    theorem_proven_ratio: float
    system_coherent: bool


class AxiomAnalyzeResponse(BaseModel):
    text: str
    tokens: list[str]
    axioms: list[AxiomResultOut]
    lemmas: list[LemmaResultOut]
    theorems: list[TheoremResultOut]
    falsifications: list[FalsificationResultOut]
    metrics: AxiomMetrics


class FalsifyResponse(BaseModel):
    text: str
    falsifications: list[FalsificationResultOut]
    any_falsified: bool
