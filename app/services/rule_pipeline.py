from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import InferenceUnit
from app.models.entities import LayerExecution
from app.models.entities import LexemeUnit
from app.models.entities import RuleConflict
from app.models.entities import RuleUnit
from app.models.entities import TarjihDecision
from app.services.inference_pipeline import run_inference_pipeline


@dataclass
class RuleEvaluationResult:
    run_id: str
    rules: list[dict]
    conflicts: list[dict]
    tarjih_decisions: list[dict]
    rule_count: int
    conflict_count: int
    resolved_conflict_count: int
    avg_rule_confidence: float


def evidence_strength(rank: str) -> int:
    if rank == "qat_i":
        return 2
    return 1


def run_rule_evaluation_pipeline(db: Session, text: str) -> RuleEvaluationResult:
    inference = run_inference_pipeline(db=db, text=text)

    lexemes = db.query(LexemeUnit).filter(LexemeUnit.run_id == inference.run_id).all()
    inference_units = db.query(InferenceUnit).filter(InferenceUnit.run_id == inference.run_id).all()
    default_inference_id = inference_units[0].id if inference_units else None

    tokens = [tok for tok in inference.normalized_text.split() if tok]
    token_prev: dict[str, str | None] = {}
    for idx, tok in enumerate(tokens):
        token_prev[tok] = tokens[idx - 1] if idx > 0 else None

    rule_rows: list[RuleUnit] = []
    rules_out: list[dict] = []

    for lexeme in lexemes:
        if lexeme.pos == "particle" or not default_inference_id:
            continue

        prev_tok = token_prev.get(lexeme.surface_form)
        polarity = "prohibit" if prev_tok == "لا" else "allow"
        evidence_rank = "qat_i" if polarity == "prohibit" else "zanni"
        confidence = 0.9 if evidence_rank == "qat_i" else 0.7
        hukm_text = f"{polarity}:{lexeme.lemma}"

        row = RuleUnit(
            run_id=inference.run_id,
            inference_id=default_inference_id,
            hukm_text=hukm_text,
            evidence_rank=evidence_rank,
            tarjih_basis="strength_of_evidence",
            confidence_score=confidence,
        )
        db.add(row)
        db.flush()
        rule_rows.append(row)

        rules_out.append(
            {
                "id": row.id,
                "hukm_text": hukm_text,
                "evidence_rank": evidence_rank,
                "tarjih_basis": "strength_of_evidence",
                "confidence_score": confidence,
            }
        )

    rules_by_lemma: dict[str, list[dict]] = {}
    for rule in rules_out:
        _, lemma = rule["hukm_text"].split(":", 1)
        rules_by_lemma.setdefault(lemma, []).append(rule)

    conflict_rows: list[RuleConflict] = []
    conflicts_out: list[dict] = []
    tarjih_rows: list[TarjihDecision] = []
    tarjih_out: list[dict] = []

    for lemma, lemma_rules in rules_by_lemma.items():
        allow = [r for r in lemma_rules if r["hukm_text"].startswith("allow:")]
        prohibit = [r for r in lemma_rules if r["hukm_text"].startswith("prohibit:")]
        if not allow or not prohibit:
            continue

        for a in allow:
            for b in prohibit:
                conflict = RuleConflict(
                    run_id=inference.run_id,
                    rule_a_id=a["id"],
                    rule_b_id=b["id"],
                    conflict_type="opposition",
                    resolved=True,
                )
                db.add(conflict)
                db.flush()
                conflict_rows.append(conflict)

                stronger = b if evidence_strength(b["evidence_rank"]) >= evidence_strength(a["evidence_rank"]) else a
                weaker = a if stronger is b else b

                tarjih = TarjihDecision(
                    run_id=inference.run_id,
                    conflict_id=conflict.id,
                    winning_rule_id=stronger["id"],
                    basis="strength_of_evidence",
                    discarded_rule_ids_json=[weaker["id"]],
                )
                db.add(tarjih)
                tarjih_rows.append(tarjih)

                conflicts_out.append(
                    {
                        "conflict_type": "opposition",
                        "rule_a_ref": a["id"],
                        "rule_b_ref": b["id"],
                        "resolved": True,
                    }
                )
                tarjih_out.append(
                    {
                        "winning_rule_ref": stronger["id"],
                        "basis": "strength_of_evidence",
                        "discarded_rule_refs": [weaker["id"]],
                    }
                )

    db.add(
        LayerExecution(
            run_id=inference.run_id,
            layer_name="L11",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={
                "rule_count": len(rules_out),
                "conflict_count": len(conflicts_out),
            },
        )
    )
    db.commit()

    avg_confidence = sum(r["confidence_score"] for r in rules_out) / len(rules_out) if rules_out else 0.0

    return RuleEvaluationResult(
        run_id=inference.run_id,
        rules=[
            {
                "hukm_text": r["hukm_text"],
                "evidence_rank": r["evidence_rank"],
                "tarjih_basis": r["tarjih_basis"],
                "confidence_score": r["confidence_score"],
            }
            for r in rules_out
        ],
        conflicts=conflicts_out,
        tarjih_decisions=tarjih_out,
        rule_count=len(rules_out),
        conflict_count=len(conflicts_out),
        resolved_conflict_count=len([c for c in conflicts_out if c["resolved"]]),
        avg_rule_confidence=avg_confidence,
    )
