from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.tracing import start_span
from app.db.session import get_db
from app.schemas.analysis import QiyasMetrics
from app.schemas.analysis import QiyasRequest
from app.schemas.analysis import QiyasResponse
from app.schemas.analysis import QiyasDaalLinkOut
from app.schemas.analysis import QiyasTransferOut
from app.services.qiyas_pipeline import DaalType
from app.services.qiyas_pipeline import QiyasTransferInput
from app.services.qiyas_pipeline import run_qiyas_pipeline

router = APIRouter(prefix="/qiyas")


@router.post("/transfer", response_model=QiyasResponse)
def qiyas_transfer(payload: QiyasRequest, db: Session = Depends(get_db)) -> QiyasResponse:
    """Execute one or more Qiyas (analogical) transfers.

    Each transfer maps a judgment (Hukm) from a source case (Asl) to a new
    case (Far) via an effective cause (Illa).  The ``daal_type`` field must be
    one of the canonical ``DaalType`` values:
    ``mutabaqa``, ``tadammun``, ``iltizam``, ``nass``, ``zahir``, ``mafhum``.
    """
    try:
        transfer_inputs = [
            QiyasTransferInput(
                asl_text=t.asl_text,
                asl_judgment=t.asl_judgment,
                far_text=t.far_text,
                illa_description=t.illa_description,
                daal_type=DaalType(t.daal_type),
                evidence=[{"text": e.text, "source": e.source, "strength": e.strength} for e in t.evidence],
            )
            for t in payload.transfers
        ]
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    with start_span("pipeline.qiyas_transfer", {"nahda.layer": "Qiyas"}):
        result = run_qiyas_pipeline(db=db, text=payload.text, transfers=transfer_inputs)

    return QiyasResponse(
        run_id=result.run_id,
        normalized_text=result.normalized_text,
        transfers=[
            QiyasTransferOut(
                qiyas_id=t.qiyas_id,
                asl_text=t.asl_text,
                asl_judgment=t.asl_judgment,
                far_text=t.far_text,
                illa_description=t.illa_description,
                daal_type=t.daal_type,
                transferred_judgment=t.transferred_judgment,
                transfer_state=t.transfer_state,
                rationale=t.rationale,
                confidence_score=t.confidence_score,
                daal_links=[
                    QiyasDaalLinkOut(
                        evidence_text=lnk["evidence_text"],
                        evidence_source=lnk["evidence_source"],
                        strength=lnk["strength"],
                    )
                    for lnk in t.daal_links
                ],
            )
            for t in result.transfers
        ],
        metrics=QiyasMetrics(
            transfer_count=len(result.transfers),
            valid_count=result.valid_count,
            invalid_count=result.invalid_count,
            suspend_count=result.suspend_count,
            avg_confidence=result.avg_confidence,
        ),
    )
