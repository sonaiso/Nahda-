from pydantic import BaseModel, Field, field_validator


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)

    @field_validator("text")
    @classmethod
    def ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class UnicodeScalarOut(BaseModel):
    idx: int
    value: int
    char: str


class UnicodeMetrics(BaseModel):
    input_length: int
    normalized_length: int
    changed_characters: int
    normalization_ratio: float


class UnicodeAnalyzeResponse(BaseModel):
    run_id: str
    unicode: list[UnicodeScalarOut]
    normalized_text: str
    metrics: UnicodeMetrics


class SyllableOut(BaseModel):
    text: str
    pattern: str


class PatternOut(BaseModel):
    token: str
    root: list[str]
    pattern_name: str
    augmentations: list[str]


class MorphologyMetrics(BaseModel):
    token_count: int
    syllable_count: int
    avg_syllables_per_token: float
    valid_syllable_ratio: float
    triliteral_root_ratio: float


class MorphologyAnalyzeResponse(BaseModel):
    run_id: str
    normalized_text: str
    syllables: list[SyllableOut]
    patterns: list[PatternOut]
    metrics: MorphologyMetrics


class LexemeOut(BaseModel):
    token: str
    lemma: str
    pos: str
    independence: bool


class MeaningSenseOut(BaseModel):
    sense_type: str
    gloss: str
    priority_rank: int


class MeaningRegistryOut(BaseModel):
    token: str
    qareena_required: bool
    senses: list[MeaningSenseOut]


class IndicationOut(BaseModel):
    token: str
    mutabaqa: list[str]
    tadammun: list[str]
    iltizam: list[str]


class RelationOut(BaseModel):
    relation_type: str
    source_ref: str
    target_ref: str


class SemanticsMetrics(BaseModel):
    lexeme_count: int
    independent_lexeme_ratio: float
    indication_coverage_ratio: float
    relation_count: int


class SemanticsAnalyzeResponse(BaseModel):
    run_id: str
    normalized_text: str
    lexemes: list[LexemeOut]
    meaning_registry: list[MeaningRegistryOut]
    indications: list[IndicationOut]
    relations: list[RelationOut]
    metrics: SemanticsMetrics


class MafhumOut(BaseModel):
    iqtida: list[str]
    ishara: list[str]
    ima: list[str]
    muwafaqa: list[str]
    mukhalafa: list[str]


class InferenceOut(BaseModel):
    speech_type: str
    mantuq: list[str]
    mafhum: MafhumOut
    confidence_score: float


class InferMetrics(BaseModel):
    speech_count: int
    inference_count: int
    mafhum_item_count: int
    avg_inference_confidence: float


class InferResponse(BaseModel):
    run_id: str
    normalized_text: str
    inference: list[InferenceOut]
    metrics: InferMetrics


class RuleOut(BaseModel):
    hukm_text: str
    evidence_rank: str
    tarjih_basis: str
    confidence_score: float


class ConflictOut(BaseModel):
    conflict_type: str
    rule_a_ref: str
    rule_b_ref: str
    resolved: bool


class TarjihOut(BaseModel):
    winning_rule_ref: str
    basis: str
    discarded_rule_refs: list[str]


class RuleEvaluateMetrics(BaseModel):
    rule_count: int
    conflict_count: int
    resolved_conflict_count: int
    avg_rule_confidence: float


class RuleEvaluateResponse(BaseModel):
    run_id: str
    rules: list[RuleOut]
    conflicts: list[ConflictOut]
    tarjih_decisions: list[TarjihOut]
    metrics: RuleEvaluateMetrics


class CaseFeatureIn(BaseModel):
    feature_key: str
    feature_value: str
    verification_state: str = "verified"


class ManatApplyRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    external_case_id: str | None = None
    description: str = ""
    case_features: list[CaseFeatureIn] = Field(default_factory=list)

    @field_validator("text")
    @classmethod
    def ensure_text_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class ManatItemOut(BaseModel):
    rule_ref: str
    hukm_text: str
    verified_features: list[str]
    missing_features: list[str]
    applies_state: str
    confidence_score: float
    rationale: str


class TanzilDecisionOut(BaseModel):
    manat_ref: str
    final_decision: str
    rationale: str


class ManatApplyMetrics(BaseModel):
    rule_evaluated_count: int
    applies_true_count: int
    applies_false_count: int
    suspend_count: int


class ManatApplyResponse(BaseModel):
    run_id: str
    case_id: str
    manat: list[ManatItemOut]
    tanzil_decisions: list[TanzilDecisionOut]
    metrics: ManatApplyMetrics


class LayerExecutionOut(BaseModel):
    layer_name: str
    success: bool
    quality_score: float
    details: dict


class ExplainSummaryOut(BaseModel):
    unicode_scalars: int
    graphemes: int
    phonetic_atoms: int
    syllables: int
    patterns: int
    lexemes: int
    meanings: int
    indications: int
    relations: int
    speech: int
    inferences: int
    rules: int
    manat: int
    concepts: int
    scale_assessments: int
    spirit_signals: int
    inclination_profiles: int
    will_decisions: int


class ExplainResponse(BaseModel):
    run_id: str
    status: str
    layers: list[LayerExecutionOut]
    summary: ExplainSummaryOut


class TraceEventOut(BaseModel):
    sequence: int
    event_type: str
    payload: dict


class TraceResponse(BaseModel):
    run_id: str
    events: list[TraceEventOut]


class AwarenessApplyRequest(BaseModel):
    run_id: str = Field(min_length=1, max_length=64)


class ConceptOut(BaseModel):
    concept_key: str
    summary: str
    confidence_score: float


class ScaleOut(BaseModel):
    scale_name: str
    value_score: float
    rationale: str


class SpiritOut(BaseModel):
    alignment_score: float
    remembrance_level: str
    rationale: str


class InclinationOut(BaseModel):
    tendency: str
    intensity_score: float
    rationale: str


class WillOut(BaseModel):
    action: str
    confidence_score: float
    rationale: str


class AwarenessMetrics(BaseModel):
    manat_total: int
    applies_true: int
    applies_false: int
    suspend_count: int


class AwarenessApplyResponse(BaseModel):
    run_id: str
    concept: ConceptOut
    scale: ScaleOut
    spirit: SpiritOut
    inclination: InclinationOut
    will: WillOut
    metrics: AwarenessMetrics


# ---------------------------------------------------------------------------
# Qiyas Schemas
# ---------------------------------------------------------------------------


class QiyasEvidenceIn(BaseModel):
    text: str = Field(min_length=1, max_length=2000)
    source: str = Field(default="nass", max_length=64)
    strength: str = Field(default="zanni", max_length=16)


class QiyasTransferIn(BaseModel):
    asl_text: str = Field(min_length=1, max_length=2000)
    # Allow empty strings so the pipeline can return transfer_state="suspend"
    # instead of rejecting the request with 422.
    asl_judgment: str = Field(max_length=128, default="")
    far_text: str = Field(min_length=1, max_length=2000)
    illa_description: str = Field(max_length=1000, default="")
    daal_type: str = Field(default="mutabaqa", max_length=32)
    evidence: list[QiyasEvidenceIn] = Field(default_factory=list)


class QiyasRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    transfers: list[QiyasTransferIn] = Field(min_length=1)
    # Optional: anchor transfers to an already-executed run instead of
    # creating a new one.  When provided, the pipeline skips the inference
    # step and attaches Qiyas rows to the existing PipelineRun.
    run_id: str | None = Field(default=None, max_length=64)

    @field_validator("text")
    @classmethod
    def ensure_not_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("text must not be empty")
        return value


class QiyasDaalLinkOut(BaseModel):
    evidence_text: str
    evidence_source: str
    strength: str


class QiyasTransferOut(BaseModel):
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
    daal_links: list[QiyasDaalLinkOut]


class QiyasMetrics(BaseModel):
    transfer_count: int
    valid_count: int
    invalid_count: int
    suspend_count: int
    avg_confidence: float


class QiyasResponse(BaseModel):
    run_id: str
    normalized_text: str
    transfers: list[QiyasTransferOut]
    metrics: QiyasMetrics
