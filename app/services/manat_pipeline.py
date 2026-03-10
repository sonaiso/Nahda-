from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.models.entities import ApplicabilityCheck
from app.models.entities import CaseFeature
from app.models.entities import CaseProfile
from app.models.entities import LayerExecution
from app.models.entities import ManatUnit
from app.models.entities import RuleUnit
from app.models.entities import TanzilDecision
from app.services.rule_pipeline import run_rule_evaluation_pipeline

TRUTHY_VALUES = {"present", "true", "1", "yes", "applicable", "verified"}


@dataclass
class ManatApplyResult:
    run_id: str
    case_id: str
    manat: list[dict]
    tanzil_decisions: list[dict]
    rule_evaluated_count: int
    applies_true_count: int
    applies_false_count: int
    suspend_count: int


def is_feature_present(feature_value: str) -> bool:
    return feature_value.strip().lower() in TRUTHY_VALUES


def run_manat_apply_pipeline(
    db: Session,
    text: str,
    case_features: list[dict],
    external_case_id: str | None = None,
    description: str = "",
) -> ManatApplyResult:
    rule_eval = run_rule_evaluation_pipeline(db=db, text=text)

    case_profile = CaseProfile(
        external_case_id=external_case_id or "",
        description=description,
    )
    db.add(case_profile)
    db.flush()

    feature_rows: list[CaseFeature] = []
    feature_map: dict[str, tuple[str, str]] = {}
    for feature in case_features:
        key = feature["feature_key"]
        value = feature["feature_value"]
        verification_state = feature.get("verification_state", "verified")
        feature_rows.append(
            CaseFeature(
                case_id=case_profile.id,
                feature_key=key,
                feature_value=value,
                verification_state=verification_state,
            )
        )
        feature_map[key] = (value, verification_state)

    db.add_all(feature_rows)

    rules = db.query(RuleUnit).filter(RuleUnit.run_id == rule_eval.run_id).all()

    manat_rows: list[ManatUnit] = []
    check_rows: list[ApplicabilityCheck] = []
    tanzil_rows: list[TanzilDecision] = []
    manat_out: list[dict] = []
    decisions_out: list[dict] = []

    for rule in rules:
        polarity, _, lemma = rule.hukm_text.partition(":")
        feature = feature_map.get(lemma)

        verified_features: list[str] = []
        missing_features: list[str] = []

        if not feature:
            missing_features.append(lemma)
            applies_state = "suspend"
            rationale = f"missing required feature: {lemma}"
            confidence = max(rule.confidence_score - 0.35, 0.0)
        else:
            feature_value, verification_state = feature
            if verification_state != "verified":
                missing_features.append(lemma)
                applies_state = "suspend"
                rationale = f"feature not verified: {lemma}"
                confidence = max(rule.confidence_score - 0.25, 0.0)
            else:
                verified_features.append(lemma)
                present = is_feature_present(feature_value)
                if polarity == "prohibit":
                    applies_state = "true" if present else "false"
                else:
                    applies_state = "true" if present else "false"
                rationale = f"rule {polarity} evaluated with feature {lemma}={feature_value}"
                confidence = rule.confidence_score

        if applies_state == "true" and missing_features:
            applies_state = "suspend"
            rationale = "suspend due to missing features despite tentative applies=true"
            confidence = max(confidence - 0.2, 0.0)

        manat = ManatUnit(
            run_id=rule_eval.run_id,
            rule_id=rule.id,
            case_id=case_profile.id,
            verified_features_json=verified_features,
            missing_features_json=missing_features,
            applies_state=applies_state,
            confidence_score=confidence,
        )
        db.add(manat)
        db.flush()
        manat_rows.append(manat)

        check_rows.append(
            ApplicabilityCheck(
                manat_id=manat.id,
                check_type="feature_presence",
                passed=not missing_features,
                details_json={
                    "verified": verified_features,
                    "missing": missing_features,
                },
            )
        )

        tanzil_rows.append(
            TanzilDecision(
                manat_id=manat.id,
                final_decision=applies_state,
                rationale=rationale,
            )
        )

        manat_out.append(
            {
                "rule_ref": rule.id,
                "hukm_text": rule.hukm_text,
                "verified_features": verified_features,
                "missing_features": missing_features,
                "applies_state": applies_state,
                "confidence_score": confidence,
                "rationale": rationale,
            }
        )
        decisions_out.append(
            {
                "manat_ref": manat.id,
                "final_decision": applies_state,
                "rationale": rationale,
            }
        )

    db.add_all(check_rows)
    db.add_all(tanzil_rows)
    db.add(
        LayerExecution(
            run_id=rule_eval.run_id,
            layer_name="L12",
            success=True,
            duration_ms=0,
            quality_score=1.0,
            details_json={
                "manat_count": len(manat_rows),
                "case_feature_count": len(feature_rows),
            },
        )
    )
    db.commit()

    return ManatApplyResult(
        run_id=rule_eval.run_id,
        case_id=case_profile.id,
        manat=manat_out,
        tanzil_decisions=decisions_out,
        rule_evaluated_count=len(manat_out),
        applies_true_count=len([m for m in manat_out if m["applies_state"] == "true"]),
        applies_false_count=len([m for m in manat_out if m["applies_state"] == "false"]),
        suspend_count=len([m for m in manat_out if m["applies_state"] == "suspend"]),
    )
