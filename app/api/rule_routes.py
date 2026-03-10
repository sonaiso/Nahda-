from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest
from app.schemas.analysis import RuleEvaluateMetrics
from app.schemas.analysis import RuleEvaluateResponse
from app.services.rule_pipeline import run_rule_evaluation_pipeline

router = APIRouter()


@router.post("/rule/evaluate", response_model=RuleEvaluateResponse)
def rule_evaluate(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> RuleEvaluateResponse:
    result = run_rule_evaluation_pipeline(db=db, text=payload.text)
    return RuleEvaluateResponse(
        run_id=result.run_id,
        rules=result.rules,
        conflicts=result.conflicts,
        tarjih_decisions=result.tarjih_decisions,
        metrics=RuleEvaluateMetrics(
            rule_count=result.rule_count,
            conflict_count=result.conflict_count,
            resolved_conflict_count=result.resolved_conflict_count,
            avg_rule_confidence=round(result.avg_rule_confidence, 4),
        ),
    )
