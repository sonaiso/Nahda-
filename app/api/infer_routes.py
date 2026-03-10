from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest
from app.schemas.analysis import InferMetrics
from app.schemas.analysis import InferResponse
from app.services.inference_pipeline import run_inference_pipeline

router = APIRouter()


@router.post("/infer", response_model=InferResponse)
def infer(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> InferResponse:
    result = run_inference_pipeline(db=db, text=payload.text)
    return InferResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        inference=result.inference,
        metrics=InferMetrics(
            speech_count=result.speech_count,
            inference_count=result.inference_count,
            mafhum_item_count=result.mafhum_item_count,
            avg_inference_confidence=round(result.avg_inference_confidence, 4),
        ),
    )
