from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import ConceptUnit
from app.models.entities import InclinationProfile
from app.models.entities import LayerExecution
from app.models.entities import ManatUnit
from app.models.entities import PipelineRun
from app.models.entities import ScaleAssessment
from app.models.entities import SpiritSignal
from app.models.entities import WillDecision


@dataclass
class AwarenessResult:
    run_id: str
    concept: dict
    scale: dict
    spirit: dict
    inclination: dict
    will: dict
    metrics: dict


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, round(value, 4)))


def run_awareness_pipeline(db: Session, run_id: str) -> AwarenessResult | None:
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        return None

    manat_rows = db.query(ManatUnit).filter(ManatUnit.run_id == run_id).all()
    if not manat_rows:
        return None

    applies_true = len([m for m in manat_rows if m.applies_state == "true"])
    applies_false = len([m for m in manat_rows if m.applies_state == "false"])
    suspend_count = len([m for m in manat_rows if m.applies_state == "suspend"])
    total = len(manat_rows)

    true_ratio = applies_true / total if total else 0.0
    suspend_ratio = suspend_count / total if total else 0.0

    concept_confidence = _clamp(0.55 + (true_ratio * 0.35) - (suspend_ratio * 0.25))
    concept_summary = (
        f"derived from {total} manat checks: true={applies_true}, false={applies_false}, suspend={suspend_count}"
    )
    concept_row = ConceptUnit(
        run_id=run_id,
        concept_key="post_tanzil_awareness",
        summary=concept_summary,
        confidence_score=concept_confidence,
    )
    db.add(concept_row)

    scale_score = _clamp((0.5 * true_ratio) + (0.5 * concept_confidence))
    scale_rationale = "weighted by manat applicability and concept confidence"
    scale_row = ScaleAssessment(
        run_id=run_id,
        scale_name="sharia_value",
        value_score=scale_score,
        rationale=scale_rationale,
    )
    db.add(scale_row)

    spirit_alignment = _clamp((0.65 * scale_score) + (0.35 * (1 - suspend_ratio)))
    remembrance_level = "high" if spirit_alignment >= 0.75 else "moderate" if spirit_alignment >= 0.45 else "low"
    spirit_rationale = "alignment score derived from scale and certainty level"
    spirit_row = SpiritSignal(
        run_id=run_id,
        alignment_score=spirit_alignment,
        remembrance_level=remembrance_level,
        rationale=spirit_rationale,
    )
    db.add(spirit_row)

    if suspend_ratio > 0.0:
        tendency = "suspend"
        intensity = _clamp(0.4 + suspend_ratio * 0.6)
        inclination_rationale = "uncertainty preserved to avoid unsafe commitment"
    elif applies_true >= applies_false:
        tendency = "engage"
        intensity = _clamp(0.5 + true_ratio * 0.5)
        inclination_rationale = "positive applicability dominates"
    else:
        tendency = "restrain"
        intensity = _clamp(0.5 + (applies_false / total) * 0.5)
        inclination_rationale = "negative applicability dominates"

    inclination_row = InclinationProfile(
        run_id=run_id,
        tendency=tendency,
        intensity_score=intensity,
        rationale=inclination_rationale,
    )
    db.add(inclination_row)

    if tendency == "suspend":
        action = "suspend"
        will_confidence = _clamp(0.45 + (1 - suspend_ratio) * 0.2)
        will_rationale = "decision suspended until prerequisites are complete"
    elif tendency == "engage":
        action = "do"
        will_confidence = _clamp((0.55 * concept_confidence) + (0.45 * spirit_alignment))
        will_rationale = "decision to act due to satisfied conditions"
    else:
        action = "avoid"
        will_confidence = _clamp((0.5 * concept_confidence) + (0.5 * spirit_alignment))
        will_rationale = "decision to avoid due to dominant non-applicability"

    will_row = WillDecision(
        run_id=run_id,
        action=action,
        rationale=will_rationale,
        confidence_score=will_confidence,
    )
    db.add(will_row)

    for layer_name, details in [
        ("L15", {"concept_confidence": concept_confidence}),
        ("L16", {"scale_score": scale_score}),
        ("L17", {"spirit_alignment": spirit_alignment}),
        ("L18", {"tendency": tendency, "intensity": intensity}),
        ("L19", {"action": action, "confidence": will_confidence}),
    ]:
        db.add(
            LayerExecution(
                run_id=run_id,
                layer_name=layer_name,
                success=True,
                duration_ms=0,
                quality_score=1.0,
                details_json=details,
            )
        )

    db.commit()

    return AwarenessResult(
        run_id=run_id,
        concept={
            "concept_key": concept_row.concept_key,
            "summary": concept_row.summary,
            "confidence_score": concept_row.confidence_score,
        },
        scale={
            "scale_name": scale_row.scale_name,
            "value_score": scale_row.value_score,
            "rationale": scale_row.rationale,
        },
        spirit={
            "alignment_score": spirit_row.alignment_score,
            "remembrance_level": spirit_row.remembrance_level,
            "rationale": spirit_row.rationale,
        },
        inclination={
            "tendency": inclination_row.tendency,
            "intensity_score": inclination_row.intensity_score,
            "rationale": inclination_row.rationale,
        },
        will={
            "action": will_row.action,
            "confidence_score": will_row.confidence_score,
            "rationale": will_row.rationale,
        },
        metrics={
            "manat_total": total,
            "applies_true": applies_true,
            "applies_false": applies_false,
            "suspend_count": suspend_count,
        },
    )
