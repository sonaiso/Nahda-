from __future__ import annotations

from fastapi import APIRouter

from app.schemas.axiomatic import AxiomAnalyzeResponse
from app.schemas.axiomatic import AxiomMetrics
from app.schemas.axiomatic import AxiomRequest
from app.schemas.axiomatic import FalsifyResponse
from app.services.axiomatic_engine import run_axiomatic_engine

router = APIRouter(prefix="/axiomatic")


@router.post("/analyze", response_model=AxiomAnalyzeResponse)
def axiomatic_analyze(payload: AxiomRequest) -> AxiomAnalyzeResponse:
    """Run the full axiomatic analysis (A1–A20, Lemmas L1–L5, Theorems T1–T5)."""
    result = run_axiomatic_engine(payload.text)
    return AxiomAnalyzeResponse(
        text=result.text,
        tokens=result.tokens,
        axioms=[
            {"code": a.code, "name": a.name, "satisfied": a.satisfied, "evidence": a.evidence}
            for a in result.axioms
        ],
        lemmas=[
            {
                "code": lm.code,
                "name": lm.name,
                "derived_from": lm.derived_from,
                "holds": lm.holds,
                "rationale": lm.rationale,
            }
            for lm in result.lemmas
        ],
        theorems=[
            {
                "code": th.code,
                "name": th.name,
                "depends_on": th.depends_on,
                "proven": th.proven,
                "rationale": th.rationale,
            }
            for th in result.theorems
        ],
        falsifications=[
            {
                "code": f.code,
                "name": f.name,
                "score": f.score,
                "threshold": f.threshold,
                "falsified": f.falsified,
                "details": f.details,
            }
            for f in result.falsifications
        ],
        metrics=AxiomMetrics(
            axiom_satisfaction_ratio=result.axiom_satisfaction_ratio,
            lemma_hold_ratio=result.lemma_hold_ratio,
            theorem_proven_ratio=result.theorem_proven_ratio,
            system_coherent=result.system_coherent,
        ),
    )


@router.post("/falsify", response_model=FalsifyResponse)
def axiomatic_falsify(payload: AxiomRequest) -> FalsifyResponse:
    """Run only the five falsification tests (F1–F5) against the given text."""
    result = run_axiomatic_engine(payload.text)
    return FalsifyResponse(
        text=result.text,
        falsifications=[
            {
                "code": f.code,
                "name": f.name,
                "score": f.score,
                "threshold": f.threshold,
                "falsified": f.falsified,
                "details": f.details,
            }
            for f in result.falsifications
        ],
        any_falsified=any(f.falsified for f in result.falsifications),
    )
