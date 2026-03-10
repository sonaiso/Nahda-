from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import DocumentSegment
from app.models.entities import InferenceMafhumItem
from app.models.entities import InferenceUnit
from app.models.entities import LayerExecution
from app.models.entities import SpeechUnit
from app.services.semantics_pipeline import run_semantics_pipeline

SEGMENT_SPLIT_REGEX = re.compile(r"[\n\.!؟؛]+")


@dataclass
class InferencePipelineResult:
    run_id: str
    normalized_text: str
    inference: list[dict]
    speech_count: int
    inference_count: int
    mafhum_item_count: int
    avg_inference_confidence: float


def classify_speech_type(segment_text: str) -> str:
    if "!" in segment_text or segment_text.strip().startswith("يا"):
        return "insha"
    return "khabar"


def build_mafhum(tokens: list[str]) -> dict[str, list[str]]:
    mafhum = {
        "iqtida": [],
        "ishara": [],
        "ima": [],
        "muwafaqa": [],
        "mukhalafa": [],
    }
    if tokens:
        mafhum["iqtida"].append(tokens[0])
    if "في" in tokens:
        mafhum["ishara"].append("context:containment")
    if any(tok in {"إن", "اذا", "إذا"} for tok in tokens):
        mafhum["ima"].append("causality:conditional")
    if any(tok.startswith("ال") for tok in tokens):
        mafhum["muwafaqa"].append("definite_reference")
    if "لا" in tokens:
        mafhum["mukhalafa"].append("negation_implies_opposite")
    return mafhum


def run_inference_pipeline(db: Session, text: str) -> InferencePipelineResult:
    semantics = run_semantics_pipeline(db=db, text=text)

    segment = db.query(DocumentSegment).filter(DocumentSegment.content == semantics.normalized_text).first()
    if not segment:
        segment = DocumentSegment(document_id="", content=semantics.normalized_text, segment_index=0)

    raw_segments = [seg.strip() for seg in SEGMENT_SPLIT_REGEX.split(semantics.normalized_text) if seg.strip()]
    if not raw_segments:
        raw_segments = [semantics.normalized_text]

    speech_rows: list[SpeechUnit] = []
    inference_rows: list[InferenceUnit] = []
    mafhum_rows: list[InferenceMafhumItem] = []
    inference_out: list[dict] = []

    prev_speech_id: str | None = None
    for raw_segment in raw_segments:
        speech_type = classify_speech_type(raw_segment)
        speech = SpeechUnit(
            run_id=semantics.run_id,
            segment_id=segment.id,
            speech_type=speech_type,
            prev_speech_id=prev_speech_id,
        )
        db.add(speech)
        db.flush()

        if prev_speech_id and speech_rows:
            speech_rows[-1].next_speech_id = speech.id

        speech_rows.append(speech)
        prev_speech_id = speech.id

        tokens = [tok for tok in raw_segment.split() if tok]
        mafhum = build_mafhum(tokens)
        confidence = 0.8 if speech_type == "khabar" else 0.65

        inference = InferenceUnit(
            run_id=semantics.run_id,
            speech_id=speech.id,
            mantuq_json=tokens,
            illa_explicit_json=[tok for tok in tokens if tok.startswith("ل") and len(tok) > 1],
            illa_implied_json=["sequence_relation"] if len(tokens) > 1 else [],
            confidence_score=confidence,
        )
        db.add(inference)
        db.flush()

        inference_rows.append(inference)

        for mafhum_type, items in mafhum.items():
            for item in items:
                mafhum_rows.append(
                    InferenceMafhumItem(
                        inference_id=inference.id,
                        mafhum_type=mafhum_type,
                        content=item,
                    )
                )

        inference_out.append(
            {
                "speech_type": speech_type,
                "mantuq": tokens,
                "mafhum": mafhum,
                "confidence_score": confidence,
            }
        )

    db.add_all(mafhum_rows)
    db.add(
        LayerExecution(
            run_id=semantics.run_id,
            layer_name="L9-L10",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={
                "speech_count": len(speech_rows),
                "inference_count": len(inference_rows),
            },
        )
    )
    db.commit()

    avg_confidence = sum(item["confidence_score"] for item in inference_out) / len(inference_out) if inference_out else 0.0

    return InferencePipelineResult(
        run_id=semantics.run_id,
        normalized_text=semantics.normalized_text,
        inference=inference_out,
        speech_count=len(speech_rows),
        inference_count=len(inference_rows),
        mafhum_item_count=len(mafhum_rows),
        avg_inference_confidence=avg_confidence,
    )
