from __future__ import annotations

import hashlib
import unicodedata
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import Document
from app.models.entities import DocumentSegment
from app.models.entities import GraphemeUnit
from app.models.entities import LayerExecution
from app.models.entities import PipelineRun
from app.models.entities import UnicodeScalar

ALEF_VARIANTS = {"\u0623", "\u0625", "\u0622", "\u0671"}
ARABIC_YEH = "\u064A"
ALEF_MAQSURA = "\u0649"
ARABIC_KAF = "\u0643"
FARSI_KEHEH = "\u06A9"
TATWEEL = "\u0640"


@dataclass
class UnicodePipelineResult:
    run_id: str
    scalars: list[dict]
    normalized_text: str
    input_length: int
    normalized_length: int
    changed_characters: int


def normalize_arabic_text(text: str) -> tuple[str, int]:
    normalized_chars: list[str] = []
    changed = 0

    for ch in text:
        new_ch = ch
        if ch in ALEF_VARIANTS:
            new_ch = "\u0627"
        elif ch == ALEF_MAQSURA:
            new_ch = ARABIC_YEH
        elif ch == FARSI_KEHEH:
            new_ch = ARABIC_KAF
        elif ch == TATWEEL:
            new_ch = ""

        new_ch = unicodedata.normalize("NFC", new_ch)
        if new_ch != ch:
            changed += 1
        normalized_chars.append(new_ch)

    normalized = "".join(normalized_chars)
    return normalized, changed


def run_unicode_pipeline(db: Session, text: str) -> UnicodePipelineResult:
    normalized_text, changed = normalize_arabic_text(text)
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()

    document = Document(title="api_input", language="ar")
    db.add(document)
    db.flush()

    segment = DocumentSegment(document_id=document.id, content=normalized_text, segment_index=0)
    db.add(segment)
    db.flush()

    run = PipelineRun(document_id=document.id, input_hash=content_hash, status="completed")
    db.add(run)
    db.flush()

    scalar_rows: list[UnicodeScalar] = []
    scalar_output: list[dict] = []
    for idx, char in enumerate(normalized_text):
        row = UnicodeScalar(
            run_id=run.id,
            segment_id=segment.id,
            scalar_value=ord(char),
            char_value=char,
            position_index=idx,
        )
        scalar_rows.append(row)
        scalar_output.append({"idx": idx, "value": ord(char), "char": char})

    db.add_all(scalar_rows)
    db.flush()

    for i, row in enumerate(scalar_rows):
        row.prev_scalar_id = scalar_rows[i - 1].id if i > 0 else None
        row.next_scalar_id = scalar_rows[i + 1].id if i < len(scalar_rows) - 1 else None

    grapheme_rows: list[GraphemeUnit] = []
    token_idx = 0
    char_idx = 0
    for scalar in scalar_rows:
        if scalar.char_value.isspace():
            token_idx += 1
            char_idx = 0
            continue
        grapheme_rows.append(
            GraphemeUnit(
                run_id=run.id,
                base_scalar_id=scalar.id,
                marks_json=[],
                norm_class="standard",
                token_index=token_idx,
                char_index=char_idx,
                normalized_char=scalar.char_value,
            )
        )
        char_idx += 1

    db.add_all(grapheme_rows)

    layer = LayerExecution(
        run_id=run.id,
        layer_name="L0-L1",
        success=True,
        duration_ms=0,
        quality_score=1.0,
        details_json={"changed_characters": changed},
    )
    db.add(layer)
    db.commit()

    return UnicodePipelineResult(
        run_id=run.id,
        scalars=scalar_output,
        normalized_text=normalized_text,
        input_length=len(text),
        normalized_length=len(normalized_text),
        changed_characters=changed,
    )
