import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


def utcnow() -> datetime:
    return datetime.now(UTC)


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title: Mapped[str] = mapped_column(String(255), default="untitled")
    language: Mapped[str] = mapped_column(String(32), default="ar")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class DocumentSegment(Base):
    __tablename__ = "document_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    segment_index: Mapped[int] = mapped_column(Integer, default=0)


class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    input_hash: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(24), default="completed")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class LayerExecution(Base):
    __tablename__ = "layer_executions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    layer_name: Mapped[str] = mapped_column(String(32), index=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True)
    duration_ms: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=1.0)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class ProcessingError(Base):
    __tablename__ = "processing_errors"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    layer_name: Mapped[str] = mapped_column(String(32), index=True)
    error_code: Mapped[str] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class UnicodeScalar(Base):
    __tablename__ = "unicode_scalars"
    __table_args__ = (UniqueConstraint("run_id", "position_index", name="uq_unicode_run_position"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    segment_id: Mapped[str] = mapped_column(ForeignKey("document_segments.id", ondelete="CASCADE"), index=True)
    scalar_value: Mapped[int] = mapped_column(Integer)
    char_value: Mapped[str] = mapped_column(String(4))
    position_index: Mapped[int] = mapped_column(Integer, index=True)
    prev_scalar_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_scalar_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class GraphemeUnit(Base):
    __tablename__ = "grapheme_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    base_scalar_id: Mapped[str] = mapped_column(ForeignKey("unicode_scalars.id", ondelete="CASCADE"), index=True)
    marks_json: Mapped[list] = mapped_column(JSON, default=list)
    norm_class: Mapped[str] = mapped_column(String(32), default="standard")
    token_index: Mapped[int] = mapped_column(Integer, index=True)
    char_index: Mapped[int] = mapped_column(Integer, index=True)
    normalized_char: Mapped[str] = mapped_column(String(4))


class PhoneticAtom(Base):
    __tablename__ = "phonetic_atoms"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    grapheme_id: Mapped[str | None] = mapped_column(ForeignKey("grapheme_units.id", ondelete="CASCADE"), index=True, nullable=True)
    atom_type: Mapped[str] = mapped_column(String(8), index=True)
    lower_features_json: Mapped[dict] = mapped_column(JSON, default=dict)
    prev_atom_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_atom_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class SyllableUnit(Base):
    __tablename__ = "syllable_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    pattern: Mapped[str] = mapped_column(String(12), index=True)
    text: Mapped[str] = mapped_column(String(16))
    atoms_json: Mapped[list] = mapped_column(JSON, default=list)
    prev_syllable_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_syllable_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class PatternUnit(Base):
    __tablename__ = "pattern_units"
    __table_args__ = (
        CheckConstraint("length(root_c1) <= 4", name="ck_root_c1_len"),
        CheckConstraint("length(root_c2) <= 4", name="ck_root_c2_len"),
        CheckConstraint("length(root_c3) <= 4", name="ck_root_c3_len"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    token: Mapped[str] = mapped_column(String(128), index=True)
    root_c1: Mapped[str] = mapped_column(String(4))
    root_c2: Mapped[str] = mapped_column(String(4))
    root_c3: Mapped[str] = mapped_column(String(4))
    pattern_name: Mapped[str] = mapped_column(String(48))
    class_type: Mapped[str] = mapped_column(String(16), default="mushtaq")
    augmentations_json: Mapped[list] = mapped_column(JSON, default=list)
    semantic_shift_json: Mapped[dict] = mapped_column(JSON, default=dict)


class LexemeUnit(Base):
    __tablename__ = "lexeme_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    surface_form: Mapped[str] = mapped_column(String(128), index=True)
    pos: Mapped[str] = mapped_column(String(24), index=True)
    independence: Mapped[bool] = mapped_column(Boolean, default=True)
    pattern_id: Mapped[str] = mapped_column(ForeignKey("pattern_units.id", ondelete="CASCADE"), index=True)
    lemma: Mapped[str] = mapped_column(String(128), index=True)


class MeaningRegistry(Base):
    __tablename__ = "meaning_registries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    lexeme_id: Mapped[str] = mapped_column(ForeignKey("lexeme_units.id", ondelete="CASCADE"), index=True)
    qareena_required: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")


class MeaningSense(Base):
    __tablename__ = "meaning_senses"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    registry_id: Mapped[str] = mapped_column(ForeignKey("meaning_registries.id", ondelete="CASCADE"), index=True)
    sense_type: Mapped[str] = mapped_column(String(24), index=True)
    gloss: Mapped[str] = mapped_column(String(255))
    priority_rank: Mapped[int] = mapped_column(Integer, default=1)


class IndicationUnit(Base):
    __tablename__ = "indication_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    lexeme_id: Mapped[str] = mapped_column(ForeignKey("lexeme_units.id", ondelete="CASCADE"), index=True)
    mutabaqa_json: Mapped[list] = mapped_column(JSON, default=list)
    tadammun_json: Mapped[list] = mapped_column(JSON, default=list)
    iltizam_json: Mapped[list] = mapped_column(JSON, default=list)


class RelationUnit(Base):
    __tablename__ = "relation_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    relation_type: Mapped[str] = mapped_column(String(24), index=True)
    source_ref: Mapped[str] = mapped_column(String(128), index=True)
    target_ref: Mapped[str] = mapped_column(String(128), index=True)


class SpeechUnit(Base):
    __tablename__ = "speech_units"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    segment_id: Mapped[str] = mapped_column(ForeignKey("document_segments.id", ondelete="CASCADE"), index=True)
    speech_type: Mapped[str] = mapped_column(String(16), index=True)
    prev_speech_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    next_speech_id: Mapped[str | None] = mapped_column(String(36), nullable=True)


class InferenceUnit(Base):
    __tablename__ = "inference_units"
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_inference_confidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    speech_id: Mapped[str] = mapped_column(ForeignKey("speech_units.id", ondelete="CASCADE"), index=True)
    mantuq_json: Mapped[list] = mapped_column(JSON, default=list)
    illa_explicit_json: Mapped[list] = mapped_column(JSON, default=list)
    illa_implied_json: Mapped[list] = mapped_column(JSON, default=list)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)


class InferenceMafhumItem(Base):
    __tablename__ = "inference_mafhum_items"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    inference_id: Mapped[str] = mapped_column(ForeignKey("inference_units.id", ondelete="CASCADE"), index=True)
    mafhum_type: Mapped[str] = mapped_column(String(24), index=True)
    content: Mapped[str] = mapped_column(Text)


class RuleUnit(Base):
    __tablename__ = "rule_units"
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_rule_confidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    inference_id: Mapped[str] = mapped_column(ForeignKey("inference_units.id", ondelete="CASCADE"), index=True)
    hukm_text: Mapped[str] = mapped_column(Text)
    evidence_rank: Mapped[str] = mapped_column(String(16), index=True)
    tarjih_basis: Mapped[str] = mapped_column(String(64))
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)


class RuleConflict(Base):
    __tablename__ = "rule_conflicts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    rule_a_id: Mapped[str] = mapped_column(ForeignKey("rule_units.id", ondelete="CASCADE"), index=True)
    rule_b_id: Mapped[str] = mapped_column(ForeignKey("rule_units.id", ondelete="CASCADE"), index=True)
    conflict_type: Mapped[str] = mapped_column(String(24), default="opposition")
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)


class TarjihDecision(Base):
    __tablename__ = "tarjih_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    conflict_id: Mapped[str] = mapped_column(ForeignKey("rule_conflicts.id", ondelete="CASCADE"), index=True)
    winning_rule_id: Mapped[str] = mapped_column(ForeignKey("rule_units.id", ondelete="CASCADE"), index=True)
    basis: Mapped[str] = mapped_column(String(64), default="strength_of_evidence")
    discarded_rule_ids_json: Mapped[list] = mapped_column(JSON, default=list)


class CaseProfile(Base):
    __tablename__ = "case_profiles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    external_case_id: Mapped[str] = mapped_column(String(128), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CaseFeature(Base):
    __tablename__ = "case_features"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    case_id: Mapped[str] = mapped_column(ForeignKey("case_profiles.id", ondelete="CASCADE"), index=True)
    feature_key: Mapped[str] = mapped_column(String(128), index=True)
    feature_value: Mapped[str] = mapped_column(String(128))
    verification_state: Mapped[str] = mapped_column(String(32), default="verified")


class ManatUnit(Base):
    __tablename__ = "manat_units"
    __table_args__ = (
        CheckConstraint("applies_state IN ('true','false','suspend')", name="ck_manat_applies_state"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_manat_confidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    rule_id: Mapped[str] = mapped_column(ForeignKey("rule_units.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("case_profiles.id", ondelete="CASCADE"), index=True)
    verified_features_json: Mapped[list] = mapped_column(JSON, default=list)
    missing_features_json: Mapped[list] = mapped_column(JSON, default=list)
    applies_state: Mapped[str] = mapped_column(String(16), default="suspend")
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)


class TanzilDecision(Base):
    __tablename__ = "tanzil_decisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manat_id: Mapped[str] = mapped_column(ForeignKey("manat_units.id", ondelete="CASCADE"), index=True)
    final_decision: Mapped[str] = mapped_column(String(16), index=True)
    rationale: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ApplicabilityCheck(Base):
    __tablename__ = "applicability_checks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    manat_id: Mapped[str] = mapped_column(ForeignKey("manat_units.id", ondelete="CASCADE"), index=True)
    check_type: Mapped[str] = mapped_column(String(64), index=True)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    event_type: Mapped[str] = mapped_column(String(64), index=True)
    payload_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ExplainabilityTrace(Base):
    __tablename__ = "explainability_traces"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    trace_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ConceptUnit(Base):
    __tablename__ = "concept_units"
    __table_args__ = (
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_concept_confidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    concept_key: Mapped[str] = mapped_column(String(128), index=True)
    summary: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ScaleAssessment(Base):
    __tablename__ = "scale_assessments"
    __table_args__ = (
        CheckConstraint("value_score >= 0 AND value_score <= 1", name="ck_scale_value"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    scale_name: Mapped[str] = mapped_column(String(64), default="sharia_value")
    value_score: Mapped[float] = mapped_column(Float, default=0.5)
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class SpiritSignal(Base):
    __tablename__ = "spirit_signals"
    __table_args__ = (
        CheckConstraint("alignment_score >= 0 AND alignment_score <= 1", name="ck_spirit_alignment"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    alignment_score: Mapped[float] = mapped_column(Float, default=0.5)
    remembrance_level: Mapped[str] = mapped_column(String(24), default="moderate")
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class InclinationProfile(Base):
    __tablename__ = "inclination_profiles"
    __table_args__ = (
        CheckConstraint("intensity_score >= 0 AND intensity_score <= 1", name="ck_inclination_intensity"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    tendency: Mapped[str] = mapped_column(String(24), default="suspend")
    intensity_score: Mapped[float] = mapped_column(Float, default=0.5)
    rationale: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class WillDecision(Base):
    __tablename__ = "will_decisions"
    __table_args__ = (
        CheckConstraint("action IN ('do','avoid','suspend')", name="ck_will_action"),
        CheckConstraint("confidence_score >= 0 AND confidence_score <= 1", name="ck_will_confidence"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    action: Mapped[str] = mapped_column(String(16), default="suspend")
    rationale: Mapped[str] = mapped_column(Text)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GenerationRun(Base):
    """Tracks a backward generation run: MeaningStructure → Arabic text."""

    __tablename__ = "generation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id: Mapped[str] = mapped_column(ForeignKey("pipeline_runs.id", ondelete="CASCADE"), index=True)
    target_meaning: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(24), default="completed", index=True)
    branch_count: Mapped[int] = mapped_column(Integer, default=0)
    top_score: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class GenerationBranch(Base):
    """One candidate generated text branch from a backward generation run."""

    __tablename__ = "generation_branches"
    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 1", name="ck_gen_branch_score"),
        CheckConstraint("rank >= 1", name="ck_gen_branch_rank"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    generation_run_id: Mapped[str] = mapped_column(
        ForeignKey("generation_runs.id", ondelete="CASCADE"), index=True
    )
    text: Mapped[str] = mapped_column(Text)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)
    trace_json: Mapped[dict] = mapped_column(JSON, default=dict)
    rank: Mapped[int] = mapped_column(Integer, default=1, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
