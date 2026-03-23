"""API routes for the bidirectional Arabic language engine.

Exposes:
  POST /bidirectional/analyze  – Forward function A: text  → MeaningStructure
  POST /bidirectional/generate – Backward function G: meaning → text
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.tracing import start_span
from app.db.session import get_db
from app.schemas.bidirectional import (
    BidirectionalAnalyzeRequest,
    BidirectionalAnalyzeResponse,
    BidirectionalAnalyzeMetrics,
    BidirectionalGenerateRequest,
    BidirectionalGenerateResponse,
    ConstructionNetworkOut,
    GateTraceOut,
    MeaningStructureOut,
)
from app.services.bidirectional_engine import run_analyze_forward, run_generate_backward

router = APIRouter()


@router.post("/bidirectional/analyze", response_model=BidirectionalAnalyzeResponse)
def bidirectional_analyze(
    payload: BidirectionalAnalyzeRequest,
    db: Session = Depends(get_db),
) -> BidirectionalAnalyzeResponse:
    """Forward analysis: text (L0) → MeaningStructure (L8).

    Runs the full 9-layer gate pipeline and returns structured output for
    every layer (UnicodeAtom … MeaningStructure) together with a proof trace.
    """
    with start_span("pipeline.bidirectional.analyze", {"nahda.layer": "L0-L8"}):
        result = run_analyze_forward(db=db, text=payload.text)

    cn_raw = result.construction_network
    cn_out = ConstructionNetworkOut(
        id=cn_raw.get("id", 0),
        lexeme_count=cn_raw.get("lexeme_count", 0),
        predication_relations=cn_raw.get("predication_relations", []),
        inclusion_relations=cn_raw.get("inclusion_relations", []),
        restriction_relations=cn_raw.get("restriction_relations", []),
        case_values=cn_raw.get("case_values", {}),
    )

    ms_raw = result.meaning_structure
    ms_out: MeaningStructureOut | None = None
    if ms_raw:
        ms_out = MeaningStructureOut(
            id=ms_raw.get("id", 0),
            entities=ms_raw.get("entities", []),
            events=ms_raw.get("events", []),
            qualities=ms_raw.get("qualities", []),
            relations=ms_raw.get("relations", []),
            universal_meanings=ms_raw.get("universal_meanings", []),
            particulars=ms_raw.get("particulars", []),
            entailments=ms_raw.get("entailments", []),
        )

    trace_raw = result.trace
    trace_out = GateTraceOut(
        steps=trace_raw.get("steps", []),
        contradictions=trace_raw.get("contradictions", []),
        score=trace_raw.get("score", 1.0),
    )

    entity_count = len(ms_raw.get("entities", [])) if ms_raw else 0
    event_count = len(ms_raw.get("events", [])) if ms_raw else 0
    relation_count = len(ms_raw.get("relations", [])) if ms_raw else 0

    metrics = BidirectionalAnalyzeMetrics(
        atom_count=len(result.unicode_atoms),
        functional_unit_count=len(result.functional_units),
        ils_count=len(result.intra_lexeme_structures),
        syllable_count=len(result.syllable_circuits),
        lexeme_count=len(result.lexemes),
        relation_count=relation_count,
        entity_count=entity_count,
        event_count=event_count,
        gate_score=trace_out.score,
    )

    return BidirectionalAnalyzeResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        unicode_atoms=result.unicode_atoms,
        functional_units=result.functional_units,
        intra_lexeme_structures=result.intra_lexeme_structures,
        syllable_circuits=result.syllable_circuits,
        root_patterns=result.root_patterns,
        lexemes=result.lexemes,
        construction_network=cn_out,
        meaning_structure=ms_out,
        trace=trace_out,
        valid=result.valid,
        metrics=metrics,
    )


@router.post("/bidirectional/generate", response_model=BidirectionalGenerateResponse)
def bidirectional_generate(payload: BidirectionalGenerateRequest) -> BidirectionalGenerateResponse:
    """Backward generation: MeaningStructure (L8) → Arabic text (L0).

    Accepts a meaning structure (entities, events, qualities, relations) and
    generates candidate Arabic surface forms, returning the best-ranked form.
    """
    with start_span("pipeline.bidirectional.generate", {"nahda.layer": "L8-L0"}):
        meaning_dict = payload.model_dump()
        result = run_generate_backward(meaning_dict)

    trace_out = GateTraceOut(
        steps=result.trace.get("steps", []),
        contradictions=result.trace.get("contradictions", []),
        score=result.trace.get("score", 1.0),
    )

    return BidirectionalGenerateResponse(
        generated_text=result.generated_text,
        candidate_forms=result.candidate_forms,
        trace=trace_out,
        valid=result.valid,
    )
