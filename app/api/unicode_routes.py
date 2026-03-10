from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest
from app.schemas.analysis import UnicodeAnalyzeResponse
from app.schemas.analysis import UnicodeMetrics
from app.services.unicode_pipeline import run_unicode_pipeline

router = APIRouter()


@router.post("/analyze/unicode", response_model=UnicodeAnalyzeResponse)
def analyze_unicode(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> UnicodeAnalyzeResponse:
    result = run_unicode_pipeline(db=db, text=payload.text)
    ratio = (result.changed_characters / result.input_length) if result.input_length else 0.0
    return UnicodeAnalyzeResponse(
        run_id=result.run_id,
        unicode=result.scalars,
        normalized_text=result.normalized_text,
        metrics=UnicodeMetrics(
            input_length=result.input_length,
            normalized_length=result.normalized_length,
            changed_characters=result.changed_characters,
            normalization_ratio=round(ratio, 4),
        ),
    )
