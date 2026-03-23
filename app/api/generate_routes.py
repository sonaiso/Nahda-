"""
Backward generation API routes.

POST /generate/backward  – given a target meaning, generate ranked Arabic text
                           candidates with round-trip verification.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.tracing import start_span
from app.db.session import get_db
from app.schemas.analysis import (
    GenerateBackwardResponse,
    GenerationBranchOut,
    GenerateMetrics,
    GenerateRequest,
)
from app.services.generate_backward_pipeline import run_generate_backward_pipeline

router = APIRouter(prefix="/generate")


@router.post("/backward", response_model=GenerateBackwardResponse)
def generate_backward(
    payload: GenerateRequest, db: Session = Depends(get_db)
) -> GenerateBackwardResponse:
    """
    Backward generation pipeline (GENERATE_BACKWARD).

    Accepts a target meaning expressed as Arabic text and returns ranked
    candidate Arabic sentences.  Each candidate is verified by round-tripping
    through the forward analysis pipeline to confirm semantic equivalence.
    """
    with start_span("pipeline.generate_backward", {"nahda.layer": "G0-G9"}):
        result = run_generate_backward_pipeline(db=db, target_meaning=payload.meaning)

    return GenerateBackwardResponse(
        run_id=result.run_id,
        target_meaning=result.target_meaning,
        top_text=result.top_text,
        branches=[
            GenerationBranchOut(
                text=b["text"],
                score=b["score"],
                verified=b["verified"],
                rank=b["rank"],
            )
            for b in result.branches
        ],
        metrics=GenerateMetrics(
            branch_count=result.branch_count,
            verified_count=result.verified_count,
            top_score=result.top_score,
        ),
    )
