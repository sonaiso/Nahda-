from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest
from app.schemas.analysis import SemanticsAnalyzeResponse
from app.schemas.analysis import SemanticsMetrics
from app.core.tracing import start_span
from app.services.semantics_pipeline import run_semantics_pipeline

router = APIRouter()


@router.post("/analyze/semantics", response_model=SemanticsAnalyzeResponse)
def analyze_semantics(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> SemanticsAnalyzeResponse:
    with start_span("pipeline.semantics", {"nahda.layer": "L5-L8"}):
        result = run_semantics_pipeline(db=db, text=payload.text)
    return SemanticsAnalyzeResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        lexemes=result.lexemes,
        meaning_registry=result.meaning_registry,
        indications=result.indications,
        relations=result.relations,
        metrics=SemanticsMetrics(
            lexeme_count=result.lexeme_count,
            independent_lexeme_ratio=round(result.independent_lexeme_ratio, 4),
            indication_coverage_ratio=round(result.indication_coverage_ratio, 4),
            relation_count=result.relation_count,
        ),
    )
