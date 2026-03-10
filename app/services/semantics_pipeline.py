from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import IndicationUnit
from app.models.entities import LayerExecution
from app.models.entities import LexemeUnit
from app.models.entities import MeaningRegistry
from app.models.entities import MeaningSense
from app.models.entities import PatternUnit
from app.models.entities import RelationUnit
from app.services.morphology_pipeline import run_morphology_pipeline

PARTICLES = {"في", "من", "الى", "على", "عن", "و", "ف", "ب", "ك", "ل", "ثم", "او", "أو"}
VERB_PREFIXES = ("ي", "ت", "ن", "ا")


@dataclass
class SemanticsPipelineResult:
    run_id: str
    normalized_text: str
    lexemes: list[dict]
    meaning_registry: list[dict]
    indications: list[dict]
    relations: list[dict]
    lexeme_count: int
    independent_lexeme_ratio: float
    indication_coverage_ratio: float
    relation_count: int


def infer_pos(token: str) -> str:
    if token in PARTICLES:
        return "particle"
    if token.startswith("ال"):
        return "noun"
    if len(token) >= 3 and token[0] in VERB_PREFIXES:
        return "verb"
    return "noun"


def is_independent(pos: str) -> bool:
    return pos in {"noun", "verb", "adjective"}


def make_senses(token: str, pos: str) -> list[dict]:
    base_gloss = f"literal:{token}"
    senses = [
        {"sense_type": "wad_original", "gloss": base_gloss, "priority_rank": 1},
    ]

    if pos == "noun":
        senses.append({"sense_type": "naql_urfi", "gloss": f"customary:{token}", "priority_rank": 2})
    if token.startswith("ال"):
        senses.append({"sense_type": "naql_shari", "gloss": f"shari:{token}", "priority_rank": 3})
    senses.append({"sense_type": "majaz", "gloss": f"figurative:{token}", "priority_rank": 4})
    return senses


def run_semantics_pipeline(db: Session, text: str) -> SemanticsPipelineResult:
    morphology = run_morphology_pipeline(db=db, text=text)

    pattern_by_token: dict[str, PatternUnit] = {
        row.token: row
        for row in db.query(PatternUnit).filter(PatternUnit.run_id == morphology.run_id).all()
    }

    lexeme_rows: list[LexemeUnit] = []
    meaning_rows: list[MeaningRegistry] = []
    sense_rows: list[MeaningSense] = []
    indication_rows: list[IndicationUnit] = []
    relation_rows: list[RelationUnit] = []

    lexemes_out: list[dict] = []
    meaning_out: list[dict] = []
    indications_out: list[dict] = []
    relations_out: list[dict] = []

    tokens = [tok for tok in morphology.normalized_text.split() if tok]
    previous_lexeme_id: str | None = None

    for token in tokens:
        pattern = pattern_by_token.get(token)
        if not pattern:
            continue

        pos = infer_pos(token)
        independence = is_independent(pos)
        lemma = token.removeprefix("ال") if token.startswith("ال") else token

        lexeme = LexemeUnit(
            run_id=morphology.run_id,
            surface_form=token,
            pos=pos,
            independence=independence,
            pattern_id=pattern.id,
            lemma=lemma,
        )
        lexeme_rows.append(lexeme)
        db.add(lexeme)
        db.flush()

        senses = make_senses(token=token, pos=pos)
        registry = MeaningRegistry(
            run_id=morphology.run_id,
            lexeme_id=lexeme.id,
            qareena_required=True,
            notes="auto-generated semantic registry",
        )
        meaning_rows.append(registry)
        db.add(registry)
        db.flush()

        for sense in senses:
            sense_row = MeaningSense(
                registry_id=registry.id,
                sense_type=sense["sense_type"],
                gloss=sense["gloss"],
                priority_rank=sense["priority_rank"],
            )
            sense_rows.append(sense_row)

        mutabaqa = [senses[0]["gloss"]]
        tadammun = [lemma] if lemma != token else []
        iltizam = [f"entity:{pos}"]
        indication = IndicationUnit(
            run_id=morphology.run_id,
            lexeme_id=lexeme.id,
            mutabaqa_json=mutabaqa,
            tadammun_json=tadammun,
            iltizam_json=iltizam,
        )
        indication_rows.append(indication)

        lexemes_out.append({"token": token, "lemma": lemma, "pos": pos, "independence": independence})
        meaning_out.append(
            {
                "token": token,
                "qareena_required": True,
                "senses": senses,
            }
        )
        indications_out.append(
            {
                "token": token,
                "mutabaqa": mutabaqa,
                "tadammun": tadammun,
                "iltizam": iltizam,
            }
        )

        if previous_lexeme_id:
            relation = RelationUnit(
                run_id=morphology.run_id,
                relation_type="isnadi",
                source_ref=previous_lexeme_id,
                target_ref=lexeme.id,
            )
            relation_rows.append(relation)
            relations_out.append(
                {
                    "relation_type": "isnadi",
                    "source_ref": previous_lexeme_id,
                    "target_ref": lexeme.id,
                }
            )

        previous_lexeme_id = lexeme.id

    db.add_all(sense_rows)
    db.add_all(indication_rows)
    db.add_all(relation_rows)

    db.add(
        LayerExecution(
            run_id=morphology.run_id,
            layer_name="L5-L8",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={
                "lexeme_count": len(lexemes_out),
                "relation_count": len(relations_out),
            },
        )
    )
    db.commit()

    independent_count = len([lx for lx in lexemes_out if lx["independence"]])
    indicated_count = len([ind for ind in indications_out if ind["mutabaqa"] or ind["tadammun"] or ind["iltizam"]])

    return SemanticsPipelineResult(
        run_id=morphology.run_id,
        normalized_text=morphology.normalized_text,
        lexemes=lexemes_out,
        meaning_registry=meaning_out,
        indications=indications_out,
        relations=relations_out,
        lexeme_count=len(lexemes_out),
        independent_lexeme_ratio=(independent_count / len(lexemes_out)) if lexemes_out else 0.0,
        indication_coverage_ratio=(indicated_count / len(lexemes_out)) if lexemes_out else 0.0,
        relation_count=len(relations_out),
    )
