from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.tracing import start_span
from app.db.session import get_db
from app.schemas.analysis import AwarenessApplyRequest
from app.schemas.analysis import AwarenessApplyResponse
from app.services.awareness_pipeline import run_awareness_pipeline

router = APIRouter(prefix="/awareness")


@router.post("/apply", response_model=AwarenessApplyResponse)
def awareness_apply(payload: AwarenessApplyRequest, db: Session = Depends(get_db)) -> AwarenessApplyResponse:
    with start_span("pipeline.awareness_apply", {"nahda.layer": "L15-L19"}):
        result = run_awareness_pipeline(db=db, run_id=payload.run_id)

    if not result:
        raise HTTPException(status_code=404, detail="run_id not found or missing manat artifacts")

    return AwarenessApplyResponse(
        run_id=result.run_id,
        concept=result.concept,
        scale=result.scale,
        spirit=result.spirit,
        inclination=result.inclination,
        will=result.will,
        metrics=result.metrics,
    )
