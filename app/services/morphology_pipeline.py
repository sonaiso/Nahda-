from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import LayerExecution
from app.models.entities import PatternUnit
from app.models.entities import PhoneticAtom
from app.models.entities import SyllableUnit
from app.services.unicode_pipeline import run_unicode_pipeline

SHORT_VOWELS = {"\u064E", "\u064F", "\u0650"}
LONG_VOWELS = {"\u0627", "\u0648", "\u064A"}
SUKUN = "\u0652"
ARABIC_LETTER_START = 0x0621
ARABIC_LETTER_END = 0x064A
PREFIXES = ("ال", "و", "ف", "ب", "ك", "ل", "س")
SUFFIXES = ("ها", "هم", "هن", "كما", "كم", "نا", "ات", "ون", "ين", "ة", "ه", "ي")


@dataclass
class MorphologyPipelineResult:
    run_id: str
    normalized_text: str
    syllables: list[dict]
    patterns: list[dict]
    token_count: int
    syllable_count: int
    valid_syllable_ratio: float
    triliteral_root_ratio: float


def is_arabic_letter(ch: str) -> bool:
    code = ord(ch)
    return ARABIC_LETTER_START <= code <= ARABIC_LETTER_END


def atom_type(ch: str) -> str:
    if ch in SHORT_VOWELS or ch in LONG_VOWELS:
        return "V"
    if ch == SUKUN:
        return "S"
    if is_arabic_letter(ch):
        return "C"
    return "X"


def syllabify(token: str) -> list[tuple[str, str]]:
    atoms = [(ch, atom_type(ch)) for ch in token if not ch.isspace()]
    if not atoms:
        return []

    out: list[tuple[str, str]] = []
    i = 0
    while i < len(atoms):
        chunk = [atoms[i][0]]
        pattern = [atoms[i][1]]

        if i + 1 < len(atoms) and atoms[i + 1][1] == "V":
            i += 1
            chunk.append(atoms[i][0])
            pattern.append("V")

        if i + 1 < len(atoms) and atoms[i + 1][1] == "C" and (i + 2 == len(atoms) or atoms[i + 2][1] != "V"):
            i += 1
            chunk.append(atoms[i][0])
            pattern.append("C")

        out.append(("".join(chunk), "".join(pattern)))
        i += 1

    return out


def normalize_token_for_root(token: str) -> tuple[str, list[str]]:
    work = token
    augmentations: list[str] = []

    if work.startswith("ال"):
        work = work[2:]
        augmentations.append("prefix:ال")

    for pref in PREFIXES:
        if work.startswith(pref) and len(work) > 3:
            work = work[len(pref):]
            augmentations.append(f"prefix:{pref}")
            break

    for suffix in SUFFIXES:
        if work.endswith(suffix) and len(work) - len(suffix) >= 3:
            work = work[:-len(suffix)]
            augmentations.append(f"suffix:{suffix}")
            break

    return work, augmentations


def derive_root_and_pattern(token: str) -> tuple[list[str], str, list[str]]:
    normalized, augmentations = normalize_token_for_root(token)
    consonants = [c for c in normalized if atom_type(c) == "C"]

    if len(consonants) >= 3:
        root = consonants[:3]
    elif len(consonants) == 2:
        root = consonants + ["_"]
    elif len(consonants) == 1:
        root = consonants + ["_", "_"]
    else:
        root = ["_", "_", "_"]

    pattern_name = f"w{len(normalized)}_c{len(consonants)}"
    return root, pattern_name, augmentations


def run_morphology_pipeline(db: Session, text: str) -> MorphologyPipelineResult:
    base_result = run_unicode_pipeline(db=db, text=text)
    tokens = [tok for tok in base_result.normalized_text.split() if tok]

    syllable_rows: list[SyllableUnit] = []
    pattern_rows: list[PatternUnit] = []
    atom_rows: list[PhoneticAtom] = []

    syllables_out: list[dict] = []
    patterns_out: list[dict] = []

    for token in tokens:
        token_syllables = syllabify(token)
        for syllable_text, syllable_pattern in token_syllables:
            row = SyllableUnit(
                run_id=base_result.run_id,
                pattern=syllable_pattern,
                text=syllable_text,
                atoms_json=[ch for ch in syllable_text],
            )
            syllable_rows.append(row)
            syllables_out.append({"text": syllable_text, "pattern": syllable_pattern})

        root, pattern_name, augmentations = derive_root_and_pattern(token)
        pattern_rows.append(
            PatternUnit(
                run_id=base_result.run_id,
                token=token,
                root_c1=root[0],
                root_c2=root[1],
                root_c3=root[2],
                pattern_name=pattern_name,
                class_type="mushtaq",
                augmentations_json=augmentations,
                semantic_shift_json={},
            )
        )
        patterns_out.append(
            {
                "token": token,
                "root": root,
                "pattern_name": pattern_name,
                "augmentations": augmentations,
            }
        )

        for ch in token:
            atom_rows.append(
                PhoneticAtom(
                    run_id=base_result.run_id,
                    grapheme_id=None,
                    atom_type=atom_type(ch),
                    lower_features_json={"char": ch},
                )
            )

    db.add_all(atom_rows)
    db.add_all(syllable_rows)
    db.add_all(pattern_rows)

    valid_syllables = [s for s in syllables_out if s["pattern"].startswith("C")]
    triliteral = [p for p in patterns_out if "_" not in p["root"]]

    db.add(
        LayerExecution(
            run_id=base_result.run_id,
            layer_name="L2-L4",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={"token_count": len(tokens), "syllable_count": len(syllables_out)},
        )
    )
    db.commit()

    return MorphologyPipelineResult(
        run_id=base_result.run_id,
        normalized_text=base_result.normalized_text,
        syllables=syllables_out,
        patterns=patterns_out,
        token_count=len(tokens),
        syllable_count=len(syllables_out),
        valid_syllable_ratio=(len(valid_syllables) / len(syllables_out)) if syllables_out else 0.0,
        triliteral_root_ratio=(len(triliteral) / len(patterns_out)) if patterns_out else 0.0,
    )
