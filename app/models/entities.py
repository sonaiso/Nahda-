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
