from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analysis import AnalyzeRequest
from app.schemas.analysis import MorphologyAnalyzeResponse
from app.schemas.analysis import MorphologyMetrics
from app.services.morphology_pipeline import run_morphology_pipeline

router = APIRouter()


@router.post("/analyze/morphology", response_model=MorphologyAnalyzeResponse)
def analyze_morphology(payload: AnalyzeRequest, db: Session = Depends(get_db)) -> MorphologyAnalyzeResponse:
    result = run_morphology_pipeline(db=db, text=payload.text)
    avg_syllables = (result.syllable_count / result.token_count) if result.token_count else 0.0
    return MorphologyAnalyzeResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        syllables=result.syllables,
        patterns=result.patterns,
        metrics=MorphologyMetrics(
            token_count=result.token_count,
            syllable_count=result.syllable_count,
            avg_syllables_per_token=round(avg_syllables, 4),
            valid_syllable_ratio=round(result.valid_syllable_ratio, 4),
            triliteral_root_ratio=round(result.triliteral_root_ratio, 4),
        ),
    )
