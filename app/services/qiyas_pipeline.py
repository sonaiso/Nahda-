"""Qiyas (قياس) — Analogical Reasoning Pipeline.

Transfers a known judgment (Hukm) from a source case (Asl) to a target case
(Far) when they share an effective cause (Illa).  The link between Asl and Far
is characterised by a ``DaalType`` that describes *how* the textual indication
operates.

Canonical ``DaalType`` values
------------------------------
mutabaqa  — full congruence between sign and signified
tadammun  — the signified is contained within the sign
iltizam   — the signified is logically entailed by the sign
nass      — explicit scriptural text
zahir     — apparent/probable meaning
mafhum    — implicit understanding (including muwafaqa and mukhalafa)

Design note
-----------
Use **only** ``DaalType`` across all code and documentation.  The aliases
``DaalForm`` and ``DaalFunction`` must not appear; they represent the same
concept under different informal names and were identified as a source of
confusion in the API surface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sqlalchemy.orm import Session

from app.models.entities import LayerExecution
from app.models.entities import PipelineRun
from app.models.entities import QiyasDaalLink
from app.models.entities import QiyasUnit
from app.services.inference_pipeline import run_inference_pipeline


class DaalType(str, Enum):
    """Canonical vocabulary for the indication (دلالة) type used in Qiyas.

    Never use the informal aliases ``DaalForm`` or ``DaalFunction``; this
    single enum is the authoritative source of truth.
    """

    MUTABAQA = "mutabaqa"
    TADAMMUN = "tadammun"
    ILTIZAM = "iltizam"
    NASS = "nass"
    ZAHIR = "zahir"
    MAFHUM = "mafhum"


@dataclass
class QiyasTransferInput:
    """Input description for a single analogical transfer."""

    asl_text: str
    asl_judgment: str
    far_text: str
    illa_description: str
    daal_type: DaalType = DaalType.MUTABAQA
    evidence: list[dict] = field(default_factory=list)


@dataclass
class QiyasTransferResult:
    """Result of a single analogical transfer."""

    qiyas_id: str
    asl_text: str
    asl_judgment: str
    far_text: str
    illa_description: str
    daal_type: str
    transferred_judgment: str
    transfer_state: str
    rationale: str
    confidence_score: float
    daal_links: list[dict]


@dataclass
class QiyasPipelineResult:
    """Aggregate result returned by ``run_qiyas_pipeline``."""

    run_id: str
    normalized_text: str
    transfers: list[QiyasTransferResult]
    valid_count: int
    invalid_count: int
    suspend_count: int
    avg_confidence: float


# ---------------------------------------------------------------------------
# Precondition checks
# ---------------------------------------------------------------------------

_PRECONDITION_WEIGHTS = {
    DaalType.NASS: 0.95,
    DaalType.ZAHIR: 0.80,
    DaalType.MUTABAQA: 0.75,
    DaalType.MAFHUM: 0.70,
    DaalType.TADAMMUN: 0.65,
    DaalType.ILTIZAM: 0.60,
}


def _evaluate_preconditions(transfer: QiyasTransferInput) -> tuple[bool, str, float]:
    """Check whether the transfer can proceed.

    The Illa is the *abstract effective cause* linking Asl to Far; it does not
    need to appear verbatim in either text.  Preconditions are:

    1. ``illa_description`` must be non-empty.
    2. ``asl_judgment`` must be non-empty (checked in ``_execute_transfer``).

    When the Illa tokens are literally traceable in both texts, confidence is
    higher.  When they are implicit (common case for Mafhum transfers) the
    pipeline still proceeds but applies a penalty.

    Returns
    -------
    (passes, rationale, base_confidence)
    """
    if not transfer.illa_description.strip():
        return False, "illa_description is empty; transfer suspended", 0.0

    illa_tokens = {tok.strip() for tok in transfer.illa_description.split() if tok.strip()}
    asl_tokens = set(transfer.asl_text.split())
    far_tokens = set(transfer.far_text.split())

    asl_overlap = illa_tokens & asl_tokens
    far_overlap = illa_tokens & far_tokens

    base_confidence = _PRECONDITION_WEIGHTS.get(transfer.daal_type, 0.65)

    if asl_overlap and far_overlap:
        return True, f"illa traceable in both asl and far ({sorted(asl_overlap | far_overlap)})", base_confidence

    if asl_overlap and not far_overlap:
        return (
            True,
            f"illa partially present in asl only ({sorted(asl_overlap)}); far requires inference",
            max(base_confidence - 0.10, 0.45),
        )

    if not asl_overlap and far_overlap:
        return (
            True,
            f"illa partially present in far only ({sorted(far_overlap)}); asl requires inference",
            max(base_confidence - 0.10, 0.45),
        )

    # Illa not literally in either text — allowed for mafhum, penalised otherwise
    if transfer.daal_type == DaalType.MAFHUM:
        return True, "illa implied via mafhum; confidence reduced", max(base_confidence - 0.15, 0.40)

    # For all other daal types the illa is asserted conceptually by the caller;
    # trust the assertion but apply a modest penalty.
    return (
        True,
        "illa asserted by caller; not literally traceable in texts",
        max(base_confidence - 0.05, 0.50),
    )


# ---------------------------------------------------------------------------
# Transfer engine
# ---------------------------------------------------------------------------


def _execute_transfer(transfer: QiyasTransferInput) -> tuple[str, str, str, float]:
    """Execute a single Qiyas transfer.

    Returns
    -------
    (transferred_judgment, transfer_state, rationale, confidence_score)
    """
    passes, rationale, confidence = _evaluate_preconditions(transfer)

    if not passes:
        return "", "suspend", rationale, 0.0

    if not transfer.asl_judgment.strip():
        return "", "suspend", "asl_judgment is empty; cannot transfer", 0.0

    transferred_judgment = transfer.asl_judgment
    return transferred_judgment, "valid", rationale, confidence


# ---------------------------------------------------------------------------
# Public pipeline entry point
# ---------------------------------------------------------------------------


def run_qiyas_pipeline(
    db: Session,
    text: str,
    transfers: list[QiyasTransferInput],
    run_id: str | None = None,
) -> QiyasPipelineResult | None:
    """Run the Qiyas pipeline and apply each requested transfer.

    When *run_id* is provided the pipeline attaches Qiyas rows to the
    existing ``PipelineRun`` without re-running the inference layer.
    Returns ``None`` if the given *run_id* does not exist in the database.

    When *run_id* is ``None`` the pipeline runs the inference layer on
    *text* to obtain a fresh ``run_id``.

    Parameters
    ----------
    db:
        Active SQLAlchemy session.
    text:
        Arabic input text to analyse.  Required when *run_id* is ``None``;
        ignored (but still accepted) when anchoring to an existing run.
    transfers:
        One or more ``QiyasTransferInput`` descriptors.
    run_id:
        Optional identifier of an existing ``PipelineRun`` to anchor to.
    """
    if run_id is not None:
        existing_run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
        if not existing_run:
            return None
        normalized_text = text
    else:
        inference = run_inference_pipeline(db=db, text=text)
        run_id = inference.run_id
        normalized_text = inference.normalized_text

    results: list[QiyasTransferResult] = []

    for t in transfers:
        transferred_judgment, transfer_state, rationale, confidence = _execute_transfer(t)

        unit = QiyasUnit(
            run_id=run_id,
            asl_text=t.asl_text,
            asl_judgment=t.asl_judgment,
            far_text=t.far_text,
            illa_description=t.illa_description,
            daal_type=t.daal_type.value,
            transferred_judgment=transferred_judgment,
            transfer_state=transfer_state,
            rationale=rationale,
            confidence_score=confidence,
        )
        db.add(unit)
        db.flush()

        daal_link_rows: list[dict] = []
        for ev in t.evidence:
            link = QiyasDaalLink(
                qiyas_id=unit.id,
                evidence_text=ev.get("text", ""),
                evidence_source=ev.get("source", "nass"),
                strength=ev.get("strength", "zanni"),
            )
            db.add(link)
            daal_link_rows.append(
                {
                    "evidence_text": link.evidence_text,
                    "evidence_source": link.evidence_source,
                    "strength": link.strength,
                }
            )

        results.append(
            QiyasTransferResult(
                qiyas_id=unit.id,
                asl_text=t.asl_text,
                asl_judgment=t.asl_judgment,
                far_text=t.far_text,
                illa_description=t.illa_description,
                daal_type=t.daal_type.value,
                transferred_judgment=transferred_judgment,
                transfer_state=transfer_state,
                rationale=rationale,
                confidence_score=confidence,
                daal_links=daal_link_rows,
            )
        )

    valid_count = sum(1 for r in results if r.transfer_state == "valid")
    invalid_count = sum(1 for r in results if r.transfer_state == "invalid")
    suspend_count = sum(1 for r in results if r.transfer_state == "suspend")
    avg_confidence = sum(r.confidence_score for r in results) / len(results) if results else 0.0

    db.add(
        LayerExecution(
            run_id=run_id,
            layer_name="Qiyas",
            success=True,
            duration_ms=0,
            quality_score=round(avg_confidence, 4),
            details_json={
                "transfer_count": len(results),
                "valid": valid_count,
                "invalid": invalid_count,
                "suspend": suspend_count,
            },
        )
    )
    db.commit()

    return QiyasPipelineResult(
        run_id=run_id,
        normalized_text=normalized_text,
        transfers=results,
        valid_count=valid_count,
        invalid_count=invalid_count,
        suspend_count=suspend_count,
        avg_confidence=avg_confidence,
    )
