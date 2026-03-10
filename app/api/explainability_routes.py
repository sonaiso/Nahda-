from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import ExplainResponse
from app.schemas.analysis import TraceResponse
from app.services.explainability_service import get_explain
from app.services.explainability_service import get_trace

router = APIRouter()


@router.get("/explain/{run_id}", response_model=ExplainResponse)
def explain(run_id: str, db: Session = Depends(get_db)) -> ExplainResponse:
    payload = get_explain(db=db, run_id=run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="run_id not found")
    return ExplainResponse(**payload)


@router.get("/trace/{run_id}", response_model=TraceResponse)
def trace(run_id: str, db: Session = Depends(get_db)) -> TraceResponse:
    payload = get_trace(db=db, run_id=run_id)
    if not payload:
        raise HTTPException(status_code=404, detail="run_id not found")
    return TraceResponse(**payload)
