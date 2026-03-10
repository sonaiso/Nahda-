from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.entities import AuditEvent
from app.models.entities import ExplainabilityTrace
from app.models.entities import GraphemeUnit
from app.models.entities import IndicationUnit
from app.models.entities import InferenceUnit
from app.models.entities import LayerExecution
from app.models.entities import LexemeUnit
from app.models.entities import ManatUnit
from app.models.entities import MeaningRegistry
from app.models.entities import PatternUnit
from app.models.entities import PhoneticAtom
from app.models.entities import PipelineRun
from app.models.entities import RelationUnit
from app.models.entities import RuleUnit
from app.models.entities import SpeechUnit
from app.models.entities import SyllableUnit
from app.models.entities import UnicodeScalar
from app.models.entities import ConceptUnit
from app.models.entities import ScaleAssessment
from app.models.entities import SpiritSignal
from app.models.entities import InclinationProfile
from app.models.entities import WillDecision


def _count_by_run(db: Session, model, run_id: str) -> int:
    return db.query(model).filter(model.run_id == run_id).count()


def get_explain(db: Session, run_id: str) -> dict | None:
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        return None

    layers = (
        db.query(LayerExecution)
        .filter(LayerExecution.run_id == run_id)
        .order_by(LayerExecution.layer_name.asc())
        .all()
    )

    summary = {
        "unicode_scalars": _count_by_run(db, UnicodeScalar, run_id),
        "graphemes": _count_by_run(db, GraphemeUnit, run_id),
        "phonetic_atoms": _count_by_run(db, PhoneticAtom, run_id),
        "syllables": _count_by_run(db, SyllableUnit, run_id),
        "patterns": _count_by_run(db, PatternUnit, run_id),
        "lexemes": _count_by_run(db, LexemeUnit, run_id),
        "meanings": _count_by_run(db, MeaningRegistry, run_id),
        "indications": _count_by_run(db, IndicationUnit, run_id),
        "relations": _count_by_run(db, RelationUnit, run_id),
        "speech": _count_by_run(db, SpeechUnit, run_id),
        "inferences": _count_by_run(db, InferenceUnit, run_id),
        "rules": _count_by_run(db, RuleUnit, run_id),
        "manat": _count_by_run(db, ManatUnit, run_id),
        "concepts": _count_by_run(db, ConceptUnit, run_id),
        "scale_assessments": _count_by_run(db, ScaleAssessment, run_id),
        "spirit_signals": _count_by_run(db, SpiritSignal, run_id),
        "inclination_profiles": _count_by_run(db, InclinationProfile, run_id),
        "will_decisions": _count_by_run(db, WillDecision, run_id),
    }

    explain_payload = {
        "run_id": run_id,
        "status": run.status,
        "layers": [
            {
                "layer_name": layer.layer_name,
                "success": layer.success,
                "quality_score": layer.quality_score,
                "details": layer.details_json,
            }
            for layer in layers
        ],
        "summary": summary,
    }

    db.add(
        ExplainabilityTrace(
            run_id=run_id,
            trace_json=explain_payload,
        )
    )
    db.commit()

    return explain_payload


def get_trace(db: Session, run_id: str) -> dict | None:
    run = db.query(PipelineRun).filter(PipelineRun.id == run_id).first()
    if not run:
        return None

    layer_events = (
        db.query(LayerExecution)
        .filter(LayerExecution.run_id == run_id)
        .order_by(LayerExecution.layer_name.asc())
        .all()
    )
    audit_events = (
        db.query(AuditEvent)
        .filter(AuditEvent.run_id == run_id)
        .order_by(AuditEvent.created_at.asc())
        .all()
    )

    events: list[dict] = []
    seq = 1
    for layer in layer_events:
        events.append(
            {
                "sequence": seq,
                "event_type": f"layer:{layer.layer_name}",
                "payload": {
                    "success": layer.success,
                    "quality_score": layer.quality_score,
                    "details": layer.details_json,
                },
            }
        )
        seq += 1

    for event in audit_events:
        events.append(
            {
                "sequence": seq,
                "event_type": f"audit:{event.event_type}",
                "payload": event.payload_json,
            }
        )
        seq += 1

    db.add(
        AuditEvent(
            run_id=run_id,
            event_type="trace_read",
            payload_json={"events_returned": len(events)},
        )
    )
    db.commit()

    return {"run_id": run_id, "events": events}
