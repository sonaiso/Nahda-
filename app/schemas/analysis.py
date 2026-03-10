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
