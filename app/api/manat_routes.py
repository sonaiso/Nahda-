from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import ManatApplyMetrics
from app.schemas.analysis import ManatApplyRequest
from app.schemas.analysis import ManatApplyResponse
from app.services.manat_pipeline import run_manat_apply_pipeline

router = APIRouter()


@router.post("/manat/apply", response_model=ManatApplyResponse)
def manat_apply(payload: ManatApplyRequest, db: Session = Depends(get_db)) -> ManatApplyResponse:
    result = run_manat_apply_pipeline(
        db=db,
        text=payload.text,
        case_features=[feature.model_dump() for feature in payload.case_features],
        external_case_id=payload.external_case_id,
        description=payload.description,
    )
    return ManatApplyResponse(
        run_id=result.run_id,
        case_id=result.case_id,
        manat=result.manat,
        tanzil_decisions=result.tanzil_decisions,
        metrics=ManatApplyMetrics(
            rule_evaluated_count=result.rule_evaluated_count,
            applies_true_count=result.applies_true_count,
            applies_false_count=result.applies_false_count,
            suspend_count=result.suspend_count,
        ),
    )
