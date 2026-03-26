# PRD + Technical Design
## Fractal Arabic Awareness Engine

Version: 1.0.0  
Date: 2026-03-10  
Status: Approved for Engineering Execution

## 1. Product Requirement Document (PRD)

## 1.1 Product Vision

Build an Arabic awareness engine that performs a governed transition from symbol to decision:

Unicode -> Arabic structure -> semantic meaning -> inference -> rule -> manat -> applied decision -> concept/scale/spirit/inclination -> will in act.

The system must be:

1. Layered.
2. Explainable.
3. Auditable.
4. Deterministic where required.
5. Able to suspend instead of hallucinating a final outcome.

## 1.2 Business Goals

1. Deliver an enterprise-grade reasoning pipeline for Arabic legal-semantic processing.
2. Guarantee traceability from final decision to raw Unicode source artifacts.
3. Provide production-ready governance: CI quality gates, security scanning, observability, and controlled release posture.

## 1.3 Stakeholders

1. Product Owner: Defines governed reasoning behavior and acceptance.
2. Language/Usul Experts: Validate linguistic and inferential correctness.
3. Platform Team: Owns reliability, security, observability, and deployability.
4. API Consumers: Use endpoints for analysis, inference, application, and awareness decisions.

## 1.4 In Scope

1. Full layered architecture from L0 to L19.
2. Strict provenance chain and explainability.
3. Manat gating with applies/not_applies/suspend outcomes.
4. Awareness layers that consume applied outcomes and emit will decisions.
5. Enterprise controls (auth, rate limiting, branch protection policy assets, security scans, observability stack).

## 1.5 Out of Scope

1. External fatwa authority integration.
2. Multi-tenant billing and quotas.
3. Human juristic workflow UI (dashboard runtime exists; jurist workstation UX not included here).

## 1.6 Success Metrics

1. Coverage floor >= 85% and current target >= 90%.
2. CI gate pass rate >= 95% over rolling 30 days.
3. 100% explainability reconstruction for accepted decisions.
4. 0 critical vulnerabilities in dependency and code scanning at release time.
5. Explicit suspend behavior for missing prerequisites in all required pipelines.

## 1.7 Functional Requirements

1. Parse and normalize Arabic text from Unicode with traceable artifacts.
2. Produce phonetic, syllabic, root-pattern, and lexeme artifacts.
3. Resolve layered meanings and lexical indications.
4. Build relation graphs and clause speech mode.
5. Extract mantuq/mafhum and cause model.
6. Synthesize rule objects with conflict and tarjih basis.
7. Verify manat against case features and generate applied outcomes.
8. Run awareness pipeline L15-L19 and return concept/scale/spirit/inclination/will outputs.
9. Expose explain and trace endpoints for all run identifiers.

## 1.8 Non-Functional Requirements

1. Security:
1. JWT-based protected endpoints.
2. Rate limiting.
3. CI SAST + dependency audit.

2. Reliability:
1. Safe startup guards in production.
2. Deterministic behavior for key transforms.

3. Observability:
1. Request ID and trace ID propagation.
2. Metrics in JSON and Prometheus formats.
3. OTLP profile and collector overlay.

4. Maintainability:
1. Layered code organization.
2. Migration-driven schema evolution.
3. Typed request/response contracts.

## 1.9 Acceptance Criteria (Product)

1. Any final action decision can be traced backward from L19 to lower layers through run-linked artifacts.
2. System returns suspend when critical prerequisites fail.
3. No production deployment approved unless all CI checks are green.
4. Explainability and trace APIs return auditable events and summaries.

## 2. Technical Design Document (TDD)

## 2.1 Architecture Overview

The architecture is a strict layered pipeline with governed transitions.

Layers:

1. L0 Unicode raw.
2. L1 Script normalization.
3. L2 Phonetic atomization.
4. L3 Syllabification.
5. L4 Root/pattern derivation.
6. L5 Lexeme formation.
7. L6 WAD/Naql/Majaz registry.
8. L7 Lexical indications.
9. L8 Relation graph.
10. L9 Speech mode.
11. L10 Mantuq/Mafhum field.
12. L11 Illa model.
13. L12 Rule synthesis.
14. L13 Case structuring.
15. L14 Manat verification.
16. L15 Concept.
17. L16 Scale.
18. L17 Spirit.
19. L18 Inclination.
20. L19 Will in act.

## 2.2 Current Implementation Baseline

Implemented and operational:

1. API framework, DB layer, migrations up to awareness layer migration.
2. Security and governance controls.
3. Explainability and tracing.
4. Awareness pipeline endpoint and persistence models.

## 2.3 Data Model

Core entity groups:

1. Runtime:
1. documents
2. document_segments
3. pipeline_runs
4. layer_executions
5. processing_errors

2. Linguistic and semantics:
1. unicode_scalars
2. grapheme_units
3. phonetic_atoms
4. syllable_units
5. pattern_units
6. lexeme_units
7. meaning_registries
8. meaning_senses
9. indication_units
10. relation_units

3. Inference and rule:
1. speech_units
2. inference_units
3. inference_mafhum_items
4. rule_units
5. rule_conflicts
6. tarjih_decisions

4. Application and manat:
1. case_profiles
2. case_features
3. manat_units
4. applicability_checks
5. tanzil_decisions

5. Explainability and governance:
1. audit_events
2. explainability_traces

6. Awareness:
1. concept_units
2. scale_assessments
3. spirit_signals
4. inclination_profiles
5. will_decisions

## 2.4 API Surface

Public endpoints:

1. POST /auth/token
2. GET /health/live
3. GET /health/ready
4. GET /health/metrics
5. GET /health/metrics/prometheus

Protected endpoints:

1. POST /analyze/unicode
2. POST /analyze/morphology
3. POST /analyze/semantics
4. POST /infer
5. POST /rule/evaluate
6. POST /manat/apply
7. POST /awareness/apply
8. GET /explain/{run_id}
9. GET /trace/{run_id}
10. All above available under /v1 prefix as well.

## 2.5 Transition Contract Rules

1. No layer may emit final decisions without upstream artifact references.
2. No majaz activation without a qareena artifact.
3. No rule finalization without evidence linkage.
4. No manat applies=true with unresolved missing features.
5. Suspend is mandatory under unresolved prerequisites.

## 2.6 Observability and SRE

1. Request correlation headers:
1. X-Request-ID
2. X-Trace-ID

2. Metrics:
1. JSON endpoint for internal quick diagnostics.
2. Prometheus endpoint for scraping and alerting.

3. Tracing:
1. OpenTelemetry instrumentation.
2. OTLP collector profile and Jaeger visualization.

4. Alerting and dashboards:
1. Alertmanager with webhook and Slack channels.
2. Grafana dashboard provisioning.

## 2.7 Security and Governance Controls

1. JWT authentication.
2. Role-based gate at endpoint level.
3. Rate limiting middleware.
4. CI checks:
1. ruff
2. mypy
3. bandit
4. pip-audit
5. pytest with coverage threshold

5. Branch protection policy files and automation script included.

## 2.8 Delivery Plan (Milestones)

Milestone A: L0-L5 hardening.

1. Deterministic transforms and richer confidence attribution.
2. Artifact completeness checks.

Milestone B: L6-L8 strict meaning layers.

1. Explicit truth type registry.
2. Qareena-gated majaz logic.

Milestone C: L9-L12 inference rigor.

1. Stronger mantuq/mafhum trace links.
2. Illa evidence structure and ranking basis.

Milestone D: L13-L14 application rigor.

1. Case model completeness scoring.
2. Formal suspend reasons taxonomy.

Milestone E: L15-L19 awareness optimization.

1. Deterministic and policy-driven awareness decisions.
2. Full reverse explainability from will to Unicode-linked evidence chain.

Milestone F: Enterprise release readiness.

1. Protected main enforcement with admin privileges.
2. Production secrets managed via secret provider.
3. Alert channels tested end-to-end.

## 2.9 Test Strategy

1. Unit tests per service and layer transitions.
2. Integration tests for endpoint chains.
3. E2E tests for full route and v1 route parity.
4. Regression fixtures for Arabic edge forms.
5. Explainability integrity tests (forward and reverse trace).

## 2.10 Definition of Done

The program is considered complete when:

1. L0-L19 transitions are implemented with strict artifact provenance.
2. explain and trace can reconstruct decision logic end-to-end.
3. CI and security gates pass consistently.
4. Branch protection is active on main with required checks and reviews.
5. Production observability and alerting channels are operational and validated.

---

## Appendix A: Program Decisions

1. Suspend is preferred over uncertain final judgment.
2. Evidence-linked reasoning is mandatory.
3. Layered meaning policy is non-optional.
4. Governance and observability are first-class architecture constraints.

## Appendix B: Implementation Notes

1. This document is intended for engineering execution and release governance.
2. Any deviation requires explicit versioned update of this document.